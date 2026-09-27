"""Pattern 25: Union Find. Original statements; outputs come from `reference`."""

from __future__ import annotations

import heapq
import random
from collections import defaultdict, deque

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sample, word

PATTERN_NUMBER = 25


class _DisjointSet:
    """Union by size with path halving."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        return True


def _components(nodes: list, adjacent: dict) -> list[list]:
    """Connected components by BFS (used by the brute oracles)."""
    seen, out = set(), []
    for start in nodes:
        if start in seen:
            continue
        seen.add(start)
        component, queue = [], deque([start])
        while queue:
            v = queue.popleft()
            component.append(v)
            for w in adjacent.get(v, ()):
                if w not in seen:
                    seen.add(w)
                    queue.append(w)
        out.append(component)
    return out


def _grid_neighbours(m: int, n: int, i: int, j: int):
    for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
        if 0 <= a < m and 0 <= b < n:
            yield a, b


# ---------------------------------------------------------------- Number of Islands


def _num_islands(grid: list[list[str]]) -> int:
    m, n = len(grid), len(grid[0])
    ds = _DisjointSet(m * n)
    water = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == "0":
                water += 1
                continue
            for a, b in ((i + 1, j), (i, j + 1)):
                if a < m and b < n and grid[a][b] == "1":
                    ds.union(i * n + j, a * n + b)
    return ds.components - water


def _islands_brute(grid: list[list[str]]) -> int:
    m, n = len(grid), len(grid[0])
    land = [(i, j) for i in range(m) for j in range(n) if grid[i][j] == "1"]
    adjacent = {c: [d for d in _grid_neighbours(m, n, *c) if grid[d[0]][d[1]] == "1"] for c in land}
    return len(_components(land, adjacent))


NUMBER_OF_ISLANDS = ProblemSource(
    title="Number of Islands",
    statement="""
`grid` is a map of `"1"` (land) and `"0"` (water). An island is a group of land cells connected horizontally or vertically, and everything
outside the grid is water. Return the number of islands.
""",
    constraints="""
- `1 <= m, n <= 300`
- `grid[i][j]` is `"0"` or `"1"`
""",
    signature=function("numIslands", [("grid", "char[][]")], "int"),
    reference=_num_islands,
    brute=_islands_brute,
    examples=[
        Example([[list("11110"), list("11010"), list("11000"), list("00000")]]),
        Example([[list("11000"), list("11000"), list("00100"), list("00011")]]),
    ],
    edge_cases=[[[["0"]]], [[["1"]]], [[list("101"), list("010"), list("101")]]],
    generator=lambda rng: [[["1" if rng.random() < d else "0" for _ in range(n)] for _ in range(m)] for m, n, d in [(pick_n(rng, 1, 8, big=60), pick_n(rng, 1, 8, big=60), rng.choice([0.3, 0.5, 0.6]))]],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Consecutive Sequence


def _longest_consecutive(nums: list[int]) -> int:
    values = set(nums)
    best = 0
    for x in values:
        if x - 1 not in values:  # only start counting at the beginning of a run
            length = 1
            while x + length in values:
                length += 1
            best = max(best, length)
    return best


def _consecutive_brute(nums: list[int]) -> int:
    values = sorted(set(nums))
    best = run = 0
    for i, x in enumerate(values):
        run = run + 1 if i and x == values[i - 1] + 1 else 1
        best = max(best, run)
    return best


LONGEST_CONSECUTIVE = ProblemSource(
    title="Longest Consecutive Sequence",
    statement="""
Return the length of the longest run of consecutive integers (like `4, 5, 6, 7`) whose values all appear in the unsorted array `nums`. Your
algorithm should run in `O(n)` time.
""",
    constraints="""
