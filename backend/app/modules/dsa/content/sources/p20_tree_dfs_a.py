"""Pattern 20: Tree Depth-First Search (part 1 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import random
from collections import deque

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ops, pick_n, random_tree, sample
from app.modules.dsa.judge.codec import TreeNode, tree_from_json, tree_to_json

PATTERN_NUMBER = 20


# ---------------------------------------------------------------- shared tree helpers


def _all_nodes(root: TreeNode | None) -> list[TreeNode]:
    out, stack = [], [root] if root else []
    while stack:
        node = stack.pop()
        out.append(node)
        stack += [c for c in (node.right, node.left) if c]
    return out


def _parents(root: TreeNode | None) -> dict[TreeNode, TreeNode | None]:
    parent: dict[TreeNode, TreeNode | None] = {root: None} if root else {}
    for node in _all_nodes(root):
        for child in (node.left, node.right):
            if child:
                parent[child] = node
    return parent


def _inorder(root: TreeNode | None) -> list[int]:
    out, stack, node = [], [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        out.append(node.val)
        node = node.right
    return out


def _bst_json(values: list[int]) -> list[int | None]:
    """Level-order JSON of the BST built by inserting `values` in order."""
    root = None
    for v in values:
        if root is None:
            root = TreeNode(v)
            continue
        node = root
        while True:
            side = "left" if v < node.val else "right"
            if getattr(node, side) is None:
                setattr(node, side, TreeNode(v))
                break
            node = getattr(node, side)
    return tree_to_json(root)


def _random_bst(rng: random.Random, n: int, lo: int, hi: int) -> list[int | None]:
    return _bst_json(sample(rng, range(lo, hi + 1), n))


def _size(rng: random.Random, big: int = 1000) -> int:
    return pick_n(rng, 1, 15, big=big)


# ---------------------------------------------------------------- Serialize and Deserialize Binary Tree


class _Codec:
    def serialize(self, root: TreeNode | None) -> str:
        out, stack = [], [root]
        while stack:
            node = stack.pop()
            if node is None:
                out.append("#")
            else:
                out.append(str(node.val))
                stack += [node.right, node.left]
        return ",".join(out)

    def deserialize(self, data: str) -> TreeNode | None:
        tokens = iter(data.split(","))

        def build() -> TreeNode | None:
            token = next(tokens)
            if token == "#":
                return None
            node = TreeNode(int(token))
            node.left = build()
            node.right = build()
            return node

        return build()


class _CodecBrute:
    def serialize(self, root: TreeNode | None) -> str:
        if root is None:
            return "#"
        return f"{root.val},{self.serialize(root.left)},{self.serialize(root.right)}"

    def deserialize(self, data: str) -> TreeNode | None:
        tokens = data.split(",")
        root = TreeNode(0)  # sentinel whose left child becomes the real root
        stack: list[tuple[TreeNode, str]] = [(root, "left")]
        for token in tokens:
            parent, side = stack.pop()
            if token == "#":
                continue
            node = TreeNode(int(token))
            setattr(parent, side, node)
            stack += [(node, "right"), (node, "left")]
        return root.left


def _codec_gen(rng: random.Random) -> dict:
    calls: list[tuple[str, list]] = [("Codec", [])]
    for _ in range(rng.randint(1, 3)):
        tree = random_tree(rng, pick_n(rng, 0, 12, big=500), -1000, 1000)
        if rng.random() < 0.5:
            calls.append(("serialize", [tree]))
        else:
            calls.append(("deserialize", [_Codec().serialize(tree_from_json(tree))]))
    return ops(*calls)


SERIALIZE_TREE = ProblemSource(
    title="Serialize and Deserialize Binary Tree",
    statement="""
*Adapted I/O:* design `Codec`, which converts a binary tree to a string and back. Because the judge compares your strings directly, the format
is fixed: a **pre-order** walk that writes each node's value, writes `#` for every missing child, and separates tokens with commas. For example
the tree `[1,2,3,null,null,4,5]` becomes `"1,2,#,#,3,4,#,#,5,#,#"`, and the empty tree becomes `"#"`.

