"""Pattern 19: Graphs (part 2 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import heapq
import itertools
import random
from collections import deque
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, function, pick_n, sample

PATTERN_NUMBER = 19
_STEPS = ((0, 1), (0, -1), (1, 0), (-1, 0))  # right, left, down, up (matches the arrow codes 1..4 below)
_INF_ROOM = 2147483647


def _dims(rng: random.Random, lo: int, hi: int, big: int) -> tuple[int, int]:
    return pick_n(rng, lo, hi, big=big), pick_n(rng, lo, hi, big=big)


def _binary_grid(rng: random.Random, m: int, n: int, density: float) -> list[list[int]]:
    return [[int(rng.random() < density) for _ in range(n)] for _ in range(m)]


def _neighbours(m: int, n: int, i: int, j: int):
    for di, dj in _STEPS:
        if 0 <= i + di < m and 0 <= j + dj < n:
            yield i + di, j + dj


def _tree_edges(rng: random.Random, n: int) -> list[list[int]]:
    labels = sample(rng, range(n), n)
    return [[labels[rng.randint(max(0, i - rng.choice([1, 3, i])), i - 1)], labels[i]] for i in range(1, n)]


# ---------------------------------------------------------------- Minimum Cost to Make at Least One Valid Path in a Grid


def _min_cost_valid_path(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    cost = [[float("inf")] * n for _ in range(m)]
    cost[0][0] = 0
    queue = deque([(0, 0)])
    while queue:  # 0-1 BFS: following the arrow is free, any other move costs 1
        i, j = queue.popleft()
        for code, (di, dj) in enumerate(_STEPS, start=1):
            a, b = i + di, j + dj
            if not (0 <= a < m and 0 <= b < n):
                continue
            step = 0 if grid[i][j] == code else 1
            if cost[i][j] + step < cost[a][b]:
                cost[a][b] = cost[i][j] + step
                (queue.appendleft if step == 0 else queue.append)((a, b))
    return int(cost[m - 1][n - 1])


def _valid_path_brute(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    cost = {(i, j): float("inf") for i in range(m) for j in range(n)}
    cost[(0, 0)] = 0
    changed = True
    while changed:  # Bellman-Ford style relaxation until stable
        changed = False
        for (i, j), c in list(cost.items()):
            for code, (di, dj) in enumerate(_STEPS, start=1):
                a, b = i + di, j + dj
                if (a, b) in cost and c + (grid[i][j] != code) < cost[(a, b)]:
                    cost[(a, b)] = c + (grid[i][j] != code)
                    changed = True
    return int(cost[(m - 1, n - 1)])


VALID_PATH_COST = ProblemSource(
    title="Minimum Cost to Make at Least One Valid Path in a Grid",
    statement="""
Each cell of `grid` holds an arrow telling you where to go next: `1` = right, `2` = left, `3` = down, `4` = up (an arrow may point outside the
grid). Starting at the top-left cell and following the arrows gives a path. You may change the arrow in any cell at a cost of `1` per change
(each cell at most once). Return the minimum total cost so that following the arrows leads from the top-left to the bottom-right cell.
""",
    constraints="""