- `0 <= nums.length <= 10^5`
- `-10^9 <= nums[i] <= 10^9`
""",
    signature=function("longestConsecutive", [("nums", "int[]")], "int"),
    reference=_longest_consecutive,
    brute=_consecutive_brute,
    examples=[Example([[100, 4, 200, 1, 3, 2]], "1, 2, 3, 4."), Example([[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]]), Example([[]])],
    edge_cases=[[[5]], [[1, 1, 1]], [[-1000000000, 1000000000]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=5000), -(hi := rng.choice([15, 10**9])), hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Redundant Connection


def _find_redundant_connection(edges: list[list[int]]) -> list[int]:
    ds = _DisjointSet(len(edges) + 1)
    answer: list[int] = []
    for a, b in edges:
        if not ds.union(a, b):
            answer = [a, b]
    return answer


def _redundant_brute(edges: list[list[int]]) -> list[int]:
    n = len(edges)
    for skip in range(n - 1, -1, -1):  # the last edge whose removal leaves a tree
        adjacent: dict[int, list[int]] = defaultdict(list)
        for k, (a, b) in enumerate(edges):
            if k != skip:
                adjacent[a].append(b)
                adjacent[b].append(a)
        if len(_components(list(range(1, n + 1)), adjacent)) == 1:
            return edges[skip]
    raise AssertionError("some edge is redundant")


def _redundant_gen(rng: random.Random) -> list:
    n = pick_n(rng, 3, 10, big=1000)
    labels = [x + 1 for x in sample(rng, range(n), n)]
    edges = [[labels[rng.randint(0, i - 1)], labels[i]] for i in range(1, n)]
    tree = {tuple(sorted(e)) for e in edges}
    while True:
        a, b = sorted(sample(rng, range(1, n + 1), 2))
        if (a, b) not in tree:
            edges.append([a, b])
            break
    rng.shuffle(edges)
    return [[sorted(e) for e in edges]]


REDUNDANT_CONNECTION = ProblemSource(
    title="Redundant Connection",
    statement="""
A tree on nodes `1` to `n` had one extra edge added, giving the `n` undirected edges in `edges` (each written `[a, b]` with `a < b`). Return an
edge whose removal leaves a tree; if several qualify, return the one that appears **last** in `edges`.
""",
    constraints="""
- `3 <= n <= 1000`, `edges.length == n`
- no repeated edges; the graph is connected
""",
    signature=function("findRedundantConnection", [("edges", "int[][]")], "int[]"),
    reference=_find_redundant_connection,
    brute=_redundant_brute,
    brute_input_limit=1500,
    examples=[Example([[[1, 2], [1, 3], [2, 3]]]), Example([[[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]], "The cycle is 1-2-3-4; [1,4] comes last among its edges.")],
    edge_cases=[[[[1, 2], [2, 3], [1, 3]]], [[[2, 3], [1, 2], [1, 3], [3, 4]]]],
    generator=_redundant_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Most Stones Removed with Same Row or Column


def _remove_stones(stones: list[list[int]]) -> int:
    ds = _DisjointSet(len(stones))
    first_in_row: dict[int, int] = {}
    first_in_col: dict[int, int] = {}
    for k, (r, c) in enumerate(stones):
        ds.union(k, first_in_row.setdefault(r, k))
        ds.union(k, first_in_col.setdefault(c, k))
    return len(stones) - ds.components


def _stones_brute(stones: list[list[int]]) -> int:
    n = len(stones)
    adjacent = {i: [j for j in range(n) if j != i and (stones[i][0] == stones[j][0] or stones[i][1] == stones[j][1])] for i in range(n)}
    return n - len(_components(list(range(n)), adjacent))


def _stones_gen(rng: random.Random) -> list:
    hi = rng.choice([4, 10, 10**4])
    points = {(rng.randint(0, hi), rng.randint(0, hi)) for _ in range(pick_n(rng, 1, 15, big=1000))}
    return [[list(pt) for pt in sorted(points)]]


MOST_STONES = ProblemSource(
    title="Most Stones Removed with Same Row or Column",
    statement="""
Stones sit at distinct integer points `stones[i] = [row, col]`. A stone can be removed if another remaining stone shares its row or its
column. Return the largest number of stones that can be removed.
""",
    constraints="""
- `1 <= stones.length <= 1000`
- `0 <= row, col <= 10^4`; no two stones share a position
""",
    signature=function("removeStones", [("stones", "int[][]")], "int"),
    reference=_remove_stones,
    brute=_stones_brute,
    brute_input_limit=4000,
    examples=[Example([[[0, 0], [0, 1], [1, 0], [1, 2], [2, 1], [2, 2]]], "All connected: remove 5."), Example([[[0, 0], [0, 2], [1, 1], [2, 0], [2, 2]]]), Example([[[0, 0]]])],
    edge_cases=[[[[0, 0], [1, 1]]], [[[0, 0], [0, 10000]]]],
    generator=_stones_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Last Day Where You Can Still Cross


def _latest_day_to_cross(row: int, col: int, cells: list[list[int]]) -> int:
    top, bottom = row * col, row * col + 1
    ds = _DisjointSet(row * col + 2)
    land = [[False] * col for _ in range(row)]
    for day in range(len(cells) - 1, -1, -1):  # add land back in reverse
        r, c = cells[day][0] - 1, cells[day][1] - 1
        land[r][c] = True
        cell = r * col + c
        if r == 0:
            ds.union(cell, top)
        if r == row - 1:
            ds.union(cell, bottom)
        for a, b in _grid_neighbours(row, col, r, c):
            if land[a][b]:
                ds.union(cell, a * col + b)
        if ds.find(top) == ds.find(bottom):
            return day
    return 0


def _cross_brute(row: int, col: int, cells: list[list[int]]) -> int:
    def can_cross(day: int) -> bool:
        flooded = {(r - 1, c - 1) for r, c in cells[:day]}
        queue = deque((0, c) for c in range(col) if (0, c) not in flooded)
        seen = set(queue)
        while queue:
            v = queue.popleft()
            if v[0] == row - 1:
                return True
            for w in _grid_neighbours(row, col, *v):
                if w not in seen and w not in flooded:
                    seen.add(w)
                    queue.append(w)
        return False

    return max(day for day in range(len(cells) + 1) if can_cross(day))


def _cross_gen(rng: random.Random) -> list:
    row, col = rng.randint(2, rng.choice([5, 60])), rng.randint(2, rng.choice([5, 60]))
    order = sample(rng, [[r, c] for r in range(1, row + 1) for c in range(1, col + 1)], row * col)
    return [row, col, order]


LAST_DAY_CROSS = ProblemSource(
    title="Last Day Where You Can Still Cross",
    statement="""