- `serialize(root)` returns the string for the tree.
- `deserialize(data)` rebuilds and returns the tree described by `data`.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the
constructor). Trees are shown in level order.
""",
    constraints="""
- `0 <= number of nodes <= 10^4`
- `-1000 <= Node.val <= 1000`
""",
    signature=design("Codec", [], [("serialize", [("root", "TreeNode")], "string"), ("deserialize", [("data", "string")], "TreeNode")]),
    reference=_Codec,
    brute=_CodecBrute,
    is_variant=True,
    examples=[
        Example(ops(("Codec", []), ("serialize", [[1, 2, 3, None, None, 4, 5]]), ("deserialize", ["1,2,#,#,3,4,#,#,5,#,#"])), "The string round-trips to the same tree."),
        Example(ops(("Codec", []), ("serialize", [[]]), ("deserialize", ["#"]))),
    ],
    edge_cases=[ops(("Codec", []), ("serialize", [[-1000]]), ("deserialize", ["-5,#,7,#,#"]))],
    generator=_codec_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Invert Binary Tree


def _invert_tree(root: TreeNode | None) -> TreeNode | None:
    for node in _all_nodes(root):
        node.left, node.right = node.right, node.left
    return root


def _invert_brute(root: TreeNode | None) -> TreeNode | None:
    if root is None:
        return None
    return TreeNode(root.val, _invert_brute(root.right), _invert_brute(root.left))


INVERT_TREE = ProblemSource(
    title="Invert Binary Tree",
    statement="""
Mirror the binary tree: swap the left and right children of every node. Return the root of the mirrored tree.
""",
    constraints="""
- `0 <= number of nodes <= 100`
- `-100 <= Node.val <= 100`
""",
    signature=function("invertTree", [("root", "TreeNode")], "TreeNode"),
    reference=_invert_tree,
    brute=_invert_brute,
    examples=[Example([[4, 2, 7, 1, 3, 6, 9]], "Becomes [4,7,2,9,6,3,1]."), Example([[2, 1, 3]]), Example([[]])],
    edge_cases=[[[1]], [[1, 2]], [[1, None, 2, None, 3]]],
    generator=lambda rng: [random_tree(rng, pick_n(rng, 1, 15, big=100), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Binary Tree Maximum Path Sum


def _max_path_sum(root: TreeNode) -> int:
    best = root.val

    def gain(node: TreeNode | None) -> int:
        nonlocal best
        if node is None:
            return 0
        left, right = max(gain(node.left), 0), max(gain(node.right), 0)
        best = max(best, node.val + left + right)
        return node.val + max(left, right)

    gain(root)
    return best


def _path_sum_brute(root: TreeNode) -> int:
    nodes = _all_nodes(root)
    if len(nodes) > 80:
        return NotImplemented
    parent = _parents(root)

    def ancestors(node: TreeNode) -> list[TreeNode]:
        chain = []
        while node is not None:
            chain.append(node)
            node = parent[node]
        return chain

    best = max(n.val for n in nodes)
    for a, b in itertools.combinations(nodes, 2):
        up_a, up_b = ancestors(a), ancestors(b)
        common = next(x for x in up_a if x in up_b)
        path = up_a[: up_a.index(common) + 1] + up_b[: up_b.index(common)]
        best = max(best, sum(x.val for x in path))
    return best


MAX_PATH_SUM = ProblemSource(
    title="Binary Tree Maximum Path Sum",
    statement="""
A *path* in a binary tree is a sequence of nodes where each adjacent pair is joined by an edge; a node appears at most once, and the path does
not need to pass through the root. Its *path sum* is the sum of its node values. Return the maximum path sum of any non-empty path.
""",
    constraints="""
