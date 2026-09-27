"""Pattern 21: Tree Breadth-First Search. Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import random
from collections import defaultdict, deque
from fractions import Fraction

from app.modules.dsa.content.model import Example, ProblemSource, function, pick_n, random_tree, sample, word
from app.modules.dsa.content.sources.p20_tree_dfs_a import _all_nodes, _parents, _random_bst, _size
from app.modules.dsa.judge.codec import TreeNode, tree_from_json, tree_to_json

PATTERN_NUMBER = 21


def _levels(root: TreeNode | None) -> list[list[TreeNode]]:
    out, level = [], [root] if root else []
    while level:
        out.append(level)
        level = [c for n in level for c in (n.left, n.right) if c]
    return out


def _small_tree(rng: random.Random, lo: int = -100, hi: int = 100, big: int = 2000) -> list[int | None]:
    return random_tree(rng, pick_n(rng, 1, 15, big=big), lo, hi)


def _tree_edges(rng: random.Random, n: int, first: int = 0) -> list[list[int]]:
    labels = [first + x for x in sample(rng, range(n), n)]
    return [[labels[rng.randint(max(0, i - rng.choice([1, 3, i])), i - 1)], labels[i]] for i in range(1, n)]


def _adjacency(n: int, edges: list[list[int]], first: int = 0) -> list[list[int]]:
    adjacent: list[list[int]] = [[] for _ in range(n + first)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    return adjacent


def _bfs(adjacent: list[list[int]], source: int) -> dict[int, int]:
    dist = {source: 0}
    queue = deque([source])
    while queue:
        v = queue.popleft()
        for w in adjacent[v]:
            if w not in dist:
                dist[w] = dist[v] + 1
                queue.append(w)
    return dist


# ---------------------------------------------------------------- Level Order Traversal of Binary Tree


def _level_order(root: TreeNode | None) -> list[list[int]]:
    out: list[list[int]] = []
    queue = deque([root] if root else [])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            queue.extend(c for c in (node.left, node.right) if c)
        out.append(level)
    return out


def _level_order_brute(root: TreeNode | None) -> list[list[int]]:
    rows: dict[int, list[int]] = defaultdict(list)

    def walk(node: TreeNode | None, depth: int) -> None:
        if node:
            rows[depth].append(node.val)
            walk(node.left, depth + 1)
            walk(node.right, depth + 1)

    walk(root, 0)
    return [rows[d] for d in range(len(rows))]


LEVEL_ORDER = ProblemSource(
    title="Level Order Traversal of Binary Tree",
    statement="""
Return the values of the binary tree level by level: one list per level, from the root down, each listed left to right.
""",
    constraints="""
- `0 <= number of nodes <= 2000`
- `-1000 <= Node.val <= 1000`
""",
    signature=function("levelOrder", [("root", "TreeNode")], "int[][]"),
    reference=_level_order,
    brute=_level_order_brute,
    examples=[Example([[3, 9, 20, None, None, 15, 7]], "[[3],[9,20],[15,7]]."), Example([[1]]), Example([[]])],
    edge_cases=[[[1, 2, None, 3]], [[1, None, 2, None, 3]]],
    generator=lambda rng: [_small_tree(rng, -1000, 1000)],
    random_count=8,
)


# ---------------------------------------------------------------- Binary Tree Zigzag Level Order Traversal


def _zigzag_level_order(root: TreeNode | None) -> list[list[int]]:
    out = []
    for depth, level in enumerate(_level_order(root)):
        out.append(level if depth % 2 == 0 else level[::-1])
    return out


def _zigzag_brute(root: TreeNode | None) -> list[list[int]]:
    out, level, left_to_right = [], [root] if root else [], True
    while level:
        values = [n.val for n in level]
        out.append(values if left_to_right else list(reversed(values)))
        left_to_right = not left_to_right
        level = [c for n in level for c in (n.left, n.right) if c]
    return out


ZIGZAG = ProblemSource(
    title="Binary Tree Zigzag Level Order Traversal",
    statement="""
Return the binary tree's values level by level, alternating direction: the first level left to right, the next right to left, and so on.
""",
    constraints="""
