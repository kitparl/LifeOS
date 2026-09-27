"""Problem signatures: what the user implements, and the JSON shape of every test value.

Types: scalars (`int`, `long`, `double`, `bool`, `string`, `char`), their `[]`, `[][]` and `[][][]`
arrays, `ListNode`, `ListNode[]`, `TreeNode`; `void` is a return type only (pair it with `mutates`).
Class problems ("design X") are driven by an operation sequence.

Function specs may also declare:
- `mutates`: an array param changed in place. With `returns: "void"` the output is that array;
  with a value return the output is `[returned, mutated_array]` (e.g. "remove in place, return k").
- `links`: pointer structures built from hidden params before the call (see Link below), and
  `circular_output` when a returned list (or each list) is circular.
"""

from __future__ import annotations

import math
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter, model_validator

SCALAR_TYPES = ("int", "long", "double", "bool", "string", "char")
NODE_TYPES = ("ListNode", "ListNode[]", "TreeNode")
VALUE_TYPES = frozenset([*SCALAR_TYPES, *(t + "[]" * depth for t in SCALAR_TYPES for depth in (1, 2, 3)), *NODE_TYPES])
RETURN_TYPES = VALUE_TYPES | {"void"}

INT32 = (-(2**31), 2**31 - 1)
INT64 = (-(2**63), 2**63 - 1)

_IDENT = r"^[A-Za-z_][A-Za-z0-9_]{0,39}$"

Identifier = Annotated[str, Field(pattern=_IDENT)]


class SignatureError(ValueError):
    """A value or spec does not match the declared signature."""


class Param(BaseModel):
    name: Identifier
    type: str

    @model_validator(mode="after")
    def _known_type(self) -> Param:
        if self.type not in VALUE_TYPES:
            raise ValueError(f"unknown param type {self.type!r}")
        return self


class Method(BaseModel):
    name: Identifier
    params: list[Param] = Field(default_factory=list, max_length=8)
    returns: str

    @model_validator(mode="after")
    def _known_return(self) -> Method:
        if self.returns not in RETURN_TYPES:
            raise ValueError(f"unknown return type {self.returns!r}")
        return self


class CycleLink(BaseModel):
    """Tail of `list` points back to the node at index `pos` (hidden int param; -1 = no cycle)."""

    kind: Literal["cycle"]
    list: Identifier
    pos: Identifier


class CircularLink(BaseModel):
    """Tail of `list` points back to its head."""

    kind: Literal["circular"]
    list: Identifier


class JoinLink(BaseModel):
    """`shared` (hidden int[] param) becomes one run of nodes appended to both `a` and `b`."""

    kind: Literal["join"]
    a: Identifier
    b: Identifier
    shared: Identifier


Link = Annotated[CycleLink | CircularLink | JoinLink, Field(discriminator="kind")]


class FunctionSpec(BaseModel):
    kind: Literal["function"] = "function"
    name: Identifier
    params: list[Param] = Field(min_length=1, max_length=8)
    returns: str
    mutates: Identifier | None = None
    links: list[Link] = Field(default_factory=list, max_length=2)
    circular_output: bool = False

    @model_validator(mode="after")
    def _consistent(self) -> FunctionSpec:
        if self.returns not in RETURN_TYPES:
            raise ValueError(f"unknown return type {self.returns!r}")
        names = [p.name for p in self.params]
        if len(set(names)) != len(names):
            raise ValueError("duplicate param names")
        if self.mutates is not None:
            param = next((p for p in self.params if p.name == self.mutates), None)
            if param is None or not param.type.endswith("[]") or param.type == "ListNode[]":
                raise ValueError("mutates must name an array param")
        elif self.returns == "void":
            raise ValueError("returns 'void' requires mutates")
        self._check_links()
        if self.circular_output and self.returns not in ("ListNode", "ListNode[]"):
            raise ValueError("circular_output requires a ListNode or ListNode[] return")
        return self

    def _check_links(self) -> None:
        types = {p.name: p.type for p in self.params}
        claimed: list[str] = []
        for link in self.links:
            if isinstance(link, CycleLink):
                wanted = {link.list: "ListNode", link.pos: "int"}
            elif isinstance(link, CircularLink):
                wanted = {link.list: "ListNode"}
            else:
                wanted = {link.a: "ListNode", link.b: "ListNode", link.shared: "int[]"}
            for name, type_ in wanted.items():
                if types.get(name) != type_:
                    raise ValueError(f"link {link.kind!r}: param {name!r} must be {type_}")
            claimed += list(wanted)
        if len(set(claimed)) != len(claimed):
            raise ValueError("a param is used by more than one link")
        if self.mutates is not None and self.mutates in self.hidden_params:
            raise ValueError("a hidden param cannot be mutated")
        if len(self.hidden_params) == len(self.params):
            raise ValueError("at least one param must be visible")

    @property
    def hidden_params(self) -> set[str]:
        """Params that only describe test structure; they are not passed to the user's function."""
        hidden = set()
        for link in self.links:
            if isinstance(link, CycleLink):
                hidden.add(link.pos)
            elif isinstance(link, JoinLink):
                hidden.add(link.shared)
        return hidden

    def param_type(self, name: str) -> str:
        return next(p.type for p in self.params if p.name == name)


class ClassSpec(BaseModel):
    kind: Literal["class"] = "class"
    name: Identifier
    constructor: list[Param] = Field(default_factory=list, max_length=8)
    methods: list[Method] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def _unique_methods(self) -> ClassSpec:
        names = [m.name for m in self.methods]
        if len(set(names)) != len(names):
            raise ValueError("duplicate method names")
        if self.name in names:
            raise ValueError("a method cannot share the class name")
        return self

    def method(self, name: str) -> Method | None:
        return next((m for m in self.methods if m.name == name), None)


