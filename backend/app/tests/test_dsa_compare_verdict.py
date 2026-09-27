import pytest
from app.modules.dsa.judge import compare
from app.modules.dsa.judge.compare import outputs_match
from app.modules.dsa.judge.verdict import (
    CaseResult,
    CompileOutcome,
    Grading,
    RunOutcome,
    Verdict,
    decide,
)
from hypothesis import given
from hypothesis import strategies as st

JSON_LEAF = st.one_of(st.none(), st.booleans(), st.integers(-1000, 1000), st.text(max_size=4))
JSON_VALUE = st.recursive(JSON_LEAF, lambda inner: st.lists(inner, max_size=5), max_leaves=30)
INT_MATRIX = st.lists(st.lists(st.integers(-50, 50), max_size=4), max_size=6)


# ---------------------------------------------------------------- compare


@pytest.mark.parametrize(
    ("mode", "expected", "actual", "match"),
    [
        ("exact", [1, 2], [1, 2], True),
        ("exact", [1, 2], [2, 1], False),
        ("exact", 2, 2.0, True),
        ("exact", True, 1, False),
        ("exact", [], None, False),
        ("exact", "a", ["a"], False),
        ("unordered", [1, 2, 2], [2, 1, 2], True),
        ("unordered", [1, 2], [1, 2, 2], False),
        ("unordered_nested", [[-1, 0, 1], [0, 0, 0]], [[0, 0, 0], [1, -1, 0]], True),
        ("unordered_nested", [[1, 2]], [[1, 3]], False),
        ("unordered_nested", [[1]], [1], False),
        ("float_tolerance", 0.1 + 0.2, 0.3, True),
        ("float_tolerance", [1.0, 2.000001], [1, 2], True),
        ("float_tolerance", 1.0, 1.1, False),
    ],
)
def test_outputs_match(mode, expected, actual, match):
    assert outputs_match(mode, expected, actual) is match


def test_checker_registry(monkeypatch):
    monkeypatch.setattr(compare, "CHECKERS", {})

    @compare.checker("any_permutation_of_input")
    def _perm(test_input, expected, actual):
        return sorted(test_input[0]) == sorted(actual)

    assert outputs_match("checker", None, [3, 1, 2], checker_name="any_permutation_of_input", test_input=[[1, 2, 3]])
    with pytest.raises(ValueError):
        outputs_match("checker", None, [], checker_name="missing")


def test_unknown_mode():
    with pytest.raises(ValueError):
        outputs_match("fuzzy", 1, 1)


# PBT-03: invariants
@given(JSON_VALUE)
def test_exact_is_reflexive(value):
    assert outputs_match("exact", value, value)
    assert outputs_match("float_tolerance", value, value)


@given(st.lists(JSON_VALUE, max_size=8), st.randoms())
def test_unordered_ignores_shuffle(values, rnd):
    shuffled = list(values)
    rnd.shuffle(shuffled)
    assert outputs_match("unordered", values, shuffled)


@given(INT_MATRIX, st.randoms())
def test_unordered_nested_ignores_inner_and_outer_order(values, rnd):
    shuffled = [rnd.sample(row, len(row)) for row in values]
    rnd.shuffle(shuffled)
    assert outputs_match("unordered_nested", values, shuffled)


@given(JSON_VALUE, JSON_VALUE)
def test_exact_is_symmetric(a, b):
    assert outputs_match("exact", a, b) == outputs_match("exact", b, a)


# ---------------------------------------------------------------- verdict


def _grading(n: int, expected=None, limit=100.0, mode="exact") -> Grading:
    return Grading(
        inputs=[[i] for i in range(n)], expected=expected or list(range(n)), per_test_limit_ms=limit, compare_mode=mode
    )


def _ok(i, out=None, ms=1.0) -> CaseResult:
    return CaseResult(i, ok=True, out=i if out is None else out, ms=ms)