- `1 <= m, n <= 100`
- `1 <= grid[i][j] <= 4`
""",
    signature=function("minCost", [("grid", "int[][]")], "int"),
    reference=_min_cost_valid_path,
    brute=_valid_path_brute,
    brute_input_limit=600,
    examples=[Example([[[1, 1, 1, 1], [2, 2, 2, 2], [1, 1, 1, 1], [2, 2, 2, 2]]], "Three changes, e.g. make (0, 3), (1, 0) and (2, 3) point down."), Example([[[1, 1, 3], [3, 2, 2], [1, 1, 4]]], "Already valid: cost 0."), Example([[[1, 2], [4, 3]]])],
    edge_cases=[[[[4]]], [[[2, 2, 2]]], [[[1], [1], [1]]]],
    generator=lambda rng: [[[rng.randint(1, 4) for _ in range(n)] for _ in range(m)] for m, n in [_dims(rng, 1, 7, 100)]],
    random_count=8,
)


# ---------------------------------------------------------------- Shortest Cycle in a Graph


def _find_shortest_cycle(n: int, edges: list[list[int]]) -> int:
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    best = float("inf")
    for source in range(n):
        dist, parent = {source: 0}, {source: -1}
        queue = deque([source])
        while queue:
            v = queue.popleft()
            for w in adjacent[v]:
                if w not in dist:
                    dist[w], parent[w] = dist[v] + 1, v
                    queue.append(w)
                elif parent[v] != w:
                    best = min(best, dist[v] + dist[w] + 1)
    return -1 if best == float("inf") else int(best)


def _shortest_cycle_brute(n: int, edges: list[list[int]]) -> int:
    """For each edge, the shortest cycle through it is the shortest path between its ends without it, plus 1."""
    best = -1
    for skip, (a, b) in enumerate(edges):
        adjacent: list[list[int]] = [[] for _ in range(n)]
        for k, (x, y) in enumerate(edges):
            if k != skip:
                adjacent[x].append(y)
                adjacent[y].append(x)
        dist = {a: 0}
        queue = deque([a])
        while queue:
            v = queue.popleft()
            for w in adjacent[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
        if b in dist and (best == -1 or dist[b] + 1 < best):
            best = dist[b] + 1
    return best


def _cycle_graph_gen(rng: random.Random) -> list:
    n = pick_n(rng, 3, 14, big=1000)
    if rng.random() < 0.5:  # a ring plus a few chords: long cycles
        labels = sample(rng, range(n), n)
        edges = {tuple(sorted((labels[i], labels[(i + 1) % n]))) for i in range(n)}
        extra = rng.randint(0, 2)
    else:
        edges = {tuple(sorted(e)) for e in _tree_edges(rng, n)}
        extra = rng.randint(0, 3)
    for _ in range(extra):
        a, b = sample(rng, range(n), 2)
        edges.add((min(a, b), max(a, b)))
    out = [list(e) for e in sorted(edges)]
    rng.shuffle(out)
    return [n, out]


SHORTEST_CYCLE = ProblemSource(
    title="Shortest Cycle in a Graph",
    statement="""
An undirected graph has `n` nodes labelled `0` to `n - 1` and the edges in `edges` (no self-loops, no repeated edges). Return the length of the
shortest cycle in the graph, or `-1` if there is none. A cycle starts and ends at the same node and uses each edge at most once.
""",
    constraints="""
- `2 <= n <= 1000`, `1 <= edges.length <= 1000`
""",
    signature=function("findShortestCycle", [("n", "int"), ("edges", "int[][]")], "int"),
    reference=_find_shortest_cycle,
    brute=_shortest_cycle_brute,
    brute_input_limit=800,
    examples=[Example([7, [[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 6], [6, 3]]], "0-1-2 has length 3."), Example([4, [[0, 1], [0, 2]]])],
    edge_cases=[[2, [[0, 1]]], [4, [[0, 1], [1, 2], [2, 3], [3, 0]]], [5, [[0, 1], [1, 2], [2, 0], [0, 3], [3, 4], [4, 0]]]],
    generator=_cycle_graph_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Shortest Path Visiting All Nodes


def _shortest_path_length(graph: list[list[int]]) -> int:
    n = len(graph)
    full = (1 << n) - 1
    queue = deque((v, 1 << v, 0) for v in range(n))
    seen = {(v, 1 << v) for v in range(n)}
    while queue:
        v, mask, steps = queue.popleft()
        if mask == full:
            return steps
        for w in graph[v]:
            state = (w, mask | 1 << w)
            if state not in seen:
                seen.add(state)
                queue.append((*state, steps + 1))
    raise AssertionError("the graph is connected")


def _visit_all_brute(graph: list[list[int]]) -> int:
    n = len(graph)
    if n > 7:
        return NotImplemented
    dist = [[0 if i == j else (1 if j in graph[i] else n * n) for j in range(n)] for i in range(n)]
    for k, i, j in itertools.product(range(n), repeat=3):
        dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    return min(sum(dist[a][b] for a, b in itertools.pairwise(order)) for order in itertools.permutations(range(n)))


def _connected_adjacency_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 7, big=12)
    edges = {tuple(sorted(e)) for e in _tree_edges(rng, n)}
    for _ in range(rng.randint(0, n)):
        if n >= 2:
            a, b = sample(rng, range(n), 2)
            edges.add((min(a, b), max(a, b)))
    graph: list[list[int]] = [[] for _ in range(n)]
    for a, b in sorted(edges):
        graph[a].append(b)
        graph[b].append(a)
    return [graph]


VISIT_ALL_NODES = ProblemSource(
    title="Shortest Path Visiting All Nodes",
    statement="""
`graph[i]` lists the neighbours of node `i` in a connected undirected graph with `n` nodes. Return the length (number of edges) of the shortest
walk that visits every node. You may start and stop anywhere, revisit nodes, and reuse edges.
""",
    constraints="""
