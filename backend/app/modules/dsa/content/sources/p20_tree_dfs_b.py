"""Pattern 20: Tree Depth-First Search (part 2 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import random
import re
from collections import deque

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, random_tree, sample
from app.modules.dsa.content.sources.p20_tree_dfs_a import (
    _all_nodes,
    _parents,
    _random_bst,
    _size,
    _sorted_array_brute,
)
from app.modules.dsa.judge.codec import ListNode, TreeNode, tree_from_json

PATTERN_NUMBER = 20


def _is_leaf(node: TreeNode) -> bool:
    return node.left is None and node.right is None


# ---------------------------------------------------------------- Height of Binary Tree After Subtree Removal Queries


def _tree_queries(root: TreeNode, queries: list[int]) -> list[int]:
    depth: dict[int, int] = {}
    height: dict[int, int] = {}  # edges on the longest downward path

    def walk(node: TreeNode | None, d: int) -> int:
        if node is None:
            return -1
        depth[node.val] = d
        height[node.val] = 1 + max(walk(node.left, d + 1), walk(node.right, d + 1))
        return height[node.val]

    walk(root, 0)
    best_two: dict[int, list[int]] = {}  # per depth: the two largest depth + height values
    for v, d in depth.items():
        top = best_two.setdefault(d, [])
        top.append(d + height[v])
        top.sort(reverse=True)
        del top[2:]
    out = []
    for q in queries:
        d = depth[q]
        top = best_two[d]
        if len(top) == 1:
            out.append(d - 1)  # q was alone at its depth: the tree now ends at its parent
        else:
            out.append(top[1] if top[0] == d + height[q] else top[0])
    return out


def _tree_queries_brute(root: TreeNode, queries: list[int]) -> list[int]:
    def height_without(node: TreeNode | None, removed: int) -> int:
        if node is None or node.val == removed:
            return -1
        return 1 + max(height_without(node.left, removed), height_without(node.right, removed))

    return [height_without(root, q) for q in queries]


def _removal_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 15, big=3000)
    labels = sample(rng, range(1, n + 1), n)
    tree = [labels.pop() if v is not None else None for v in random_tree(rng, n, 0, 0)]
    non_root = [v for v in tree[1:] if v is not None]
    return [tree, [rng.choice(non_root) for _ in range(rng.randint(1, min(len(non_root), rng.choice([4, 50]))))]]


SUBTREE_REMOVAL = ProblemSource(
    title="Height of Binary Tree After Subtree Removal Queries",
    statement="""
The binary tree has `n` nodes with the distinct values `1` to `n`. For each `queries[i]`, remove the whole subtree rooted at the node with that
value (never the root) and record the height of the remaining tree; then restore the tree before the next query. The *height* is the number of
edges on the longest path from the root to a node. Return the recorded heights.
""",
    constraints="""