def test_accepted_reports_max_runtime_and_memory():
    run = RunOutcome("Accepted", memory_kb=2048, cases=[_ok(0, ms=3.4), _ok(1, ms=7.6)])
    out = decide(None, run, _grading(2))
    assert out.verdict == Verdict.ACCEPTED
    assert (out.passed, out.total, out.runtime_ms, out.memory_kb, out.failed_case) == (2, 2, 8, 2048, None)


def test_compile_error():
    out = decide(CompileOutcome(False, "main.cpp:1: error"), None, _grading(3))
    assert out.verdict == Verdict.COMPILE_ERROR and out.message == "main.cpp:1: error" and out.total == 3


def test_wrong_answer_is_first_failure():
    run = RunOutcome("Accepted", cases=[_ok(0), _ok(1, out=99), CaseResult(2, ok=False, err="boom")])
    out = decide(None, run, _grading(3))
    assert out.verdict == Verdict.WRONG_ANSWER and out.failed_case == 2 and out.passed == 1


def test_runtime_error_line():
    run = RunOutcome("Accepted", cases=[CaseResult(0, ok=False, err="IndexError: x")])
    out = decide(None, run, _grading(1))
    assert out.verdict == Verdict.RUNTIME_ERROR and out.message == "IndexError: x"


def test_per_test_time_limit():
    run = RunOutcome("Accepted", cases=[_ok(0), _ok(1, ms=150)])
    assert decide(None, run, _grading(2)).verdict == Verdict.TIME_LIMIT


@pytest.mark.parametrize(
    ("status", "verdict"),
    [
        ("Time Limit Exceeded", Verdict.TIME_LIMIT),
        ("Memory Limit Exceeded", Verdict.MEMORY_LIMIT),
        ("Signalled", Verdict.RUNTIME_ERROR),
        ("Nonzero Exit Status", Verdict.RUNTIME_ERROR),
        ("Accepted", Verdict.RUNTIME_ERROR),
    ],
)
def test_missing_line_takes_sandbox_status(status, verdict):
    run = RunOutcome(status, cases=[_ok(0)])
    out = decide(None, run, _grading(3))
    assert out.verdict == verdict and out.failed_case == 2 and out.passed == 1


def test_sandbox_failure_after_all_lines():
    run = RunOutcome("Memory Limit Exceeded", cases=[_ok(0), _ok(1)])
    assert decide(None, run, _grading(2)).verdict == Verdict.MEMORY_LIMIT


@pytest.mark.parametrize("status", ["Internal Error", "File Error", "Dangerous Syscall"])
def test_unexpected_sandbox_status_is_internal_error(status):
    run = RunOutcome(status, cases=[_ok(0)])
    assert decide(None, run, _grading(1)).verdict == Verdict.INTERNAL_ERROR


def test_custom_inputs_are_not_compared():
    grading = Grading(inputs=[[0], [5]], expected=[0, None], per_test_limit_ms=100, compare_mode="exact")
    run = RunOutcome("Accepted", cases=[_ok(0), _ok(1, out=123)])
    out = decide(None, run, grading)
    assert out.verdict == Verdict.ACCEPTED and out.passed == 1
    assert out.cases[1].passed is None and out.cases[1].actual == 123


# PBT-03: never Accepted when any test fails
@given(
    st.lists(st.sampled_from(["pass", "wrong", "error", "slow", "missing"]), min_size=1, max_size=10),
    st.sampled_from(["Accepted", "Time Limit Exceeded", "Memory Limit Exceeded", "Signalled", "Internal Error"]),
)
def test_never_accepted_when_any_case_fails(kinds, status):
    cases = []
    for i, kind in enumerate(kinds):
        if kind == "missing":
            break
        if kind == "pass":
            cases.append(_ok(i))
        elif kind == "wrong":
            cases.append(_ok(i, out=-1))
        elif kind == "error":
            cases.append(CaseResult(i, ok=False, err="e"))
        else:
            cases.append(_ok(i, ms=10_000))
    out = decide(None, RunOutcome(status, cases=cases), _grading(len(kinds)))
    all_passed = all(k == "pass" for k in kinds) and status == "Accepted"
    assert (out.verdict == Verdict.ACCEPTED) == all_passed
    assert out.passed <= out.total