A `row x col` grid (1-indexed) starts as all land. On day `i` (1-indexed) the cell `cells[i - 1]` floods and stays water; every cell floods
exactly once. You can walk between land cells sharing a side. Return the **last** day on which it is still possible to walk from some cell in the
top row to some cell in the bottom row using only land (day `0` means before any flooding).
""",
    constraints="""
- `2 <= row, col <= 2 * 10^4`, `row * col <= 2 * 10^4`
- `cells` is a permutation of all cells
""",
    signature=function("latestDayToCross", [("row", "int"), ("col", "int"), ("cells", "int[][]")], "int"),
    reference=_latest_day_to_cross,
    brute=lambda row, col, cells: _cross_brute(row, col, cells) if row * col <= 60 else NotImplemented,
    examples=[Example([2, 2, [[1, 1], [2, 1], [1, 2], [2, 2]]], "After day 2 column 2 is still land."), Example([2, 2, [[1, 1], [1, 2], [2, 1], [2, 2]]]), Example([3, 3, [[1, 2], [2, 1], [3, 3], [2, 2], [1, 1], [1, 3], [2, 3], [3, 2], [3, 1]]])],
    edge_cases=[[2, 3, [[1, 1], [1, 2], [1, 3], [2, 1], [2, 2], [2, 3]]]],
    generator=_cross_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Regions Cut by Slashes


def _regions_by_slashes(grid: list[str]) -> int:
    n = len(grid)
    ds = _DisjointSet(4 * n * n)  # each cell is split into 4 triangles: 0 top, 1 right, 2 bottom, 3 left

    def tri(i: int, j: int, k: int) -> int:
        return 4 * (i * n + j) + k

    for i in range(n):
        for j in range(n):
            ch = grid[i][j]
            if ch == "/":
                ds.union(tri(i, j, 0), tri(i, j, 3))
                ds.union(tri(i, j, 1), tri(i, j, 2))
            elif ch == "\\":
                ds.union(tri(i, j, 0), tri(i, j, 1))
                ds.union(tri(i, j, 2), tri(i, j, 3))
            else:
                for k in (1, 2, 3):
                    ds.union(tri(i, j, 0), tri(i, j, k))
            if i + 1 < n:
                ds.union(tri(i, j, 2), tri(i + 1, j, 0))
            if j + 1 < n:
                ds.union(tri(i, j, 1), tri(i, j + 1, 3))
    return ds.components


def _slashes_brute(grid: list[str]) -> int:
    n = len(grid)
    size = 3 * n
    wall = [[False] * size for _ in range(size)]
    for i, row in enumerate(grid):
        for j, ch in enumerate(row):
            for k in range(3):
                if ch == "/":
                    wall[3 * i + k][3 * j + 2 - k] = True
                elif ch == "\\":
                    wall[3 * i + k][3 * j + k] = True
    open_cells = [(i, j) for i in range(size) for j in range(size) if not wall[i][j]]
    adjacent = {c: [d for d in _grid_neighbours(size, size, *c) if not wall[d[0]][d[1]]] for c in open_cells}
    return len(_components(open_cells, adjacent))


REGIONS_SLASHES = ProblemSource(
    title="Regions Cut by Slashes",
    statement="""
An `n x n` grid is drawn from 1 x 1 squares, each containing `"/"`, `"\\"` or a blank `" "`, which splits the square diagonally (or not at
all). `grid[i]` gives row `i`. Return the number of regions the whole grid is divided into.
""",
    constraints="""
