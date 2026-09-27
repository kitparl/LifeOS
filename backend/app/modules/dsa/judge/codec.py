"""JSON <-> Python values for problem signatures, and invoking a solution on one test input.

Standard library only and self-contained: the content build imports it to compute expected
outputs, and the Python driver embeds this file's source verbatim, so reference and user code
see identical decoding. `spec` here is the plain signature dict (see signature.py).
"""

import math

MAX_NODES = 200_000


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def list_from_json(values):
    dummy = ListNode()
    tail = dummy
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def list_to_json(head):
    out = []
    while head is not None:
        if len(out) >= MAX_NODES:
            raise ValueError("linked list too long or has a cycle")
        out.append(head.val)
        head = head.next
    return out


def circular_list_to_json(head):
    """Values of a circular list, one lap starting at `head`."""
    out = []
    node = head
    while node is not None:
        if len(out) >= MAX_NODES:
            raise ValueError("circular list too long")
        out.append(node.val)
        node = node.next
        if node is head:
            return out
    if out:
        raise ValueError("expected a circular list (the tail should point back to the head)")
    return out


def _append(head, tail):
    if head is None:
        return tail
    node = head
    while node.next is not None:
        node = node.next
    node.next = tail
    return head


def _nodes(head):
    out = []
    while head is not None:
        out.append(head)
        head = head.next
    return out


def apply_links(links, args):
    """Build cycles / circular lists / shared tails in the decoded `args` dict; returns hidden names."""
    hidden = set()
    for link in links:
        kind = link["kind"]
        if kind == "cycle":
            hidden.add(link["pos"])
            nodes, pos = _nodes(args[link["list"]]), args[link["pos"]]
            if nodes and pos >= 0:
                nodes[-1].next = nodes[pos]
        elif kind == "circular":
            nodes = _nodes(args[link["list"]])
            if nodes:
                nodes[-1].next = nodes[0]
        else:
            hidden.add(link["shared"])
            shared = list_from_json(args[link["shared"]])
            args[link["a"]] = _append(args[link["a"]], shared)
            args[link["b"]] = _append(args[link["b"]], shared)
    return hidden


def tree_from_json(values):
    if not values:
        return None
    nodes = [None if v is None else TreeNode(v) for v in values]
    children = iter(nodes[1:])
    for node in nodes:
        if node is None:
            continue
        node.left = next(children, None)
        node.right = next(children, None)
    return nodes[0]


def tree_to_json(root):
    out = []
    queue = [root]
    i = 0
    while i < len(queue):
        node = queue[i]
        i += 1
        if node is None:
            out.append(None)
            continue
        if len(out) >= MAX_NODES:
            raise ValueError("tree too large or has a cycle")
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def decode(type_, value):
    if type_ == "ListNode":
        return list_from_json(value)
    if type_ == "ListNode[]":
        return [list_from_json(v) for v in value]
    if type_ == "TreeNode":
        return tree_from_json(value)
    if type_.endswith("[]"):
        inner = type_[:-2]
        return [decode(inner, v) for v in value]
    if type_ == "double":
        return float(value)
    return value


def encode(type_, value, circular=False):
    if type_ == "void":
        return None
    to_json = circular_list_to_json if circular else list_to_json
    if type_ == "ListNode":
        return to_json(value)
    if type_ == "ListNode[]":
        return [to_json(v) for v in value]
    if type_ == "TreeNode":
        return tree_to_json(value)
    if type_.endswith("[]"):
        if isinstance(value, str) and type_ == "char[]":
            return list(value)
        inner = type_[:-2]
        return [encode(inner, v) for v in value]
    if type_ == "double":
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("result is not a finite number")
        return value
    if type_ in ("int", "long") and isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def invoke(spec, target, test_input):
    """Run `target` on one decoded test input and return the JSON-encodable output.

    Function specs: `target` is the callable. Class specs: `target` is the class, and the
    output is one value per op (null for the constructor and void methods).
    """
    if spec["kind"] == "function":
        params = spec["params"]
        args = {p["name"]: decode(p["type"], a) for p, a in zip(params, test_input, strict=True)}
        hidden = apply_links(spec.get("links") or [], args)
        result = target(*[args[p["name"]] for p in params if p["name"] not in hidden])
        mutates = spec.get("mutates")
        if mutates:
            mutated = encode(next(p["type"] for p in params if p["name"] == mutates), args[mutates])
            return mutated if spec["returns"] == "void" else [encode(spec["returns"], result), mutated]
        return encode(spec["returns"], result, spec.get("circular_output", False))

    methods = {m["name"]: m for m in spec["methods"]}
    ops, all_args = test_input["ops"], test_input["args"]
    ctor_args = [decode(p["type"], a) for p, a in zip(spec["constructor"], all_args[0], strict=True)]
    obj = target(*ctor_args)
    out = [None]
    for op, op_args in zip(ops[1:], all_args[1:], strict=True):
        method = methods[op]
        args = [decode(p["type"], a) for p, a in zip(method["params"], op_args, strict=True)]
        out.append(encode(method["returns"], getattr(obj, op)(*args)))
    return out