- `1 <= n <= 12`
- `graph` is connected, undirected, with no self-loops or repeated edges
""",
    signature=function("shortestPathLength", [("graph", "int[][]")], "int"),
    reference=_shortest_path_length,
    brute=_visit_all_brute,
    examples=[Example([[[1, 2, 3], [0], [0], [0]]], "1 -> 0 -> 2 -> 0 -> 3."), Example([[[1], [0, 2, 4], [1, 3, 4], [2], [1, 2]]], "0 -> 1 -> 4 -> 2 -> 3.")],
    edge_cases=[[[[]]], [[[1], [0]]], [[[1], [0, 2], [1, 3], [2]]]],
    generator=_connected_adjacency_gen,
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Max Area of Island


def _max_area_of_island(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    best = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] and (i, j) not in seen:
                seen.add((i, j))
                stack, area = [(i, j)], 0
                while stack:
                    a, b = stack.pop()
                    area += 1
                    for c in _neighbours(m, n, a, b):
                        if grid[c[0]][c[1]] and c not in seen:
                            seen.add(c)
                            stack.append(c)
                best = max(best, area)
    return best


def _max_area_brute(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    parent = {(i, j): (i, j) for i in range(m) for j in range(n) if grid[i][j]}

    def find(x: tuple[int, int]) -> tuple[int, int]:
        while parent[x] != x:
            x = parent[x]
        return x

    for i, j in parent:
        for c in ((i + 1, j), (i, j + 1)):
            if c in parent:
                parent[find(c)] = find((i, j))
    sizes: dict[tuple[int, int], int] = {}
    for cell in parent:
        root = find(cell)
        sizes[root] = sizes.get(root, 0) + 1
    return max(sizes.values(), default=0)


MAX_AREA_ISLAND = ProblemSource(
    title="Max Area of Island",
    statement="""
In the binary grid, `1` is land and `0` is water; an *island* is a group of land cells connected horizontally or vertically. Return the area
(number of cells) of the largest island, or `0` if there is no land.
""",
    constraints="""
- `1 <= m, n <= 50`
- `grid[i][j]` is `0` or `1`
""",
    signature=function("maxAreaOfIsland", [("grid", "int[][]")], "int"),
    reference=_max_area_of_island,
    brute=_max_area_brute,
    examples=[Example([[[0, 0, 1, 0, 0], [0, 1, 1, 0, 0], [0, 1, 0, 0, 1], [0, 0, 0, 1, 1]]], "The island on the left has 4 cells."), Example([[[0, 0, 0, 0]]])],
    edge_cases=[[[[1]]], [[[1, 0, 1]]], [[[1, 1], [1, 1]]]],
    generator=lambda rng: [_binary_grid(rng, *_dims(rng, 1, 8, 50), rng.choice([0.3, 0.5, 0.65]))],
    random_count=8,
)


# ---------------------------------------------------------------- Shortest Path in a Grid with Obstacles Elimination


def _shortest_path_elimination(grid: list[list[int]], k: int) -> int:
    m, n = len(grid), len(grid[0])
    if k >= m + n - 2:
        return m + n - 2
    queue = deque([(0, 0, k, 0)])
    seen = {(0, 0, k)}
    while queue:
        i, j, left, steps = queue.popleft()
        if (i, j) == (m - 1, n - 1):
            return steps
        for a, b in _neighbours(m, n, i, j):
            remaining = left - grid[a][b]
            if remaining >= 0 and (a, b, remaining) not in seen:
                seen.add((a, b, remaining))
                queue.append((a, b, remaining, steps + 1))
    return -1


def _elimination_brute(grid: list[list[int]], k: int) -> int:
    """best[cell] = fewest obstacles removed on a walk of at most t steps; stop at the first t that fits k."""
    m, n = len(grid), len(grid[0])
    inf = float("inf")
    best = [[inf] * n for _ in range(m)]
    best[0][0] = 0
    for t in range(m * n + 1):
        if best[m - 1][n - 1] <= k:
            return t
        best = [[min([best[i][j]] + [best[a][b] + grid[i][j] for a, b in _neighbours(m, n, i, j)]) for j in range(n)] for i in range(m)]
    return -1


def _elimination_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 7, 40)
    grid = _binary_grid(rng, m, n, rng.choice([0.2, 0.4]))
    grid[0][0] = grid[m - 1][n - 1] = 0
    return [grid, rng.randint(1, rng.choice([2, m * n]))]


OBSTACLE_ELIMINATION = ProblemSource(
    title="Shortest Path in a Grid with Obstacles Elimination",
    statement="""
