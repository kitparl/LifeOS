"""Pattern 19: Graphs (part 1 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import heapq
import itertools
import random
from collections import defaultdict, deque

from app.modules.dsa.content.model import Example, ProblemSource, function, pick_n, sample

PATTERN_NUMBER = 19


def _tree_edges(rng: random.Random, n: int, spread: int | None = None) -> list[list[int]]:
    """Random tree on 0..n-1 (shuffled labels). A small `spread` makes long, path-like trees."""
    labels = sample(rng, range(n), n)
    reach = spread or n
    return [[labels[rng.randint(max(0, i - reach), i - 1)], labels[i]] for i in range(1, n)]


def _random_edges(rng: random.Random, n: int, m: int) -> list[list[int]]:
    """Up to m distinct undirected edges on 0..n-1 without self-loops."""
    pairs = set()
    for _ in range(3 * m):
        if len(pairs) >= m or n < 2:
            break
        a, b = sample(rng, range(n), 2)
        pairs.add((min(a, b), max(a, b)))
    edges = [list(p) for p in sorted(pairs)]
    rng.shuffle(edges)
    return edges


def _bfs_distances(adjacent: dict[int, list[int]] | list[list[int]], source: int) -> dict[int, int]:
    dist = {source: 0}
    queue = deque([source])
    while queue:
        v = queue.popleft()
        for w in adjacent[v]:
            if w not in dist:
                dist[w] = dist[v] + 1
                queue.append(w)
    return dist


# ---------------------------------------------------------------- Clone Graph


def _clone_graph(adjList: list[list[int]]) -> list[list[int]]:
    if not adjList:
        return []
    new_label = {1: 1}
    order = [1]
    queue = deque([1])
    while queue:
        v = queue.popleft()
        for w in adjList[v - 1]:
            if w not in new_label:
                new_label[w] = len(new_label) + 1
                order.append(w)
                queue.append(w)
    return [[new_label[w] for w in adjList[v - 1]] for v in order]


class _Node:
    def __init__(self, val: int) -> None:
        self.val = val
        self.neighbors: list[_Node] = []


def _clone_graph_brute(adjList: list[list[int]]) -> list[list[int]]:
    """Build real nodes, deep-copy them with a visited map, then serialise the copy in BFS order."""
    if not adjList:
        return []
    nodes = [_Node(i + 1) for i in range(len(adjList))]
    for node, neighbours in zip(nodes, adjList, strict=True):
        node.neighbors = [nodes[w - 1] for w in neighbours]
    copies: dict[_Node, _Node] = {}

    def clone(node: _Node) -> _Node:
        if node not in copies:
            copies[node] = _Node(node.val)
            copies[node].neighbors = [clone(w) for w in node.neighbors]
        return copies[node]

    root = clone(nodes[0])
    label = {root: 1}
    order = [root]
    for node in order:  # grows while iterating: a BFS
        for w in node.neighbors:
            if w not in label:
                label[w] = len(label) + 1
                order.append(w)
    return [[label[w] for w in node.neighbors] for node in order]


def _connected_graph_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 10, big=100)
    edges = _tree_edges(rng, n) + _random_edges(rng, n, rng.randint(0, n))
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in {(min(a, b), max(a, b)) for a, b in edges}:
        adjacent[a].append(b + 1)
        adjacent[b].append(a + 1)
    for neighbours in adjacent:
        rng.shuffle(neighbours)
    return [adjacent]


CLONE_GRAPH = ProblemSource(
    title="Clone Graph",
    statement="""
*Adapted I/O:* the original problem hands you a node of a connected undirected graph and asks for a deep copy. Our judge has no graph-node type,
so the graph arrives as adjacency lists — `adjList[i]` lists the neighbours of node `i + 1`, in order — and you return the adjacency lists of your
copy with its nodes **renumbered in the order a breadth-first traversal from node 1 first reaches them** (node 1 keeps label 1; neighbours are
explored in list order). Each node's neighbour list keeps its original order, expressed in the new labels.