- `0 <= number of nodes <= 2000`
- `-100 <= Node.val <= 100`
""",
    signature=function("zigzagLevelOrder", [("root", "TreeNode")], "int[][]"),
    reference=_zigzag_level_order,
    brute=_zigzag_brute,
    examples=[Example([[3, 9, 20, None, None, 15, 7]], "[[3],[20,9],[15,7]]."), Example([[1]]), Example([[]])],
    edge_cases=[[[1, 2, 3, 4, 5, 6, 7]], [[1, 2, None, 3, None, 4]]],
    generator=lambda rng: [_small_tree(rng)],
    random_count=8,
)


# ---------------------------------------------------------------- Populating Next Right Pointers in Each Node


def _connect(root: TreeNode | None) -> list[str]:
    """Link each level with O(1) extra space, then serialise by following the links."""
    nxt: dict[TreeNode, TreeNode | None] = {}
    leftmost = root
    while leftmost and leftmost.left:
        node = leftmost
        while node:
            nxt[node.left] = node.right
            nxt[node.right] = nxt[node].left if nxt.get(node) else None
            node = nxt.get(node)
        leftmost = leftmost.left
    out, leftmost = [], root
    while leftmost:
        node = leftmost
        while node:
            out.append(str(node.val))
            node = nxt.get(node)
        out.append("#")
        leftmost = leftmost.left
    return out


def _connect_brute(root: TreeNode | None) -> list[str]:
    out = []
    for level in _levels(root):
        out += [str(n.val) for n in level] + ["#"]
    return out


def _perfect_tree(rng: random.Random) -> list:
    depth = rng.randint(0, rng.choice([4, 12]))
    return [[rng.randint(-1000, 1000) for _ in range(2**depth - 1)]]


POPULATE_NEXT = ProblemSource(
    title="Populating Next Right Pointers in Each Node",
    statement="""
The binary tree is *perfect*: every level is completely full. Conceptually, give every node a `next` pointer to the node immediately to its right
on the same level (`null` for the last node of each level), using only `O(1)` extra space besides the tree.

*Adapted I/O:* the judge's tree nodes have no `next` field, so return the result of **following your next pointers**: starting from the leftmost
node of each level, the values in the order the pointers visit them (as strings), with `"#"` after each level.
""",
    constraints="""
- `0 <= number of nodes <= 2^12 - 1`
- `-1000 <= Node.val <= 1000`
""",
    signature=function("connect", [("root", "TreeNode")], "string[]"),
    reference=_connect,
    brute=_connect_brute,
    is_variant=True,
    examples=[Example([[1, 2, 3, 4, 5, 6, 7]], "[\"1\",\"#\",\"2\",\"3\",\"#\",\"4\",\"5\",\"6\",\"7\",\"#\"]."), Example([[]])],
    edge_cases=[[[0]], [[1, 2, 3]]],
    generator=_perfect_tree,
    random_count=6,
)


# ---------------------------------------------------------------- Vertical Order Traversal of a Binary Tree


def _vertical_traversal(root: TreeNode) -> list[list[int]]:
    cells: list[tuple[int, int, int]] = []
    queue = deque([(root, 0, 0)])
    while queue:
        node, row, col = queue.popleft()
        cells.append((col, row, node.val))
        queue.extend((c, row + 1, col + d) for c, d in ((node.left, -1), (node.right, 1)) if c)
    cells.sort()
    return [[val for _, _, val in group] for _, group in itertools.groupby(cells, key=lambda c: c[0])]


def _vertical_brute(root: TreeNode) -> list[list[int]]:
    where: dict[int, list[tuple[int, int]]] = defaultdict(list)

    def walk(node: TreeNode | None, row: int, col: int) -> None:
        if node:
            where[col].append((row, node.val))
            walk(node.left, row + 1, col - 1)
            walk(node.right, row + 1, col + 1)

    walk(root, 0, 0)
    return [[v for _, v in sorted(where[c])] for c in sorted(where)]


VERTICAL_TRAVERSAL = ProblemSource(
    title="Vertical Order Traversal of a Binary Tree",
    statement="""
Place the root at row `0`, column `0`; a node at `(row, col)` has its left child at `(row + 1, col - 1)` and its right child at
`(row + 1, col + 1)`. Return one list per column, from the leftmost column to the rightmost. Within a column, order nodes from top to bottom;
nodes sharing the same row and column are ordered by value.
""",
    constraints="""