- `1 <= number of nodes <= 3 * 10^4`
- `-1000 <= Node.val <= 1000`
""",
    signature=function("maxPathSum", [("root", "TreeNode")], "int"),
    reference=_max_path_sum,
    brute=_path_sum_brute,
    brute_input_limit=600,
    examples=[Example([[1, 2, 3]], "2 -> 1 -> 3."), Example([[-10, 9, 20, None, None, 15, 7]], "15 -> 20 -> 7.")],
    edge_cases=[[[-3]], [[-2, -1]], [[2, -1]], [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1]]],
    generator=lambda rng: [random_tree(rng, _size(rng, 3000), -rng.choice([10, 1000]), 1000)],
    random_count=8,
)


# ---------------------------------------------------------------- Build Binary Tree from Preorder and Inorder Traversal


def _build_tree(preorder: list[int], inorder: list[int]) -> TreeNode | None:
    where = {v: i for i, v in enumerate(inorder)}
    values = iter(preorder)

    def build(lo: int, hi: int) -> TreeNode | None:
        if lo > hi:
            return None
        node = TreeNode(next(values))
        mid = where[node.val]
        node.left = build(lo, mid - 1)
        node.right = build(mid + 1, hi)
        return node

    return build(0, len(inorder) - 1)


def _build_brute(preorder: list[int], inorder: list[int]) -> TreeNode | None:
    if not preorder:
        return None
    mid = inorder.index(preorder[0])
    return TreeNode(preorder[0], _build_brute(preorder[1 : mid + 1], inorder[:mid]), _build_brute(preorder[mid + 1 :], inorder[mid + 1 :]))


def _traversals(tree: list[int | None]) -> list[list[int]]:
    root = tree_from_json(tree)
    pre = [n.val for n in _all_nodes(root)]
    return [pre, _inorder(root)]


BUILD_FROM_TRAVERSALS = ProblemSource(
    title="Build Binary Tree from Preorder and Inorder Traversal",
    statement="""
`preorder` and `inorder` are the pre-order and in-order traversals of the same binary tree, whose values are all distinct. Rebuild the tree and
return its root.
""",
    constraints="""
- `1 <= preorder.length == inorder.length <= 3000`
- `-3000 <= values <= 3000`, all distinct
""",
    signature=function("buildTree", [("preorder", "int[]"), ("inorder", "int[]")], "TreeNode"),
    reference=_build_tree,
    brute=_build_brute,
    brute_input_limit=4000,
    examples=[Example([[3, 9, 20, 15, 7], [9, 3, 15, 20, 7]], "[3,9,20,null,null,15,7]."), Example([[-1], [-1]])],
    edge_cases=[[[1, 2], [2, 1]], [[1, 2], [1, 2]], [[1, 2, 3], [3, 2, 1]]],
    generator=lambda rng: _traversals(random_tree(rng, _size(rng, 1500), -3000, 3000, unique=True)),
    random_count=8,
)


# ---------------------------------------------------------------- Lowest Common Ancestor of a Binary Tree


def _lowest_common_ancestor(root: TreeNode, p: int, q: int) -> int:
    def walk(node: TreeNode | None) -> TreeNode | None:
        if node is None or node.val in (p, q):
            return node
        left, right = walk(node.left), walk(node.right)
        return node if left and right else left or right

    return walk(root).val  # type: ignore[union-attr]


def _lca_brute(root: TreeNode, p: int, q: int) -> int:
    parent = _parents(root)
    by_value = {n.val: n for n in _all_nodes(root)}
    seen = set()
    node = by_value[p]
    while node is not None:
        seen.add(node)
        node = parent[node]
    node = by_value[q]
    while node not in seen:
        node = parent[node]
    return node.val


def _lca_gen(rng: random.Random) -> list:
    tree = random_tree(rng, pick_n(rng, 2, 15, big=2000), -(10**9), 10**9, unique=True)
    p, q = sample(rng, [v for v in tree if v is not None], 2)
    return [tree, p, q]


LCA_BINARY_TREE = ProblemSource(
    title="Lowest Common Ancestor of a Binary Tree",
    statement="""
*Adapted I/O:* instead of two node references you receive their values `p` and `q` (all values in the tree are distinct and both exist). Return the
value of their *lowest common ancestor*: the deepest node that has both `p` and `q` as descendants, where a node counts as a descendant of itself.
""",
    constraints="""