This is exactly the old-to-new mapping a clone builds while it walks the graph. An empty graph (`[]`) returns `[]`.
""",
    constraints="""
- `0 <= n <= 100`
- the graph is connected and undirected, with no self-loops or repeated edges
""",
    signature=function("cloneGraph", [("adjList", "int[][]")], "int[][]"),
    reference=_clone_graph,
    brute=_clone_graph_brute,
    is_variant=True,
    examples=[
        Example([[[2, 4], [1, 3], [2, 4], [1, 3]]], "BFS from 1 reaches 2, then 4, then 3, so old 4 becomes 3 and old 3 becomes 4."),
        Example([[[]]], "A single node without neighbours."),
        Example([[]], "An empty graph."),
    ],
    edge_cases=[[[[2], [1]]], [[[3], [3], [1, 2]]], [[[2, 3, 4], [1], [1], [1]]]],
    generator=_connected_graph_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Graph Valid Tree


def _valid_tree(n: int, edges: list[list[int]]) -> bool:
    if len(edges) != n - 1:
        return False
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
    return True


def _valid_tree_brute(n: int, edges: list[list[int]]) -> bool:
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    return len(edges) == n - 1 and len(_bfs_distances(adjacent, 0)) == n


def _tree_or_not_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 10, big=2000)
    edges = _tree_edges(rng, n)
    roll = rng.random()
    if roll < 0.3 and edges:
        edges.pop(rng.randrange(len(edges)))  # a forest
    elif roll < 0.6 and n >= 3:
        edges += [e for e in _random_edges(rng, n, 1) if sorted(e) not in [sorted(x) for x in edges]]  # a cycle
    rng.shuffle(edges)
    return [n, edges]


GRAPH_VALID_TREE = ProblemSource(
    title="Graph Valid Tree",
    statement="""
There are `n` nodes labelled `0` to `n - 1`, and `edges[i] = [a, b]` is an undirected edge. Return `true` if the edges form a valid tree: all
nodes connected, with no cycles.
""",
    constraints="""
- `1 <= n <= 2000`, `0 <= edges.length <= 5000`
- no self-loops or repeated edges
""",
    signature=function("validTree", [("n", "int"), ("edges", "int[][]")], "bool"),
    reference=_valid_tree,
    brute=_valid_tree_brute,
    examples=[Example([5, [[0, 1], [0, 2], [0, 3], [1, 4]]]), Example([5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]], "1-2-3 forms a cycle.")],
    edge_cases=[[1, []], [2, []], [4, [[0, 1], [2, 3]]], [3, [[0, 1], [1, 2]]]],
    generator=_tree_or_not_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Network Delay Time


def _network_delay_time(times: list[list[int]], n: int, k: int) -> int:
    adjacent: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        adjacent[u].append((v, w))
    dist: dict[int, int] = {}
    heap = [(0, k)]
    while heap:
        d, v = heapq.heappop(heap)
        if v in dist:
            continue
        dist[v] = d
        for w, cost in adjacent[v]:
            if w not in dist:
                heapq.heappush(heap, (d + cost, w))
    return max(dist.values()) if len(dist) == n else -1


def _network_brute(times: list[list[int]], n: int, k: int) -> int:
    inf = float("inf")
    dist = [inf] * (n + 1)
    dist[k] = 0
    for _ in range(n - 1):
        for u, v, w in times:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    worst = max(dist[1:])
    return -1 if worst == inf else int(worst)


def _weighted_digraph_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 8, big=100)
    draws = rng.randint(0, 3 * n) if n >= 2 else 0
    pairs = {tuple(sample(rng, range(1, n + 1), 2)) for _ in range(draws)}
    times = [[a, b, rng.randint(0, 100)] for a, b in sorted(pairs)]
    rng.shuffle(times)
    return [times, n, rng.randint(1, n)]


NETWORK_DELAY = ProblemSource(
    title="Network Delay Time",
    statement="""