- `1 <= number of nodes <= 1000`
- `0 <= Node.val <= 1000`
""",
    signature=function("verticalTraversal", [("root", "TreeNode")], "int[][]"),
    reference=_vertical_traversal,
    brute=_vertical_brute,
    examples=[Example([[3, 9, 20, None, None, 15, 7]], "[[9],[3,15],[20],[7]]."), Example([[1, 2, 3, 4, 5, 6, 7]], "5 and 6 share row 2, column 0: sorted by value."), Example([[1, 2, 3, 4, 6, 5, 7]])],
    edge_cases=[[[1]], [[1, 2]], [[1, None, 2]]],
    generator=lambda rng: [_small_tree(rng, 0, rng.choice([5, 1000]), 1000)],
    random_count=8,
)


# ---------------------------------------------------------------- Symmetric Tree


def _is_symmetric(root: TreeNode) -> bool:
    queue = deque([(root.left, root.right)])
    while queue:
        a, b = queue.popleft()
        if a is None and b is None:
            continue
        if a is None or b is None or a.val != b.val:
            return False
        queue += [(a.left, b.right), (a.right, b.left)]
    return True


def _symmetric_brute(root: TreeNode) -> bool:
    return all(level == level[::-1] for level in _levels_with_gaps(root))


def _levels_with_gaps(root: TreeNode) -> list[list[int | None]]:
    out, level = [], [root]
    while any(level):
        out.append([n.val if n else None for n in level])
        level = [c for n in level for c in ((n.left, n.right) if n else (None, None))]
    return out


def _symmetric_gen(rng: random.Random) -> list:
    half = random_tree(rng, pick_n(rng, 0, 7, big=200), 1, rng.choice([3, 100]))

    def mirror(node: TreeNode | None) -> TreeNode | None:
        return None if node is None else TreeNode(node.val, mirror(node.right), mirror(node.left))

    left = tree_from_json(half)
    root = TreeNode(rng.randint(1, 100), left, mirror(left))
    nodes = _all_nodes(root)
    if rng.random() < 0.4 and len(nodes) > 1:
        rng.choice(nodes[1:]).val += 1
    return [tree_to_json(root)]


SYMMETRIC_TREE = ProblemSource(
    title="Symmetric Tree",
    statement="""
Return `true` if the binary tree is a mirror image of itself around its centre.
""",
    constraints="""
- `1 <= number of nodes <= 1000`
- `-100 <= Node.val <= 100`
""",
    signature=function("isSymmetric", [("root", "TreeNode")], "bool"),
    reference=_is_symmetric,
    brute=_symmetric_brute,
    examples=[Example([[1, 2, 2, 3, 4, 4, 3]]), Example([[1, 2, 2, None, 3, None, 3]], "Both 3s are right children.")],
    edge_cases=[[[1]], [[1, 2]], [[1, 2, 2]], [[1, 2, 2, 2, None, 2]]],
    generator=_symmetric_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Word Ladder


def _ladder_length(beginWord: str, endWord: str, wordList: list[str]) -> int:
    words = set(wordList)
    if endWord not in words:
        return 0
    front, back, seen, steps = {beginWord}, {endWord}, {beginWord, endWord}, 1
    while front and back:  # bidirectional BFS, always expanding the smaller side
        if len(front) > len(back):
            front, back = back, front
        steps += 1
        nxt = set()
        for w in front:
            for i in range(len(w)):
                for ch in "abcdefghijklmnopqrstuvwxyz":
                    candidate = w[:i] + ch + w[i + 1 :]
                    if candidate in back:
                        return steps
                    if candidate in words and candidate not in seen:
                        seen.add(candidate)
                        nxt.add(candidate)
        front = nxt
    return 0


def _ladder_brute(beginWord: str, endWord: str, wordList: list[str]) -> int:
    nodes = list(dict.fromkeys([beginWord, *wordList]))
    dist = {beginWord: 1}
    queue = deque([beginWord])
    while queue:
        w = queue.popleft()
        if w == endWord:
            return dist[w]
        for v in nodes:
            if v not in dist and sum(a != b for a, b in zip(v, w, strict=True)) == 1:
                dist[v] = dist[w] + 1
                queue.append(v)
    return 0


def _ladder_gen(rng: random.Random) -> list:
    length = rng.randint(2, 5)
    alphabet = "abcdef"[: rng.randint(2, 6)]
    begin = word(rng, length, alphabet)
    chain, current = [], begin
    for _ in range(rng.randint(1, 8)):  # a guaranteed ladder, often with detours available
        i = rng.randrange(length)
        current = current[:i] + rng.choice(alphabet) + current[i + 1 :]
        chain.append(current)
    noise = {word(rng, length, alphabet) for _ in range(rng.randint(0, rng.choice([10, 80])))}
    words = sorted((set(chain) | noise) - {begin})
    if not words:
        words = [word(rng, length, "xyz")]
    end = chain[-1] if chain[-1] != begin and rng.random() < 0.85 else rng.choice(words)
    return [begin, end, words]


WORD_LADDER = ProblemSource(
    title="Word Ladder",
    statement="""
A *transformation sequence* from `beginWord` to `endWord` is a list of words starting with `beginWord` and ending with `endWord` in which
consecutive words differ in exactly one letter, and every word after the first appears in `wordList`. Return the number of words in the shortest
such sequence, or `0` if none exists.
""",
    constraints="""