- `1 <= n <= 30`
- each character is `"/"`, `"\\"` or `" "`
""",
    signature=function("regionsBySlashes", [("grid", "string[]")], "int"),
    reference=_regions_by_slashes,
    brute=_slashes_brute,
    examples=[Example([[" /", "/ "]]), Example([[" /", "  "]]), Example([["/\\", "\\/"]], "The slashes enclose a diamond in the middle: 5 regions.")],
    edge_cases=[[[" "]], [["/"]], [["\\"]]],
    generator=lambda rng: [["".join(rng.choice("/\\ ") for _ in range(n)) for _ in range(n)] for n in [rng.randint(1, rng.choice([6, 30]))]],
    random_count=8,
)


# ---------------------------------------------------------------- Accounts Merge


def _accounts_merge(accounts: list[list[str]]) -> list[list[str]]:
    ds = _DisjointSet(len(accounts))
    owner: dict[str, int] = {}
    for k, account in enumerate(accounts):
        for email in account[1:]:
            ds.union(k, owner.setdefault(email, k))
    groups: dict[int, set[str]] = defaultdict(set)
    for k, account in enumerate(accounts):
        groups[ds.find(k)].update(account[1:])
    return [[accounts[root][0], *sorted(emails)] for root, emails in groups.items()]


def _accounts_brute(accounts: list[list[str]]) -> list[list[str]]:
    merged = [[a[0], set(a[1:])] for a in accounts]
    changed = True
    while changed:
        changed = False
        for i in range(len(merged)):
            for j in range(i + 1, len(merged)):
                if merged[i][1] & merged[j][1]:
                    merged[i][1] |= merged.pop(j)[1]
                    changed = True
                    break
            if changed:
                break
    return [[name, *sorted(emails)] for name, emails in merged]


def _accounts_gen(rng: random.Random) -> list:
    people = [(word(rng, 4, "ABCDEFGH").capitalize(), [f"{word(rng, 3, 'abc')}{p}_{k}@x.com" for k in range(rng.randint(1, 5))]) for p in range(rng.randint(1, 5))]
    accounts = []
    for name, emails in people:
        for _ in range(rng.randint(1, 3)):
            accounts.append([name, *sample(rng, emails, rng.randint(1, len(emails)))])
    rng.shuffle(accounts)
    return [accounts]


ACCOUNTS_MERGE = ProblemSource(
    title="Accounts Merge",
    statement="""
Each `accounts[i]` is a name followed by that account's emails. Two accounts belong to the same person if they share at least one email (directly
or through a chain of accounts); accounts of one person always have the same name, but different people may share a name. Merge the accounts and
return one entry per person: the name, followed by all their emails in sorted order. The entries themselves may be in any order.
""",
    constraints="""
- `1 <= accounts.length <= 1000`, `2 <= accounts[i].length <= 10`
- names and emails are short strings of letters, digits, `_`, `@` and `.`
""",
    signature=function("accountsMerge", [("accounts", "string[][]")], "string[][]"),
    reference=_accounts_merge,
    brute=_accounts_brute,
    compare="unordered",
    examples=[
        Example([[["John", "johnsmith@mail.com", "john_newyork@mail.com"], ["John", "johnsmith@mail.com", "john00@mail.com"], ["Mary", "mary@mail.com"], ["John", "johnnybravo@mail.com"]]], "The first two John accounts share an email."),
        Example([[["Gabe", "Gabe0@m.co", "Gabe3@m.co"], ["Kevin", "Kevin3@m.co", "Kevin5@m.co"], ["Gabe", "Gabe1@m.co", "Gabe0@m.co"]]]),
    ],
    edge_cases=[[[["A", "a@x"]]], [[["A", "a@x"], ["A", "b@x"], ["A", "a@x", "b@x"]]]],
    generator=_accounts_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimize Malware Spread


def _min_malware_spread(graph: list[list[int]], initial: list[int]) -> int:
    n = len(graph)
    ds = _DisjointSet(n)
    for i in range(n):
        for j in range(i + 1, n):
            if graph[i][j]:
                ds.union(i, j)
    infected_in: dict[int, int] = defaultdict(int)
    for v in initial:
        infected_in[ds.find(v)] += 1
    best, saved = min(initial), -1
    for v in sorted(initial):
        root = ds.find(v)
        gain = ds.size[root] if infected_in[root] == 1 else 0  # removing v only helps if it's alone in its component
        if gain > saved:
            best, saved = v, gain
    return best


def _malware_brute(graph: list[list[int]], initial: list[int]) -> int:
    n = len(graph)

    def spread(sources: list[int]) -> int:
        seen, queue = set(sources), deque(sources)
        while queue:
            v = queue.popleft()
            for w in range(n):
                if graph[v][w] and w not in seen:
                    seen.add(w)
                    queue.append(w)
        return len(seen)

    return min(initial, key=lambda r: (spread([v for v in initial if v != r]), r))


def _malware_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 10, big=300)
    graph = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for _ in range(rng.randint(0, 2 * n)):
        a, b = sample(rng, range(n), 2)
        graph[a][b] = graph[b][a] = 1
    return [graph, sorted(sample(rng, range(n), rng.randint(1, n - 1)))]


MINIMIZE_MALWARE = ProblemSource(
    title="Minimize Malware Spread",
    statement="""