A network has `n` nodes labelled `1` to `n`. `times[i] = [u, v, w]` means a signal sent from `u` reaches `v` after `w` units of time (edges are
directed). A signal is sent from node `k`. Return the time it takes for every node to receive it, or `-1` if some node never does.
""",
    constraints="""
- `1 <= k <= n <= 100`
- `1 <= times.length <= 6000`, `0 <= w <= 100`
- no repeated `(u, v)` pairs and no self-loops
""",
    signature=function("networkDelayTime", [("times", "int[][]"), ("n", "int"), ("k", "int")], "int"),
    reference=_network_delay_time,
    brute=_network_brute,
    examples=[Example([[[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2], "Node 4 is the last to hear, at time 2."), Example([[[1, 2, 1]], 2, 1]), Example([[[1, 2, 1]], 2, 2], "Node 1 is never reached.")],
    edge_cases=[[[], 1, 1], [[[1, 2, 0]], 2, 1], [[[1, 2, 5], [1, 3, 1], [3, 2, 1]], 3, 1]],
    generator=_weighted_digraph_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Paths in Maze That Lead to Same Room


def _number_of_paths(n: int, corridors: list[list[int]]) -> int:
    adjacent: list[set[int]] = [set() for _ in range(n + 1)]
    for a, b in corridors:
        adjacent[a].add(b)
        adjacent[b].add(a)
    count = 0
    for a, b in corridors:  # each triangle is found once, from its two smallest rooms
        lo, hi = min(a, b), max(a, b)
        count += sum(1 for c in adjacent[lo] & adjacent[hi] if c > hi)
    return count


def _paths_brute(n: int, corridors: list[list[int]]) -> int:
    if n > 40:
        return NotImplemented
    edges = {frozenset(c) for c in corridors}
    return sum(1 for a, b, c in itertools.combinations(range(1, n + 1), 3) if {frozenset((a, b)), frozenset((b, c)), frozenset((a, c))} <= edges)


MAZE_SAME_ROOM = ProblemSource(
    title="Paths in Maze That Lead to Same Room",
    statement="""
A maze has `n` rooms labelled `1` to `n`; `corridors[i] = [a, b]` is a two-way corridor between rooms `a` and `b`. The maze's *confusion score*
is the number of distinct cycles of length 3 (three rooms, each pair joined by a corridor); two cycles are different if their sets of rooms
differ. Return the confusion score.
""",
    constraints="""
- `2 <= n <= 1000`, `1 <= corridors.length <= 5 * 10^4`
- no self-loops or repeated corridors
""",
    signature=function("numberOfPaths", [("n", "int"), ("corridors", "int[][]")], "int"),
    reference=_number_of_paths,
    brute=_paths_brute,
    examples=[Example([5, [[1, 2], [5, 2], [4, 1], [2, 4], [3, 1], [3, 4]]], "Two triangles: 1-2-4 and 1-3-4."), Example([4, [[1, 2], [3, 4]]])],
    edge_cases=[[3, [[1, 2], [2, 3], [3, 1]]], [4, [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]], [2, [[1, 2]]]],
    generator=lambda rng: [(n := pick_n(rng, 3, 12, big=1000)), [[a + 1, b + 1] for a, b in _random_edges(rng, n, rng.randint(1, min(3 * n, n * (n - 1) // 2)))]],
    random_count=8,
)


# ---------------------------------------------------------------- Bus Routes


def _num_buses_to_destination(routes: list[list[int]], source: int, target: int) -> int:
    if source == target:
        return 0
    by_stop: dict[int, list[int]] = defaultdict(list)
    for r, route in enumerate(routes):
        for stop in route:
            by_stop[stop].append(r)
    used_routes: set[int] = set()
    seen_stops = {source}
    frontier = [source]
    buses = 0
    while frontier:
        buses += 1
        nxt = []
        for stop in frontier:
            for r in by_stop[stop]:
                if r in used_routes:
                    continue
                used_routes.add(r)
                for s in routes[r]:
                    if s == target:
                        return buses
                    if s not in seen_stops:
                        seen_stops.add(s)
                        nxt.append(s)
        frontier = nxt
    return -1


def _buses_brute(routes: list[list[int]], source: int, target: int) -> int:
    reached = {source}
    for buses in range(len(routes) + 1):
        if target in reached:
            return buses
        reached = reached.union(*(set(r) for r in routes if reached & set(r)))
    return -1


def _routes_gen(rng: random.Random) -> list:
    stops = rng.randint(2, rng.choice([12, 500]))
    routes = [sample(rng, range(stops), rng.randint(1, min(stops, 6))) for _ in range(rng.randint(1, rng.choice([5, 40])))]
    return [routes, rng.randrange(stops), rng.randrange(stops)]


BUS_ROUTES = ProblemSource(
    title="Bus Routes",
    statement="""