In the grid, `0` is an empty cell and `1` an obstacle; each step moves up, down, left or right. Return the minimum number of steps to walk from
the top-left to the bottom-right cell if you may eliminate at most `k` obstacles (stepping onto an obstacle eliminates it), or `-1` if that's
impossible.
""",
    constraints="""
- `1 <= m, n <= 40`
- `1 <= k <= m * n`
- `grid[0][0] == grid[m - 1][n - 1] == 0`
""",
    signature=function("shortestPath", [("grid", "int[][]"), ("k", "int")], "int"),
    reference=_shortest_path_elimination,
    brute=_elimination_brute,
    brute_input_limit=400,
    examples=[Example([[[0, 0, 0], [1, 1, 0], [0, 0, 0], [0, 1, 1], [0, 0, 0]], 1], "Eliminate the obstacle at (3, 2): 6 steps."), Example([[[0, 1, 1], [1, 1, 1], [1, 0, 0]], 1], "At least two obstacles block every path.")],
    edge_cases=[[[[0]], 1], [[[0, 1, 0]], 1], [[[0, 1, 1, 0]], 1]],
    generator=_elimination_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Snakes and Ladders


def _square_to_cell(n: int, square: int) -> tuple[int, int]:
    row, col = divmod(square - 1, n)
    return n - 1 - row, (col if row % 2 == 0 else n - 1 - col)


def _snakes_and_ladders(board: list[list[int]]) -> int:
    n = len(board)
    goal = n * n
    seen = {1}
    queue = deque([(1, 0)])
    while queue:
        square, moves = queue.popleft()
        for nxt in range(square + 1, min(square + 6, goal) + 1):
            r, c = _square_to_cell(n, nxt)
            dest = board[r][c] if board[r][c] != -1 else nxt
            if dest == goal:
                return moves + 1
            if dest not in seen:
                seen.add(dest)
                queue.append((dest, moves + 1))
    return 0 if goal == 1 else -1


def _snakes_brute(board: list[list[int]]) -> int:
    n = len(board)
    goal = n * n
    flat = {}
    for square in range(1, goal + 1):
        r, c = _square_to_cell(n, square)
        flat[square] = board[r][c]
    best = {square: float("inf") for square in range(1, goal + 1)}
    best[1] = 0
    for _ in range(goal):
        for square in range(1, goal):
            for roll in range(1, 7):
                if square + roll <= goal:
                    landing = square + roll
                    dest = flat[landing] if flat[landing] != -1 else landing
                    best[dest] = min(best[dest], best[square] + 1)
    return -1 if best[goal] == float("inf") else int(best[goal])


def _board_gen(rng: random.Random) -> list:
    n = rng.randint(2, rng.choice([5, 20]))
    goal = n * n
    board = [[-1] * n for _ in range(n)]
    for square in sample(rng, range(2, goal), rng.randint(0, goal // 3)):
        r, c = _square_to_cell(n, square)
        board[r][c] = rng.choice([rng.randint(2, goal), rng.randint(2, square)])
    return [board]


SNAKES_AND_LADDERS = ProblemSource(
    title="Snakes and Ladders",
    statement="""
The `n x n` board's squares are numbered `1` to `n^2` in a boustrophedon pattern: starting at the bottom-left cell and going right along the
bottom row, then left along the row above it, and so on, alternating direction each row.

You start on square `1`. Each move, pick a destination `next` among the next six squares (`curr + 1` to `min(curr + 6, n^2)`), as if rolling a
die. If `next`'s cell holds a value other than `-1`, it is a snake or ladder and you must move to the square it names; you only follow one snake
or ladder per move, even if the square you arrive at starts another. Squares `1` and `n^2` never hold one.

Return the minimum number of moves to reach square `n^2`, or `-1` if it's impossible.
""",
    constraints="""
