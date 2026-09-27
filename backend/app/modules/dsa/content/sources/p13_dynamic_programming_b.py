"""Pattern 13: Dynamic Programming (part 2 of 3). Original statements; outputs come from `reference`."""

from __future__ import annotations

import heapq
import itertools
import re
from collections import Counter
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, word

PATTERN_NUMBER = 13
_MOD = 10**9 + 7


def _char_grid_gen(density: float, big: int):
    def gen(rng):
        rows, cols = pick_n(rng, 1, 6, big=big), pick_n(rng, 1, 6, big=big)
        return [[["1" if rng.random() < density else "0" for _ in range(cols)] for _ in range(rows)]]

    return gen


def _int_grid_gen(lo: int, his: list[int], big: int, small: int = 5):
    def gen(rng):
        rows, cols = pick_n(rng, 1, small, big=big), pick_n(rng, 1, small, big=big)
        hi = rng.choice(his)
        return [[ints(rng, cols, lo, hi) for _ in range(rows)]]

    return gen


# ---------------------------------------------------------------- Triangle


def _minimum_total(triangle: list[list[int]]) -> int:
    best = list(triangle[-1])
    for row in reversed(triangle[:-1]):
        best = [x + min(best[i], best[i + 1]) for i, x in enumerate(row)]
    return best[0]


def _triangle_brute(triangle: list[list[int]]) -> int:
    best = None
    for moves in itertools.product((0, 1), repeat=len(triangle) - 1):
        col, total = 0, triangle[0][0]
        for r, step in enumerate(moves, start=1):
            col += step
            total += triangle[r][col]
        best = total if best is None else min(best, total)
    return best


TRIANGLE = ProblemSource(
    title="Triangle",
    statement="""
Return the minimum path sum from the top of the triangle to the bottom. From index `i` of a row you may move to index `i` or `i + 1` of the
row below.
""",
    constraints="""
- `1 <= triangle.length <= 200`, row `r` has `r + 1` numbers
- `-10^4 <= triangle[r][i] <= 10^4`
""",
    signature=function("minimumTotal", [("triangle", "int[][]")], "int"),
    reference=_minimum_total,
    brute=lambda triangle: _triangle_brute(triangle) if len(triangle) <= 12 else NotImplemented,
    examples=[Example([[[2], [3, 4], [6, 5, 7], [4, 1, 8, 3]]], "2 + 3 + 5 + 1 = 11."), Example([[[-10]]])],
    edge_cases=[[[[1], [2, 3]]], [[[-1], [2, 3], [1, -1, -3]]]],
    generator=lambda rng: [[ints(rng, r + 1, -rng.choice([9, 10**4]), rng.choice([9, 10**4])) for r in range(pick_n(rng, 1, 10, big=120))]],
    random_count=8,
)


# ---------------------------------------------------------------- Frog Jump


def _can_cross(stones: list[int]) -> bool:
    positions = {s: set() for s in stones}
    positions[0].add(0)
    for s in stones:
        for k in positions[s]:
            for step in (k - 1, k, k + 1):
                if step > 0 and s + step in positions:
                    positions[s + step].add(step)
    return bool(positions[stones[-1]])


def _can_cross_brute(stones: list[int]) -> bool:
    stone_set = set(stones)

    @cache
    def reach(pos: int, k: int) -> bool:
        if pos == stones[-1]:
            return True
        return any(step > 0 and pos + step in stone_set and reach(pos + step, step) for step in (k - 1, k, k + 1))

    return reach(0, 0)


def _stones_gen(rng):
    pos, stones = 0, [0]
    k = 0
    for _ in range(pick_n(rng, 1, 15, big=1500)):
        k = max(1, k + rng.choice([-1, 0, 1, 1]))
        pos += k if rng.random() < 0.85 else k + rng.randint(2, 5)
        stones.append(pos)
    return [stones]