`routes[i]` lists the stops that bus `i` visits, repeating forever. You start at stop `source` (not on any bus) and want to reach stop `target`,
travelling only by bus. Return the least number of buses you must take, or `-1` if it's impossible. Reaching `target` from `target` takes `0`
buses.
""",
    constraints="""
- `1 <= routes.length <= 500`, `1 <= routes[i].length <= 10^5`, stops within a route are distinct
- total stops across routes `<= 10^5`
- `0 <= routes[i][j], source, target < 10^6`
""",
    signature=function("numBusesToDestination", [("routes", "int[][]"), ("source", "int"), ("target", "int")], "int"),
    reference=_num_buses_to_destination,
    brute=_buses_brute,
    examples=[Example([[[1, 2, 7], [3, 6, 7]], 1, 6], "Bus 0 to stop 7, then bus 1 to stop 6."), Example([[[7, 12], [4, 5, 15], [6], [15, 19], [9, 12, 13]], 15, 12])],
    edge_cases=[[[[1, 2]], 1, 1], [[[1, 2]], 3, 3], [[[1, 2]], 1, 3], [[[1, 2], [2, 3], [3, 4]], 1, 4]],
    generator=_routes_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Reconstruct Itinerary


def _find_itinerary(tickets: list[list[str]]) -> list[str]:
    outgoing: dict[str, list[str]] = defaultdict(list)
    for a, b in sorted(tickets, reverse=True):
        outgoing[a].append(b)  # reverse-sorted, so pop() yields the smallest
    route: list[str] = []
    stack = ["JFK"]
    while stack:
        while outgoing[stack[-1]]:
            stack.append(outgoing[stack[-1]].pop())
        route.append(stack.pop())
    return route[::-1]


def _itinerary_brute(tickets: list[list[str]]) -> list[str]:
    if len(tickets) > 12:
        return NotImplemented
    ordered = sorted(tickets)
    used = [False] * len(ordered)
    path = ["JFK"]

    def extend() -> bool:
        if len(path) == len(ordered) + 1:
            return True
        for i, (a, b) in enumerate(ordered):
            if not used[i] and a == path[-1] and (i == 0 or used[i - 1] or ordered[i - 1] != ordered[i]):
                used[i] = True
                path.append(b)
                if extend():
                    return True
                used[i] = False
                path.pop()
        return False

    extend()
    return path


def _itinerary_gen(rng: random.Random) -> list:
    airports = ["JFK", *rng.sample(["ATL", "SFO", "MUC", "LHR", "SJC", "AAA", "BBB", "CDG", "NRT", "SYD"], rng.randint(1, 5))]
    here, tickets = "JFK", []
    for _ in range(pick_n(rng, 1, 10, big=300)):
        there = rng.choice([a for a in airports if a != here])
        tickets.append([here, there])
        here = there
    rng.shuffle(tickets)
    return [tickets]


RECONSTRUCT_ITINERARY = ProblemSource(
    title="Reconstruct Itinerary",
    statement="""
`tickets[i] = [from, to]` is a one-way flight between airports named by three capital letters. All tickets belong to one traveller who departs
from `"JFK"`, and together they form at least one valid itinerary that uses every ticket exactly once.

Return that itinerary as the list of airports visited. If several itineraries are valid, return the lexicographically smallest one (compare the
lists airport by airport).
""",
    constraints="""