- `1 <= beginWord.length <= 10`; all words have the same length
- `1 <= wordList.length <= 5000`, words are distinct lowercase strings
- `beginWord != endWord`
""",
    signature=function("ladderLength", [("beginWord", "string"), ("endWord", "string"), ("wordList", "string[]")], "int"),
    reference=_ladder_length,
    brute=_ladder_brute,
    examples=[
        Example(["hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]], "hit -> hot -> dot -> dog -> cog."),
        Example(["hit", "cog", ["hot", "dot", "dog", "lot", "log"]], "cog is not in the word list."),
    ],
    edge_cases=[["a", "c", ["a", "b", "c"]], ["ab", "cd", ["ad", "cd"]], ["ab", "cd", ["ce", "cd"]]],
    generator=_ladder_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Connect All Siblings of a Binary Tree


def _connect_all_siblings(root: TreeNode | None) -> list[int]:
    """Chain every node to the next one in level order with O(1) extra space, then walk the chain."""
    if root is None:
        return []
    nxt: dict[TreeNode, TreeNode | None] = {}
    tail, current = root, root
    while current:  # `current` walks the chain; children are appended at its tail
        for child in (current.left, current.right):
            if child:
                nxt[tail] = child
                tail = child
        current = nxt.get(current)
    out, node = [], root
    while node:
        out.append(node.val)
        node = nxt.get(node)
    return out


CONNECT_ALL_SIBLINGS = ProblemSource(
    title="Connect All Siblings of a Binary Tree",
    statement="""
Conceptually, link every node of the binary tree to the next node in **level order** through a `next` pointer: the last node of a level points
to the first node of the next level, and the very last node points to `null`. Aim for `O(1)` extra space.

*Adapted I/O:* the judge's tree nodes have no `next` field, so return the values in the order your chain visits them, starting at the root.
""",
    constraints="""
- `0 <= number of nodes <= 500`
- `-1000 <= Node.val <= 1000`
""",
    signature=function("connectAllSiblings", [("root", "TreeNode")], "int[]"),
    reference=_connect_all_siblings,
    brute=lambda root: [n.val for level in _levels(root) for n in level],
    is_variant=True,
    examples=[Example([[100, 50, 200, 25, 75, 300, 10]], "100 -> 50 -> 200 -> 25 -> 75 -> 300 -> 10."), Example([[1, 2, None, 3]])],
    edge_cases=[[[]], [[7]], [[1, None, 2, None, 3]]],
    generator=lambda rng: [_small_tree(rng, -1000, 1000, 500)],
    random_count=8,
)


# ---------------------------------------------------------------- Two Sum IV - Input is a BST


def _find_target(root: TreeNode, k: int) -> bool:
    seen: set[int] = set()
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if k - node.val in seen:
            return True
        seen.add(node.val)
        queue.extend(c for c in (node.left, node.right) if c)
    return False


def _two_sum_bst_gen(rng: random.Random) -> list:
    tree = _random_bst(rng, _size(rng, 3000), -(hi := rng.choice([20, 10**4])), hi)
    values = [v for v in tree if v is not None]
    k = sum(sample(rng, values, 2)) if rng.random() < 0.5 and len(values) >= 2 else rng.randint(-2 * hi, 2 * hi)
    return [tree, k]


TWO_SUM_BST = ProblemSource(
    title="Two Sum IV - Input is a BST",
    statement="""
Given the root of a binary search tree and an integer `k`, return `true` if two different nodes have values that add up to `k`.
""",
    constraints="""
- `1 <= number of nodes <= 10^4`
- `-10^4 <= Node.val <= 10^4`, all distinct
- `-10^5 <= k <= 10^5`
""",
    signature=function("findTarget", [("root", "TreeNode"), ("k", "int")], "bool"),
    reference=_find_target,
    brute=lambda root, k: any(a.val + b.val == k for a, b in itertools.combinations(_all_nodes(root), 2)) if len(_all_nodes(root)) <= 300 else NotImplemented,
    examples=[Example([[5, 3, 6, 2, 4, None, 7], 9], "2 + 7 or 3 + 6 or 4 + 5."), Example([[5, 3, 6, 2, 4, None, 7], 28])],
    edge_cases=[[[1], 2], [[2, 1, 3], 4], [[2, 1, 3], 2]],
    generator=_two_sum_bst_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find Minimum Diameter After Merging Two Trees


def _diameter(n: int, edges: list[list[int]]) -> int:
    adjacent = _adjacency(n, edges)
    first = _bfs(adjacent, 0)
    far = max(first, key=first.__getitem__)
    return max(_bfs(adjacent, far).values())


def _minimum_diameter_after_merge(edges1: list[list[int]], edges2: list[list[int]]) -> int:
    d1, d2 = _diameter(len(edges1) + 1, edges1), _diameter(len(edges2) + 1, edges2)
    return max(d1, d2, (d1 + 1) // 2 + (d2 + 1) // 2 + 1)


def _merge_brute(edges1: list[list[int]], edges2: list[list[int]]) -> int:
    n, m = len(edges1) + 1, len(edges2) + 1
    if n * m > 150:
        return NotImplemented
    shifted = [[a + n, b + n] for a, b in edges2]
    return min(_diameter(n + m, edges1 + shifted + [[u, v + n]]) for u in range(n) for v in range(m))


MERGE_TREES_DIAMETER = ProblemSource(
    title="Find Minimum Diameter After Merging Two Trees",
    statement="""