- `2 <= n <= 10^5`, `1 <= queries.length <= min(n, 10^4)`
- values are `1..n`, all distinct; `queries[i] != root.val`
""",
    signature=function("treeQueries", [("root", "TreeNode"), ("queries", "int[]")], "int[]"),
    reference=_tree_queries,
    brute=_tree_queries_brute,
    brute_input_limit=1500,
    examples=[Example([[1, 3, 4, 2, None, 6, 5, None, None, None, None, None, 7], [4]], "Without node 4's subtree, the path 1 -> 3 -> 2 remains: height 2."), Example([[5, 8, 9, 2, 1, 3, 7, 4, 6], [3, 2, 4, 8]])],
    edge_cases=[[[1, 2], [2]], [[1, 2, 3], [2, 3]], [[1, 2, None, 3, None, 4], [4, 3, 2]]],
    generator=_removal_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Delete Nodes And Return Forest


def _del_nodes(root: TreeNode | None, to_delete: list[int]) -> list[list[int]]:
    doomed = set(to_delete)
    roots: list[TreeNode] = []

    def prune(node: TreeNode | None, is_root: bool) -> TreeNode | None:
        if node is None:
            return None
        deleted = node.val in doomed
        if is_root and not deleted:
            roots.append(node)
        node.left = prune(node.left, deleted)
        node.right = prune(node.right, deleted)
        return None if deleted else node

    prune(root, True)
    return [[n.val for n in _all_nodes(r)] for r in roots]


def _forest_brute(root: TreeNode | None, to_delete: list[int]) -> list[list[int]]:
    parent = _parents(root)
    doomed = set(to_delete)
    out = []
    for node in _all_nodes(root):
        if node.val in doomed or (parent[node] is not None and parent[node].val not in doomed):
            continue
        tree, stack = [], [node]  # pre-order, stopping at deleted nodes
        while stack:
            n = stack.pop()
            tree.append(n.val)
            stack += [c for c in (n.right, n.left) if c and c.val not in doomed]
        out.append(tree)
    return out


def _forest_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 15, big=1000)
    tree = random_tree(rng, n, 1, 1000, unique=True)
    values = [v for v in tree if v is not None]
    return [tree, sample(rng, values, rng.randint(1, len(values)))]


DELETE_NODES_FOREST = ProblemSource(
    title="Delete Nodes And Return Forest",
    statement="""
The binary tree's values are distinct. Delete every node whose value is in `to_delete`; the remaining nodes form a forest of disjoint trees.

*Adapted I/O:* return the forest as a list of trees, each given by its **pre-order** list of values. The trees may be listed in any order.
""",
    constraints="""
- `1 <= number of nodes <= 1000`
- `1 <= Node.val <= 1000`, all distinct
- `1 <= to_delete.length <= 1000`; its values are distinct and all in the tree
""",
    signature=function("delNodes", [("root", "TreeNode"), ("to_delete", "int[]")], "int[][]"),
    reference=_del_nodes,
    brute=_forest_brute,
    compare="unordered",
    is_variant=True,
    examples=[Example([[1, 2, 3, 4, 5, 6, 7], [3, 5]], "Trees [1,2,4], [6] and [7]."), Example([[1, 2, 4, None, 3], [3]])],
    edge_cases=[[[1], [1]], [[1, 2, 3], [1]], [[1, 2, 3], [2, 3]]],
    generator=_forest_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Sum of Distances in a Tree


def _sum_of_distances(n: int, edges: list[list[int]]) -> list[int]:
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    order, parent = [0], [-1] * n
    for v in order:
        for w in adjacent[v]:
            if w != parent[v]:
                parent[w] = v
                order.append(w)
    size, down = [1] * n, [0] * n
    for v in reversed(order[1:]):
        size[parent[v]] += size[v]
        down[parent[v]] += down[v] + size[v]
    answer = [0] * n
    answer[0] = down[0]
    for v in order[1:]:  # moving the root to v brings size[v] nodes closer and the rest farther
        answer[v] = answer[parent[v]] - size[v] + (n - size[v])
    return answer


def _distances_brute(n: int, edges: list[list[int]]) -> list[int]:
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    out = []
    for s in range(n):
        dist = {s: 0}
        queue = deque([s])
        while queue:
            v = queue.popleft()
            for w in adjacent[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
        out.append(sum(dist.values()))
    return out


def _tree_edges(rng: random.Random, n: int) -> list[list[int]]:
    labels = sample(rng, range(n), n)
    return [[labels[rng.randint(max(0, i - rng.choice([1, 3, i])), i - 1)], labels[i]] for i in range(1, n)]


SUM_OF_DISTANCES = ProblemSource(
    title="Sum of Distances in a Tree",
    statement="""
An undirected tree has `n` nodes labelled `0` to `n - 1` and the given `edges`. For every node `i`, compute the sum of the distances (in edges)
between `i` and every other node. Return those sums as a list indexed by node.
""",
    constraints="""
