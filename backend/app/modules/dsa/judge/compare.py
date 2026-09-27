"""Output comparison. The backend compares; drivers only report what the user's code returned.

Modes:
  exact             deep equality (bools are not numbers; 2 == 2.0)
  unordered         top-level list order ignored
  unordered_nested  every inner list sorted, then the outer list (e.g. 3Sum triplets, subsets)
  float_tolerance   numbers within 1e-5 absolute or relative
  checker           a named trusted function (test_input, expected, actual) -> bool, for problems
                    with several valid answers; register it in CHECKERS with @checker("name").
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from typing import Literal

from app.modules.dsa.judge import codec

CompareMode = Literal["exact", "unordered", "unordered_nested", "float_tolerance", "checker"]
COMPARE_MODES: tuple[str, ...] = ("exact", "unordered", "unordered_nested", "float_tolerance", "checker")
FLOAT_TOLERANCE = 1e-5

Checker = Callable[[object, object, object], bool]
CHECKERS: dict[str, Checker] = {}


def checker(name: str) -> Callable[[Checker], Checker]:
    def register(fn: Checker) -> Checker:
        CHECKERS[name] = fn
        return fn

    return register


def outputs_match(
    mode: str,
    expected: object,
    actual: object,
    *,
    checker_name: str | None = None,
    test_input: object = None,
) -> bool:
    if mode == "exact":
        return _equal(expected, actual)
    if mode == "unordered":
        return _is_list(expected, actual) and _equal(_sorted(expected), _sorted(actual))
    if mode == "unordered_nested":
        if not _is_list(expected, actual):
            return False
        if not all(isinstance(x, list) for x in (*expected, *actual)):
            return False
        return _equal(_sorted([_sorted(x) for x in expected]), _sorted([_sorted(x) for x in actual]))
    if mode == "float_tolerance":
        return _close(expected, actual)
    if mode == "checker":
        fn = CHECKERS.get(checker_name or "")
        if fn is None:
            raise ValueError(f"unknown checker {checker_name!r}")
        return bool(fn(test_input, expected, actual))
    raise ValueError(f"unknown compare mode {mode!r}")


def _is_list(*values: object) -> bool:
    return all(isinstance(v, list) for v in values)


def _is_number(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _equal(a: object, b: object) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if _is_number(a) or _is_number(b):
        return _is_number(a) and _is_number(b) and a == b
    if isinstance(a, list) or isinstance(b, list):
        return _is_list(a, b) and len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b, strict=True))
    return type(a) is type(b) and a == b


def _close(a: object, b: object) -> bool:
    if _is_number(a) and _is_number(b):
        return math.isclose(a, b, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE)
    if isinstance(a, list) or isinstance(b, list):
        return _is_list(a, b) and len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b, strict=True))
    return _equal(a, b)


def _canon(value: object) -> str:
    """Sort key where 2 and 2.0 collide and true/1 do not."""

    def norm(v: object) -> object:
        if isinstance(v, float) and v.is_integer():
            return int(v)
        if isinstance(v, list):
            return [norm(x) for x in v]
        return v

    return json.dumps(norm(value), sort_keys=True)


def _sorted(values: list) -> list:
    return sorted(values, key=_canon)


# ---------------------------------------------------------------- built-in checkers


def _k_prefix(expected: object, actual: object, *, ordered: bool) -> bool:
    """Outputs are [k, array]; k must match and the first k elements must match."""
    if not (isinstance(actual, list) and len(actual) == 2 and isinstance(actual[1], list)):
        return False
    k, arr = expected  # type: ignore[misc]
    got_k, got_arr = actual
    if not _equal(k, got_k) or got_k > len(got_arr):
        return False
    head, got_head = arr[:k], got_arr[:k]
    return _equal(head, got_head) if ordered else _equal(_sorted(head), _sorted(got_head))


@checker("k_prefix")
def _k_prefix_ordered(test_input: object, expected: object, actual: object) -> bool:
    return _k_prefix(expected, actual, ordered=True)


@checker("k_prefix_unordered")
def _k_prefix_any_order(test_input: object, expected: object, actual: object) -> bool:
    return _k_prefix(expected, actual, ordered=False)


@checker("sorted_circular_insert")
def _sorted_circular_insert(test_input: object, expected: object, actual: object) -> bool:
    """Insert into a sorted circular list: any insertion point that keeps it sorted is valid.

    `test_input` is [original values from the head, insertVal]; `actual` is one lap of the result.
    """
    original, value = test_input  # type: ignore[misc]
    if not isinstance(actual, list) or len(actual) != len(original) + 1:
        return False
    if not any(actual[i] == value and actual[:i] + actual[i + 1 :] == original for i in range(len(actual))):
        return False
    descents = sum(actual[k] > actual[(k + 1) % len(actual)] for k in range(len(actual)))
    return descents <= 1


@checker("happy_string")
def _happy_string(test_input: object, expected: object, actual: object) -> bool:
    """Longest Happy String: same length as the best, within the letter budgets, no triple letter."""
    a, b, c = test_input  # type: ignore[misc]
    if not isinstance(actual, str) or not isinstance(expected, str) or len(actual) != len(expected):
        return False
    if set(actual) - set("abc") or actual.count("a") > a or actual.count("b") > b or actual.count("c") > c:
        return False
    return not any(t in actual for t in ("aaa", "bbb", "ccc"))


@checker("reorganize_string")
def _reorganize_string(test_input: object, expected: object, actual: object) -> bool:
    (s,) = test_input  # type: ignore[misc]
    if not isinstance(actual, str):
        return False
    if expected == "":
        return actual == ""
    return sorted(actual) == sorted(s) and all(x != y for x, y in zip(actual, actual[1:], strict=False))


@checker("sort_by_frequency")
def _sort_by_frequency(test_input: object, expected: object, actual: object) -> bool:
    """Each character's copies are contiguous and blocks come in non-increasing size."""
    (s,) = test_input  # type: ignore[misc]
    if not isinstance(actual, str) or sorted(actual) != sorted(s):
        return False
    blocks: list[tuple[str, int]] = []
    for ch in actual:
        if blocks and blocks[-1][0] == ch:
            blocks[-1] = (ch, blocks[-1][1] + 1)
        else:
            blocks.append((ch, 1))
    if len({ch for ch, _ in blocks}) != len(blocks):
        return False
    sizes = [n for _, n in blocks]
    return all(x >= y for x, y in zip(sizes, sizes[1:], strict=False))