- `2 <= n <= 20`
- `board[i][j]` is `-1` or in `[1, n^2]`
""",
    signature=function("snakesAndLadders", [("board", "int[][]")], "int"),
    reference=_snakes_and_ladders,
    brute=_snakes_brute,
    brute_input_limit=500,
    examples=[
        Example([[[-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1], [-1, 35, -1, -1, 13, -1], [-1, -1, -1, -1, -1, -1], [-1, 15, -1, -1, -1, -1]]], "1 -> 2 (ladder to 15) -> 17 (snake to 13) -> 14 (ladder to 35) -> 36."),
        Example([[[-1, -1], [-1, 3]]]),
    ],
    edge_cases=[[[[-1, -1], [-1, -1]]], [[[-1, 1, 1], [1, 1, 1], [-1, 1, -1]]]],
    generator=_board_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Walls and Gates


def _walls_and_gates(rooms: list[list[int]]) -> None:
    m, n = len(rooms), len(rooms[0])
    queue = deque((i, j) for i in range(m) for j in range(n) if rooms[i][j] == 0)
    while queue:
        i, j = queue.popleft()
        for a, b in _neighbours(m, n, i, j):
            if rooms[a][b] == _INF_ROOM:
                rooms[a][b] = rooms[i][j] + 1
                queue.append((a, b))


def _walls_brute(rooms: list[list[int]]) -> None:
    """Search from every empty room separately for its nearest gate."""
    m, n = len(rooms), len(rooms[0])
    found: dict[tuple[int, int], int] = {}
    for i in range(m):
        for j in range(n):
            if rooms[i][j] != _INF_ROOM:
                continue
            dist = {(i, j): 0}
            queue = deque([(i, j)])
            while queue:
                v = queue.popleft()
                if rooms[v[0]][v[1]] == 0:
                    found[(i, j)] = dist[v]
                    break
                for w in _neighbours(m, n, *v):
                    if w not in dist and rooms[w[0]][w[1]] != -1:
                        dist[w] = dist[v] + 1
                        queue.append(w)
    for (i, j), d in found.items():
        rooms[i][j] = d


def _rooms_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 7, 100)
    return [[[rng.choice([_INF_ROOM] * 6 + [-1, -1, 0]) for _ in range(n)] for _ in range(m)]]


WALLS_AND_GATES = ProblemSource(
    title="Walls and Gates",
    statement="""
`rooms` is a grid where `-1` is a wall, `0` is a gate and `2147483647` (INF) is an empty room. Fill each empty room **in place** with the number
of steps to its nearest gate (moving up, down, left or right, never through walls). Rooms that can't reach any gate stay INF. Nothing is
returned.
""",
    constraints="""
- `1 <= m, n <= 250`
- `rooms[i][j]` is `-1`, `0` or `2147483647`
""",
    signature=function("wallsAndGates", [("rooms", "int[][]")], "void", mutates="rooms"),
    reference=_walls_and_gates,
    brute=_walls_brute,
    brute_input_limit=1200,
    examples=[
        Example([[[_INF_ROOM, -1, 0, _INF_ROOM], [_INF_ROOM, _INF_ROOM, _INF_ROOM, -1], [_INF_ROOM, -1, _INF_ROOM, -1], [0, -1, _INF_ROOM, _INF_ROOM]]]),
        Example([[[-1]]]),
    ],
    edge_cases=[[[[_INF_ROOM]]], [[[0, _INF_ROOM, _INF_ROOM]]], [[[_INF_ROOM, -1, 0]]]],
    generator=_rooms_gen,
    random_count=8,
)


# ---------------------------------------------------------------- The Maze


def _roll(maze: list[list[int]], i: int, j: int, di: int, dj: int) -> tuple[int, int]:
    m, n = len(maze), len(maze[0])
    while 0 <= i + di < m and 0 <= j + dj < n and maze[i + di][j + dj] == 0:
        i, j = i + di, j + dj
    return i, j


def _has_path(maze: list[list[int]], start: list[int], destination: list[int]) -> bool:
    seen = {tuple(start)}
    stack = [tuple(start)]
    while stack:
        i, j = stack.pop()
        if [i, j] == destination:
            return True
        for di, dj in _STEPS:
            stop = _roll(maze, i, j, di, dj)
            if stop not in seen:
                seen.add(stop)
                stack.append(stop)
    return False


def _maze_brute(maze: list[list[int]], start: list[int], destination: list[int]) -> bool:
    reachable = {tuple(start)}
    while True:
        grown = reachable | {_roll(maze, i, j, di, dj) for i, j in reachable for di, dj in _STEPS}
        if grown == reachable:
            return tuple(destination) in reachable
        reachable = grown


def _maze_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 7, 100)
    if m * n < 2:
        n = 2
    maze = _binary_grid(rng, m, n, rng.choice([0.2, 0.35]))
    cells = sample(rng, range(m * n), 2)
    (si, sj), (di, dj) = (divmod(c, n) for c in cells)
    maze[si][sj] = maze[di][dj] = 0
    return [maze, [si, sj], [di, dj]]


THE_MAZE = ProblemSource(
    title="The Maze",
    statement="""