- `1 <= n <= 3 * 10^4`
- `edges` forms a tree
""",
    signature=function("sumOfDistancesInTree", [("n", "int"), ("edges", "int[][]")], "int[]"),
    reference=_sum_of_distances,
    brute=lambda n, edges: _distances_brute(n, edges) if n <= 200 else NotImplemented,
    examples=[Example([6, [[0, 1], [0, 2], [2, 3], [2, 4], [2, 5]]], "Node 0: 1 + 1 + 2 + 2 + 2 = 8."), Example([1, []]), Example([2, [[1, 0]]])],
    edge_cases=[[3, [[0, 1], [1, 2]]], [4, [[0, 1], [0, 2], [0, 3]]]],
    generator=lambda rng: [(n := pick_n(rng, 1, 15, big=3000)), _tree_edges(rng, n)],
    random_count=8,
)


# ---------------------------------------------------------------- Recover a Tree From Preorder Traversal


def _recover_from_preorder(traversal: str) -> TreeNode | None:
    stack: list[TreeNode] = []
    for dashes, value in re.findall(r"(-*)(\d+)", traversal):
        node = TreeNode(int(value))
        del stack[len(dashes) :]  # climb back to this node's parent
        if stack:
            parent = stack[-1]
            if parent.left is None:
                parent.left = node
            else:
                parent.right = node
        stack.append(node)
    return stack[0] if stack else None


def _recover_brute(traversal: str) -> TreeNode | None:
    tokens = [(len(d), int(v)) for d, v in re.findall(r"(-*)(\d+)", traversal)]
    position = 0

    def build(depth: int) -> TreeNode | None:
        nonlocal position
        if position == len(tokens) or tokens[position][0] != depth:
            return None
        node = TreeNode(tokens[position][1])
        position += 1
        node.left = build(depth + 1)
        node.right = build(depth + 1)
        return node

    return build(0)


def _dashed_preorder(rng: random.Random) -> list:
    """Random tree where an only child is always a left child, written as dashed pre-order."""
    n = pick_n(rng, 1, 15, big=1000)
    root = TreeNode(rng.randint(1, 10**9))
    nodes = [root]
    for _ in range(n - 1):
        parent = rng.choice([x for x in nodes if x.right is None][-8:])
        child = TreeNode(rng.randint(1, rng.choice([9, 10**9])))
        if parent.left is None:
            parent.left = child
        else:
            parent.right = child
        nodes.append(child)
    parts = []

    def write(node: TreeNode | None, depth: int) -> None:
        if node:
            parts.append("-" * depth + str(node.val))
            write(node.left, depth + 1)
            write(node.right, depth + 1)

    write(root, 0)
    return ["".join(parts)]


RECOVER_FROM_PREORDER = ProblemSource(
    title="Recover a Tree From Preorder Traversal",
    statement="""
A binary tree was written out in pre-order, each node as `D` dashes followed by its value, where `D` is the node's depth (the root has depth 0).
If a node has only one child, that child is its left child. Rebuild the tree from `traversal` and return its root.
""",
    constraints="""
- `1 <= number of nodes <= 1000`
- `1 <= Node.val <= 10^9`
""",
    signature=function("recoverFromPreorder", [("traversal", "string")], "TreeNode"),
    reference=_recover_from_preorder,
    brute=_recover_brute,
    examples=[Example(["1-2--3--4-5--6--7"], "[1,2,5,3,4,6,7]."), Example(["1-2--3---4-5--6---7"]), Example(["1-401--349---90--88"])],
    edge_cases=[["7"], ["1-2"], ["1-2-3"], ["1-2--3---4"]],
    generator=_dashed_preorder,
    random_count=8,
)


# ---------------------------------------------------------------- Binary Tree Preorder Traversal


def _preorder_traversal(root: TreeNode | None) -> list[int]:
    return [n.val for n in _all_nodes(root)]


def _preorder_brute(root: TreeNode | None) -> list[int]:
    return [] if root is None else [root.val, *_preorder_brute(root.left), *_preorder_brute(root.right)]


PREORDER_TRAVERSAL = ProblemSource(
    title="Binary Tree Preorder Traversal",
    statement="""