- `2 <= number of nodes <= 10^5`
- `-10^9 <= Node.val <= 10^9`, all distinct; `p != q`
""",
    signature=function("lowestCommonAncestor", [("root", "TreeNode"), ("p", "int"), ("q", "int")], "int"),
    reference=_lowest_common_ancestor,
    brute=_lca_brute,
    examples=[
        Example([[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1]),
        Example([[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 4], "5 is an ancestor of 4."),
        Example([[1, 2], 1, 2]),
    ],
    edge_cases=[[[1, 2, 3], 2, 3], [[1, 2, None, 3], 3, 1]],
    generator=_lca_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Validate Binary Search Tree


def _is_valid_bst(root: TreeNode | None) -> bool:
    stack: list[tuple[TreeNode | None, float, float]] = [(root, float("-inf"), float("inf"))]
    while stack:
        node, lo, hi = stack.pop()
        if node is None:
            continue
        if not lo < node.val < hi:
            return False
        stack += [(node.left, lo, node.val), (node.right, node.val, hi)]
    return True


def _valid_bst_brute(root: TreeNode | None) -> bool:
    values = _inorder(root)
    return all(a < b for a, b in itertools.pairwise(values))


def _maybe_bst_gen(rng: random.Random) -> list:
    tree = _random_bst(rng, _size(rng, 3000), -(2**31), 2**31 - 1) if rng.random() < 0.5 else _random_bst(rng, _size(rng), 0, 30)
    present = [i for i, v in enumerate(tree) if v is not None]
    roll = rng.random()
    if roll < 0.35 and len(present) >= 2:  # swap two values: usually breaks the order
        i, j = sample(rng, present, 2)
        tree[i], tree[j] = tree[j], tree[i]
    elif roll < 0.5:
        tree[rng.choice(present)] = tree[present[0]]  # a duplicate value
    return [tree]


VALIDATE_BST = ProblemSource(
    title="Validate Binary Search Tree",
    statement="""
Return `true` if the binary tree is a valid binary search tree: for every node, all values in its left subtree are strictly smaller than the node
and all values in its right subtree are strictly larger.
""",
    constraints="""
- `1 <= number of nodes <= 10^4`
- `-2^31 <= Node.val <= 2^31 - 1`
""",
    signature=function("isValidBST", [("root", "TreeNode")], "bool"),
    reference=_is_valid_bst,
    brute=_valid_bst_brute,
    examples=[Example([[2, 1, 3]]), Example([[5, 1, 4, None, None, 3, 6]], "4 is in 5's right subtree but smaller than 5.")],
    edge_cases=[[[1]], [[1, 1]], [[5, 4, 6, None, None, 3, 7]], [[-2147483648, None, 2147483647]]],
    generator=_maybe_bst_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Maximum Depth of Binary Tree


def _max_depth(root: TreeNode | None) -> int:
    if root is None:
        return 0
    return 1 + max(_max_depth(root.left), _max_depth(root.right))


def _depth_brute(root: TreeNode | None) -> int:
    depth, level = 0, [root] if root else []
    while level:
        depth += 1
        level = [c for n in level for c in (n.left, n.right) if c]
    return depth


MAX_DEPTH = ProblemSource(
    title="Maximum Depth of Binary Tree",
    statement="""
Return the maximum depth of the binary tree: the number of nodes on the longest path from the root down to a leaf (`0` for an empty tree).
""",
    constraints="""
- `0 <= number of nodes <= 10^4`
- `-100 <= Node.val <= 100`
""",
    signature=function("maxDepth", [("root", "TreeNode")], "int"),
    reference=_max_depth,
    brute=_depth_brute,
    examples=[Example([[3, 9, 20, None, None, 15, 7]]), Example([[1, None, 2]]), Example([[]])],
    edge_cases=[[[0]], [[1, 2, None, 3, None, 4]]],
    generator=lambda rng: [random_tree(rng, _size(rng, 800), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Kth Smallest Element in a BST


def _kth_smallest(root: TreeNode, k: int) -> int:
    stack, node = [], root
    while True:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val
        node = node.right


def _kth_gen(rng: random.Random) -> list:
    n = _size(rng, 3000)
    return [_random_bst(rng, n, 0, 10**4), rng.randint(1, n)]


KTH_SMALLEST_BST = ProblemSource(
    title="Kth Smallest Element in a BST",
    statement="""