SignatureSpec = Annotated[FunctionSpec | ClassSpec, Field(discriminator="kind")]
_SPEC_ADAPTER: TypeAdapter[FunctionSpec | ClassSpec] = TypeAdapter(SignatureSpec)


def parse_spec(data: object) -> FunctionSpec | ClassSpec:
    """Validate a stored/submitted signature dict. Raises pydantic.ValidationError."""
    return _SPEC_ADAPTER.validate_python(data)


def validate_value(type_: str, value: object, *, path: str = "value") -> None:
    """Raise SignatureError unless `value` is valid JSON data for `type_`."""
    if type_ == "void":
        if value is not None:
            raise SignatureError(f"{path}: expected null")
        return
    if type_.endswith("[]") and type_ not in ("ListNode[]",):
        if not isinstance(value, list):
            raise SignatureError(f"{path}: expected an array")
        inner = type_[:-2]
        for i, item in enumerate(value):
            validate_value(inner, item, path=f"{path}[{i}]")
        return
    if type_ == "ListNode":
        validate_value("int[]", value, path=path)
        return
    if type_ == "ListNode[]":
        validate_value("int[][]", value, path=path)
        return
    if type_ == "TreeNode":
        _validate_tree(value, path)
        return
    _validate_scalar(type_, value, path)


def _validate_scalar(type_: str, value: object, path: str) -> None:
    if type_ in ("int", "long"):
        lo, hi = INT32 if type_ == "int" else INT64
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise SignatureError(f"{path}: expected {type_}")
    elif type_ == "double":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise SignatureError(f"{path}: expected a finite number")
    elif type_ == "bool":
        if not isinstance(value, bool):
            raise SignatureError(f"{path}: expected true/false")
    elif type_ == "string":
        if not isinstance(value, str):
            raise SignatureError(f"{path}: expected a string")
    elif type_ == "char":
        if not isinstance(value, str) or len(value) != 1:
            raise SignatureError(f"{path}: expected a single character")
    else:
        raise SignatureError(f"{path}: unknown type {type_!r}")


def _validate_tree(value: object, path: str) -> None:
    if not isinstance(value, list):
        raise SignatureError(f"{path}: expected a level-order array")
    if value and value[0] is None:
        raise SignatureError(f"{path}: root cannot be null")
    for i, item in enumerate(value):
        if item is not None:
            _validate_scalar("int", item, f"{path}[{i}]")


def validate_input(spec: FunctionSpec | ClassSpec, data: object) -> None:
    """Validate one test input: positional args (function) or {"ops", "args"} (class)."""
    if isinstance(spec, FunctionSpec):
        if not isinstance(data, list) or len(data) != len(spec.params):
            raise SignatureError(f"expected {len(spec.params)} argument(s)")
        for param, arg in zip(spec.params, data, strict=True):
            validate_value(param.type, arg, path=param.name)
        _validate_links(spec, dict(zip((p.name for p in spec.params), data, strict=True)))
        return
    if not isinstance(data, dict) or set(data) != {"ops", "args"}:
        raise SignatureError('expected {"ops": [...], "args": [...]}')
    ops, args = data["ops"], data["args"]
    if not isinstance(ops, list) or not isinstance(args, list) or len(ops) != len(args) or not ops:
        raise SignatureError("ops and args must be non-empty arrays of equal length")
    if ops[0] != spec.name:
        raise SignatureError(f"the first op must be {spec.name!r}")
    for i, (op, op_args) in enumerate(zip(ops, args, strict=True)):
        params = spec.constructor if i == 0 else _method_params(spec, op, i)
        if not isinstance(op_args, list) or len(op_args) != len(params):
            raise SignatureError(f"ops[{i}]: expected {len(params)} argument(s)")
        for param, arg in zip(params, op_args, strict=True):
            validate_value(param.type, arg, path=f"ops[{i}].{param.name}")


def _validate_links(spec: FunctionSpec, args: dict[str, object]) -> None:
    for link in spec.links:
        if isinstance(link, CycleLink):
            size, pos = len(args[link.list]), args[link.pos]  # type: ignore[arg-type]
            if pos != -1 and not 0 <= pos < size:  # type: ignore[operator]
                raise SignatureError(f"{link.pos}: must be -1 or a valid index into {link.list}")


def _method_params(spec: ClassSpec, op: object, index: int) -> list[Param]:
    method = spec.method(op) if isinstance(op, str) else None
    if method is None:
        raise SignatureError(f"ops[{index}]: unknown method {op!r}")
    return method.params


def validate_expected(spec: FunctionSpec | ClassSpec, data: object, test_input: object) -> None:
    """Validate an expected output against the signature (and, for classes, the op sequence)."""
    if isinstance(spec, FunctionSpec):
        if spec.mutates is not None and spec.returns != "void":
            if not isinstance(data, list) or len(data) != 2:
                raise SignatureError("expected [returned value, mutated array]")
            validate_value(spec.returns, data[0], path="expected[0]")
            validate_value(spec.param_type(spec.mutates), data[1], path="expected[1]")
        else:
            validate_value(spec.param_type(spec.mutates) if spec.mutates else spec.returns, data, path="expected")
        return
    ops = test_input["ops"]  # type: ignore[index]
    if not isinstance(data, list) or len(data) != len(ops):
        raise SignatureError("expected one output per op")
    if data[0] is not None:
        raise SignatureError("expected[0] (constructor) must be null")
    for i in range(1, len(ops)):
        method = spec.method(ops[i])
        assert method is not None  # validate_input ran first
        validate_value(method.returns, data[i], path=f"expected[{i}]")