`graph` is the adjacency matrix of `n` computers (`graph[i][j] == 1` means a direct connection; `graph[i][i] == 1`). The computers in `initial`
are infected, and malware spreads along connections until nothing new can be infected. You may remove exactly one computer from `initial` (it
starts clean, but can still be infected later). Return the computer whose removal minimises the final number of infected machines; on a tie,
return the smallest index.
""",
    constraints="""
- `2 <= n <= 300`, `graph` is symmetric
- `1 <= initial.length < n`, distinct values
""",
    signature=function("minMalwareSpread", [("graph", "int[][]"), ("initial", "int[]")], "int"),
    reference=_min_malware_spread,
    brute=_malware_brute,
    brute_input_limit=3000,
    examples=[Example([[[1, 1, 0], [1, 1, 0], [0, 0, 1]], [0, 1]], "0 and 1 infect each other anyway; pick the smaller."), Example([[[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 2]]), Example([[[1, 1, 1], [1, 1, 1], [1, 1, 1]], [1, 2]])],
    edge_cases=[[[[1, 0], [0, 1]], [1]], [[[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]], [0, 2]]],
    generator=_malware_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Evaluate Division


def _calc_equation(equations: list[list[str]], values: list[float], queries: list[list[str]]) -> list[float]:
    parent: dict[str, str] = {}
    weight: dict[str, float] = {}  # value of node / value of parent

    def find(x: str) -> tuple[str, float]:
        if parent[x] == x:
            return x, 1.0
        root, w = find(parent[x])
        parent[x], weight[x] = root, weight[x] * w
        return root, weight[x]

    for (a, b), v in zip(equations, values, strict=True):
        for x in (a, b):
            if x not in parent:
                parent[x], weight[x] = x, 1.0
        (ra, wa), (rb, wb) = find(a), find(b)
        if ra != rb:
            parent[ra], weight[ra] = rb, v * wb / wa
    out = []
    for c, d in queries:
        if c not in parent or d not in parent:
            out.append(-1.0)
            continue
        (rc, wc), (rd, wd) = find(c), find(d)
        out.append(wc / wd if rc == rd else -1.0)
    return out


def _division_brute(equations: list[list[str]], values: list[float], queries: list[list[str]]) -> list[float]:
    edges: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (a, b), v in zip(equations, values, strict=True):
        edges[a].append((b, v))
        edges[b].append((a, 1 / v))
    out = []
    for c, d in queries:
        if c not in edges or d not in edges:
            out.append(-1.0)
            continue
        ratio = {c: 1.0}
        queue = deque([c])
        while queue:
            x = queue.popleft()
            for y, v in edges[x]:
                if y not in ratio:
                    ratio[y] = ratio[x] * v
                    queue.append(y)
        out.append(ratio.get(d, -1.0))
    return out


def _division_gen(rng: random.Random) -> list:
    names = [word(rng, rng.randint(1, 2), "abcxy") for _ in range(rng.randint(2, 8))]
    names = list(dict.fromkeys(names))
    if len(names) < 2:
        names.append("zz")
    value = {x: rng.randint(1, 20) / rng.randint(1, 5) for x in names}  # hidden consistent assignment
    equations, values = [], []
    for _ in range(rng.randint(1, len(names))):
        a, b = sample(rng, names, 2)
        equations.append([a, b])
        values.append(round(value[a] / value[b], 6))
    queries = [[rng.choice(names + ["q"]), rng.choice(names)] for _ in range(rng.randint(1, 8))]
    return [equations, values, queries]


EVALUATE_DIVISION = ProblemSource(
    title="Evaluate Division",
    statement="""
Each `equations[i] = [a, b]` with `values[i]` states that `a / b = values[i]` for variables named by strings. The equations are consistent.
For each query `[c, d]`, return the value of `c / d`, or `-1.0` if it can't be determined (including when a variable never appears in any
equation). Answers within `10^-5` are accepted.
""",
    constraints="""