Two undirected trees are given by `edges1` (nodes `0..n-1`) and `edges2` (nodes `0..m-1`). Add one edge joining any node of the first tree to
any node of the second. Return the minimum possible diameter (the longest path, in edges) of the combined tree.
""",
    constraints="""
- `1 <= n, m <= 10^5`
- `edges1` and `edges2` each form a tree
""",
    signature=function("minimumDiameterAfterMerge", [("edges1", "int[][]"), ("edges2", "int[][]")], "int"),
    reference=_minimum_diameter_after_merge,
    brute=_merge_brute,
    examples=[Example([[[0, 1], [0, 2], [0, 3]], [[0, 1]]], "Join node 0 of the star to either node: diameter 3."), Example([[[0, 1], [0, 2], [0, 3], [2, 4], [2, 5], [3, 6], [2, 7]], [[0, 1], [0, 2], [0, 3], [2, 4], [2, 5], [3, 6], [2, 7]]])],
    edge_cases=[[[], []], [[], [[0, 1]]], [[[0, 1], [1, 2], [2, 3]], []]],
    generator=lambda rng: [_tree_edges(rng, pick_n(rng, 1, 12, big=3000)), _tree_edges(rng, pick_n(rng, 1, 12, big=3000))],
    random_count=8,
)


# ---------------------------------------------------------------- Closest Node to Path in Tree


def _closest_node(n: int, edges: list[list[int]], query: list[list[int]]) -> list[int]:
    adjacent = _adjacency(n, edges)
    dist = [_bfs(adjacent, s) for s in range(n)]  # n <= 1000: all-pairs distances by BFS
    out = []
    for start, end, node in query:
        best, v = start, start
        while True:  # walk the path start -> end, tracking the node closest to `node`
            if dist[node][v] < dist[node][best]:
                best = v
            if v == end:
                break
            v = next(w for w in adjacent[v] if dist[end][w] == dist[end][v] - 1)
        out.append(best)
    return out


def _closest_node_brute(n: int, edges: list[list[int]], query: list[list[int]]) -> list[int]:
    adjacent = _adjacency(n, edges)
    out = []
    for start, end, node in query:
        from_start, from_end, from_node = _bfs(adjacent, start), _bfs(adjacent, end), _bfs(adjacent, node)
        path = [v for v in range(n) if from_start[v] + from_end[v] == from_start[end]]
        out.append(min(path, key=lambda v: (from_node[v], v)))
    return out


def _closest_query_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 12, big=300)
    return [n, _tree_edges(rng, n), [[rng.randrange(n) for _ in range(3)] for _ in range(rng.randint(1, rng.choice([5, 200])))]]


CLOSEST_NODE_PATH = ProblemSource(
    title="Closest Node to Path in Tree",
    statement="""
A tree has `n` nodes labelled `0` to `n - 1` joined by the undirected `edges`. Each `query[i] = [start, end, node]` asks for the node on the
(unique) path from `start` to `end` that is closest to `node`. Return the answers in query order.
""",
    constraints="""