def _counter(values: list) -> dict:
    counts: dict = {}
    for v in values:
        key = json.dumps(v)
        counts[key] = counts.get(key, 0) + 1
    return counts


@checker("top_k_frequent")
def _top_k_frequent(test_input: object, expected: object, actual: object) -> bool:
    nums, k = test_input  # type: ignore[misc]
    if not isinstance(actual, list) or len(actual) != k or len(set(map(json.dumps, actual))) != k:
        return False
    freq = _counter(nums)
    chosen = [json.dumps(v) for v in actual]
    if any(c not in freq for c in chosen):
        return False
    rest = [f for key, f in freq.items() if key not in chosen]
    return not rest or min(freq[c] for c in chosen) >= max(rest)


@checker("k_closest_points")
def _k_closest_points(test_input: object, expected: object, actual: object) -> bool:
    points, k = test_input  # type: ignore[misc]
    if not isinstance(actual, list) or len(actual) != k:
        return False
    available = _counter(points)
    for p in actual:
        key = json.dumps(p)
        if available.get(key, 0) == 0:
            return False
        available[key] -= 1

    def dist(key: str) -> int:
        x, y = json.loads(key)
        return x * x + y * y

    chosen_max = max(dist(json.dumps(p)) for p in actual) if actual else -1
    remaining = [dist(key) for key, n in available.items() for _ in range(n)]
    return not remaining or chosen_max <= min(remaining)


@checker("k_smallest_pairs")
def _k_smallest_pairs(test_input: object, expected: object, actual: object) -> bool:
    nums1, nums2, _ = test_input  # type: ignore[misc]
    if not isinstance(actual, list) or len(actual) != len(expected):  # type: ignore[arg-type]
        return False
    c1, c2 = _counter(nums1), _counter(nums2)
    used = _counter(actual)
    for key, n in used.items():
        pair = json.loads(key)
        if not (isinstance(pair, list) and len(pair) == 2):
            return False
        if n > c1.get(json.dumps(pair[0]), 0) * c2.get(json.dumps(pair[1]), 0):
            return False
    return sorted(u + v for u, v in actual) == sorted(u + v for u, v in expected)  # type: ignore[union-attr]


@checker("k_subsequence_max_sum")
def _k_subsequence_max_sum(test_input: object, expected: object, actual: object) -> bool:
    nums, k = test_input  # type: ignore[misc]
    if not isinstance(actual, list) or len(actual) != k:
        return False
    it = iter(nums)
    if not all(any(x == y for y in it) for x in actual):
        return False
    return sum(actual) == sum(expected)  # type: ignore[arg-type]


@checker("peak_index")
def _peak_index(test_input: object, expected: object, actual: object) -> bool:
    """Any index whose value is strictly greater than its neighbours (outside the array is -inf)."""
    (nums,) = test_input  # type: ignore[misc]
    if isinstance(actual, bool) or not isinstance(actual, int) or not 0 <= actual < len(nums):
        return False
    left = nums[actual - 1] if actual > 0 else None
    right = nums[actual + 1] if actual + 1 < len(nums) else None
    return (left is None or nums[actual] > left) and (right is None or nums[actual] > right)