Given the root of a binary search tree and an integer `k`, return the `k`-th smallest value (1-indexed) among all its nodes.
""",
    constraints="""
- `1 <= k <= n <= 10^4`
- `0 <= Node.val <= 10^4`, all distinct
""",
    signature=function("kthSmallest", [("root", "TreeNode"), ("k", "int")], "int"),
    reference=_kth_smallest,
    brute=lambda root, k: sorted(n.val for n in _all_nodes(root))[k - 1],
    examples=[Example([[3, 1, 4, None, 2], 1]), Example([[5, 3, 6, 2, 4, None, None, 1], 3])],
    edge_cases=[[[7], 1], [[2, 1, 3], 3]],
    generator=_kth_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Flatten Binary Tree to Linked List


def _flatten(root: TreeNode | None) -> TreeNode | None:
    node = root
    while node:  # Morris-style: splice the left subtree in front of the right one
        if node.left:
            tail = node.left
            while tail.right:
                tail = tail.right
            tail.right = node.right
            node.right, node.left = node.left, None
        node = node.right
    return root


def _flatten_brute(root: TreeNode | None) -> TreeNode | None:
    values = [n.val for n in _all_nodes(root)]  # pre-order
    head = None
    for v in reversed(values):
        head = TreeNode(v, None, head)
    return head


FLATTEN_TREE = ProblemSource(
    title="Flatten Binary Tree to Linked List",
    statement="""
Flatten the binary tree into a "linked list" made of the same nodes: each node's `right` pointer points to the next node in pre-order, and every
`left` pointer is `null`. *Adapted I/O:* do it in place, then return the root (the head of the flattened list).

Try to use `O(1)` extra space.
""",
    constraints="""
- `0 <= number of nodes <= 2000`
- `-100 <= Node.val <= 100`
""",
    signature=function("flatten", [("root", "TreeNode")], "TreeNode"),
    reference=_flatten,
    brute=_flatten_brute,
    examples=[Example([[1, 2, 5, 3, 4, None, 6]], "[1,null,2,null,3,null,4,null,5,null,6]."), Example([[]]), Example([[0]])],
    edge_cases=[[[1, 2]], [[1, None, 2, 3]]],
    generator=lambda rng: [random_tree(rng, _size(rng, 400), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Diameter of Binary Tree


def _diameter_of_binary_tree(root: TreeNode | None) -> int:
    best = 0

    def height(node: TreeNode | None) -> int:
        nonlocal best
        if node is None:
            return 0
        left, right = height(node.left), height(node.right)
        best = max(best, left + right)
        return 1 + max(left, right)

    height(root)
    return best


def _diameter_brute(root: TreeNode | None) -> int:
    nodes = _all_nodes(root)
    if len(nodes) > 150:
        return NotImplemented
    parent = _parents(root)
    adjacent: dict[TreeNode, list[TreeNode]] = {n: [c for c in (n.left, n.right, parent[n]) if c] for n in nodes}
    best = 0
    for start in nodes:
        dist = {start: 0}
        queue = deque([start])
        while queue:
            v = queue.popleft()
            for w in adjacent[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
        best = max(best, *dist.values())
    return best


DIAMETER_BINARY_TREE = ProblemSource(
    title="Diameter of Binary Tree",
    statement="""
Return the *diameter* of the binary tree: the number of edges on the longest path between any two nodes (the path may skip the root).
""",
    constraints="""
- `1 <= number of nodes <= 10^4`
- `-100 <= Node.val <= 100`
""",
    signature=function("diameterOfBinaryTree", [("root", "TreeNode")], "int"),
    reference=_diameter_of_binary_tree,
    brute=_diameter_brute,
    examples=[Example([[1, 2, 3, 4, 5]], "4 -> 2 -> 1 -> 3 or 5 -> 2 -> 1 -> 3."), Example([[1, 2]])],
    edge_cases=[[[1]], [[1, 2, None, 3, 4, 5, None, None, 6]]],
    generator=lambda rng: [random_tree(rng, _size(rng, 3000), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Convert Sorted Array to Binary Search Tree


def _sorted_array_to_bst(nums: list[int]) -> TreeNode | None:
    def build(lo: int, hi: int) -> TreeNode | None:
        if lo > hi:
            return None
        mid = (lo + hi) // 2
        return TreeNode(nums[mid], build(lo, mid - 1), build(mid + 1, hi))

    return build(0, len(nums) - 1)


def _sorted_array_brute(nums: list[int]) -> TreeNode | None:
    if not nums:
        return None
    mid = len(nums) // 2  # the upper middle: a different but equally valid tree
    return TreeNode(nums[mid], _sorted_array_brute(nums[:mid]), _sorted_array_brute(nums[mid + 1 :]))


SORTED_ARRAY_TO_BST = ProblemSource(
    title="Convert Sorted Array to Binary Search Tree",
    statement="""