- `1 <= n <= 1000`, `1 <= query.length <= 1000`
- `edges` forms a tree; `0 <= start, end, node < n`
""",
    signature=function("closestNode", [("n", "int"), ("edges", "int[][]"), ("query", "int[][]")], "int[]"),
    reference=_closest_node,
    brute=_closest_node_brute,
    brute_input_limit=3000,
    examples=[Example([7, [[0, 1], [0, 2], [0, 3], [1, 4], [2, 5], [2, 6]], [[5, 3, 4], [5, 3, 6]]], "Path 5-2-0-3: node 4 is closest to 0, node 6 to 2."), Example([3, [[0, 1], [1, 2]], [[0, 1, 2]]]), Example([3, [[0, 1], [1, 2]], [[0, 0, 0]]])],
    edge_cases=[[1, [], [[0, 0, 0]]], [2, [[0, 1]], [[0, 1, 1], [1, 1, 0]]]],
    generator=_closest_query_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Frog Position After T Seconds


def _frog_position(n: int, edges: list[list[int]], t: int, target: int) -> float:
    adjacent = _adjacency(n, edges, first=1)
    level = [(1, 0, 1.0)]  # (vertex, parent, probability)
    for _ in range(t):
        nxt = []
        for v, parent, p in level:
            children = [w for w in adjacent[v] if w != parent]
            if not children:
                nxt.append((v, parent, p))  # stuck: it stays forever
            nxt += [(w, v, p / len(children)) for w in children]
        level = nxt
    return sum(p for v, _, p in level if v == target)


def _frog_brute(n: int, edges: list[list[int]], t: int, target: int) -> float:
    adjacent = _adjacency(n, edges, first=1)

    def walk(v: int, visited: frozenset[int], time: int) -> Fraction:
        options = [w for w in adjacent[v] if w not in visited]
        if time == 0 or not options:
            return Fraction(int(v == target))
        return sum((walk(w, visited | {w}, time - 1) for w in options), Fraction(0)) / len(options)

    return float(walk(1, frozenset({1}), t))


FROG_POSITION = ProblemSource(
    title="Frog Position After T Seconds",
    statement="""
An undirected tree has vertices `1` to `n`. A frog starts on vertex `1`. Every second it jumps to an unvisited neighbouring vertex, chosen
uniformly at random; if every neighbour has been visited it stays where it is forever. Return the probability that the frog is on `target` after
exactly `t` seconds. Answers within `10^-5` are accepted.
""",
    constraints="""
- `1 <= n <= 100`, `edges.length == n - 1`
- `1 <= t <= 50`, `1 <= target <= n`
""",
    signature=function("frogPosition", [("n", "int"), ("edges", "int[][]"), ("t", "int"), ("target", "int")], "double"),
    reference=_frog_position,
    brute=_frog_brute,
    compare="float_tolerance",
    examples=[Example([7, [[1, 2], [1, 3], [1, 7], [2, 4], [2, 6], [3, 5]], 2, 4], "1/3 to reach 2, then 1/2 to reach 4."), Example([7, [[1, 2], [1, 3], [1, 7], [2, 4], [2, 6], [3, 5]], 1, 7])],
    edge_cases=[[1, [], 5, 1], [2, [[1, 2]], 1, 1], [3, [[2, 1], [3, 2]], 1, 2], [3, [[2, 1], [3, 2]], 20, 3]],
    generator=lambda rng: [(n := pick_n(rng, 1, 12, big=100)), _tree_edges(rng, n, first=1), rng.randint(1, rng.choice([4, 50])), rng.randint(1, n)],
    random_count=8,
)


# ---------------------------------------------------------------- Average of Levels in Binary Tree


def _average_of_levels(root: TreeNode) -> list[float]:
    return [sum(n.val for n in level) / len(level) for level in _levels(root)]


AVERAGE_OF_LEVELS = ProblemSource(
    title="Average of Levels in Binary Tree",
    statement="""
Return the average value of the nodes on each level of the binary tree, from the root down. Answers within `10^-5` are accepted.
""",
    constraints="""
- `1 <= number of nodes <= 10^4`
- `-2^31 <= Node.val <= 2^31 - 1`
""",
    signature=function("averageOfLevels", [("root", "TreeNode")], "double[]"),
    reference=_average_of_levels,
    brute=lambda root: [sum(v for v in row) / len(row) for row in _level_order_brute(root)],
    compare="float_tolerance",
    examples=[Example([[3, 9, 20, None, None, 15, 7]], "3, then 14.5, then 11."), Example([[3, 9, 20, 15, 7]])],
    edge_cases=[[[1]], [[2147483647, 2147483647, 2147483647]], [[-2147483648, 1, -1]]],
    generator=lambda rng: [_small_tree(rng, -(2**31), 2**31 - 1, 3000)],
    random_count=8,
)


# ---------------------------------------------------------------- Open the Lock


def _turns(code: str) -> list[str]:
    out = []
    for i, ch in enumerate(code):
        for d in (1, 9):
            out.append(code[:i] + str((int(ch) + d) % 10) + code[i + 1 :])
    return out


def _open_lock(deadends: list[str], target: str) -> int:
    dead = set(deadends)
    if "0000" in dead:
        return -1
    front, back, seen, steps = {"0000"}, {target}, {"0000", target}, 0
    if target == "0000":
        return 0
    while front and back:
        if len(front) > len(back):
            front, back = back, front
        steps += 1
        nxt = set()
        for code in front:
            for c in _turns(code):
                if c in back:
                    return steps
                if c not in dead and c not in seen:
                    seen.add(c)
                    nxt.add(c)
        front = nxt
    return -1


def _open_lock_brute(deadends: list[str], target: str) -> int:
    dead = set(deadends)
    if "0000" in dead:
        return -1
    dist = {"0000": 0}
    queue = deque(["0000"])
    while queue:
        code = queue.popleft()
        if code == target:
            return dist[code]
        for c in _turns(code):
            if c not in dead and c not in dist:
                dist[c] = dist[code] + 1
                queue.append(c)
    return -1


def _lock_gen(rng: random.Random) -> list:
    target = "".join(str(rng.randint(0, 9)) for _ in range(4))
    dead = {"".join(str(rng.randint(0, 9)) for _ in range(4)) for _ in range(rng.randint(1, rng.choice([10, 500])))}
    if rng.random() < 0.3:
        dead |= set(_turns(target))  # wall off the target
    dead.discard(target)
    return [sorted(dead), target]


OPEN_THE_LOCK = ProblemSource(
    title="Open the Lock",
    statement="""