A ball sits in a maze where `0` is empty space and `1` is a wall; the border of the grid also acts as a wall. The ball can be pushed up, down,
left or right, and then keeps rolling until it hits a wall; only then can it be pushed again. Return `true` if the ball can come to **rest** at
`destination`, starting from `start`.
""",
    constraints="""
- `1 <= m, n <= 100`
- `start` and `destination` are distinct empty cells
""",
    signature=function("hasPath", [("maze", "int[][]"), ("start", "int[]"), ("destination", "int[]")], "bool"),
    reference=_has_path,
    brute=_maze_brute,
    examples=[
        Example([[[0, 0, 1, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 1, 0], [1, 1, 0, 1, 1], [0, 0, 0, 0, 0]], [0, 4], [4, 4]], "left, down, left, down, right."),
        Example([[[0, 0, 1, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 1, 0], [1, 1, 0, 1, 1], [0, 0, 0, 0, 0]], [0, 4], [3, 2]], "The ball can pass (3, 2) but never stop there."),
    ],
    edge_cases=[[[[0, 0]], [0, 0], [0, 1]], [[[0, 0, 0]], [0, 0], [0, 1]], [[[0], [1], [0]], [0, 0], [2, 0]]],
    generator=_maze_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Shortest Path in Binary Matrix


_KING = [(di, dj) for di in (-1, 0, 1) for dj in (-1, 0, 1) if (di, dj) != (0, 0)]


def _shortest_path_binary_matrix(grid: list[list[int]]) -> int:
    n = len(grid)
    if grid[0][0] or grid[n - 1][n - 1]:
        return -1
    dist = {(0, 0): 1}
    queue = deque([(0, 0)])
    while queue:
        i, j = queue.popleft()
        if (i, j) == (n - 1, n - 1):
            return dist[(i, j)]
        for di, dj in _KING:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < n and not grid[a][b] and (a, b) not in dist:
                dist[(a, b)] = dist[(i, j)] + 1
                queue.append((a, b))
    return -1


def _binary_matrix_brute(grid: list[list[int]]) -> int:
    n = len(grid)
    open_cells = {(i, j) for i in range(n) for j in range(n) if not grid[i][j]}
    heap = [(1, 0, 0)] if (0, 0) in open_cells else []
    done: set[tuple[int, int]] = set()
    while heap:
        d, i, j = heapq.heappop(heap)
        if (i, j) in done:
            continue
        done.add((i, j))
        if (i, j) == (n - 1, n - 1):
            return d
        heap += [(d + 1, i + di, j + dj) for di, dj in _KING if (i + di, j + dj) in open_cells]
        heapq.heapify(heap)
    return -1


def _binary_matrix_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 8, big=100)
    grid = _binary_grid(rng, n, n, rng.choice([0.15, 0.3, 0.4]))
    if rng.random() < 0.8:  # mostly open corners, so paths usually exist
        grid[0][0] = grid[n - 1][n - 1] = 0
    return [grid]


BINARY_MATRIX_PATH = ProblemSource(
    title="Shortest Path in Binary Matrix",
    statement="""
In the `n x n` binary grid, a *clear path* goes from the top-left to the bottom-right cell through cells holding `0` only, moving in any of the 8
directions (including diagonals) between cells that share an edge or a corner. Return the number of cells on the shortest clear path, or `-1` if
there is none.
""",
    constraints="""
- `1 <= n <= 100`
- `grid[i][j]` is `0` or `1`
""",
    signature=function("shortestPathBinaryMatrix", [("grid", "int[][]")], "int"),
    reference=_shortest_path_binary_matrix,
    brute=_binary_matrix_brute,
    brute_input_limit=2500,
    examples=[Example([[[0, 1], [1, 0]]], "One diagonal step: 2 cells."), Example([[[0, 0, 0], [1, 1, 0], [1, 1, 0]]]), Example([[[1, 0, 0], [1, 1, 0], [1, 1, 0]]], "The start is blocked.")],
    edge_cases=[[[[0]]], [[[1]]], [[[0, 0], [0, 1]]]],
    generator=_binary_matrix_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Making A Large Island


def _largest_island(grid: list[list[int]]) -> int:
    n = len(grid)
    label = [[0] * n for _ in range(n)]
    sizes = {0: 0}
    next_label = 1
    for i in range(n):
        for j in range(n):
            if grid[i][j] and not label[i][j]:
                label[i][j] = next_label
                stack, size = [(i, j)], 0
                while stack:
                    a, b = stack.pop()
                    size += 1
                    for c, d in _neighbours(n, n, a, b):
                        if grid[c][d] and not label[c][d]:
                            label[c][d] = next_label
                            stack.append((c, d))
                sizes[next_label] = size
                next_label += 1
    best = max(sizes.values())
    for i in range(n):
        for j in range(n):
            if not grid[i][j]:
                touching = {label[a][b] for a, b in _neighbours(n, n, i, j)}
                best = max(best, 1 + sum(sizes[t] for t in touching))
    return best


def _large_island_brute(grid: list[list[int]]) -> int:
    n = len(grid)
    options = [grid] + [[[1 if (a, b) == (i, j) else grid[a][b] for b in range(n)] for a in range(n)] for i in range(n) for j in range(n) if not grid[i][j]]
    return max(_max_area_brute(option) for option in options)


LARGE_ISLAND = ProblemSource(
    title="Making A Large Island",
    statement="""