`nums` is sorted in strictly increasing order. Build a *height-balanced* binary search tree containing exactly these values (in every node, the
heights of the two subtrees differ by at most one) and return its root. Any valid tree is accepted.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-10^4 <= nums[i] <= 10^4`, strictly increasing
""",
    signature=function("sortedArrayToBST", [("nums", "int[]")], "TreeNode"),
    reference=_sorted_array_to_bst,
    brute=_sorted_array_brute,
    compare="checker",
    checker="balanced_bst",
    examples=[Example([[-10, -3, 0, 5, 9]], "[0,-3,9,-10,null,5] is one answer; [0,-10,5,null,-3,null,9] is another."), Example([[1, 3]])],
    edge_cases=[[[7]], [[1, 2, 3]], [list(range(-10000, -9985))]],
    generator=lambda rng: [sorted(sample(rng, range(-(10**4), 10**4 + 1), _size(rng, 3000)))],
    random_count=8,
)


# ---------------------------------------------------------------- Binary Tree Right Side View


def _right_side_view(root: TreeNode | None) -> list[int]:
    view: list[int] = []

    def walk(node: TreeNode | None, depth: int) -> None:
        if node is None:
            return
        if depth == len(view):
            view.append(node.val)
        walk(node.right, depth + 1)
        walk(node.left, depth + 1)

    walk(root, 0)
    return view


def _right_view_brute(root: TreeNode | None) -> list[int]:
    out, level = [], [root] if root else []
    while level:
        out.append(level[-1].val)
        level = [c for n in level for c in (n.left, n.right) if c]
    return out


RIGHT_SIDE_VIEW = ProblemSource(
    title="Binary Tree Right Side View",
    statement="""
Imagine standing to the right of the binary tree. Return the values of the nodes you can see, from top to bottom (the rightmost node of each
level).
""",
    constraints="""
- `0 <= number of nodes <= 100`
- `-100 <= Node.val <= 100`
""",
    signature=function("rightSideView", [("root", "TreeNode")], "int[]"),
    reference=_right_side_view,
    brute=_right_view_brute,
    examples=[Example([[1, 2, 3, None, 5, None, 4]]), Example([[1, 2, 3, 4, None, None, None, 5]], "The left branch is deeper, so 4 and 5 are visible."), Example([[]])],
    edge_cases=[[[1]], [[1, 2]], [[1, None, 3]]],
    generator=lambda rng: [random_tree(rng, pick_n(rng, 1, 15, big=100), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Nested List Weight Sum II


def _depth_sum_inverse(tokens: list[str]) -> int:
    level_sums: list[int] = []
    depth = 0
    for token in tokens:
        if token == "[":
            depth += 1
        elif token == "]":
            depth -= 1
        else:
            while len(level_sums) < depth:
                level_sums.append(0)
            level_sums[depth - 1] += int(token)
    # weight = maxDepth - depth + 1: accumulating running prefix sums gives each level its weight
    total = running = 0
    for level_sum in level_sums:
        running += level_sum
        total += running
    return total


def _depth_sum_brute(tokens: list[str]) -> int:
    depths, values, depth = [], [], 0
    max_depth = 0
    for token in tokens:
        if token == "[":
            depth += 1
        elif token == "]":
            depth -= 1
        else:
            max_depth = max(max_depth, depth)
            depths.append(depth)
            values.append(int(token))
    return sum(v * (max_depth - d + 1) for v, d in zip(values, depths, strict=True)) if values else 0


def _nested_tokens(rng: random.Random, depth: int) -> list[str]:
    out = ["["]
    for _ in range(rng.randint(0, 4)):
        if depth and rng.random() < 0.4:
            out += _nested_tokens(rng, depth - 1)
        else:
            out.append(str(rng.randint(-100, 100)))
    return out + ["]"]


NESTED_WEIGHT_SUM_II = ProblemSource(
    title="Nested List Weight Sum II",
    statement="""
*Adapted I/O:* a nested list of integers arrives as a **token stream**: `"["` opens a list, `"]"` closes it, any other token is an integer. For
example `[[1,1],2,[1,1]]` is `["[", "[", "1", "1", "]", "2", "[", "1", "1", "]", "]"]`.

The *depth* of an integer is the number of lists it is inside (integers directly in the outermost list have depth 1). Let `maxDepth` be the largest
depth of any **integer** (empty lists don't count). Each integer's *weight* is `maxDepth - depth + 1`. Return the sum of every integer
multiplied by its weight (`0` if there are no integers).
""",
    constraints="""
- the outermost list is always present; lists may be empty
- `1 <= tokens.length <= 10^4`, nesting depth `<= 50`
- `-100 <= integer <= 100`
""",
    signature=function("depthSumInverse", [("tokens", "string[]")], "int"),
    reference=_depth_sum_inverse,
    brute=_depth_sum_brute,
    is_variant=True,
    examples=[
        Example([["[", "[", "1", "1", "]", "2", "[", "1", "1", "]", "]"]], "Four 1s at depth 2 (weight 1) and one 2 at depth 1 (weight 2): 8."),
        Example([["[", "1", "[", "4", "[", "6", "]", "]", "]"]], "1*3 + 4*2 + 6*1 = 17."),
    ],
    edge_cases=[[["[", "]"]], [["[", "5", "]"]], [["[", "[", "[", "]", "]", "3", "]"]]],
    generator=lambda rng: [_nested_tokens(rng, rng.randint(1, 5))],
    random_count=12,
)


# ---------------------------------------------------------------- Inorder Successor in BST


def _inorder_successor(root: TreeNode | None, p: int) -> int:
    best = -1
    node = root
    while node:
        if node.val > p:
            best = node.val
            node = node.left
        else:
            node = node.right
    return best


def _successor_gen(rng: random.Random) -> list:
    tree = _random_bst(rng, _size(rng, 3000), 0, rng.choice([40, 10**5]))
    return [tree, rng.choice([v for v in tree if v is not None])]


INORDER_SUCCESSOR = ProblemSource(
    title="Inorder Successor in BST",
    statement="""
*Adapted I/O:* given the root of a binary search tree and the value `p` of one of its nodes, return the value of `p`'s *in-order successor* (the
node with the smallest value greater than `p`), or `-1` if it has none. All values are distinct and non-negative.
""",
    constraints="""
- `1 <= number of nodes <= 10^4`
- `0 <= Node.val <= 10^5`, all distinct; `p` is in the tree
""",
    signature=function("inorderSuccessor", [("root", "TreeNode"), ("p", "int")], "int"),
    reference=_inorder_successor,
    brute=lambda root, p: min((n.val for n in _all_nodes(root) if n.val > p), default=-1),
    examples=[Example([[2, 1, 3], 1]), Example([[5, 3, 6, 2, 4, None, None, 1], 6], "6 is the largest value.")],
    edge_cases=[[[0], 0], [[5, 3, 6, 2, 4, None, None, 1], 4], [[1, None, 2], 1]],
    generator=_successor_gen,
    random_count=8,
)


PROBLEMS = [
    SERIALIZE_TREE,
    INVERT_TREE,
    MAX_PATH_SUM,
    BUILD_FROM_TRAVERSALS,
    LCA_BINARY_TREE,
    VALIDATE_BST,
    MAX_DEPTH,
    KTH_SMALLEST_BST,
    FLATTEN_TREE,
    DIAMETER_BINARY_TREE,
    SORTED_ARRAY_TO_BST,
    RIGHT_SIDE_VIEW,
    NESTED_WEIGHT_SUM_II,
    INORDER_SUCCESSOR,
]
