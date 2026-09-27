"""Pattern 12: Backtracking (part 2 of 2). Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import itertools
from collections import defaultdict, deque

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, random_tree, sample, word

PATTERN_NUMBER = 12


# ---------------------------------------------------------------- Binary Tree Paths


def _binary_tree_paths(root) -> list[str]:
    out = []

    def walk(node, path: list[str]) -> None:
        path = path + [str(node.val)]
        if not node.left and not node.right:
            out.append("->".join(path))
        for child in (node.left, node.right):
            if child:
                walk(child, path)

    walk(root, [])
    return out


def _tree_paths_brute(root) -> list[str]:
    out, stack = [], [(root, str(root.val))]
    while stack:
        node, path = stack.pop()
        if not node.left and not node.right:
            out.append(path)
        for child in (node.right, node.left):
            if child:
                stack.append((child, f"{path}->{child.val}"))
    return out


TREE_PATHS = ProblemSource(
    title="Binary Tree Paths",
    statement="""
Return every root-to-leaf path of the binary tree, in any order. Write a path as its node values joined by `"->"`, for example `"1->2->5"`.
A leaf is a node with no children.
""",
    constraints="""
- the tree has between `1` and `100` nodes
- `-100 <= Node.val <= 100`
""",
    signature=function("binaryTreePaths", [("root", "TreeNode")], "string[]"),
    reference=_binary_tree_paths,
    brute=_tree_paths_brute,
    compare="unordered",
    examples=[Example([[1, 2, 3, None, 5]], "\"1->2->5\" and \"1->3\"."), Example([[1]])],
    edge_cases=[[[1, 1, 1]], [[-100, None, 100]]],
    generator=lambda rng: [random_tree(rng, pick_n(rng, 1, 15, big=100), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- All Paths From Source to Target


def _all_paths(graph: list[list[int]]) -> list[list[int]]:
    target, out = len(graph) - 1, []

    def walk(node: int, path: list[int]) -> None:
        if node == target:
            out.append(path)
            return
        for nxt in graph[node]:
            walk(nxt, path + [nxt])

    walk(0, [0])
    return out


def _all_paths_brute(graph: list[list[int]]) -> list[list[int]]:
    target, out, frontier = len(graph) - 1, [], deque([[0]])
    while frontier:
        path = frontier.popleft()
        if path[-1] == target:
            out.append(path)
            continue
        frontier.extend(path + [nxt] for nxt in graph[path[-1]])
    return out


def _dag_gen(rng):
    n = rng.randint(2, rng.choice([6, 12]))
    graph = [sorted(sample(rng, range(i + 1, n), rng.randint(0, min(3, n - i - 1)))) for i in range(n)]
    graph[-1] = []
    return [graph]


ALL_PATHS = ProblemSource(
    title="All Paths From Source to Target",
    statement="""
A directed acyclic graph has nodes `0..n-1`; `graph[i]` lists the nodes reachable from node `i` by one edge. Return every path from node
`0` to node `n - 1`, in any order.
""",
    constraints="""
- `2 <= n <= 15`
- `graph[i]` holds distinct nodes, never `i` itself, and the graph has no cycles
""",
    signature=function("allPathsSourceTarget", [("graph", "int[][]")], "int[][]"),
    reference=_all_paths,
    brute=_all_paths_brute,
    compare="unordered",
    examples=[Example([[[1, 2], [3], [3], []]], "0 -> 1 -> 3 and 0 -> 2 -> 3."), Example([[[4, 3, 1], [3, 2, 4], [3], [4], []]])],
    edge_cases=[[[[1], []]], [[[], []]], [[[1, 2], [2], []]]],
    generator=_dag_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Remove Invalid Parentheses


def _valid_parens(t: str) -> bool:
    depth = 0
    for ch in t:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def _remove_invalid(s: str) -> list[str]:
    level = {s}
    while True:
        valid = [t for t in level if _valid_parens(t)]
        if valid:
            return sorted(valid)
        level = {t[:i] + t[i + 1 :] for t in level for i in range(len(t)) if t[i] in "()"}


def _remove_invalid_brute(s: str) -> list[str]:
    for keep in range(len(s), -1, -1):
        found = {"".join(s[i] for i in idx) for idx in itertools.combinations(range(len(s)), keep)}
        found = {t for t in found if _valid_parens(t) and sorted(c for c in t if c not in "()") == sorted(c for c in s if c not in "()")}
        if found:
            return sorted(found)
    return [""]


REMOVE_INVALID_PARENS = ProblemSource(
    title="Remove Invalid Parentheses",
    statement="""