- `1 <= tickets.length <= 300`
- airport names are 3 uppercase English letters; `from != to`
- at least one valid itinerary exists
""",
    signature=function("findItinerary", [("tickets", "string[][]")], "string[]"),
    reference=_find_itinerary,
    brute=_itinerary_brute,
    examples=[
        Example([[["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]]]),
        Example([[["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "ATL"], ["ATL", "JFK"], ["ATL", "SFO"]]], "[\"JFK\",\"SFO\",\"ATL\",\"JFK\",\"ATL\",\"SFO\"] is also valid but lexicographically larger."),
    ],
    edge_cases=[[[["JFK", "AAA"]]], [[["JFK", "KUL"], ["JFK", "NRT"], ["NRT", "JFK"]]], [[["JFK", "AAA"], ["AAA", "JFK"], ["JFK", "AAA"]]]],
    generator=_itinerary_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Lucky Numbers in a Matrix


def _lucky_numbers(matrix: list[list[int]]) -> list[int]:
    row_mins = {min(row) for row in matrix}
    col_maxes = {max(col) for col in zip(*matrix, strict=True)}
    return sorted(row_mins & col_maxes)


def _lucky_brute(matrix: list[list[int]]) -> list[int]:
    out = []
    for row in matrix:
        for j, v in enumerate(row):
            if v == min(row) and all(matrix[k][j] <= v for k in range(len(matrix))):
                out.append(v)
    return out


def _lucky_gen(rng: random.Random) -> list:
    m, n = pick_n(rng, 1, 6, big=50), pick_n(rng, 1, 6, big=50)
    values = sample(rng, range(1, 5 * 10**4), m * n)  # headroom so a planted row stays <= 10^5
    grid = [values[i * n : (i + 1) * n] for i in range(m)]
    if rng.random() < 0.5:  # plant a lucky number: the largest value, placed as the minimum of its row
        i, j = rng.randrange(m), rng.randrange(n)
        top = max(values) + 1
        grid[i] = [v + top for v in grid[i]]
        grid[i][j] = top
    return [grid]


LUCKY_NUMBERS = ProblemSource(
    title="Lucky Numbers in a Matrix",
    statement="""
`matrix` holds distinct integers. A *lucky number* is an element that is the minimum of its row and the maximum of its column. Return all lucky
numbers, in any order.
""",
    constraints="""
- `1 <= m, n <= 50`
- `1 <= matrix[i][j] <= 10^5`, all distinct
""",
    signature=function("luckyNumbers", [("matrix", "int[][]")], "int[]"),
    reference=_lucky_numbers,
    brute=_lucky_brute,
    compare="unordered",
    examples=[Example([[[3, 7, 8], [9, 11, 13], [15, 16, 17]]], "15 is the smallest in its row and largest in its column."), Example([[[1, 10, 4, 2], [9, 3, 8, 7], [15, 16, 17, 12]]]), Example([[[7, 8], [1, 2]]])],
    edge_cases=[[[[5]]], [[[1, 2, 3]]], [[[3], [2], [1]]], [[[2, 1], [3, 4]]]],
    generator=_lucky_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Path with Maximum Probability


def _max_probability(n: int, edges: list[list[int]], succProb: list[float], start_node: int, end_node: int) -> float:
    adjacent: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for (a, b), p in zip(edges, succProb, strict=True):
        adjacent[a].append((b, p))
        adjacent[b].append((a, p))
    best = {start_node: 1.0}
    heap = [(-1.0, start_node)]
    done: set[int] = set()
    while heap:
        neg, v = heapq.heappop(heap)
        if v in done:
            continue
        if v == end_node:
            return -neg
        done.add(v)
        for w, p in adjacent[v]:
            if -neg * p > best.get(w, 0.0):
                best[w] = -neg * p
                heapq.heappush(heap, (-best[w], w))
    return 0.0


def _probability_brute(n: int, edges: list[list[int]], succProb: list[float], start_node: int, end_node: int) -> float:
    best = [0.0] * n
    best[start_node] = 1.0
    for _ in range(n):
        for (a, b), p in zip(edges, succProb, strict=True):
            best[b] = max(best[b], best[a] * p)
            best[a] = max(best[a], best[b] * p)
    return best[end_node]


def _probability_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 9, big=1000)
    edges = _random_edges(rng, n, rng.randint(1, min(2 * n, n * (n - 1) // 2)))
    probabilities = [round(rng.random(), 2) for _ in edges]
    start, end = sample(rng, range(n), 2)
    return [n, edges, probabilities, start, end]


MAX_PROBABILITY = ProblemSource(
    title="Path with Maximum Probability",
    statement="""