Return the values of the binary tree in pre-order: each node, then its left subtree, then its right subtree. Try an iterative solution.
""",
    constraints="""
- `0 <= number of nodes <= 100`
- `-100 <= Node.val <= 100`
""",
    signature=function("preorderTraversal", [("root", "TreeNode")], "int[]"),
    reference=_preorder_traversal,
    brute=_preorder_brute,
    examples=[Example([[1, None, 2, 3]]), Example([[1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9]]), Example([[]])],
    edge_cases=[[[1]], [[1, 2]]],
    generator=lambda rng: [random_tree(rng, pick_n(rng, 1, 15, big=100), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Univalued Binary Tree


def _is_unival_tree(root: TreeNode) -> bool:
    return all(n.val == root.val for n in _all_nodes(root))


def _unival_brute(root: TreeNode) -> bool:
    def same(node: TreeNode | None) -> bool:
        return node is None or (node.val == root.val and same(node.left) and same(node.right))

    return same(root)


UNIVALUED_TREE = ProblemSource(
    title="Univalued Binary Tree",
    statement="""
Return `true` if every node in the binary tree holds the same value.
""",
    constraints="""
- `1 <= number of nodes <= 100`
- `0 <= Node.val < 100`
""",
    signature=function("isUnivalTree", [("root", "TreeNode")], "bool"),
    reference=_is_unival_tree,
    brute=_unival_brute,
    examples=[Example([[1, 1, 1, 1, 1, None, 1]]), Example([[2, 2, 2, 5, 2]])],
    edge_cases=[[[0]], [[1, 2]], [[3, None, 3]]],
    generator=lambda rng: [[v if v is None or rng.random() > 0.06 else v + 1 for v in random_tree(rng, pick_n(rng, 1, 15, big=100), 7, 7)]],
    random_count=8,
)


# ---------------------------------------------------------------- Path Sum


def _has_path_sum(root: TreeNode | None, targetSum: int) -> bool:
    stack = [(root, root.val)] if root else []
    while stack:
        node, total = stack.pop()
        if _is_leaf(node) and total == targetSum:
            return True
        stack += [(c, total + c.val) for c in (node.left, node.right) if c]
    return False


def _path_sum_brute(root: TreeNode | None, targetSum: int) -> bool:
    parent = _parents(root)
    for node in _all_nodes(root):
        if _is_leaf(node):
            total, walk = 0, node
            while walk is not None:
                total += walk.val
                walk = parent[walk]
            if total == targetSum:
                return True
    return False


def _path_sum_gen(rng: random.Random) -> list:
    tree = random_tree(rng, pick_n(rng, 1, 15, big=3000), -rng.choice([5, 1000]), 1000)
    root = tree_from_json(tree)
    leaf_sums = []
    parent = _parents(root)
    for node in _all_nodes(root):
        if _is_leaf(node):
            total, walk = 0, node
            while walk is not None:
                total, walk = total + walk.val, parent[walk]
            leaf_sums.append(total)
    target = rng.choice(leaf_sums) if rng.random() < 0.5 else rng.randint(-1000, 1000)
    return [tree, target]


PATH_SUM = ProblemSource(
    title="Path Sum",
    statement="""
Return `true` if the binary tree has a root-to-leaf path whose values add up to `targetSum`. A leaf is a node with no children; an empty tree has
no paths.
""",
    constraints="""