@checker("gas_station_start")
def _gas_station_start(test_input: object, expected: object, actual: object) -> bool:
    """Any start index that completes the circuit, or -1 exactly when none does."""
    gas, cost = test_input  # type: ignore[misc]
    if isinstance(actual, bool) or not isinstance(actual, int):
        return False
    if expected == -1 or actual == -1:
        return actual == expected
    if not 0 <= actual < len(gas):
        return False
    tank = 0
    for step in range(len(gas)):
        i = (actual + step) % len(gas)
        tank += gas[i] - cost[i]
        if tank < 0:
            return False
    return True


def _positions(order: list) -> dict | None:
    """value -> index, or None if `order` has duplicates."""
    pos = {json.dumps(v): i for i, v in enumerate(order)}
    return pos if len(pos) == len(order) else None


def _respects(order: list, before_after: list[tuple[object, object]]) -> bool:
    pos = _positions(order)
    if pos is None:
        return False
    return all(pos[json.dumps(a)] < pos[json.dumps(b)] for a, b in before_after)


@checker("alien_order")
def _alien_order(test_input: object, expected: object, actual: object) -> bool:
    """Any letter order consistent with the sorted word list; "" exactly when no order exists."""
    (words,) = test_input  # type: ignore[misc]
    if not isinstance(actual, str):
        return False
    if expected == "":
        return actual == ""
    letters = set("".join(words))
    if set(actual) != letters or len(actual) != len(letters):
        return False
    pairs = []
    for a, b in zip(words, words[1:], strict=False):
        for x, y in zip(a, b, strict=False):
            if x != y:
                pairs.append((x, y))
                break
    return _respects(list(actual), pairs)


@checker("compilation_order")
def _compilation_order(test_input: object, expected: object, actual: object) -> bool:
    """dependencies[i] = [a, b]: b must come before a. [] exactly when there is a cycle."""
    (deps,) = test_input  # type: ignore[misc]
    if not isinstance(actual, list):
        return False
    if expected == []:
        return actual == []
    nodes = {x for pair in deps for x in pair}
    return set(actual) == nodes and len(actual) == len(nodes) and _respects(actual, [(b, a) for a, b in deps])


@checker("course_order")
def _course_order(test_input: object, expected: object, actual: object) -> bool:
    """prerequisites[i] = [a, b]: take b before a. [] exactly when impossible."""
    n, prereqs = test_input  # type: ignore[misc]
    if not isinstance(actual, list):
        return False
    if expected == []:
        return actual == []
    return sorted(actual) == list(range(n)) and _respects(actual, [(b, a) for a, b in prereqs])


@checker("sort_items_groups")
def _sort_items_groups(test_input: object, expected: object, actual: object) -> bool:
    n, _m, group, before_items = test_input  # type: ignore[misc]
    if not isinstance(actual, list):
        return False
    if expected == []:
        return actual == []
    if sorted(actual) != list(range(n)):
        return False
    if not _respects(actual, [(j, i) for i in range(n) for j in before_items[i]]):
        return False
    seen_groups: set[int] = set()
    previous = None
    for item in actual:
        g = group[item]
        if g != -1 and g != previous and g in seen_groups:
            return False  # a group's items must be contiguous
        if g != -1:
            seen_groups.add(g)
        previous = g
    return True


@checker("matrix_conditions")
def _matrix_conditions(test_input: object, expected: object, actual: object) -> bool:
    k, row_conditions, col_conditions = test_input  # type: ignore[misc]
    if not isinstance(actual, list):
        return False
    if expected == []:
        return actual == []
    if len(actual) != k or any(not isinstance(r, list) or len(r) != k for r in actual):
        return False
    where = {}
    for i, row in enumerate(actual):
        for j, v in enumerate(row):
            if v != 0:
                if v in where or not isinstance(v, int) or not 1 <= v <= k:
                    return False
                where[v] = (i, j)
    if len(where) != k:
        return False
    return all(where[a][0] < where[b][0] for a, b in row_conditions) and all(where[a][1] < where[b][1] for a, b in col_conditions)


@checker("parity_ii")
def _parity_ii(test_input: object, expected: object, actual: object) -> bool:
    (nums,) = test_input  # type: ignore[misc]
    return isinstance(actual, list) and sorted(actual) == sorted(nums) and all(v % 2 == i % 2 for i, v in enumerate(actual))