@pytest.mark.parametrize(
    ("name", "expected", "actual", "match"),
    [
        ("k_prefix", [2, [1, 2, 9]], [2, [1, 2, 0]], True),
        ("k_prefix", [2, [1, 2, 9]], [2, [2, 1, 0]], False),
        ("k_prefix", [2, [1, 2]], [3, [1, 2, 3]], False),
        ("k_prefix", [2, [1, 2]], [2, [1]], False),
        ("k_prefix", [2, [1, 2]], 2, False),
        ("k_prefix_unordered", [2, [1, 2, 9]], [2, [2, 1, 7]], True),
        ("k_prefix_unordered", [0, [5]], [0, [7]], True),
    ],
)
def test_k_prefix_checkers(name, expected, actual, match):
    assert outputs_match("checker", expected, actual, checker_name=name) is match


@pytest.mark.parametrize(
    ("test_input", "actual", "match"),
    [
        ([[3, 4, 1], 2], [3, 4, 1, 2], True),
        ([[3, 4, 1], 2], [3, 4, 2, 1], False),
        ([[3, 3, 3], 5], [3, 5, 3, 3], True),
        ([[3, 3, 3], 5], [3, 3, 3, 5], True),
        ([[], 1], [1], True),
        ([[1], 0], [1, 0], True),
        ([[1, 3], 2], [1, 3], False),
    ],
)
def test_sorted_circular_insert_checker(test_input, actual, match):
    assert outputs_match("checker", None, actual, checker_name="sorted_circular_insert", test_input=test_input) is match


@pytest.mark.parametrize(
    ("name", "test_input", "expected", "actual", "match"),
    [
        ("happy_string", [1, 1, 7], "ccaccbcc", "ccbccacc", True),
        ("happy_string", [1, 1, 7], "ccaccbcc", "cccaccbc", False),
        ("happy_string", [7, 1, 0], "aabaa", "aabaa", True),
        ("happy_string", [7, 1, 0], "aabaa", "aaba", False),
        ("reorganize_string", ["aab"], "aba", "aba", True),
        ("reorganize_string", ["aab"], "aba", "aab", False),
        ("reorganize_string", ["aaab"], "", "", True),
        ("reorganize_string", ["aaab"], "", "abaa", False),
        ("sort_by_frequency", ["tree"], "eert", "eetr", True),
        ("sort_by_frequency", ["tree"], "eert", "eter", False),
        ("sort_by_frequency", ["Aabb"], "bbAa", "bbaA", True),
        ("top_k_frequent", [[1, 1, 1, 2, 2, 3], 2], [1, 2], [2, 1], True),
        ("top_k_frequent", [[1, 1, 1, 2, 2, 3], 2], [1, 2], [1, 3], False),
        ("top_k_frequent", [[1, 2, 3], 1], [1], [3], True),
        ("k_closest_points", [[[1, 3], [-2, 2], [2, -2]], 1], [[-2, 2]], [[2, -2]], True),
        ("k_closest_points", [[[1, 3], [-2, 2]], 1], [[-2, 2]], [[1, 3]], False),
        ("k_closest_points", [[[1, 1]], 1], [[1, 1]], [[2, 2]], False),
        ("k_smallest_pairs", [[1, 1, 2], [1, 2, 3], 2], [[1, 1], [1, 1]], [[1, 1], [1, 1]], True),
        ("k_smallest_pairs", [[1, 2], [3], 1], [[1, 3]], [[2, 2]], False),
        ("k_smallest_pairs", [[1, 7], [2, 4], 2], [[1, 2], [1, 4]], [[1, 4], [1, 2]], True),
        ("k_subsequence_max_sum", [[3, 4, 3, 3], 2], [3, 4], [4, 3], True),
        ("k_subsequence_max_sum", [[3, 4, 3, 3], 2], [3, 4], [3, 3], False),
        ("k_subsequence_max_sum", [[2, 1, 3, 3], 2], [3, 3], [3, 3], True),
    ],
)
def test_b2_checkers(name, test_input, expected, actual, match):
    assert outputs_match("checker", expected, actual, checker_name=name, test_input=test_input) is match