- `0 <= number of nodes <= 5000`
- `-1000 <= Node.val, targetSum <= 1000`
""",
    signature=function("hasPathSum", [("root", "TreeNode"), ("targetSum", "int")], "bool"),
    reference=_has_path_sum,
    brute=_path_sum_brute,
    examples=[Example([[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 22], "5 -> 4 -> 11 -> 2."), Example([[1, 2, 3], 5]), Example([[], 0], "An empty tree has no root-to-leaf path.")],
    edge_cases=[[[1, 2], 1], [[1, 2], 3], [[-2, None, -3], -5]],
    generator=_path_sum_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Closest Binary Search Tree Value


def _closest_value(root: TreeNode, target: float) -> int:
    best = root.val
    node = root
    while node:
        if abs(node.val - target) < abs(best - target) or (abs(node.val - target) == abs(best - target) and node.val < best):
            best = node.val
        node = node.left if target < node.val else node.right
    return best


def _closest_gen(rng: random.Random) -> list:
    tree = _random_bst(rng, _size(rng, 3000), -(hi := rng.choice([30, 10**9])), hi)
    value = rng.choice([v for v in tree if v is not None])
    target = rng.choice([value + 0.5, value - 0.5, value + rng.random(), float(rng.randint(-hi, hi))])
    return [tree, target]


CLOSEST_BST_VALUE = ProblemSource(
    title="Closest Binary Search Tree Value",
    statement="""
Given the root of a binary search tree and a real number `target`, return the value in the tree closest to `target`. If two values are equally
close, return the smaller one.
""",
    constraints="""
- `1 <= number of nodes <= 10^4`
- `-10^9 <= Node.val, target <= 10^9`
""",
    signature=function("closestValue", [("root", "TreeNode"), ("target", "double")], "int"),
    reference=_closest_value,
    brute=lambda root, target: min((n.val for n in _all_nodes(root)), key=lambda v: (abs(v - target), v)),
    examples=[Example([[4, 2, 5, 1, 3], 3.714286]), Example([[1], 4.428571]), Example([[4, 2, 5, 1, 3], 3.5], "3 and 4 are equally close; 3 is smaller.")],
    edge_cases=[[[2, 1, 3], 2.0], [[2, None, 3], -1000000000.0]],
    generator=_closest_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Path Sum III


def _path_sum_iii(root: TreeNode | None, targetSum: int) -> int:
    count = 0
    prefix_counts = {0: 1}

    def walk(node: TreeNode | None, running: int) -> None:
        nonlocal count
        if node is None:
            return
        running += node.val
        count += prefix_counts.get(running - targetSum, 0)
        prefix_counts[running] = prefix_counts.get(running, 0) + 1
        walk(node.left, running)
        walk(node.right, running)
        prefix_counts[running] -= 1

    walk(root, 0)
    return count


def _path_sum_iii_brute(root: TreeNode | None, targetSum: int) -> int:
    parent = _parents(root)
    count = 0
    for node in _all_nodes(root):  # every downward path ends at some node: walk up from it
        total, walk = 0, node
        while walk is not None:
            total += walk.val
            count += total == targetSum
            walk = parent[walk]
    return count


PATH_SUM_III = ProblemSource(
    title="Path Sum III",
    statement="""
Count the paths in the binary tree whose values add up to `targetSum`. A path may start and end at any nodes but must go **downward** (from a
parent to its child at every step).
""",
    constraints="""
- `0 <= number of nodes <= 1000`
- `-10^9 <= Node.val <= 10^9`
- `-1000 <= targetSum <= 1000`
""",
    signature=function("pathSum", [("root", "TreeNode"), ("targetSum", "int")], "int"),
    reference=_path_sum_iii,
    brute=_path_sum_iii_brute,
    examples=[Example([[10, 5, -3, 3, 2, None, 11, 3, -2, None, 1], 8], "5->3, 5->2->1 and -3->11."), Example([[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1], 22])],
    edge_cases=[[[], 0], [[0, 0, 0], 0], [[1000000000, 1000000000, None, 294967296, None, 1000000000], 0]],
    generator=lambda rng: [random_tree(rng, pick_n(rng, 1, 15, big=1000), -5, 5), rng.randint(-6, 6)],
    random_count=8,
)


# ---------------------------------------------------------------- Boundary of Binary Tree


def _boundary_of_binary_tree(root: TreeNode) -> list[int]:
    if _is_leaf(root):
        return [root.val]
    left, node = [], root.left
    while node and not _is_leaf(node):
        left.append(node.val)
        node = node.left or node.right
    right, node = [], root.right
    while node and not _is_leaf(node):
        right.append(node.val)
        node = node.right or node.left
    leaves = [n.val for n in _all_nodes(root) if n is not root and _is_leaf(n)]
    return [root.val, *left, *leaves, *reversed(right)]


def _boundary_brute(root: TreeNode) -> list[int]:
    out = [root.val]
    tail: list[int] = []

    def walk(node: TreeNode | None, on_left: bool, on_right: bool) -> None:
        if node is None:
            return
        if on_left or _is_leaf(node):
            out.append(node.val)
        walk(node.left, on_left, on_right and node.right is None)
        walk(node.right, on_left and node.left is None, on_right)
        if on_right and not on_left and not _is_leaf(node):
            tail.append(node.val)

    walk(root.left, True, False)
    walk(root.right, False, True)
    return out + tail


BOUNDARY_TREE = ProblemSource(
    title="Boundary of Binary Tree",
    statement="""