`s` contains parentheses and lowercase letters. Remove the **minimum** number of parentheses so that the result is valid (every `(` has a
later matching `)`). Return every distinct result that achieves this minimum, in any order. Letters are never removed.
""",
    constraints="""
- `1 <= s.length <= 25`
- `s` has lowercase letters, `(` and `)`, with at most 20 parentheses
""",
    signature=function("removeInvalidParentheses", [("s", "string")], "string[]"),
    reference=_remove_invalid,
    brute=_remove_invalid_brute,
    brute_input_limit=16,
    compare="unordered",
    examples=[Example(["()())()"], "\"(())()\" and \"()()()\"."), Example(["(a)())()"]), Example([")("], "Only the empty string remains.")],
    edge_cases=[["x"], ["("], ["()"], ["((("], ["(a(b)"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([10, 18])), "(()a)")],
    random_count=8,
)


# ---------------------------------------------------------------- Unique Paths III


def _unique_paths_iii(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    empty = sum(row.count(0) for row in grid) + 1
    start = next((i, j) for i in range(m) for j in range(n) if grid[i][j] == 1)

    def walk(i: int, j: int, left: int) -> int:
        if not (0 <= i < m and 0 <= j < n) or grid[i][j] == -1:
            return 0
        if grid[i][j] == 2:
            return int(left == 0)
        grid[i][j] = -1
        total = sum(walk(i + di, j + dj, left - 1) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        grid[i][j] = 0
        return total

    return walk(*start, empty)


def _unique_paths_brute(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    cells = [(i, j) for i in range(m) for j in range(n) if grid[i][j] != -1]
    start = next(c for c in cells if grid[c[0]][c[1]] == 1)
    end = next(c for c in cells if grid[c[0]][c[1]] == 2)
    middle = [c for c in cells if c not in (start, end)]
    count = 0
    for order in itertools.permutations(middle):
        path = [start, *order, end]
        if all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in itertools.pairwise(path)):
            count += 1
    return count


def _paths_iii_gen(rng):
    m, n = rng.randint(1, 4), rng.randint(2, 4)
    grid = [[0 if rng.random() < 0.8 else -1 for _ in range(n)] for _ in range(m)]
    a, b = rng.sample([(i, j) for i in range(m) for j in range(n)], 2)
    grid[a[0]][a[1]], grid[b[0]][b[1]] = 1, 2
    return [grid]


UNIQUE_PATHS_III = ProblemSource(
    title="Unique Paths III",
    statement="""
In the grid, `1` is the start, `2` is the end, `0` is an empty square you may walk on and `-1` is an obstacle. Moving up, down, left or right,
count the walks from start to end that visit **every non-obstacle square exactly once**.
""",
    constraints="""
- `1 <= m, n <= 20`, `1 <= m * n <= 20`
- exactly one start and one end
""",
    signature=function("uniquePathsIII", [("grid", "int[][]")], "int"),
    reference=_unique_paths_iii,
    brute=lambda grid: _unique_paths_brute(grid) if sum(row.count(0) for row in grid) <= 8 else NotImplemented,
    examples=[Example([[[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 2, -1]]], "Two walks cover every square."), Example([[[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 2]]]), Example([[[0, 1], [2, 0]]], "No walk covers both empty squares.")],
    edge_cases=[[[[1, 2]]], [[[1, -1, 2]]], [[[1, 0, 2]]], [[[2, 0, 1]]]],
    generator=_paths_iii_gen,
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- N-Queens


def _solve_n_queens(n: int) -> list[list[str]]:
    out: list[list[str]] = []

    def place(row: int, cols: list[int]) -> None:
        if row == n:
            out.append(["." * c + "Q" + "." * (n - c - 1) for c in cols])
            return
        for c in range(n):
            if all(c != pc and abs(c - pc) != row - pr for pr, pc in enumerate(cols)):
                place(row + 1, cols + [c])

    place(0, [])
    return out


def _n_queens_brute(n: int) -> list[list[str]]:
    return [
        ["." * c + "Q" + "." * (n - c - 1) for c in perm]
        for perm in itertools.permutations(range(n))
        if all(abs(perm[i] - perm[j]) != j - i for i in range(n) for j in range(i + 1, n))
    ]


N_QUEENS = ProblemSource(
    title="N-Queens",
    statement="""