An undirected graph has `n` nodes labelled `0` to `n - 1`. Traversing edge `edges[i] = [a, b]` succeeds with probability `succProb[i]`. Return
the maximum probability of successfully travelling from `start_node` to `end_node` (the product of the edge probabilities along the path), or `0`
if no path exists. Answers within `10^-5` are accepted.
""",
    constraints="""
- `2 <= n <= 10^4`, `0 <= edges.length <= 2 * 10^4`
- `0 <= succProb[i] <= 1`
- `start_node != end_node`; no repeated edges
""",
    signature=function(
        "maxProbability",
        [("n", "int"), ("edges", "int[][]"), ("succProb", "double[]"), ("start_node", "int"), ("end_node", "int")],
        "double",
    ),
    reference=_max_probability,
    brute=_probability_brute,
    compare="float_tolerance",
    examples=[Example([3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.2], 0, 2], "Via node 1: 0.5 * 0.5 = 0.25 beats 0.2."), Example([3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.3], 0, 2]), Example([3, [[0, 1]], [0.5], 0, 2])],
    edge_cases=[[2, [], [], 0, 1], [2, [[0, 1]], [1.0], 1, 0], [3, [[0, 1], [1, 2]], [0.0, 1.0], 0, 2]],
    generator=_probability_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Reorder Routes to Make All Paths Lead to the City Zero


def _min_reorder(n: int, connections: list[list[int]]) -> int:
    adjacent: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for a, b in connections:
        adjacent[a].append((b, 1))  # travelling a -> b away from 0 means this road must flip
        adjacent[b].append((a, 0))
    flips, seen, stack = 0, {0}, [0]
    while stack:
        v = stack.pop()
        for w, cost in adjacent[v]:
            if w not in seen:
                seen.add(w)
                flips += cost
                stack.append(w)
    return flips


def _reorder_brute(n: int, connections: list[list[int]]) -> int:
    undirected: list[list[int]] = [[] for _ in range(n)]
    for a, b in connections:
        undirected[a].append(b)
        undirected[b].append(a)
    depth = _bfs_distances(undirected, 0)
    return sum(depth[a] < depth[b] for a, b in connections)


REORDER_ROUTES = ProblemSource(
    title="Reorder Routes to Make All Paths Lead to the City Zero",
    statement="""
`n` cities labelled `0` to `n - 1` are joined by `n - 1` one-way roads that would form a tree if they were two-way; `connections[i] = [a, b]` is a
road from `a` to `b`. Everyone is travelling to city `0`. Return the minimum number of roads whose direction must be reversed so that every city
can reach city `0`.
""",
    constraints="""