@checker("min_max_grid")
def _min_max_grid(test_input: object, expected: object, actual: object) -> bool:
    """Same shape, positive ints, same relative order in every row and column, and the optimal maximum."""
    (grid,) = test_input  # type: ignore[misc]
    if not isinstance(actual, list) or len(actual) != len(grid):
        return False
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in actual):
        return False
    if any(not isinstance(v, int) or v < 1 for row in actual for v in row):
        return False

    def same_order(a: list[int], b: list[int]) -> bool:
        return all((a[i] < a[j]) == (b[i] < b[j]) for i in range(len(a)) for j in range(len(a)) if i != j)

    rows_ok = all(same_order(g, a) for g, a in zip(grid, actual, strict=True))
    cols_ok = all(same_order(list(g), list(a)) for g, a in zip(zip(*grid, strict=True), zip(*actual, strict=True), strict=True))
    return rows_ok and cols_ok and max(map(max, actual)) == max(map(max, expected))  # type: ignore[arg-type]


@checker("min_remove_parens")
def _min_remove_parens(test_input: object, expected: object, actual: object) -> bool:
    """Balanced, obtained from s by deleting only parentheses, and no more deletions than the optimum."""
    (s,) = test_input  # type: ignore[misc]
    if not isinstance(actual, str) or len(actual) != len(expected):  # type: ignore[arg-type]
        return False
    depth = 0
    for ch in actual:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if depth < 0:
            return False
    if depth:
        return False
    it = iter(s)
    kept_all_letters = all(ch in it for ch in actual)
    return kept_all_letters and [c for c in s if c not in "()"] == [c for c in actual if c not in "()"]


@checker("balanced_bst")
def _balanced_bst(test_input: object, expected: object, actual: object) -> bool:
    """A height-balanced BST (level-order JSON) whose in-order traversal is exactly the sorted input values."""
    (values,) = test_input  # type: ignore[misc]
    if not isinstance(actual, list) or any(v is not None and not isinstance(v, int) for v in actual):
        return False
    try:
        root = codec.tree_from_json(actual)
    except (TypeError, ValueError):
        return False
    inorder: list[int] = []

    def height(node: codec.TreeNode | None) -> int:
        """Height of a balanced subtree, or -1 once any subtree is unbalanced."""
        if node is None:
            return 0
        left = height(node.left)
        inorder.append(node.val)
        right = height(node.right)
        if left < 0 or right < 0 or abs(left - right) > 1:
            return -1
        return 1 + max(left, right)

    return height(root) >= 0 and inorder == values


@checker("custom_sort")
def _custom_sort(test_input: object, expected: object, actual: object) -> bool:
    """A permutation of s in which the letters that appear in `order` keep order's relative ordering."""
    order, s = test_input  # type: ignore[misc]
    if not isinstance(actual, str) or sorted(actual) != sorted(s):
        return False
    rank = {ch: i for i, ch in enumerate(order)}
    ranked = [rank[ch] for ch in actual if ch in rank]
    return ranked == sorted(ranked)


@checker("all_one")
def _all_one(test_input: object, expected: object, actual: object) -> bool:
    """Replay inc/dec; getMaxKey/getMinKey may return any key with the extreme count ("" when empty)."""
    if not isinstance(actual, list) or not isinstance(expected, list) or len(actual) != len(expected):
        return False
    ops, args = test_input["ops"], test_input["args"]  # type: ignore[index]
    counts: dict[str, int] = {}
    for op, op_args, out in zip(ops, args, actual, strict=True):
        if op in ("inc", "dec"):
            key = op_args[0]
            counts[key] = counts.get(key, 0) + (1 if op == "inc" else -1)
            if counts[key] == 0:
                del counts[key]
            if out is not None:
                return False
        elif op in ("getMaxKey", "getMinKey"):
            if not counts:
                if out != "":
                    return False
                continue
            extreme = max(counts.values()) if op == "getMaxKey" else min(counts.values())
            if not isinstance(out, str) or counts.get(out) != extreme:
                return False
        elif out is not None:
            return False
    return True


@checker("palindrome_substring")
def _palindrome_substring(test_input: object, expected: object, actual: object) -> bool:
    """Any palindromic substring of s with the optimal length."""
    (s,) = test_input  # type: ignore[misc]
    return isinstance(actual, str) and len(actual) == len(expected) and actual == actual[::-1] and actual in s  # type: ignore[arg-type, operator]


@checker("shortest_common_supersequence")
def _shortest_common_supersequence(test_input: object, expected: object, actual: object) -> bool:
    a, b = test_input  # type: ignore[misc]

    def subsequence(small: str, big: str) -> bool:
        it = iter(big)
        return all(c in it for c in small)

    return isinstance(actual, str) and len(actual) == len(expected) and subsequence(a, actual) and subsequence(b, actual)  # type: ignore[arg-type]
