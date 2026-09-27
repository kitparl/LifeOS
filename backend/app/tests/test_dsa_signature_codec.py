import pytest
from app.modules.dsa.judge import codec
from app.modules.dsa.judge.signature import (
    ClassSpec,
    FunctionSpec,
    SignatureError,
    parse_spec,
    validate_expected,
    validate_input,
    validate_value,
)
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

INT32 = st.integers(min_value=-(2**31), max_value=2**31 - 1)
LEVEL_ORDER = st.lists(st.one_of(st.none(), INT32), max_size=127)

SUM = {"kind": "function", "name": "f", "params": [{"name": "nums", "type": "int[]"}], "returns": "int"}
DESIGN = {
    "kind": "class",
    "name": "Counter",
    "constructor": [{"name": "start", "type": "int"}],
    "methods": [
        {"name": "add", "params": [{"name": "x", "type": "int"}], "returns": "void"},
        {"name": "get", "params": [], "returns": "int"},
    ],
}


# ---------------------------------------------------------------- spec parsing


def test_parse_function_and_class():
    assert isinstance(parse_spec(SUM), FunctionSpec)
    assert isinstance(parse_spec(DESIGN), ClassSpec)


@pytest.mark.parametrize(
    "bad",
    [
        {**SUM, "returns": "float"},
        {**SUM, "params": [{"name": "x", "type": "set"}]},
        {**SUM, "name": "1bad"},
        {**SUM, "returns": "void"},  # void without mutates
        {**SUM, "returns": "void", "mutates": "missing"},
        {**SUM, "params": [{"name": "a", "type": "int"}, {"name": "a", "type": "int"}]},
        {**DESIGN, "methods": []},
        {**DESIGN, "methods": [{"name": "Counter", "params": [], "returns": "int"}]},
    ],
)
def test_parse_rejects_invalid_specs(bad):
    with pytest.raises(ValidationError):
        parse_spec(bad)


def test_mutates_must_name_array_param():
    spec = {
        "kind": "function",
        "name": "f",
        "params": [{"name": "x", "type": "int"}],
        "returns": "void",
        "mutates": "x",
    }
    with pytest.raises(ValidationError):
        parse_spec(spec)


# ---------------------------------------------------------------- value validation


@pytest.mark.parametrize(
    ("type_", "value"),
    [
        ("int", 5),
        ("long", 2**40),
        ("double", 1),
        ("double", 2.5),
        ("bool", False),
        ("string", ""),
        ("char", "x"),
        ("int[][]", [[1], []]),
        ("ListNode", [1, 2]),
        ("ListNode[]", [[1], []]),
        ("TreeNode", [1, None, 2]),
        ("TreeNode", []),
        ("void", None),
    ],
)
def test_valid_values(type_, value):
    validate_value(type_, value)


@pytest.mark.parametrize(
    ("type_", "value"),
    [
        ("int", True),
        ("int", 2**31),
        ("int", 1.5),
        ("long", 2**63),
        ("double", float("nan")),
        ("bool", 0),
        ("char", "ab"),
        ("string", None),
        ("int[]", [1, "2"]),
        ("TreeNode", [None, 1]),
        ("void", 0),
    ],
)
def test_invalid_values(type_, value):
    with pytest.raises(SignatureError):
        validate_value(type_, value)


def test_validate_input_and_expected_for_class():
    spec = parse_spec(DESIGN)
    data = {"ops": ["Counter", "add", "get"], "args": [[1], [2], []]}
    validate_input(spec, data)
    validate_expected(spec, [None, None, 3], data)
    with pytest.raises(SignatureError):
        validate_input(spec, {"ops": ["add"], "args": [[1]]})
    with pytest.raises(SignatureError):
        validate_input(spec, {"ops": ["Counter", "nope"], "args": [[1], []]})
    with pytest.raises(SignatureError):
        validate_expected(spec, [None, 1, 3], data)  # add is void


def test_validate_input_arity():
    with pytest.raises(SignatureError):
        validate_input(parse_spec(SUM), [[1], 2])


# ---------------------------------------------------------------- codec


def test_invoke_function_and_mutates():
    assert codec.invoke(SUM, lambda nums: sum(nums), [[1, 2, 3]]) == 6
    spec = {**SUM, "returns": "void", "mutates": "nums"}
    assert codec.invoke(spec, lambda nums: nums.reverse(), [[1, 2, 3]]) == [3, 2, 1]


def test_invoke_class():
    class Counter:
        def __init__(self, start):
            self.v = start

        def add(self, x):
            self.v += x

        def get(self):
            return self.v

    out = codec.invoke(DESIGN, Counter, {"ops": ["Counter", "add", "get"], "args": [[1], [2], []]})
    assert out == [None, None, 3]