FROG_JUMP = ProblemSource(
    title="Frog Jump",
    statement="""
A frog crosses a river on stones at the increasing positions `stones` (the first is `0`). Its first jump must be exactly 1 unit. If its last
jump was `k` units, the next jump must be `k - 1`, `k` or `k + 1` units, always forward and always landing on a stone. Return `true` if the
frog can reach the last stone.
""",
    constraints="""
- `2 <= stones.length <= 2000`
- `0 <= stones[i] <= 2^31 - 1`, strictly increasing, `stones[0] == 0`
""",
    signature=function("canCross", [("stones", "int[]")], "bool"),
    reference=_can_cross,
    brute=_can_cross_brute,
    examples=[Example([[0, 1, 3, 5, 6, 8, 12, 17]], "Jumps of 1, 2, 2, 3, 4, 5."), Example([[0, 1, 2, 3, 4, 8, 9, 11]], "The gap from 4 to 8 is too wide.")],
    edge_cases=[[[0, 1]], [[0, 2]], [[0, 1, 3, 6, 10, 15, 21]], [[0, 1, 2147483647]]],
    generator=_stones_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Cherry Pickup


def _cherry_pickup(grid: list[list[int]]) -> int:
    n = len(grid)

    @cache
    def best(r1: int, c1: int, r2: int) -> float:
        c2 = r1 + c1 - r2
        if r1 >= n or c1 >= n or r2 >= n or c2 >= n or grid[r1][c1] == -1 or grid[r2][c2] == -1:
            return float("-inf")
        if r1 == c1 == n - 1:
            return grid[r1][c1]
        here = grid[r1][c1] + (grid[r2][c2] if (r1, c1) != (r2, c2) else 0)
        return here + max(best(r1 + 1, c1, r2 + 1), best(r1 + 1, c1, r2), best(r1, c1 + 1, r2 + 1), best(r1, c1 + 1, r2))

    return max(0, int(best(0, 0, 0)) if best(0, 0, 0) != float("-inf") else 0)


def _cherry_brute(grid: list[list[int]]) -> int:
    n = len(grid)
    paths = []
    for moves in set(itertools.permutations("R" * (n - 1) + "D" * (n - 1))):
        r = c = 0
        cells = [(0, 0)]
        for m in moves:
            r, c = (r + 1, c) if m == "D" else (r, c + 1)
            cells.append((r, c))
        if all(grid[i][j] != -1 for i, j in cells):
            paths.append(set(cells))
    if not paths:
        return 0
    return max(sum(grid[i][j] for i, j in a | b) for a in paths for b in paths)


def _cherry_gen(rng):
    n = rng.randint(1, rng.choice([4, 12]))
    grid = [[rng.choice([0, 1, 1, -1]) for _ in range(n)] for _ in range(n)]
    grid[0][0] = grid[-1][-1] = rng.randint(0, 1)
    return [grid]


CHERRY_PICKUP = ProblemSource(
    title="Cherry Pickup",
    statement="""
In the `n x n` grid, `1` is a cherry, `0` is empty and `-1` is a thorn you can't pass. Walk from `(0, 0)` to `(n-1, n-1)` moving only right or
down, then walk back to `(0, 0)` moving only left or up. Passing a cherry picks it up (the cell becomes empty). Return the most cherries you can
collect, or `0` if there's no valid path to the far corner.
""",
    constraints="""
- `1 <= n <= 50`
- `grid[i][j]` is `-1`, `0` or `1`; `grid[0][0]` and `grid[n-1][n-1]` are not `-1`
""",
    signature=function("cherryPickup", [("grid", "int[][]")], "int"),
    reference=_cherry_pickup,
    brute=lambda grid: _cherry_brute(grid) if len(grid) <= 4 else NotImplemented,
    examples=[Example([[[0, 1, -1], [1, 0, -1], [1, 1, 1]]], "Five cherries."), Example([[[1, 1, -1], [1, -1, 1], [-1, 1, 1]]], "The far corner is unreachable.")],
    edge_cases=[[[[1]]], [[[0, 1], [1, 0]]], [[[1, 1, 1], [1, 1, 1], [1, 1, 1]]]],
    generator=_cherry_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Regular Expression Matching


def _regex_match(s: str, p: str) -> bool:
    @cache
    def match(i: int, j: int) -> bool:
        if j == len(p):
            return i == len(s)
        first = i < len(s) and p[j] in (s[i], ".")
        if j + 1 < len(p) and p[j + 1] == "*":
            return match(i, j + 2) or (first and match(i + 1, j))
        return first and match(i + 1, j + 1)

    return match(0, 0)


def _regex_gen(rng):
    s = word(rng, rng.randint(1, 12), "ab")
    tokens = [rng.choice(["a", "b", ".", "a*", "b*", ".*"]) for _ in range(rng.randint(1, 8))]
    return [s, "".join(tokens)[:30]]


REGEX_MATCHING = ProblemSource(
    title="Regular Expression Matching",
    statement="""
Match the whole string `s` against the pattern `p`, where `.` matches any single character and `x*` matches zero or more copies of the preceding
element `x`. Return `true` if `p` matches all of `s`.
""",
    constraints="""
- `1 <= s.length <= 20`, `1 <= p.length <= 30`
- `s` has lowercase letters; `p` has lowercase letters, `.` and `*`
- every `*` has a valid preceding character
""",
    signature=function("isMatch", [("s", "string"), ("p", "string")], "bool"),
    reference=_regex_match,
    brute=lambda s, p: re.fullmatch(p, s) is not None,
    examples=[Example(["aa", "a"]), Example(["aa", "a*"]), Example(["ab", ".*"])],
    edge_cases=[["aab", "c*a*b"], ["mississippi", "mis*is*p*."], ["a", "ab*"], ["aaa", "a*a"]],
    generator=_regex_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Dungeon Game


def _calculate_minimum_hp(dungeon: list[list[int]]) -> int:
    m, n = len(dungeon), len(dungeon[0])
    need = [[float("inf")] * (n + 1) for _ in range(m + 1)]
    need[m][n - 1] = need[m - 1][n] = 1
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            need[i][j] = max(1, min(need[i + 1][j], need[i][j + 1]) - dungeon[i][j])
    return int(need[0][0])


def _dungeon_brute(dungeon: list[list[int]]) -> int:
    m, n = len(dungeon), len(dungeon[0])
    best = None
    for moves in set(itertools.permutations("R" * (n - 1) + "D" * (m - 1))):
        r = c = 0
        health, lowest = dungeon[0][0], dungeon[0][0]
        for step in moves:
            r, c = (r + 1, c) if step == "D" else (r, c + 1)
            health += dungeon[r][c]
            lowest = min(lowest, health)
        start = max(1, 1 - lowest)
        best = start if best is None else min(best, start)
    return best


def _dungeon_rows(rng):
    rows, cols = pick_n(rng, 1, 5, big=60), pick_n(rng, 1, 5, big=60)
    return [[ints(rng, cols, -rng.choice([10, 1000]), rng.choice([5, 1000])) for _ in range(rows)]]


DUNGEON_GAME = ProblemSource(
    title="Dungeon Game",
    statement="""
A knight starts in the top-left room of an `m x n` dungeon and must reach the princess in the bottom-right room, moving only right or down. Each
room changes the knight's health by `dungeon[i][j]` (negative: a demon; positive: a potion), including the first and last rooms. If the
knight's health ever drops to `0` or below, he dies.

Return the minimum initial health that lets him reach the princess.
""",
    constraints="""
- `1 <= m, n <= 200`
- `-1000 <= dungeon[i][j] <= 1000`
""",
    signature=function("calculateMinimumHP", [("dungeon", "int[][]")], "int"),
    reference=_calculate_minimum_hp,
    brute=lambda dungeon: _dungeon_brute(dungeon) if len(dungeon) + len(dungeon[0]) <= 10 else NotImplemented,
    examples=[Example([[[-2, -3, 3], [-5, -10, 1], [10, 30, -5]]], "Start with 7: right, right, down, down."), Example([[[0]]])],
    edge_cases=[[[[-5]]], [[[5]]], [[[1, -3, 3], [0, -2, 0], [-3, -3, -3]]]],
    generator=_dungeon_rows,
    random_count=8,
)


# ---------------------------------------------------------------- Burst Balloons


def _max_coins(nums: list[int]) -> int:
    vals = [1] + nums + [1]
    n = len(vals)
    best = [[0] * n for _ in range(n)]
    for width in range(2, n):
        for left in range(n - width):
            right = left + width
            best[left][right] = max(vals[left] * vals[k] * vals[right] + best[left][k] + best[k][right] for k in range(left + 1, right))
    return best[0][n - 1]


def _burst_brute(nums: list[int]) -> int:
    @cache
    def best(balloons: tuple[int, ...]) -> int:
        if not balloons:
            return 0
        out = 0
        for i, b in enumerate(balloons):
            left = balloons[i - 1] if i else 1
            right = balloons[i + 1] if i + 1 < len(balloons) else 1
            out = max(out, left * b * right + best(balloons[:i] + balloons[i + 1 :]))
        return out

    return best(tuple(nums))


BURST_BALLOONS = ProblemSource(
    title="Burst Balloons",
    statement="""
Balloons in a row carry numbers `nums`. Bursting balloon `i` earns `left * nums[i] * right` coins, where `left` and `right` are the numbers on its
current neighbours (a missing neighbour counts as `1`); afterwards its neighbours become adjacent. Burst every balloon and return the maximum
total coins.
""",
    constraints="""
- `1 <= nums.length <= 300`
- `0 <= nums[i] <= 100`
""",
    signature=function("maxCoins", [("nums", "int[]")], "int"),
    reference=_max_coins,
    brute=lambda nums: _burst_brute(nums) if len(nums) <= 9 else NotImplemented,
    examples=[Example([[3, 1, 5, 8]], "3*1*5 + 3*5*8 + 1*3*8 + 1*8*1 = 167."), Example([[1, 5]])],
    edge_cases=[[[7]], [[0, 0]], [[9, 76, 64, 21]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 9, big=120), 0, rng.choice([9, 100]))],
    random_count=8,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Shortest Common Supersequence


def _shortest_common_supersequence(str1: str, str2: str) -> str:
    m, n = len(str1), len(str2)
    lcs = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            lcs[i][j] = lcs[i + 1][j + 1] + 1 if str1[i] == str2[j] else max(lcs[i + 1][j], lcs[i][j + 1])
    out, i, j = [], 0, 0
    while i < m and j < n:
        if str1[i] == str2[j]:
            out.append(str1[i])
            i, j = i + 1, j + 1
        elif lcs[i + 1][j] >= lcs[i][j + 1]:
            out.append(str1[i])
            i += 1
        else:
            out.append(str2[j])
            j += 1
    return "".join(out) + str1[i:] + str2[j:]


def _scs_brute(str1: str, str2: str) -> str:
    @cache
    def best(i: int, j: int) -> str:
        if i == len(str1):
            return str2[j:]
        if j == len(str2):
            return str1[i:]
        if str1[i] == str2[j]:
            return str1[i] + best(i + 1, j + 1)
        a, b = str1[i] + best(i + 1, j), str2[j] + best(i, j + 1)
        return a if len(a) <= len(b) else b

    return best(0, 0)


SCS = ProblemSource(
    title="Shortest Common Supersequence",
    statement="""
Return a shortest string that has both `str1` and `str2` as subsequences. If several shortest strings exist, any of them is accepted.
""",
    constraints="""
- `1 <= str1.length, str2.length <= 1000`
- lowercase English letters only
""",
    signature=function("shortestCommonSupersequence", [("str1", "string"), ("str2", "string")], "string"),
    reference=_shortest_common_supersequence,
    brute=_scs_brute,
    brute_input_limit=200,
    compare="checker",
    checker="shortest_common_supersequence",
    examples=[Example(["abac", "cab"], "\"cabac\" contains both."), Example(["aaaaaaaa", "aaaaaaaa"])],
    edge_cases=[["a", "b"], ["ab", "ba"], ["abc", "abc"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 15, big=400), "abc"), word(rng, pick_n(rng, 1, 15, big=400), "abc")],
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Interleaving String


def _is_interleave(s1: str, s2: str, s3: str) -> bool:
    if len(s1) + len(s2) != len(s3):
        return False
    ok = [False] * (len(s2) + 1)
    for i in range(len(s1) + 1):
        for j in range(len(s2) + 1):
            if i == j == 0:
                ok[j] = True
            else:
                from_s1 = i > 0 and ok[j] and s1[i - 1] == s3[i + j - 1]
                from_s2 = j > 0 and ok[j - 1] and s2[j - 1] == s3[i + j - 1]
                ok[j] = from_s1 or from_s2
    return ok[-1]


def _interleave_brute(s1: str, s2: str, s3: str) -> bool:
    @cache
    def go(i: int, j: int) -> bool:
        k = i + j
        if k == len(s3):
            return i == len(s1) and j == len(s2)
        return (i < len(s1) and s1[i] == s3[k] and go(i + 1, j)) or (j < len(s2) and s2[j] == s3[k] and go(i, j + 1))

    return len(s1) + len(s2) == len(s3) and go(0, 0)


def _interleave_gen(rng):
    s1, s2 = word(rng, rng.randint(0, 12), "ab"), word(rng, rng.randint(0, 12), "ab")
    merged, i, j = [], 0, 0
    while i < len(s1) or j < len(s2):
        if j == len(s2) or (i < len(s1) and rng.random() < 0.5):
            merged.append(s1[i])
            i += 1
        else:
            merged.append(s2[j])
            j += 1
    s3 = "".join(merged)
    if rng.random() < 0.4 and s3:
        k = rng.randrange(len(s3))
        s3 = s3[:k] + ("a" if s3[k] == "b" else "b") + s3[k + 1 :]
    return [s1, s2, s3]


INTERLEAVING = ProblemSource(
    title="Interleaving String",
    statement="""
Return `true` if `s3` is an interleaving of `s1` and `s2`: all characters of `s1` and all characters of `s2` merged into one string, each
keeping its own internal order.
""",
    constraints="""
- `0 <= s1.length, s2.length <= 100`, `0 <= s3.length <= 200`
- lowercase English letters only
""",
    signature=function("isInterleave", [("s1", "string"), ("s2", "string"), ("s3", "string")], "bool"),
    reference=_is_interleave,
    brute=_interleave_brute,
    examples=[Example(["aabcc", "dbbca", "aadbbcbcac"]), Example(["aabcc", "dbbca", "aadbbbaccc"]), Example(["", "", ""])],
    edge_cases=[["a", "", "a"], ["", "b", "a"], ["ab", "ab", "abab"], ["a", "b", "ab"]],
    generator=_interleave_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Maximal Rectangle


def _largest_histogram(heights: list[int]) -> int:
    stack, best = [], 0
    for i, h in enumerate(heights + [0]):
        start = i
        while stack and stack[-1][1] >= h:
            start, height = stack.pop()
            best = max(best, height * (i - start))
        stack.append((start, h))
    return best


def _maximal_rectangle(matrix: list[list[str]]) -> int:
    heights = [0] * len(matrix[0])
    best = 0
    for row in matrix:
        heights = [h + 1 if c == "1" else 0 for h, c in zip(heights, row, strict=True)]
        best = max(best, _largest_histogram(heights))
    return best


def _rectangle_brute(matrix: list[list[str]]) -> int:
    m, n = len(matrix), len(matrix[0])
    best = 0
    for r1 in range(m):
        for r2 in range(r1, m):
            for c1 in range(n):
                for c2 in range(c1, n):
                    if all(matrix[r][c] == "1" for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)):
                        best = max(best, (r2 - r1 + 1) * (c2 - c1 + 1))
    return best


MAXIMAL_RECTANGLE = ProblemSource(
    title="Maximal Rectangle",
    statement="""
Given a binary matrix of `'0'` and `'1'` characters, return the area of the largest rectangle that contains only `'1'`s.
""",
    constraints="""
- `1 <= rows, cols <= 200`
- each cell is `'0'` or `'1'`
""",
    signature=function("maximalRectangle", [("matrix", "char[][]")], "int"),
    reference=_maximal_rectangle,
    brute=_rectangle_brute,
    brute_input_limit=600,
    examples=[Example([[["1", "0", "1", "0", "0"], ["1", "0", "1", "1", "1"], ["1", "1", "1", "1", "1"], ["1", "0", "0", "1", "0"]]], "A 2 x 3 block of ones."), Example([[["0"]]]), Example([[["1"]]])],
    edge_cases=[[[["1", "1"], ["1", "1"]]], [[["0", "1"], ["1", "0"]]]],
    generator=_char_grid_gen(0.7, 60),
    random_count=8,
)


# ---------------------------------------------------------------- Longest Increasing Path in a Matrix


def _longest_increasing_path(matrix: list[list[int]]) -> int:
    m, n = len(matrix), len(matrix[0])

    @cache
    def longest(i: int, j: int) -> int:
        best = 1
        for x, y in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= x < m and 0 <= y < n and matrix[x][y] > matrix[i][j]:
                best = max(best, 1 + longest(x, y))
        return best

    return max(longest(i, j) for i in range(m) for j in range(n))


def _increasing_path_brute(matrix: list[list[int]]) -> int:
    m, n = len(matrix), len(matrix[0])
    cells = sorted(((matrix[i][j], i, j) for i in range(m) for j in range(n)), reverse=True)
    best = {}
    for value, i, j in cells:
        best[(i, j)] = 1 + max(
            (best[(x, y)] for x, y in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)) if (x, y) in best and matrix[x][y] > value),
            default=0,
        )
    return max(best.values())


INCREASING_PATH = ProblemSource(
    title="Longest Increasing Path in a Matrix",
    statement="""
Return the length of the longest path in the matrix along which values strictly increase, moving up, down, left or right (no diagonal moves, no
wrapping around).
""",
    constraints="""
- `1 <= m, n <= 200`
- `0 <= matrix[i][j] <= 2^31 - 1`
""",
    signature=function("longestIncreasingPath", [("matrix", "int[][]")], "int"),
    reference=_longest_increasing_path,
    brute=_increasing_path_brute,
    examples=[Example([[[9, 9, 4], [6, 6, 8], [2, 1, 1]]], "1 -> 2 -> 6 -> 9."), Example([[[3, 4, 5], [3, 2, 6], [2, 2, 1]]]), Example([[[1]]])],
    edge_cases=[[[[1, 2, 3, 4]]], [[[7, 7], [7, 7]]]],
    generator=_int_grid_gen(0, [5, 2**31 - 1], 60, small=7),
    random_count=8,
)


# ---------------------------------------------------------------- Min Cost Climbing Stairs


def _min_cost_climbing(cost: list[int]) -> int:
    a = b = 0
    for c in cost:
        a, b = b, min(a, b) + c
    return min(a, b)


def _climbing_brute(cost: list[int]) -> int:
    @cache
    def best(i: int) -> int:
        if i >= len(cost):
            return 0
        return cost[i] + min(best(i + 1), best(i + 2))

    return min(best(0), best(1))


MIN_COST_STAIRS = ProblemSource(
    title="Min Cost Climbing Stairs",
    statement="""
Stepping on stair `i` costs `cost[i]`; after paying you may climb one or two stairs. You may start on stair `0` or stair `1`. Return the minimum
cost to reach the top, which is just past the last stair.
""",
    constraints="""
- `2 <= cost.length <= 1000`
- `0 <= cost[i] <= 999`
""",
    signature=function("minCostClimbingStairs", [("cost", "int[]")], "int"),
    reference=_min_cost_climbing,
    brute=_climbing_brute,
    examples=[Example([[10, 15, 20]], "Start at 15 and jump two stairs."), Example([[1, 100, 1, 1, 1, 100, 1, 1, 100, 1]])],
    edge_cases=[[[0, 0]], [[5, 1]], [[1, 5]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 2, 30, big=1000), 0, 999)],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Longest Increasing Subsequence


def _find_number_of_lis(nums: list[int]) -> int:
    length = [1] * len(nums)
    count = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                if length[j] + 1 > length[i]:
                    length[i], count[i] = length[j] + 1, count[j]
                elif length[j] + 1 == length[i]:
                    count[i] += count[j]
    best = max(length)
    return sum(c for size, c in zip(length, count, strict=True) if size == best)


def _number_of_lis_brute(nums: list[int]) -> int:
    best_len, best_count = 0, 0
    for mask in range(1, 1 << len(nums)):
        seq = [nums[i] for i in range(len(nums)) if mask >> i & 1]
        if all(a < b for a, b in itertools.pairwise(seq)):
            if len(seq) > best_len:
                best_len, best_count = len(seq), 1
            elif len(seq) == best_len:
                best_count += 1
    return best_count


def _lis_gen(rng):
    n = pick_n(rng, 1, 14, big=600)
    spread = 5 if n <= 14 else 10**6  # a tiny value range on long arrays overflows the 32-bit count
    return [ints(rng, n, -spread, spread)]


NUMBER_OF_LIS = ProblemSource(
    title="Number of Longest Increasing Subsequence",
    statement="""
Return how many **strictly increasing** subsequences of `nums` have the maximum possible length. Subsequences at different positions count
separately. The answer fits in a 32-bit integer.
""",
    constraints="""
- `1 <= nums.length <= 2000`
- `-10^6 <= nums[i] <= 10^6`
""",
    signature=function("findNumberOfLIS", [("nums", "int[]")], "int"),
    reference=_find_number_of_lis,
    brute=lambda nums: _number_of_lis_brute(nums) if len(nums) <= 14 else NotImplemented,
    examples=[Example([[1, 3, 5, 4, 7]], "[1,3,4,7] and [1,3,5,7]."), Example([[2, 2, 2, 2, 2]], "Every single element is a longest subsequence.")],
    edge_cases=[[[1]], [[1, 2]], [[2, 1]], [[1, 2, 4, 3, 5, 4, 7, 2]]],
    generator=_lis_gen,
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Distinct Subsequences


def _num_distinct(s: str, t: str) -> int:
    ways = [1] + [0] * len(t)
    for ch in s:
        for j in range(len(t), 0, -1):
            if t[j - 1] == ch:
                ways[j] += ways[j - 1]
    return ways[-1]


def _num_distinct_brute(s: str, t: str) -> int:
    return sum("".join(c) == t for c in itertools.combinations(s, len(t)))


DISTINCT_SUBSEQUENCES = ProblemSource(
    title="Distinct Subsequences",
    statement="""
Count the ways to pick characters of `s` (keeping their order) that spell exactly `t`; different sets of positions count as different ways. The
answer fits in a 32-bit signed integer.
""",
    constraints="""
- `1 <= s.length, t.length <= 1000`
- English letters only
""",
    signature=function("numDistinct", [("s", "string"), ("t", "string")], "int"),
    reference=_num_distinct,
    brute=lambda s, t: _num_distinct_brute(s, t) if len(s) <= 16 else NotImplemented,
    examples=[Example(["rabbbit", "rabbit"], "Three ways to drop one of the three b's."), Example(["babgbag", "bag"])],
    edge_cases=[["a", "a"], ["a", "b"], ["aaa", "aa"], ["b", "bb"]],
    generator=lambda rng: [word(rng, rng.randint(1, 16), "ab"), word(rng, rng.randint(1, 4), "ab")],
    random_count=8,
)


# ---------------------------------------------------------------- Cheapest Flights Within K Stops


def _find_cheapest_price(n: int, flights: list[list[int]], src: int, dst: int, k: int) -> int:
    cost = [float("inf")] * n
    cost[src] = 0
    for _ in range(k + 1):
        nxt = cost[:]
        for a, b, price in flights:
            if cost[a] + price < nxt[b]:
                nxt[b] = cost[a] + price
        cost = nxt
    return -1 if cost[dst] == float("inf") else int(cost[dst])


def _cheapest_brute(n: int, flights: list[list[int]], src: int, dst: int, k: int) -> int:
    graph: dict[int, list[tuple[int, int]]] = {}
    for a, b, price in flights:
        graph.setdefault(a, []).append((b, price))
    heap = [(0, src, 0)]
    best: dict[tuple[int, int], int] = {}
    while heap:
        total, city, used = heapq.heappop(heap)
        if city == dst:
            return total
        if used > k or best.get((city, used), 10**18) < total:
            continue
        for b, price in graph.get(city, []):
            state = (b, used + 1)
            if total + price < best.get(state, 10**18):
                best[state] = total + price
                heapq.heappush(heap, (total + price, b, used + 1))
    return -1


def _flights_gen(rng):
    n = rng.randint(2, rng.choice([6, 60]))
    pairs = [(a, b) for a in range(n) for b in range(n) if a != b]
    rng.shuffle(pairs)
    flights = [[a, b, rng.randint(1, rng.choice([10, 10**4]))] for a, b in pairs[: rng.randint(1, min(len(pairs), 200))]]
    src, dst = rng.sample(range(n), 2)
    return [n, flights, src, dst, rng.randint(0, n - 1)]


CHEAPEST_FLIGHTS = ProblemSource(
    title="Cheapest Flights Within K Stops",
    statement="""
There are `n` cities and flights `flights[i] = [from_i, to_i, price_i]`. Return the cheapest price from `src` to `dst` using at most `k` stops
(that is, at most `k + 1` flights), or `-1` if no such route exists.
""",
    constraints="""
- `2 <= n <= 100`
- `0 <= flights.length <= n * (n - 1) / 2`, no duplicate flights, no self-flights
- `1 <= price_i <= 10^4`
- `0 <= src, dst, k < n`, `src != dst`
""",
    signature=function("findCheapestPrice", [("n", "int"), ("flights", "int[][]"), ("src", "int"), ("dst", "int"), ("k", "int")], "int"),
    reference=_find_cheapest_price,
    brute=_cheapest_brute,
    examples=[Example([4, [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]], 0, 3, 1], "0 -> 1 -> 3 costs 700."), Example([3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1]), Example([3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0])],
    edge_cases=[[2, [], 0, 1, 1], [2, [[0, 1, 5]], 0, 1, 0], [3, [[0, 1, 1], [1, 2, 1]], 0, 2, 0]],
    generator=_flights_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Minimum Path Sum


def _min_path_sum(grid: list[list[int]]) -> int:
    best = list(itertools.accumulate(grid[0]))
    for row in grid[1:]:
        best[0] += row[0]
        for j in range(1, len(row)):
            best[j] = min(best[j], best[j - 1]) + row[j]
    return best[-1]


def _min_path_brute(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    if m + n > 10:
        return NotImplemented
    best = None
    for moves in set(itertools.permutations("R" * (n - 1) + "D" * (m - 1))):
        r = c = 0
        total = grid[0][0]
        for step in moves:
            r, c = (r + 1, c) if step == "D" else (r, c + 1)
            total += grid[r][c]
        best = total if best is None else min(best, total)
    return best


MIN_PATH_SUM = ProblemSource(
    title="Minimum Path Sum",
    statement="""
Walk from the top-left to the bottom-right of the grid of non-negative numbers, moving only right or down. Return the minimum possible sum of
the numbers along the path.
""",
    constraints="""
- `1 <= m, n <= 200`
- `0 <= grid[i][j] <= 200`
""",
    signature=function("minPathSum", [("grid", "int[][]")], "int"),
    reference=_min_path_sum,
    brute=_min_path_brute,
    examples=[Example([[[1, 3, 1], [1, 5, 1], [4, 2, 1]]], "1 -> 3 -> 1 -> 1 -> 1."), Example([[[1, 2, 3], [4, 5, 6]]])],
    edge_cases=[[[[7]]], [[[1, 2]]], [[[1], [2]]]],
    generator=_int_grid_gen(0, [200], 100),
    random_count=8,
)


# ---------------------------------------------------------------- Best Time to Buy and Sell Stock III


def _max_profit_iii(prices: list[int]) -> int:
    buy1 = buy2 = float("-inf")
    sell1 = sell2 = 0
    for p in prices:
        buy1 = max(buy1, -p)
        sell1 = max(sell1, buy1 + p)
        buy2 = max(buy2, sell1 - p)
        sell2 = max(sell2, buy2 + p)
    return int(sell2)


def _profit_iii_brute(prices: list[int]) -> int:
    def one(seq: list[int]) -> int:
        return max([0] + [seq[j] - seq[i] for i in range(len(seq)) for j in range(i + 1, len(seq))])

    return max(one(prices[:k]) + one(prices[k:]) for k in range(len(prices) + 1))


BEST_TIME_III = ProblemSource(
    title="Best Time to Buy and Sell Stock III",
    statement="""
`prices[i]` is a stock's price on day `i`. Make **at most two** transactions (buy then sell); you can't hold more than one share at a time.
Return the maximum profit.
""",
    constraints="""
- `1 <= prices.length <= 10^5`
- `0 <= prices[i] <= 10^5`
""",
    signature=function("maxProfit", [("prices", "int[]")], "int"),
    reference=_max_profit_iii,
    brute=_profit_iii_brute,
    brute_input_limit=200,
    examples=[Example([[3, 3, 5, 0, 0, 3, 1, 4]], "Buy at 0 sell at 3, buy at 1 sell at 4: 6."), Example([[1, 2, 3, 4, 5]]), Example([[7, 6, 4, 3, 1]])],
    edge_cases=[[[1]], [[2, 1, 4]], [[1, 4, 2, 7]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 30, big=5000), 0, rng.choice([10, 10**5]))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximal Square


def _maximal_square(matrix: list[list[str]]) -> int:
    n = len(matrix[0])
    prev = [0] * (n + 1)
    best = 0
    for row in matrix:
        cur = [0] * (n + 1)
        for j in range(1, n + 1):
            if row[j - 1] == "1":
                cur[j] = min(prev[j], prev[j - 1], cur[j - 1]) + 1
                best = max(best, cur[j])
        prev = cur
    return best * best


def _square_brute(matrix: list[list[str]]) -> int:
    m, n = len(matrix), len(matrix[0])
    best = 0
    for i in range(m):
        for j in range(n):
            size = 1
            while i + size <= m and j + size <= n and all(matrix[r][c] == "1" for r in range(i, i + size) for c in range(j, j + size)):
                best = max(best, size)
                size += 1
    return best * best


MAXIMAL_SQUARE = ProblemSource(
    title="Maximal Square",
    statement="""
Given a binary matrix of `'0'` and `'1'` characters, return the area of the largest square that contains only `'1'`s.
""",
    constraints="""
- `1 <= rows, cols <= 300`
- each cell is `'0'` or `'1'`
""",
    signature=function("maximalSquare", [("matrix", "char[][]")], "int"),
    reference=_maximal_square,
    brute=_square_brute,
    brute_input_limit=1500,
    examples=[Example([[["1", "0", "1", "0", "0"], ["1", "0", "1", "1", "1"], ["1", "1", "1", "1", "1"], ["1", "0", "0", "1", "0"]]], "A 2 x 2 square."), Example([[["0", "1"], ["1", "0"]]]), Example([[["0"]]])],
    edge_cases=[[[["1"]]], [[["1", "1"], ["1", "1"]]]],
    generator=_char_grid_gen(0.75, 80),
    random_count=8,
)


# ---------------------------------------------------------------- The Number of Good Subsets

_SMALL_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def _mask(x: int) -> int | None:
    mask = 0
    for i, p in enumerate(_SMALL_PRIMES):
        if x % (p * p) == 0:
            return None
        if x % p == 0:
            mask |= 1 << i
    return mask


def _number_of_good_subsets(nums: list[int]) -> int:
    counts = Counter(nums)
    ways = [0] * (1 << len(_SMALL_PRIMES))
    ways[0] = 1
    for x in range(2, 31):
        m = _mask(x)
        if m is None or not counts[x]:
            continue
        for state in range(len(ways) - 1, -1, -1):
            if state & m == m:
                ways[state] = (ways[state] + ways[state ^ m] * counts[x]) % _MOD
    return (sum(ways) - 1) * pow(2, counts[1], _MOD) % _MOD


def _good_subsets_brute(nums: list[int]) -> int:
    def good(values: list[int]) -> bool:
        product = 1
        for v in values:
            product *= v
        return product > 1 and all(product % (p * p) for p in _SMALL_PRIMES)

    return sum(good([nums[i] for i in range(len(nums)) if mask >> i & 1]) for mask in range(1, 1 << len(nums))) % _MOD


GOOD_SUBSETS = ProblemSource(
    title="The Number of Good Subsets",
    statement="""
A subset of `nums` (a choice of positions) is *good* if the product of its values can be written as a product of **distinct** primes, each used
once. For example with `[1, 2, 3, 4]`, the subsets with products `2`, `6` (= 2 * 3) and `3` are good, but `4` (= 2 * 2) is not.

Return the number of good subsets modulo `10^9 + 7`. Subsets that pick different positions count separately.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 30`
""",
    signature=function("numberOfGoodSubsets", [("nums", "int[]")], "int"),
    reference=_number_of_good_subsets,
    brute=lambda nums: _good_subsets_brute(nums) if len(nums) <= 14 else NotImplemented,
    examples=[Example([[1, 2, 3, 4]], "Six good subsets."), Example([[4, 2, 3, 15]], "Five good subsets.")],
    edge_cases=[[[1]], [[4]], [[2]], [[1, 1, 2]], [[30, 30]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 14, big=5000), 1, 30)],
    random_count=8,
)


# ---------------------------------------------------------------- Freedom Trail


def _find_rotate_steps(ring: str, key: str) -> int:
    n = len(ring)
    positions: dict[str, list[int]] = {}
    for i, ch in enumerate(ring):
        positions.setdefault(ch, []).append(i)

    @cache
    def best(pos: int, k: int) -> int:
        if k == len(key):
            return 0
        return min(min(abs(pos - j), n - abs(pos - j)) + 1 + best(j, k + 1) for j in positions[key[k]])

    return best(0, 0)


def _rotate_brute(ring: str, key: str) -> int:
    n = len(ring)
    dist = {0: 0}
    for ch in key:
        nxt: dict[int, int] = {}
        for pos, d in dist.items():
            for step in range(-n, n + 1):
                j = (pos + step) % n
                if ring[j] == ch:
                    nxt[j] = min(nxt.get(j, 10**9), d + abs(step) + 1)
        dist = nxt
    return min(dist.values())


def _ring_gen(rng):
    ring = word(rng, rng.randint(1, rng.choice([8, 100])), "abcd")
    return [ring, "".join(rng.choice(ring) for _ in range(rng.randint(1, rng.choice([5, 100]))))]


FREEDOM_TRAIL = ProblemSource(
    title="Freedom Trail",
    statement="""
A dial shows the characters of `ring` around its edge, with `ring[0]` at the top (12 o'clock). To spell `key`, for each character in order you
rotate the dial one position at a time (clockwise or anticlockwise, one step each) until that character is at 12 o'clock, then press the centre
button (one step). Return the minimum total number of steps to spell all of `key`.
""",
    constraints="""
- `1 <= ring.length, key.length <= 100`
- lowercase letters only; `key` can always be spelled with `ring`
""",
    signature=function("findRotateSteps", [("ring", "string"), ("key", "string")], "int"),
    reference=_find_rotate_steps,
    brute=_rotate_brute,
    examples=[Example(["godding", "gd"], "Press g (1), rotate twice to d, press (3): 4."), Example(["godding", "godding"])],
    edge_cases=[["a", "a"], ["ab", "ba"], ["abcde", "ea"]],
    generator=_ring_gen,
    random_count=8,
)


PROBLEMS = [
    TRIANGLE,
    FROG_JUMP,
    CHERRY_PICKUP,
    REGEX_MATCHING,
    DUNGEON_GAME,
    BURST_BALLOONS,
    SCS,
    INTERLEAVING,
    MAXIMAL_RECTANGLE,
    INCREASING_PATH,
    MIN_COST_STAIRS,
    NUMBER_OF_LIS,
    DISTINCT_SUBSEQUENCES,
    CHEAPEST_FLIGHTS,
    MIN_PATH_SUM,
    BEST_TIME_III,
    MAXIMAL_SQUARE,
    GOOD_SUBSETS,
    FREEDOM_TRAIL,
]