@pytest.mark.parametrize(("nums", "actual", "match"), [([1, 2, 1, 3, 5, 6, 4], 1, True), ([1, 2, 1, 3, 5, 6, 4], 5, True), ([1, 2, 1, 3, 5, 6, 4], 4, False), ([1], 0, True), ([2, 1], 0, True), ([2, 1], 2, False)])
def test_peak_index_checker(nums, actual, match):
    assert outputs_match("checker", None, actual, checker_name="peak_index", test_input=[nums]) is match


@pytest.mark.parametrize(
    ("gas", "cost", "expected", "actual", "match"),
    [([1, 2, 3, 4, 5], [3, 4, 5, 1, 2], 3, 3, True), ([1, 1], [1, 1], 1, 0, True), ([2, 3, 4], [3, 4, 3], -1, -1, True), ([2, 3, 4], [3, 4, 3], -1, 0, False), ([1, 2, 3, 4, 5], [3, 4, 5, 1, 2], 3, 0, False)],
)
def test_gas_station_checker(gas, cost, expected, actual, match):
    assert outputs_match("checker", expected, actual, checker_name="gas_station_start", test_input=[gas, cost]) is match


@pytest.mark.parametrize(
    ("name", "test_input", "expected", "actual", "match"),
    [
        ("alien_order", [["wrt", "wrf", "er", "ett", "rftt"]], "wertf", "wertf", True),
        ("alien_order", [["z", "x"]], "zx", "xz", False),
        ("alien_order", [["ab", "adc"]], "abcd", "cabd", True),
        ("alien_order", [["abc", "ab"]], "", "abc", False),
        ("compilation_order", [[["B", "A"], ["C", "B"]]], ["A", "B", "C"], ["A", "B", "C"], True),
        ("compilation_order", [[["B", "A"], ["C", "A"]]], ["A", "B", "C"], ["A", "C", "B"], True),
        ("compilation_order", [[["B", "A"], ["A", "B"]]], [], ["A", "B"], False),
        ("course_order", [2, [[1, 0]]], [0, 1], [0, 1], True),
        ("course_order", [3, []], [0, 1, 2], [2, 0, 1], True),
        ("course_order", [2, [[1, 0]]], [0, 1], [1, 0], False),
        ("sort_items_groups", [4, 2, [0, -1, 0, 1], [[], [], [], []]], [0, 2, 1, 3], [1, 2, 0, 3], True),
        ("sort_items_groups", [4, 2, [0, -1, 0, 1], [[], [], [], []]], [0, 2, 1, 3], [0, 1, 2, 3], False),
        ("matrix_conditions", [2, [[1, 2]], [[2, 1]]], [[0, 1], [2, 0]], [[0, 1], [2, 0]], True),
        ("matrix_conditions", [2, [[1, 2]], [[2, 1]]], [[0, 1], [2, 0]], [[1, 0], [0, 2]], False),
        ("parity_ii", [[4, 2, 5, 7]], [4, 5, 2, 7], [2, 7, 4, 5], True),
        ("parity_ii", [[4, 2, 5, 7]], [4, 5, 2, 7], [5, 4, 7, 2], False),
        ("shortest_common_supersequence", ["abac", "cab"], "cabac", "cabac", True),
        ("shortest_common_supersequence", ["abac", "cab"], "cabac", "abcab", False),
    ],
)
def test_b4_checkers(name, test_input, expected, actual, match):
    assert outputs_match("checker", expected, actual, checker_name=name, test_input=test_input) is match