def test_list_to_json_detects_cycle(monkeypatch):
    monkeypatch.setattr(codec, "MAX_NODES", 10)
    node = codec.ListNode(1)
    node.next = node
    with pytest.raises(ValueError):
        codec.list_to_json(node)


def test_double_must_be_finite():
    with pytest.raises(ValueError):
        codec.encode("double", float("inf"))


# PBT-02: round-trips
@given(st.lists(INT32, max_size=200))
def test_list_round_trip(values):
    assert codec.list_to_json(codec.list_from_json(values)) == values


@given(LEVEL_ORDER.filter(lambda v: not v or v[0] is not None))
def test_tree_round_trip_is_normalizing(values):
    once = codec.tree_to_json(codec.tree_from_json(values))
    assert codec.tree_to_json(codec.tree_from_json(once)) == once
    assert not once or once[-1] is not None


@given(st.lists(INT32, max_size=127))
def test_complete_tree_round_trip_is_exact(values):
    assert codec.tree_to_json(codec.tree_from_json(values)) == values


@given(st.lists(st.lists(INT32, max_size=20), max_size=20))
def test_nested_array_decode_encode_round_trip(values):
    assert codec.encode("int[][]", codec.decode("int[][]", values)) == values


@given(st.lists(st.text(max_size=5), max_size=20))
def test_string_array_round_trip(values):
    validate_value("string[]", values)
    assert codec.encode("string[]", codec.decode("string[]", values)) == values


# ---------------------------------------------------------------- links, mutate+return, depth 3

CYCLE = {
    "kind": "function",
    "name": "hasCycle",
    "params": [{"name": "head", "type": "ListNode"}, {"name": "pos", "type": "int"}],
    "returns": "bool",
    "links": [{"kind": "cycle", "list": "head", "pos": "pos"}],
}


def test_links_hide_params_and_validate_positions():
    spec = parse_spec(CYCLE)
    assert spec.hidden_params == {"pos"}
    validate_input(spec, [[1, 2], 1])
    validate_input(spec, [[], -1])
    with pytest.raises(SignatureError):
        validate_input(spec, [[1, 2], 2])


@pytest.mark.parametrize(
    "bad",
    [
        {**CYCLE, "links": [{"kind": "cycle", "list": "pos", "pos": "head"}]},  # wrong types
        {**CYCLE, "links": [{"kind": "cycle", "list": "head", "pos": "missing"}]},
        {**CYCLE, "links": [{"kind": "circular", "list": "head"}, {"kind": "cycle", "list": "head", "pos": "pos"}]},
        {**CYCLE, "circular_output": True},  # returns bool
        {
            "kind": "function",
            "name": "f",
            "params": [{"name": "shared", "type": "int[]"}],
            "returns": "int",
            "links": [{"kind": "join", "a": "shared", "b": "shared", "shared": "shared"}],
        },
    ],
)
def test_invalid_links(bad):
    with pytest.raises(ValidationError):
        parse_spec(bad)


def test_mutate_and_return_output_shape():
    spec = parse_spec(
        {
            "kind": "function",
            "name": "f",
            "params": [{"name": "nums", "type": "int[]"}],
            "returns": "int",
            "mutates": "nums",
        }
    )
    validate_expected(spec, [1, [5, 0]], [[5, 0]])
    with pytest.raises(SignatureError):
        validate_expected(spec, 1, [[5, 0]])


def test_depth_three_arrays():
    validate_value("int[][][]", [[[1], []], []])
    with pytest.raises(SignatureError):
        validate_value("int[][][]", [[1]])


def test_circular_output_requires_a_lap():
    head = codec.list_from_json([1, 2])
    with pytest.raises(ValueError):
        codec.circular_list_to_json(head)  # not circular
    head.next.next = head
    assert codec.circular_list_to_json(head) == [1, 2]
    assert codec.circular_list_to_json(None) == []


# PBT-02: link round-trips
@given(st.lists(INT32, max_size=60), st.lists(INT32, max_size=60), st.lists(INT32, max_size=60))
def test_join_builds_shared_nodes(a, b, shared):
    args = {"a": codec.list_from_json(a), "b": codec.list_from_json(b), "s": shared}
    hidden = codec.apply_links([{"kind": "join", "a": "a", "b": "b", "shared": "s"}], args)
    assert hidden == {"s"}
    assert codec.list_to_json(args["a"]) == a + shared
    assert codec.list_to_json(args["b"]) == b + shared
    tail_a, tail_b = args["a"], args["b"]
    for _ in range(len(a)):
        tail_a = tail_a.next
    for _ in range(len(b)):
        tail_b = tail_b.next
    assert tail_a is tail_b  # same nodes, not copies


@given(st.lists(INT32, min_size=1, max_size=60))
def test_circular_round_trip(values):
    args = {"h": codec.list_from_json(values)}
    codec.apply_links([{"kind": "circular", "list": "h"}], args)
    assert codec.circular_list_to_json(args["h"]) == values