A lock has four circular wheels with the digits `0`-`9`; one move turns a single wheel one step either way (`9` wraps to `0` and back). The lock
starts at `"0000"`. If it ever shows a code in `deadends`, it jams. Return the minimum number of moves to reach `target` without jamming, or `-1`
if that's impossible.
""",
    constraints="""
- `1 <= deadends.length <= 500`; every code has 4 digits
- `target` is not in `deadends`
""",
    signature=function("openLock", [("deadends", "string[]"), ("target", "string")], "int"),
    reference=_open_lock,
    brute=_open_lock_brute,
    examples=[
        Example([["0201", "0101", "0102", "1212", "2002"], "0202"], "0000 -> 1000 -> 1100 -> 1200 -> 1201 -> 1202 -> 0202."),
        Example([["8888"], "0009"], "Turn the last wheel backwards once."),
        Example([["8887", "8889", "8878", "8898", "8788", "8988", "7888", "9888"], "8888"], "Every neighbour of the target is a deadend."),
    ],
    edge_cases=[[["0000"], "8888"], [["1111"], "0000"], [["1234"], "5555"]],
    generator=_lock_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Shortest Distance from All Buildings


def _shortest_distance(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    total = [[0] * n for _ in range(m)]
    reach = [[0] * n for _ in range(m)]
    buildings = [(i, j) for i in range(m) for j in range(n) if grid[i][j] == 1]
    for bi, bj in buildings:
        dist = {(bi, bj): 0}
        queue = deque([(bi, bj)])
        while queue:
            i, j = queue.popleft()
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if 0 <= a < m and 0 <= b < n and grid[a][b] == 0 and (a, b) not in dist:
                    dist[(a, b)] = dist[(i, j)] + 1
                    total[a][b] += dist[(a, b)]
                    reach[a][b] += 1
                    queue.append((a, b))
    options = [total[i][j] for i in range(m) for j in range(n) if grid[i][j] == 0 and reach[i][j] == len(buildings)]
    return min(options, default=-1)


def _all_buildings_brute(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    buildings = {(i, j) for i in range(m) for j in range(n) if grid[i][j] == 1}
    best = -1
    for i in range(m):
        for j in range(n):
            if grid[i][j]:
                continue
            dist = {(i, j): 0}
            queue = deque([(i, j)])
            found = 0
            while queue:
                a, b = queue.popleft()
                for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= c < m and 0 <= d < n and (c, d) not in dist and grid[c][d] != 2:
                        dist[(c, d)] = dist[(a, b)] + 1
                        if grid[c][d] == 1:
                            found += dist[(c, d)]
                        else:
                            queue.append((c, d))
            if all(bld in dist for bld in buildings):
                best = found if best == -1 else min(best, found)
    return best


def _buildings_gen(rng: random.Random) -> list:
    m, n = pick_n(rng, 1, 7, big=50), pick_n(rng, 1, 7, big=50)
    grid = [[rng.choice([0, 0, 0, 0, 1, 2]) for _ in range(n)] for _ in range(m)]
    i, j = rng.randrange(m), rng.randrange(n)
    grid[i][j] = 1  # at least one building
    return [grid]


ALL_BUILDINGS = ProblemSource(
    title="Shortest Distance from All Buildings",
    statement="""
In the grid, `0` is empty land you can walk through, `1` is a building you can't pass through, and `2` is an obstacle. Find an empty cell from
which every building can be reached, moving up, down, left or right through empty land, with the smallest **sum** of shortest distances to all
buildings. Return that sum, or `-1` if no such cell exists.
""",
    constraints="""