- `1 <= equations.length, queries.length <= 20`
- `0 < values[i] <= 20`; variable names are short lowercase strings
""",
    signature=function("calcEquation", [("equations", "string[][]"), ("values", "double[]"), ("queries", "string[][]")], "double[]"),
    reference=_calc_equation,
    brute=_division_brute,
    compare="float_tolerance",
    examples=[
        Example([[["a", "b"], ["b", "c"]], [2.0, 3.0], [["a", "c"], ["b", "a"], ["a", "e"], ["a", "a"], ["x", "x"]]], "a/c = 6; x never appears, so x/x is -1."),
        Example([[["a", "b"]], [0.5], [["a", "b"], ["b", "a"], ["a", "c"], ["x", "y"]]]),
    ],
    edge_cases=[[[["a", "b"]], [1.0], [["b", "b"]]], [[["a", "b"], ["c", "d"]], [2.0, 4.0], [["a", "d"], ["d", "c"]]]],
    generator=_division_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find if Path Exists in Graph


def _valid_path(n: int, edges: list[list[int]], source: int, destination: int) -> bool:
    ds = _DisjointSet(n)
    for a, b in edges:
        ds.union(a, b)
    return ds.find(source) == ds.find(destination)


def _path_brute(n: int, edges: list[list[int]], source: int, destination: int) -> bool:
    adjacent: dict[int, list[int]] = defaultdict(list)
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    return any(source in c and destination in c for c in _components([source], adjacent))


def _path_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 12, big=2000)
    edges = {tuple(sorted(sample(rng, range(n), 2))) for _ in range(rng.randint(0, n)) if n >= 2}
    return [n, [list(e) for e in sorted(edges)], rng.randrange(n), rng.randrange(n)]


PATH_EXISTS = ProblemSource(
    title="Find if Path Exists in Graph",
    statement="""
An undirected graph has `n` vertices labelled `0` to `n - 1` and the given `edges`. Return `true` if there is a path from `source` to
`destination`.
""",
    constraints="""
- `1 <= n <= 2 * 10^5`, `0 <= edges.length <= 2 * 10^5`
- no self-loops or repeated edges
""",
    signature=function("validPath", [("n", "int"), ("edges", "int[][]"), ("source", "int"), ("destination", "int")], "bool"),
    reference=_valid_path,
    brute=_path_brute,
    examples=[Example([3, [[0, 1], [1, 2], [2, 0]], 0, 2]), Example([6, [[0, 1], [0, 2], [3, 5], [5, 4], [4, 3]], 0, 5])],
    edge_cases=[[1, [], 0, 0], [2, [], 0, 1], [2, [[0, 1]], 1, 0]],
    generator=_path_gen,
    random_count=8,
)


# ---------------------------------------------------------------- The Skyline Problem


def _get_skyline(buildings: list[list[int]]) -> list[list[int]]:
    events = sorted([(left, -h, right) for left, right, h in buildings] + [(right, 0, 0) for _, right, _ in buildings])
    out: list[list[int]] = []
    live = [(0, float("inf"))]  # (-height, right edge)
    for x, neg_h, right in events:
        while live[0][1] <= x:
            heapq.heappop(live)
        if neg_h:
            heapq.heappush(live, (neg_h, right))
        height = -live[0][0]
        if not out or out[-1][1] != height:
            out.append([x, height])
    return out


def _skyline_brute(buildings: list[list[int]]) -> list[list[int]]:
    xs = sorted({x for left, right, _ in buildings for x in (left, right)})
    out: list[list[int]] = []
    for x in xs:
        height = max((h for left, right, h in buildings if left <= x < right), default=0)
        if not out or out[-1][1] != height:
            out.append([x, height])
    return out


def _skyline_gen(rng: random.Random) -> list:
    hi = rng.choice([20, 2**31 - 1])
    buildings = []
    for _ in range(pick_n(rng, 1, 10, big=2000)):
        left = rng.randint(0, hi - 1)
        buildings.append([left, rng.randint(left + 1, min(hi, left + rng.choice([5, hi]))), rng.randint(1, rng.choice([10, hi]))])
    return [sorted(buildings)]


SKYLINE = ProblemSource(
    title="The Skyline Problem",
    statement="""
`buildings[i] = [left, right, height]` is a rectangle standing on flat ground from `x = left` to `x = right`. The buildings are sorted by `left`.
Return the skyline's *key points* `[x, height]`, sorted by `x`: each is the left end of a horizontal segment of the outline, and the last one
(with height `0`) marks where the rightmost building ends. Consecutive key points never have equal heights.
""",
    constraints="""