`grid` is an `n x n` binary matrix (`1` = land). You may change **at most one** `0` into a `1`. Return the size of the largest island possible
afterwards, where an island is a group of land cells connected horizontally or vertically.
""",
    constraints="""
- `1 <= n <= 500`
- `grid[i][j]` is `0` or `1`
""",
    signature=function("largestIsland", [("grid", "int[][]")], "int"),
    reference=_largest_island,
    brute=lambda grid: _large_island_brute(grid) if len(grid) <= 8 else NotImplemented,
    examples=[Example([[[1, 0], [0, 1]]], "Flip one 0 to join both cells: 3."), Example([[[1, 1], [1, 0]]]), Example([[[1, 1], [1, 1]]], "Nothing to flip.")],
    edge_cases=[[[[0]]], [[[1]]], [[[1, 0, 1], [0, 0, 0], [1, 0, 1]]]],
    generator=lambda rng: [_binary_grid(rng, (n := pick_n(rng, 1, 8, big=150)), n, rng.choice([0.3, 0.5, 0.7]))],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Edge Reversals So Every Node Is Reachable


def _min_edge_reversals(n: int, edges: list[list[int]]) -> list[int]:
    adjacent: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append((b, 0))  # following a -> b from a costs nothing
        adjacent[b].append((a, 1))  # reaching a from b needs this edge reversed
    order, parent, cost_from_parent = [0], {0: -1}, {0: 0}
    for v in order:  # BFS from node 0; the list grows while iterating
        for w, cost in adjacent[v]:
            if w not in parent:
                parent[w], cost_from_parent[w] = v, cost
                order.append(w)
    answer = [0] * n
    answer[0] = sum(cost_from_parent.values())
    for v in order[1:]:  # rerooting: moving the root across one edge only flips whether that edge needs reversing
        answer[v] = answer[parent[v]] + (1 if cost_from_parent[v] == 0 else -1)
    return answer


def _reversals_brute(n: int, edges: list[list[int]]) -> list[int]:
    undirected: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        undirected[a].append(b)
        undirected[b].append(a)
    out = []
    for root in range(n):
        depth = {root: 0}
        queue = deque([root])
        while queue:
            v = queue.popleft()
            for w in undirected[v]:
                if w not in depth:
                    depth[w] = depth[v] + 1
                    queue.append(w)
        out.append(sum(depth[a] > depth[b] for a, b in edges))  # edges pointing back toward the root
    return out


EDGE_REVERSALS = ProblemSource(
    title="Minimum Edge Reversals So Every Node Is Reachable",
    statement="""
A directed graph on nodes `0` to `n - 1` has `n - 1` edges (`edges[i] = [u, v]` points from `u` to `v`) and would be a tree if the edges were
undirected. For every node `i`, compute the minimum number of edge reversals needed so that, starting from `i`, every other node can be reached
by following directed edges. Return those counts as a list indexed by node.
""",
    constraints="""