@pytest.mark.parametrize(
    ("test_input", "expected", "actual", "match"),
    [
        ([[[3, 1], [2, 5]]], [[2, 1], [1, 2]], [[2, 1], [1, 2]], True),
        ([[[3, 1], [2, 5]]], [[2, 1], [1, 2]], [[2, 1], [1, 3]], False),  # not minimal
        ([[[3, 1], [2, 5]]], [[2, 1], [1, 2]], [[1, 2], [2, 1]], False),  # row order flipped
        ([[[10]]], [[1]], [[0]], False),  # must be positive
    ],
)
def test_min_max_grid_checker(test_input, expected, actual, match):
    assert outputs_match("checker", expected, actual, checker_name="min_max_grid", test_input=test_input) is match


@pytest.mark.parametrize(
    ("test_input", "expected", "actual", "match"),
    [
        (["lee(t(c)o)de)"], "lee(t(c)o)de", "lee(t(co)de)", True),
        (["lee(t(c)o)de)"], "lee(t(c)o)de", "lee(t(c)ode)", True),
        (["lee(t(c)o)de)"], "lee(t(c)o)de", "leet(c)ode", False),  # removed more than needed
        (["lee(t(c)o)de)"], "lee(t(c)o)de", "lee)t(c(o)de", False),  # not a subsequence / unbalanced
        (["a)b(c)d"], "ab(c)d", "ab(cd)", False),  # not a subsequence of s
        (["))(("], "", "", True),
    ],
)
def test_min_remove_parens_checker(test_input, expected, actual, match):
    assert outputs_match("checker", expected, actual, checker_name="min_remove_parens", test_input=test_input) is match


@pytest.mark.parametrize(
    ("test_input", "expected", "actual", "match"),
    [
        ([[-10, -3, 0, 5, 9]], [0, -3, 9, -10, None, 5], [0, -3, 9, -10, None, 5], True),
        ([[-10, -3, 0, 5, 9]], [0, -3, 9, -10, None, 5], [0, -10, 5, None, -3, None, 9], True),
        ([[-10, -3, 0, 5, 9]], [0, -3, 9, -10, None, 5], [-10, None, -3, None, 0, None, 5, None, 9], False),  # a chain
        ([[1, 3]], [3, 1], [1, None, 3], True),
        ([[1, 3]], [3, 1], [3, None, 1], False),  # not a BST
        ([[]], [], [], True),
    ],
)
def test_balanced_bst_checker(test_input, expected, actual, match):
    assert outputs_match("checker", expected, actual, checker_name="balanced_bst", test_input=test_input) is match


@pytest.mark.parametrize(
    ("test_input", "expected", "actual", "match"),
    [
        (["cba", "abcd"], "cbad", "cbad", True),
        (["cba", "abcd"], "cbad", "dcba", True),  # letters outside `order` may go anywhere
        (["cba", "abcd"], "cbad", "abcd", False),
        (["cba", "abcd"], "cbad", "cbaa", False),  # not a permutation of s
    ],
)
def test_custom_sort_checker(test_input, expected, actual, match):
    assert outputs_match("checker", expected, actual, checker_name="custom_sort", test_input=test_input) is match


_ALL_ONE_OPS = {"ops": ["AllOne", "inc", "inc", "getMaxKey", "getMinKey", "dec", "getMaxKey"], "args": [[], ["a"], ["b"], [], [], ["a"], []]}


@pytest.mark.parametrize(
    ("actual", "match"),
    [
        ([None, None, None, "a", "b", None, "b"], True),
        ([None, None, None, "b", "a", None, "b"], True),  # ties: either key is fine
        ([None, None, None, "a", "b", None, "a"], False),  # "a" was removed
        ([None, None, None, "a", "b", None, ""], False),
    ],
)
def test_all_one_checker(actual, match):
    expected = [None, None, None, "a", "a", None, "b"]
    assert outputs_match("checker", expected, actual, checker_name="all_one", test_input=_ALL_ONE_OPS) is match


@pytest.mark.parametrize(
    ("actual", "match"),
    [("bab", True), ("aba", True), ("ab", False), ("bcb", False), ("abc", False)],
)
def test_palindrome_substring_checker(actual, match):
    assert outputs_match("checker", "bab", actual, checker_name="palindrome_substring", test_input=["babad"]) is match