- `2 <= n <= 5 * 10^4`
- `connections.length == n - 1`; the undirected version is a tree
""",
    signature=function("minReorder", [("n", "int"), ("connections", "int[][]")], "int"),
    reference=_min_reorder,
    brute=_reorder_brute,
    examples=[Example([6, [[0, 1], [1, 3], [2, 3], [4, 0], [4, 5]]], "Flip 0->1, 1->3 and 4->5."), Example([5, [[1, 0], [1, 2], [3, 2], [3, 4]]]), Example([3, [[1, 0], [2, 0]]])],
    edge_cases=[[2, [[0, 1]]], [2, [[1, 0]]], [4, [[0, 1], [1, 2], [2, 3]]]],
    generator=lambda rng: [(n := pick_n(rng, 2, 12, big=3000)), [e if rng.random() < 0.5 else e[::-1] for e in _tree_edges(rng, n, rng.choice([2, None]))]],
    random_count=8,
)


# ---------------------------------------------------------------- Tree Diameter


def _tree_diameter(edges: list[list[int]]) -> int:
    n = len(edges) + 1
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    first = _bfs_distances(adjacent, 0)
    far = max(first, key=first.__getitem__)
    return max(_bfs_distances(adjacent, far).values())


def _diameter_brute(edges: list[list[int]]) -> int:
    n = len(edges) + 1
    if n > 150:
        return NotImplemented
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    return max(max(_bfs_distances(adjacent, s).values()) for s in range(n))


TREE_DIAMETER = ProblemSource(
    title="Tree Diameter",
    statement="""
An undirected tree has nodes `0` to `n - 1`, where `n = edges.length + 1`. Return its *diameter*: the number of edges on the longest path between
any two nodes.
""",
    constraints="""
- `1 <= n <= 10^4`
- `edges` forms a tree
""",
    signature=function("treeDiameter", [("edges", "int[][]")], "int"),
    reference=_tree_diameter,
    brute=_diameter_brute,
    examples=[Example([[[0, 1], [0, 2]]], "1 - 0 - 2."), Example([[[0, 1], [1, 2], [2, 3], [1, 4], [4, 5]]], "3 - 2 - 1 - 4 - 5.")],
    edge_cases=[[[]], [[[0, 1]]], [[[0, 1], [0, 2], [0, 3], [0, 4]]]],
    generator=lambda rng: [_tree_edges(rng, pick_n(rng, 1, 15, big=3000), rng.choice([1, 2, None]))],
    random_count=8,
)


# ---------------------------------------------------------------- Find the Town Judge


def _find_judge(n: int, trust: list[list[int]]) -> int:
    score = [0] * (n + 1)
    for a, b in trust:
        score[a] -= 1
        score[b] += 1
    return next((p for p in range(1, n + 1) if score[p] == n - 1), -1)


def _judge_brute(n: int, trust: list[list[int]]) -> int:
    pairs = {tuple(t) for t in trust}
    judges = [p for p in range(1, n + 1) if not any(a == p for a, _ in pairs) and all((q, p) in pairs for q in range(1, n + 1) if q != p)]
    return judges[0] if len(judges) == 1 else -1


def _judge_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 8, big=1000)
    pairs = {tuple(sample(rng, range(1, n + 1), 2)) for _ in range(rng.randint(0, 2 * n))} if n >= 2 else set()
    if rng.random() < 0.6:
        judge = rng.randint(1, n)
        pairs = {(a, b) for a, b in pairs if a != judge} | {(q, judge) for q in range(1, n + 1) if q != judge}
        if rng.random() < 0.3 and n >= 2:
            pairs.discard((next(q for q in range(1, n + 1) if q != judge), judge))
    trust = [list(p) for p in sorted(pairs)]
    rng.shuffle(trust)
    return [n, trust]


TOWN_JUDGE = ProblemSource(
    title="Find the Town Judge",
    statement="""
A town has `n` people labelled `1` to `n`; `trust[i] = [a, b]` means person `a` trusts person `b`. The *town judge*, if one exists, trusts nobody
and is trusted by everybody else, and at most one person fits that description. Return the judge's label, or `-1` if there is no judge.
""",
    constraints="""
- `1 <= n <= 1000`, `0 <= trust.length <= 10^4`
- `a != b`; all pairs distinct
""",
    signature=function("findJudge", [("n", "int"), ("trust", "int[][]")], "int"),
    reference=_find_judge,
    brute=_judge_brute,
    examples=[Example([2, [[1, 2]]]), Example([3, [[1, 3], [2, 3]]]), Example([3, [[1, 3], [2, 3], [3, 1]]], "Person 3 trusts person 1, so 3 can't be the judge.")],
    edge_cases=[[1, []], [2, []], [3, [[1, 2], [2, 3]]]],
    generator=_judge_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find Center of Star Graph


def _find_center(edges: list[list[int]]) -> int:
    a, b = edges[0]
    return a if a in edges[1] else b


def _star_gen(rng: random.Random) -> list:
    n = pick_n(rng, 3, 10, big=10**4)
    center = rng.randint(1, n)
    edges = [[center, v] if rng.random() < 0.5 else [v, center] for v in range(1, n + 1) if v != center]
    rng.shuffle(edges)
    return [edges]


STAR_CENTER = ProblemSource(
    title="Find Center of Star Graph",
    statement="""