Place `n` queens on an `n x n` board so that no two attack each other. Return every distinct placement, in any order. Describe a board as `n`
strings, one per row, using `'Q'` for a queen and `'.'` for an empty square.
""",
    constraints="""
- `1 <= n <= 9`
""",
    signature=function("solveNQueens", [("n", "int")], "string[][]"),
    reference=_solve_n_queens,
    brute=lambda n: _n_queens_brute(n) if n <= 7 else NotImplemented,
    compare="unordered",
    examples=[Example([4], "Two boards."), Example([1], "[[\"Q\"]].")],
    edge_cases=[[2], [3], [5], [6], [8]],
    generator=lambda rng: [rng.randint(1, 8)],
    random_count=3,
)


# ---------------------------------------------------------------- Combinations


def _combine(n: int, k: int) -> list[list[int]]:
    out: list[list[int]] = []

    def build(start: int, chosen: list[int]) -> None:
        if len(chosen) == k:
            out.append(chosen[:])
            return
        for x in range(start, n - (k - len(chosen)) + 2):
            chosen.append(x)
            build(x + 1, chosen)
            chosen.pop()

    build(1, [])
    return out


COMBINATIONS = ProblemSource(
    title="Combinations",
    statement="""
Return every way to choose `k` distinct numbers from `1..n`, in any order (each combination's numbers may be in any order too).
""",
    constraints="""
- `1 <= k <= n <= 20` (tests keep the output small)
""",
    signature=function("combine", [("n", "int"), ("k", "int")], "int[][]"),
    reference=_combine,
    brute=lambda n, k: [list(c) for c in itertools.combinations(range(1, n + 1), k)],
    compare="unordered_nested",
    examples=[Example([4, 2], "Six pairs."), Example([1, 1])],
    edge_cases=[[5, 5], [5, 1], [12, 3]],
    generator=lambda rng: [(n := rng.randint(1, 12)), rng.choice([rng.randint(1, min(n, 3)), n - rng.randint(0, min(2, n - 1))])],
    random_count=6,
)


# ---------------------------------------------------------------- Word Ladder II


def _find_ladders(beginWord: str, endWord: str, wordList: list[str]) -> list[list[str]]:
    words = set(wordList)
    if endWord not in words:
        return []
    parents: dict[str, list[str]] = defaultdict(list)
    level, seen, found = {beginWord}, {beginWord}, False
    while level and not found:
        nxt: set[str] = set()
        for w in level:
            for i in range(len(w)):
                for c in "abcdefghijklmnopqrstuvwxyz":
                    cand = w[:i] + c + w[i + 1 :]
                    if cand in words and cand not in seen:
                        if cand == endWord:
                            found = True
                        nxt.add(cand)
                        parents[cand].append(w)
        seen |= nxt
        level = nxt
    if not found:
        return []
    out: list[list[str]] = []

    def backtrack(w: str, path: list[str]) -> None:
        if w == beginWord:
            out.append(path[::-1])
            return
        for p in parents[w]:
            backtrack(p, path + [p])

    backtrack(endWord, [endWord])
    return out


def _ladders_brute(beginWord: str, endWord: str, wordList: list[str]) -> list[list[str]]:
    words = sorted(set(wordList) | {beginWord})

    def adjacent(a: str, b: str) -> bool:
        return sum(x != y for x, y in zip(a, b, strict=True)) == 1

    frontier, done = [[beginWord]], []
    for _ in range(len(words)):
        if done or not frontier:
            break
        extended = []
        for path in frontier:
            for w in words:
                if w not in path and w in wordList and adjacent(path[-1], w):
                    extended.append(path + [w])
        done = [p for p in extended if p[-1] == endWord]
        frontier = extended
    return done


def _ladder_gen(rng):
    size = rng.randint(2, 3)
    words = sorted({word(rng, size, "abc") for _ in range(rng.randint(3, 12))})
    begin = word(rng, size, "abc")
    end = rng.choice(words) if rng.random() < 0.85 else word(rng, size, "abc")
    return [begin, end, words]


WORD_LADDER_II = ProblemSource(
    title="Word Ladder II",
    statement="""
A *transformation sequence* from `beginWord` to `endWord` is a list of words starting with `beginWord` where each next word differs from
the previous one in exactly one letter and belongs to `wordList` (`beginWord` itself doesn't need to be in `wordList`).

Return **all** shortest transformation sequences from `beginWord` to `endWord`, in any order, or an empty list if there is none.
""",
    constraints="""
- `1 <= beginWord.length <= 5`, all words have the same length
- `1 <= wordList.length <= 500`, words are distinct
- words consist of lowercase English letters, and `beginWord != endWord`
""",
    signature=function("findLadders", [("beginWord", "string"), ("endWord", "string"), ("wordList", "string[]")], "string[][]"),
    reference=_find_ladders,
    brute=_ladders_brute,
    brute_input_limit=150,
    compare="unordered",
    examples=[
        Example(["hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]], "hit -> hot -> dot -> dog -> cog and hit -> hot -> lot -> log -> cog."),
        Example(["hit", "cog", ["hot", "dot", "dog", "lot", "log"]], "\"cog\" isn't in the list."),
    ],
    edge_cases=[["a", "c", ["a", "b", "c"]], ["ab", "cd", ["ad", "cb", "cd"]], ["aa", "bb", ["ab", "ba", "bb"]]],
    generator=_ladder_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Flip Game


def _generate_possible_next_moves(currentState: str) -> list[str]:
    return [currentState[:i] + "--" + currentState[i + 2 :] for i in range(len(currentState) - 1) if currentState[i : i + 2] == "++"]


def _flip_brute(currentState: str) -> list[str]:
    out = []
    for i in range(len(currentState) - 1):
        chars = list(currentState)
        if chars[i] == chars[i + 1] == "+":
            chars[i] = chars[i + 1] = "-"
            out.append("".join(chars))
    return out


FLIP_GAME = ProblemSource(
    title="Flip Game",
    statement="""
In the Flip Game, a string contains only `'+'` and `'-'`. One move flips two consecutive `"++"` into `"--"`. Return every state that can be
reached from `currentState` with exactly one move, in any order (an empty list if no move is possible).
""",
    constraints="""
- `1 <= currentState.length <= 500`
- `currentState[i]` is `'+'` or `'-'`
""",
    signature=function("generatePossibleNextMoves", [("currentState", "string")], "string[]"),
    reference=_generate_possible_next_moves,
    brute=_flip_brute,
    compare="unordered",
    examples=[Example(["++++"], "\"--++\", \"+--+\" and \"++--\"."), Example(["+"])],
    edge_cases=[["--"], ["+-+"], ["++"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 20, big=500), "++-")],
    random_count=7,
)


# ---------------------------------------------------------------- Additive Number


def _is_additive(num: str) -> bool:
    n = len(num)
    for i in range(1, n):
        for j in range(i + 1, n):
            a, b = num[:i], num[i:j]
            if (len(a) > 1 and a[0] == "0") or (len(b) > 1 and b[0] == "0"):
                continue
            x, y, k = int(a), int(b), j
            while k < n:
                z = str(x + y)
                if not num.startswith(z, k):
                    break
                k += len(z)
                x, y = y, int(z)
            else:
                return True
    return False


def _is_additive_brute(num: str) -> bool:
    n = len(num)
    for cuts_count in range(2, n):
        for cuts in itertools.combinations(range(1, n), cuts_count):
            parts = [num[a:b] for a, b in itertools.pairwise((0, *cuts, n))]
            if any(len(p) > 1 and p[0] == "0" for p in parts):
                continue
            values = list(map(int, parts))
            if all(values[i] == values[i - 1] + values[i - 2] for i in range(2, len(values))):
                return True
    return False


def _additive_gen(rng):
    if rng.random() < 0.6:
        a, b = rng.randint(0, rng.choice([9, 999])), rng.randint(0, rng.choice([9, 999]))
        seq = [a, b]
        for _ in range(rng.randint(1, 5)):
            seq.append(seq[-1] + seq[-2])
        s = "".join(map(str, seq))
        if rng.random() < 0.3:
            i = rng.randrange(len(s))
            s = s[:i] + rng.choice("0123456789") + s[i + 1 :]
        return [s[:35]]
    return [word(rng, rng.randint(1, 12), "0123456789")]


ADDITIVE_NUMBER = ProblemSource(
    title="Additive Number",
    statement="""
A string of digits is *additive* if it can be split into at least three numbers where each number after the first two is the sum of the two
before it. Numbers in the sequence can't have leading zeros (`"0"` itself is fine, `"03"` isn't).

Return `true` if `num` is additive.
""",
    constraints="""
- `1 <= num.length <= 35`
- `num` consists of digits
""",
    signature=function("isAdditiveNumber", [("num", "string")], "bool"),
    reference=_is_additive,
    brute=_is_additive_brute,
    brute_input_limit=16,
    examples=[Example(["112358"], "1, 1, 2, 3, 5, 8."), Example(["199100199"], "1, 99, 100, 199.")],
    edge_cases=[["1"], ["123"], ["000"], ["1023"], ["101"], ["198019823962"]],
    generator=_additive_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Combination Sum II


def _combination_sum_ii(candidates: list[int], target: int) -> list[list[int]]:
    candidates = sorted(candidates)
    out: list[list[int]] = []

    def build(start: int, chosen: list[int], remaining: int) -> None:
        if remaining == 0:
            out.append(chosen[:])
            return
        for i in range(start, len(candidates)):
            if i > start and candidates[i] == candidates[i - 1]:
                continue
            if candidates[i] > remaining:
                break
            chosen.append(candidates[i])
            build(i + 1, chosen, remaining - candidates[i])
            chosen.pop()

    build(0, [], target)
    return out


def _combination_sum_ii_brute(candidates: list[int], target: int) -> list[list[int]]:
    found = {tuple(sorted(c)) for r in range(1, len(candidates) + 1) for c in itertools.combinations(candidates, r) if sum(c) == target}
    return [list(t) for t in found]


COMBINATION_SUM_II = ProblemSource(
    title="Combination Sum II",
    statement="""
Given a list of positive integers `candidates` (which may contain duplicates) and a `target`, return every **distinct** combination of
candidates that adds up to `target`. Each candidate may be used at most once, and combinations are compared as multisets, so the answer never
lists the same combination twice. Any order is accepted.
""",
    constraints="""
- `1 <= candidates.length <= 100`
- `1 <= candidates[i] <= 50`
- `1 <= target <= 30`
""",
    signature=function("combinationSum2", [("candidates", "int[]"), ("target", "int")], "int[][]"),
    reference=_combination_sum_ii,
    brute=_combination_sum_ii_brute,
    brute_input_limit=45,
    compare="unordered_nested",
    examples=[Example([[10, 1, 2, 7, 6, 1, 5], 8], "[1,1,6], [1,2,5], [1,7], [2,6]."), Example([[2, 5, 2, 1, 2], 5], "[1,2,2] and [5].")],
    edge_cases=[[[1], 1], [[2], 1], [[1, 1, 1, 1], 2], [[30], 30]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 12, big=100), 1, rng.choice([6, 50])), rng.randint(1, 30)],
    random_count=8,
)


PROBLEMS = [
    TREE_PATHS,
    ALL_PATHS,
    REMOVE_INVALID_PARENS,
    UNIQUE_PATHS_III,
    N_QUEENS,
    COMBINATIONS,
    WORD_LADDER_II,
    FLIP_GAME,
    ADDITIVE_NUMBER,
    COMBINATION_SUM_II,
]