The *boundary* of a binary tree is, in order: the root; the **left boundary**; the **leaves** from left to right; the **right boundary** in
reverse order.

- The left boundary starts at the root's left child (empty if there is none) and keeps moving to the left child, or to the right child when there
  is no left child, stopping before it reaches a leaf. The right boundary is the mirror image, starting at the root's right child.
- Leaves are nodes without children; the root is never counted as a leaf.

Return the values on the boundary.
""",
    constraints="""
- `1 <= number of nodes <= 10^4`
- `-1000 <= Node.val <= 1000`
""",
    signature=function("boundaryOfBinaryTree", [("root", "TreeNode")], "int[]"),
    reference=_boundary_of_binary_tree,
    brute=_boundary_brute,
    brute_input_limit=6000,
    examples=[Example([[1, None, 2, 3, 4]], "No left boundary; leaves 3, 4; right boundary [2] reversed."), Example([[1, 2, 3, 4, 5, 6, None, None, None, 7, 8, 9, 10]])],
    edge_cases=[[[1]], [[1, 2]], [[1, None, 2]], [[1, 2, None, None, 3, 4]]],
    generator=lambda rng: [random_tree(rng, pick_n(rng, 1, 15, big=1000), -1000, 1000)],
    random_count=8,
)


# ---------------------------------------------------------------- Convert Sorted List to Binary Search Tree


def _sorted_list_to_bst(head: ListNode | None) -> TreeNode | None:
    size, node = 0, head
    while node:
        size, node = size + 1, node.next
    current = head

    def build(n: int) -> TreeNode | None:  # in-order construction consumes the list once
        nonlocal current
        if n == 0:
            return None
        left = build(n // 2)
        root = TreeNode(current.val, left)  # type: ignore[union-attr]
        current = current.next  # type: ignore[union-attr]
        root.right = build(n - n // 2 - 1)
        return root

    return build(size)


def _sorted_list_brute(head: ListNode | None) -> TreeNode | None:
    values = []
    while head:
        values.append(head.val)
        head = head.next
    return _sorted_array_brute(values)


SORTED_LIST_TO_BST = ProblemSource(
    title="Convert Sorted List to Binary Search Tree",
    statement="""
The linked list's values are sorted in strictly increasing order. Build a *height-balanced* binary search tree with exactly these values (in every
node, the subtree heights differ by at most one) and return its root. Any valid tree is accepted.
""",
    constraints="""