An undirected *star graph* on nodes `1` to `n` has one center node joined to every other node, and no other edges. Given its `n - 1` edges,
return the center.
""",
    constraints="""
- `3 <= n <= 10^5`
- `edges` describes a valid star graph
""",
    signature=function("findCenter", [("edges", "int[][]")], "int"),
    reference=_find_center,
    brute=lambda edges: max(range(1, len(edges) + 2), key=lambda v: sum(v in e for e in edges)),
    brute_input_limit=5000,
    examples=[Example([[[1, 2], [2, 3], [4, 2]]]), Example([[[1, 2], [5, 1], [1, 3], [1, 4]]])],
    edge_cases=[[[[1, 3], [2, 3]]], [[[3, 1], [1, 2]]]],
    generator=_star_gen,
    random_count=6,
)


# ---------------------------------------------------------------- Longest Cycle in a Graph


def _longest_cycle(edges: list[int]) -> int:
    visited_at = [0] * len(edges)  # global step at which a node was first visited
    step, best = 1, -1
    for start in range(len(edges)):
        begin = step
        v = start
        while v != -1 and not visited_at[v]:
            visited_at[v] = step
            step += 1
            v = edges[v]
        if v != -1 and visited_at[v] >= begin:  # closed a loop within this walk
            best = max(best, step - visited_at[v])
    return best


def _cycle_brute(edges: list[int]) -> int:
    n = len(edges)
    best = -1
    for start in range(n):
        v, steps = edges[start], 1
        while v != -1 and v != start and steps <= n:
            v, steps = edges[v], steps + 1
        if v == start:
            best = max(best, steps)
    return best


def _functional_graph_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 12, big=10**4)
    edges = [-1 if rng.random() < 0.15 else (i + rng.randint(1, n - 1)) % n for i in range(n)]  # never a self-loop
    return [edges]


LONGEST_CYCLE = ProblemSource(
    title="Longest Cycle in a Graph",
    statement="""
A directed graph has `n` nodes labelled `0` to `n - 1`, each with at most one outgoing edge: `edges[i]` is the target of node `i`'s edge, or `-1`
if it has none. Return the length (number of nodes) of the longest cycle in the graph, or `-1` if there is no cycle.
""",
    constraints="""
- `2 <= n <= 10^5`
- `edges[i] == -1` or `0 <= edges[i] < n` with `edges[i] != i`
""",
    signature=function("longestCycle", [("edges", "int[]")], "int"),
    reference=_longest_cycle,
    brute=lambda edges: _cycle_brute(edges) if len(edges) <= 300 else NotImplemented,
    examples=[Example([[3, 3, 4, 2, 3]], "Cycle 2 -> 4 -> 3 -> 2."), Example([[2, -1, 3, 1]], "No cycle.")],
    edge_cases=[[[1, 0]], [[-1, -1]], [[1, 2, 0, 4, 5, 3, 3]]],
    generator=_functional_graph_gen,
    random_count=8,
)


PROBLEMS = [
    CLONE_GRAPH,
    GRAPH_VALID_TREE,
    NETWORK_DELAY,
    MAZE_SAME_ROOM,
    BUS_ROUTES,
    RECONSTRUCT_ITINERARY,
    LUCKY_NUMBERS,
    MAX_PROBABILITY,
    REORDER_ROUTES,
    TREE_DIAMETER,
    TOWN_JUDGE,
    STAR_CENTER,
    LONGEST_CYCLE,
]