- `2 <= n <= 10^5`
- the undirected version of `edges` is a tree
""",
    signature=function("minEdgeReversals", [("n", "int"), ("edges", "int[][]")], "int[]"),
    reference=_min_edge_reversals,
    brute=lambda n, edges: _reversals_brute(n, edges) if n <= 200 else NotImplemented,
    examples=[Example([4, [[2, 0], [2, 1], [1, 3]]], "From 2 everything is already reachable."), Example([3, [[1, 2], [2, 0]]])],
    edge_cases=[[2, [[0, 1]]], [2, [[1, 0]]], [4, [[0, 1], [2, 1], [3, 1]]]],
    generator=lambda rng: [(n := pick_n(rng, 2, 12, big=3000)), [e if rng.random() < 0.5 else e[::-1] for e in _tree_edges(rng, n)]],
    random_count=8,
)


# ---------------------------------------------------------------- Keys and Rooms


def _can_visit_all_rooms(rooms: list[list[int]]) -> bool:
    seen, stack = {0}, [0]
    while stack:
        for key in rooms[stack.pop()]:
            if key not in seen:
                seen.add(key)
                stack.append(key)
    return len(seen) == len(rooms)


def _rooms_brute(rooms: list[list[int]]) -> bool:
    opened = {0}
    while True:
        grown = opened | {k for r in opened for k in rooms[r]}
        if grown == opened:
            return len(opened) == len(rooms)
        opened = grown


def _keys_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 10, big=1000)
    return [[sample(rng, range(n), rng.randint(0, min(n, rng.choice([1, 2, 3])))) for _ in range(n)]]


KEYS_AND_ROOMS = ProblemSource(
    title="Keys and Rooms",
    statement="""
There are `n` locked rooms labelled `0` to `n - 1`, except room `0`, which is open. Room `i` contains the keys listed in `rooms[i]`; each key
opens the room with that label. Starting in room `0`, return `true` if you can enter every room.
""",
    constraints="""
- `2 <= n <= 1000`, total keys `<= 3000`
- `0 <= rooms[i][j] < n`; keys within a room are distinct
""",
    signature=function("canVisitAllRooms", [("rooms", "int[][]")], "bool"),
    reference=_can_visit_all_rooms,
    brute=_rooms_brute,
    examples=[Example([[[1], [2], [3], []]]), Example([[[1, 3], [3, 0, 1], [2], [0]]], "The only key to room 2 is inside room 2.")],
    edge_cases=[[[[], []]], [[[1], []]], [[[1], [0]]]],
    generator=_keys_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Knight Moves


@cache
def _knight_distance(x: int, y: int) -> int:
    if x + y == 0:
        return 0
    if x + y == 2:
        return 2
    return 1 + min(_knight_distance(abs(x - 1), abs(y - 2)), _knight_distance(abs(x - 2), abs(y - 1)))


def _min_knight_moves(x: int, y: int) -> int:
    return _knight_distance(abs(x), abs(y))


def _knight_brute(x: int, y: int) -> int:
    if abs(x) + abs(y) > 60:
        return NotImplemented
    bound = max(abs(x), abs(y)) + 4
    dist = {(0, 0): 0}
    queue = deque([(0, 0)])
    while queue:
        a, b = queue.popleft()
        if (a, b) == (x, y):
            return dist[(a, b)]
        for da, db in ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)):
            c, d = a + da, b + db
            if abs(c) <= bound and abs(d) <= bound and (c, d) not in dist:
                dist[(c, d)] = dist[(a, b)] + 1
                queue.append((c, d))
    raise AssertionError("always reachable")


KNIGHT_MOVES = ProblemSource(
    title="Minimum Knight Moves",
    statement="""
A knight stands at `[0, 0]` on an infinite chessboard. In one move it goes two squares in one axis direction and one square in the other. Return
the minimum number of moves to reach `[x, y]` (the answer always exists).
""",
    constraints="""
- `-300 <= x, y <= 300`
- `0 <= |x| + |y| <= 300`
""",
    signature=function("minKnightMoves", [("x", "int"), ("y", "int")], "int"),
    reference=_min_knight_moves,
    brute=_knight_brute,
    examples=[Example([2, 1], "[0,0] -> [2,1]."), Example([5, 5], "4 moves.")],
    edge_cases=[[0, 0], [1, 1], [1, 0], [-1, 0], [300, 0], [-150, -150]],
    generator=lambda rng: [(x := rng.randint(-(lim := rng.choice([10, 300])), lim)), rng.randint(-(lim - abs(x)), lim - abs(x))],
    random_count=10,
)


PROBLEMS = [
    VALID_PATH_COST,
    SHORTEST_CYCLE,
    VISIT_ALL_NODES,
    MAX_AREA_ISLAND,
    OBSTACLE_ELIMINATION,
    SNAKES_AND_LADDERS,
    WALLS_AND_GATES,
    THE_MAZE,
    BINARY_MATRIX_PATH,
    LARGE_ISLAND,
    EDGE_REVERSALS,
    KEYS_AND_ROOMS,
    KNIGHT_MOVES,
]