- `1 <= buildings.length <= 10^4`
- `0 <= left < right <= 2^31 - 1`, `1 <= height <= 2^31 - 1`
""",
    signature=function("getSkyline", [("buildings", "int[][]")], "int[][]"),
    reference=_get_skyline,
    brute=lambda buildings: _skyline_brute(buildings) if len(buildings) <= 200 else NotImplemented,
    examples=[Example([[[2, 9, 10], [3, 7, 15], [5, 12, 12], [15, 20, 10], [19, 24, 8]]]), Example([[[0, 2, 3], [2, 5, 3]]], "Touching buildings of equal height merge.")],
    edge_cases=[[[[0, 1, 1]]], [[[1, 2, 1], [1, 2, 2], [1, 2, 3]]], [[[0, 5, 1], [1, 2, 3], [3, 4, 3]]]],
    generator=_skyline_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Similar String Groups


def _similar(a: str, b: str) -> bool:
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    return not diff or (len(diff) == 2 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]])


def _num_similar_groups(strs: list[str]) -> int:
    ds = _DisjointSet(len(strs))
    for i in range(len(strs)):
        for j in range(i + 1, len(strs)):
            if _similar(strs[i], strs[j]):
                ds.union(i, j)
    return ds.components


def _similar_brute(strs: list[str]) -> int:
    def one_swap(a: str) -> set[str]:
        out = {a}
        for i in range(len(a)):
            for j in range(i + 1, len(a)):
                chars = list(a)
                chars[i], chars[j] = chars[j], chars[i]
                out.add("".join(chars))
        return out

    index = defaultdict(list)
    for k, s in enumerate(strs):
        index[s].append(k)
    adjacent = {k: [j for t in one_swap(s) for j in index.get(t, ()) if j != k] for k, s in enumerate(strs)}
    return len(_components(list(range(len(strs))), adjacent))


def _similar_gen(rng: random.Random) -> list:
    base = list(word(rng, rng.randint(3, 8), "abcdefgh"))
    out = []
    for _ in range(rng.randint(1, rng.choice([8, 60]))):
        chars = base[:]
        for _ in range(rng.randint(0, 6)):  # several swaps: strings drift apart into separate groups
            i, j = rng.randrange(len(chars)), rng.randrange(len(chars))
            chars[i], chars[j] = chars[j], chars[i]
        out.append("".join(chars))
    return [out]


SIMILAR_GROUPS = ProblemSource(
    title="Similar String Groups",
    statement="""
Two strings are *similar* if they are equal or swapping two letters of one gives the other. All strings in `strs` are anagrams of each other.
Similarity links strings into groups (a string is in a group if it is similar to at least one member, transitively). Return the number of groups.
""",
    constraints="""
- `1 <= strs.length <= 300`, `1 <= strs[i].length <= 300`
- all strings are anagrams of each other; lowercase letters
""",
    signature=function("numSimilarGroups", [("strs", "string[]")], "int"),
    reference=_num_similar_groups,
    brute=_similar_brute,
    brute_input_limit=3000,
    examples=[Example([["tars", "rats", "arts", "star"]], "{tars, rats, arts} and {star}."), Example([["omv", "ovm"]])],
    edge_cases=[[["a"]], [["ab", "ab"]], [["abc", "bca", "cab"]]],
    generator=_similar_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Optimize Water Distribution in a Village


def _min_cost_to_supply_water(n: int, wells: list[int], pipes: list[list[int]]) -> int:
    edges = sorted([(cost, 0, house) for house, cost in enumerate(wells, start=1)] + [(c, a, b) for a, b, c in pipes])
    ds = _DisjointSet(n + 1)  # node 0 is a virtual water source
    return sum(cost for cost, a, b in edges if ds.union(a, b))


def _water_brute(n: int, wells: list[int], pipes: list[list[int]]) -> int:
    best: dict[tuple[int, int], int] = {}
    for house, cost in enumerate(wells, start=1):
        best[(0, house)] = cost
    for a, b, c in pipes:
        key = (min(a, b), max(a, b))
        best[key] = min(best.get(key, c), c)
    adjacent: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for (a, b), c in best.items():
        adjacent[a].append((c, b))
        adjacent[b].append((c, a))
    seen, heap, total = {0}, list(adjacent[0]), 0  # Prim's from the virtual source
    heapq.heapify(heap)
    while heap and len(seen) < n + 1:
        c, v = heapq.heappop(heap)
        if v in seen:
            continue
        seen.add(v)
        total += c
        for edge in adjacent[v]:
            heapq.heappush(heap, edge)
    return total


def _water_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 10, big=1000)
    wells = ints(rng, n, 0, rng.choice([10, 10**5]))
    pipes = [[*sample(rng, range(1, n + 1), 2), rng.randint(0, rng.choice([10, 10**5]))] for _ in range(rng.randint(0, 2 * n)) if n >= 2]
    return [n, wells, pipes]


WATER_DISTRIBUTION = ProblemSource(
    title="Optimize Water Distribution in a Village",
    statement="""