- `0 <= number of nodes <= 2 * 10^4`
- `-10^5 <= Node.val <= 10^5`, strictly increasing
""",
    signature=function("sortedListToBST", [("head", "ListNode")], "TreeNode"),
    reference=_sorted_list_to_bst,
    brute=_sorted_list_brute,
    compare="checker",
    checker="balanced_bst",
    examples=[Example([[-10, -3, 0, 5, 9]], "[0,-3,9,-10,null,5] is one valid answer."), Example([[]])],
    edge_cases=[[[1]], [[1, 2]], [[1, 2, 3, 4]]],
    generator=lambda rng: [sorted(sample(rng, range(-(10**5), 10**5 + 1), _size(rng, 3000)))],
    random_count=8,
)


# ---------------------------------------------------------------- Sum Root to Leaf Numbers


def _sum_numbers(root: TreeNode) -> int:
    total, stack = 0, [(root, root.val)]
    while stack:
        node, number = stack.pop()
        if _is_leaf(node):
            total += number
        stack += [(c, number * 10 + c.val) for c in (node.left, node.right) if c]
    return total


def _sum_numbers_brute(root: TreeNode) -> int:
    parent = _parents(root)
    total = 0
    for node in _all_nodes(root):
        if _is_leaf(node):
            digits, walk = [], node
            while walk is not None:
                digits.append(str(walk.val))
                walk = parent[walk]
            total += int("".join(reversed(digits)))
    return total


def _digit_tree(rng: random.Random) -> list:
    while True:
        tree = random_tree(rng, pick_n(rng, 1, 15, big=300), 0, 9)
        if _max_depth_json(tree) <= 10:
            return [tree]


def _max_depth_json(tree: list[int | None]) -> int:
    depth, level = 0, [tree_from_json(tree)] if tree else []
    while level:
        depth += 1
        level = [c for n in level for c in (n.left, n.right) if c]
    return depth


SUM_ROOT_TO_LEAF = ProblemSource(
    title="Sum Root to Leaf Numbers",
    statement="""
Every node holds a digit `0`-`9`. Each root-to-leaf path spells a number (for example `1 -> 2 -> 3` is `123`). Return the sum of all those
numbers.
""",
    constraints="""
- `1 <= number of nodes <= 1000`
- `0 <= Node.val <= 9`; the tree's depth is at most `10`
""",
    signature=function("sumNumbers", [("root", "TreeNode")], "int"),
    reference=_sum_numbers,
    brute=_sum_numbers_brute,
    examples=[Example([[1, 2, 3]], "12 + 13 = 25."), Example([[4, 9, 0, 5, 1]], "495 + 491 + 40 = 1026.")],
    edge_cases=[[[0]], [[9]], [[1, 0]], [[0, 1, 2]]],
    generator=_digit_tree,
    random_count=8,
)


# ---------------------------------------------------------------- Count Complete Tree Nodes


def _count_nodes(root: TreeNode | None) -> int:
    def height(node: TreeNode | None, side: str) -> int:
        h = 0
        while node:
            h, node = h + 1, getattr(node, side)
        return h

    if root is None:
        return 0
    left, right = height(root, "left"), height(root, "right")
    if left == right:
        return 2**left - 1
    return 1 + _count_nodes(root.left) + _count_nodes(root.right)


COUNT_COMPLETE_NODES = ProblemSource(
    title="Count Complete Tree Nodes",
    statement="""
Return the number of nodes in a *complete* binary tree: every level is full except possibly the last, whose nodes are packed to the left.

Design an algorithm that runs in less than `O(n)` time.
""",
    constraints="""
- `0 <= number of nodes <= 5 * 10^4`
- `0 <= Node.val <= 5 * 10^4`
""",
    signature=function("countNodes", [("root", "TreeNode")], "int"),
    reference=_count_nodes,
    brute=lambda root: len(_all_nodes(root)),
    examples=[Example([[1, 2, 3, 4, 5, 6]]), Example([[]]), Example([[1]])],
    edge_cases=[[[1, 2]], [[1, 2, 3]], [list(range(1, 16))]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 40, big=5000), 0, 5 * 10**4)],
    random_count=8,
)


PROBLEMS = [
    SUBTREE_REMOVAL,
    DELETE_NODES_FOREST,
    SUM_OF_DISTANCES,
    RECOVER_FROM_PREORDER,
    PREORDER_TRAVERSAL,
    UNIVALUED_TREE,
    PATH_SUM,
    CLOSEST_BST_VALUE,
    PATH_SUM_III,
    BOUNDARY_TREE,
    SORTED_LIST_TO_BST,
    SUM_ROOT_TO_LEAF,
    COUNT_COMPLETE_NODES,
]