- `1 <= m, n <= 50`
- `grid[i][j]` is `0`, `1` or `2`; there is at least one building
""",
    signature=function("shortestDistance", [("grid", "int[][]")], "int"),
    reference=_shortest_distance,
    brute=_all_buildings_brute,
    brute_input_limit=800,
    examples=[Example([[[1, 0, 2, 0, 1], [0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]], "Cell (1, 2) is 3 + 3 + 1 = 7 steps from the buildings."), Example([[[1, 0]]]), Example([[[1]]], "No empty land at all.")],
    edge_cases=[[[[1, 2, 0]]], [[[0, 1, 0]]], [[[1, 0, 1]]]],
    generator=_buildings_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Binary Tree Vertical Order Traversal


def _vertical_order(root: TreeNode | None) -> list[list[int]]:
    columns: dict[int, list[int]] = defaultdict(list)
    queue = deque([(root, 0)] if root else [])
    while queue:
        node, col = queue.popleft()
        columns[col].append(node.val)
        queue.extend((c, col + d) for c, d in ((node.left, -1), (node.right, 1)) if c)
    return [columns[c] for c in sorted(columns)]


def _vertical_order_brute(root: TreeNode | None) -> list[list[int]]:
    where: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for row, level in enumerate(_levels(root)):
        # recompute columns per level: a node's column is its parent's +-1
        for position, node in enumerate(level):
            where[_column_of(root, node)].append((row, position, node.val))
    return [[v for _, _, v in sorted(where[c])] for c in sorted(where)]


def _column_of(root: TreeNode | None, target: TreeNode) -> int:
    parent = _parents(root)
    col = 0
    while parent[target] is not None:
        col += -1 if parent[target].left is target else 1
        target = parent[target]
    return col


VERTICAL_ORDER = ProblemSource(
    title="Binary Tree Vertical Order Traversal",
    statement="""
Return the binary tree's values column by column, from the leftmost column to the rightmost (the root is column `0`, a left child is one column
to the left of its parent and a right child one to the right). Within a column list nodes from top to bottom, and nodes in the same row and
column from left to right.
""",
    constraints="""
- `0 <= number of nodes <= 100`
- `-100 <= Node.val <= 100`
""",
    signature=function("verticalOrder", [("root", "TreeNode")], "int[][]"),
    reference=_vertical_order,
    brute=_vertical_order_brute,
    examples=[Example([[3, 9, 20, None, None, 15, 7]], "[[9],[3,15],[20],[7]]."), Example([[3, 9, 8, 4, 0, 1, 7]], "0 and 1 share a row and column: 0 is further left."), Example([[]])],
    edge_cases=[[[1]], [[1, 2, 3, None, 4, 5]]],
    generator=lambda rng: [random_tree(rng, pick_n(rng, 1, 15, big=100), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Depth of Binary Tree


def _min_depth(root: TreeNode | None) -> int:
    queue = deque([(root, 1)] if root else [])
    while queue:
        node, depth = queue.popleft()
        if node.left is None and node.right is None:
            return depth
        queue.extend((c, depth + 1) for c in (node.left, node.right) if c)
    return 0


def _min_depth_brute(root: TreeNode | None) -> int:
    if root is None:
        return 0
    children = [c for c in (root.left, root.right) if c]
    return 1 + (min(_min_depth_brute(c) for c in children) if children else 0)


MIN_DEPTH = ProblemSource(
    title="Minimum Depth of Binary Tree",
    statement="""
Return the minimum depth of the binary tree: the number of nodes on the shortest path from the root down to a **leaf** (a node without children),
or `0` for an empty tree.
""",
    constraints="""
- `0 <= number of nodes <= 10^5`
- `-1000 <= Node.val <= 1000`
""",
    signature=function("minDepth", [("root", "TreeNode")], "int"),
    reference=_min_depth,
    brute=_min_depth_brute,
    examples=[Example([[3, 9, 20, None, None, 15, 7]]), Example([[2, None, 3, None, 4, None, 5, None, 6]], "The only leaf is 6.")],
    edge_cases=[[[]], [[1]], [[1, 2]]],
    generator=lambda rng: [_small_tree(rng, -1000, 1000, 800)],
    random_count=8,
)


PROBLEMS = [
    LEVEL_ORDER,
    ZIGZAG,
    POPULATE_NEXT,
    VERTICAL_TRAVERSAL,
    SYMMETRIC_TREE,
    WORD_LADDER,
    CONNECT_ALL_SIBLINGS,
    TWO_SUM_BST,
    MERGE_TREES_DIAMETER,
    CLOSEST_NODE_PATH,
    FROG_POSITION,
    AVERAGE_OF_LEVELS,
    OPEN_THE_LOCK,
    ALL_BUILDINGS,
    VERTICAL_ORDER,
    MIN_DEPTH,
]