A village has `n` houses labelled `1` to `n`. Building a well inside house `i` costs `wells[i - 1]`; laying the pipe `pipes[j] = [a, b, cost]`
connects houses `a` and `b` in both directions (there may be several pipes between the same pair). Every house must get water, either from its
own well or through pipes from a house that has one. Return the minimum total cost.
""",
    constraints="""
- `1 <= n <= 10^4`, `wells.length == n`, `0 <= wells[i] <= 10^5`
- `0 <= pipes.length <= 10^4`, `a != b`, `0 <= cost <= 10^5`
""",
    signature=function("minCostToSupplyWater", [("n", "int"), ("wells", "int[]"), ("pipes", "int[][]")], "int"),
    reference=_min_cost_to_supply_water,
    brute=_water_brute,
    examples=[Example([3, [1, 2, 2], [[1, 2, 1], [2, 3, 1]]], "Well in house 1, pipes to 2 and 3: 3."), Example([2, [1, 1], [[1, 2, 1], [1, 2, 2]]])],
    edge_cases=[[1, [5], []], [2, [0, 0], [[1, 2, 7]]], [3, [10, 10, 10], [[1, 2, 1], [2, 3, 1], [1, 3, 1]]]],
    generator=_water_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Number of Islands II


def _num_islands_2(m: int, n: int, positions: list[list[int]]) -> list[int]:
    ds = _DisjointSet(m * n)
    land: set[int] = set()
    count, out = 0, []
    for r, c in positions:
        cell = r * n + c
        if cell not in land:
            land.add(cell)
            count += 1
            for a, b in _grid_neighbours(m, n, r, c):
                if a * n + b in land and ds.union(cell, a * n + b):
                    count -= 1
        out.append(count)
    return out


def _islands_ii_brute(m: int, n: int, positions: list[list[int]]) -> list[int]:
    land: set[tuple[int, int]] = set()
    out = []
    for r, c in positions:
        land.add((r, c))
        adjacent = {cell: [d for d in _grid_neighbours(m, n, *cell) if d in land] for cell in land}
        out.append(len(_components(sorted(land), adjacent)))
    return out


ISLANDS_II = ProblemSource(
    title="Number of Islands II",
    statement="""
An `m x n` grid starts as all water. `positions[i] = [r, c]` turns cell `(r, c)` into land (adding land that is already land changes nothing).
After each operation, record the number of islands (groups of land cells connected horizontally or vertically). Return the recorded counts.
""",
    constraints="""
- `1 <= m, n, positions.length <= 10^4`, `m * n <= 10^4`
- `0 <= r < m`, `0 <= c < n`
""",
    signature=function("numIslands2", [("m", "int"), ("n", "int"), ("positions", "int[][]")], "int[]"),
    reference=_num_islands_2,
    brute=lambda m, n, positions: _islands_ii_brute(m, n, positions) if len(positions) <= 60 else NotImplemented,
    examples=[Example([3, 3, [[0, 0], [0, 1], [1, 2], [2, 1]]], "[1,1,2,3]."), Example([1, 1, [[0, 0]]])],
    edge_cases=[[2, 2, [[0, 0], [0, 0], [1, 1], [0, 1]]], [1, 3, [[0, 0], [0, 2], [0, 1]]]],
    generator=lambda rng: [(m := rng.randint(1, rng.choice([5, 100]))), (n := rng.randint(1, rng.choice([5, 100]))), [[rng.randrange(m), rng.randrange(n)] for _ in range(rng.randint(1, rng.choice([20, 500])))]],
    random_count=8,
)


PROBLEMS = [
    NUMBER_OF_ISLANDS,
    LONGEST_CONSECUTIVE,
    REDUNDANT_CONNECTION,
    MOST_STONES,
    LAST_DAY_CROSS,
    REGIONS_SLASHES,
    ACCOUNTS_MERGE,
    MINIMIZE_MALWARE,
    EVALUATE_DIVISION,
    PATH_EXISTS,
    SKYLINE,
    SIMILAR_GROUPS,
    WATER_DISTRIBUTION,
    ISLANDS_II,
]
