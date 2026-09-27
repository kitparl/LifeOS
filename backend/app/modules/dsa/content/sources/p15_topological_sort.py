"""Pattern 15: Topological Sort. Original statements; outputs come from `reference`."""

from __future__ import annotations

import heapq
import itertools
import random
from collections import deque
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sample, word

PATTERN_NUMBER = 15


def _kahn(nodes: list, edges: list[tuple]) -> list:
    """Topological order of `nodes` for edges (u, v) meaning u before v; [] if there is a cycle.

    The earliest ready node in `nodes` order is taken first, so the result is deterministic.
    """
    rank = {v: i for i, v in enumerate(nodes)}
    out_edges: dict = {v: [] for v in nodes}
    indegree = dict.fromkeys(nodes, 0)
    for u, v in edges:
        out_edges[u].append(v)
        indegree[v] += 1
    ready = [rank[v] for v in nodes if indegree[v] == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        u = nodes[heapq.heappop(ready)]
        order.append(u)
        for v in out_edges[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                heapq.heappush(ready, rank[v])
    return order if len(order) == len(nodes) else []


def _respects(order: list, edges: list[tuple]) -> bool:
    position = {v: i for i, v in enumerate(order)}
    return all(position[u] < position[v] for u, v in edges)


def _first_valid_permutation(nodes: list, edges: list[tuple]) -> list:
    """Brute-force topological order: the first permutation that respects every edge, or []."""
    return next((list(p) for p in itertools.permutations(nodes) if _respects(list(p), edges)), [])


def _random_dag_pairs(rng: random.Random, n: int, m: int, cycle_chance: float) -> list[list[int]]:
    """m distinct [a, b] pairs over 0..n-1 with a hidden order; sometimes one back edge is added."""
    hidden = sample(rng, range(n), n)
    pairs = set()
    for _ in range(m * 3):
        if len(pairs) >= m:
            break
        i, j = sorted(sample(rng, range(n), 2)) if n >= 2 else (0, 0)
        if i != j:
            pairs.add((hidden[i], hidden[j]))
    edges = [list(p) for p in sorted(pairs)]
    if edges and rng.random() < cycle_chance:
        a, b = rng.choice(edges)
        edges.append([b, a])
    rng.shuffle(edges)
    return edges


# ---------------------------------------------------------------- Alien Dictionary


def _alien_constraints(words: list[str]) -> list[tuple[str, str]] | None:
    pairs = []
    for a, b in itertools.pairwise(words):
        diff = next(((x, y) for x, y in zip(a, b, strict=False) if x != y), None)
        if diff is None:
            if len(a) > len(b):
                return None  # a longer word before its own prefix
            continue
        pairs.append(diff)
    return pairs


def _alien_order(words: list[str]) -> str:
    pairs = _alien_constraints(words)
    if pairs is None:
        return ""
    letters = sorted(set("".join(words)))
    return "".join(_kahn(letters, pairs))


def _alien_brute(words: list[str]) -> str:
    pairs = _alien_constraints(words)
    letters = sorted(set("".join(words)))
    if pairs is None:
        return ""
    if len(letters) > 7:
        return NotImplemented
    return "".join(_first_valid_permutation(letters, pairs))


def _alien_gen(rng: random.Random) -> list[list[str]]:
    alphabet = "".join(sample(rng, "abcdefgh", rng.randint(2, 7)))
    words = sorted({word(rng, rng.randint(1, 4), alphabet) for _ in range(rng.randint(1, 8))}, key=lambda w: [alphabet.index(c) for c in w])
    if len(words) >= 2 and rng.random() < 0.25:
        i = rng.randint(0, len(words) - 2)
        words[i], words[i + 1] = words[i + 1], words[i]
    return [words]


ALIEN_DICTIONARY = ProblemSource(
    title="Alien Dictionary",
    statement="""
An alien language uses a subset of the lowercase English letters in an unknown order. `words` is a list of words from its dictionary, claimed to
be sorted lexicographically by the alien order.

Return a string containing every letter that appears in `words` exactly once, arranged in an order consistent with the list. If the list can't be
sorted under any order, return `""`. When several orders are valid, any of them is accepted.
""",
    constraints="""
- `1 <= words.length <= 100`
- `1 <= words[i].length <= 100`
- lowercase English letters only
""",
    signature=function("alienOrder", [("words", "string[]")], "string"),
    reference=_alien_order,
    brute=_alien_brute,
    compare="checker",
    checker="alien_order",
    examples=[
        Example([["wrt", "wrf", "er", "ett", "rftt"]], "t < f, w < e, r < t, e < r gives \"wertf\"."),
        Example([["z", "x"]]),
        Example([["z", "x", "z"]], "z < x and x < z contradict each other."),
    ],
    edge_cases=[[["abc", "ab"]], [["a"]], [["ab", "abc"]], [["ba", "bc", "ac", "cab"]]],
    generator=_alien_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Course Schedule


def _can_finish(numCourses: int, prerequisites: list[list[int]]) -> bool:
    return bool(_kahn(list(range(numCourses)), [(b, a) for a, b in prerequisites]))


def _can_finish_brute(numCourses: int, prerequisites: list[list[int]]) -> bool:
    graph: dict[int, list[int]] = {v: [] for v in range(numCourses)}
    for a, b in prerequisites:
        graph[b].append(a)
    state = [0] * numCourses  # 0 new, 1 on stack, 2 done

    def has_cycle(v: int) -> bool:
        state[v] = 1
        for w in graph[v]:
            if state[w] == 1 or (state[w] == 0 and has_cycle(w)):
                return True
        state[v] = 2
        return False

    return not any(state[v] == 0 and has_cycle(v) for v in range(numCourses))


COURSE_SCHEDULE = ProblemSource(
    title="Course Schedule",
    statement="""
There are `numCourses` courses labelled `0` to `numCourses - 1`. `prerequisites[i] = [a, b]` means course `b` must be completed before course `a`.
Return `true` if it is possible to finish every course, otherwise `false`.
""",
    constraints="""
- `1 <= numCourses <= 2000`
- `0 <= prerequisites.length <= 5000`
- `prerequisites[i] = [a, b]`, `a != b`, all pairs distinct
""",
    signature=function("canFinish", [("numCourses", "int"), ("prerequisites", "int[][]")], "bool"),
    reference=_can_finish,
    brute=_can_finish_brute,
    examples=[Example([2, [[1, 0]]], "Take 0, then 1."), Example([2, [[1, 0], [0, 1]]], "Each course waits on the other.")],
    edge_cases=[[1, []], [3, [[0, 1], [1, 2], [2, 0]]], [4, [[1, 0], [2, 0], [3, 1], [3, 2]]]],
    generator=lambda rng: [(n := pick_n(rng, 1, 10, big=2000)), _random_dag_pairs(rng, n, rng.randint(0, min(3 * n, 5000)), 0.4)],
    random_count=8,
)


# ---------------------------------------------------------------- Compilation Order


def _compilation_order(dependencies: list[list[str]]) -> list[str]:
    nodes = sorted({x for pair in dependencies for x in pair})
    return _kahn(nodes, [(b, a) for a, b in dependencies])


def _compilation_brute(dependencies: list[list[str]]) -> list[str]:
    nodes = sorted({x for pair in dependencies for x in pair})
    if len(nodes) > 7:
        return NotImplemented
    return _first_valid_permutation(nodes, [(b, a) for a, b in dependencies])


def _compilation_gen(rng: random.Random) -> list[list[list[str]]]:
    n = pick_n(rng, 2, 7, big=26)
    names = sample(rng, [chr(ord("A") + i) for i in range(26)], n)
    pairs = _random_dag_pairs(rng, n, rng.randint(1, 2 * n), 0.3)
    return [[[names[a], names[b]] for a, b in pairs]]


COMPILATION_ORDER = ProblemSource(
    title="Compilation Order",
    statement="""
A build contains classes identified by names. Each `dependencies[i] = [x, y]` says class `x` depends on class `y`, so `y` must be compiled
before `x`. Return an order in which every class mentioned in `dependencies` can be compiled, each exactly once. If a circular dependency makes it
impossible, return an empty list. Any valid order is accepted.
""",
    constraints="""
- `1 <= dependencies.length <= 1000`
- class names are short strings; `x != y` in every pair
""",
    signature=function("compilationOrder", [("dependencies", "string[][]")], "string[]"),
    reference=_compilation_order,
    brute=_compilation_brute,
    compare="checker",
    checker="compilation_order",
    examples=[
        Example([[["B", "A"], ["C", "A"], ["D", "C"], ["E", "D"], ["E", "B"]]], "A first; B and C after it; D after C; E last."),
        Example([[["B", "A"], ["A", "B"]]], "A and B depend on each other."),
    ],
    edge_cases=[[[["B", "A"]]], [[["A", "B"], ["B", "C"], ["C", "A"]]], [[["X", "Y"], ["P", "Q"]]]],
    generator=_compilation_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Verifying an Alien Dictionary


def _is_alien_sorted(words: list[str], order: str) -> bool:
    rank = {c: i for i, c in enumerate(order)}
    for a, b in itertools.pairwise(words):
        for x, y in zip(a, b, strict=False):
            if x != y:
                if rank[x] > rank[y]:
                    return False
                break
        else:
            if len(a) > len(b):
                return False
    return True


def _is_alien_sorted_brute(words: list[str], order: str) -> bool:
    keyed = [[order.index(c) for c in w] for w in words]
    return keyed == sorted(keyed)


def _verify_gen(rng: random.Random) -> list:
    order = "".join(sample(rng, "abcdefghijklmnopqrstuvwxyz", 26))
    alphabet = order[: rng.randint(2, 5)] if rng.random() < 0.7 else order
    words = [word(rng, rng.randint(1, 5), alphabet) for _ in range(rng.randint(1, rng.choice([6, 100])))]
    if rng.random() < 0.5:
        words.sort(key=lambda w: [order.index(c) for c in w])
    return [words, order]


VERIFY_ALIEN = ProblemSource(
    title="Verifying an Alien Dictionary",
    statement="""
An alien language uses all 26 lowercase English letters, and `order` lists them from smallest to largest. Return `true` if `words` is sorted
lexicographically under that order. As usual, a word comes before any longer word it is a prefix of.
""",
    constraints="""
- `1 <= words.length <= 100`
- `1 <= words[i].length <= 20`
- `order` is a permutation of the 26 lowercase letters
""",
    signature=function("isAlienSorted", [("words", "string[]"), ("order", "string")], "bool"),
    reference=_is_alien_sorted,
    brute=_is_alien_sorted_brute,
    examples=[
        Example([["hello", "leetcode"], "hlabcdefgijkmnopqrstuvwxyz"], "h comes before l."),
        Example([["word", "world", "row"], "worldabcefghijkmnpqstuvxyz"], "d comes after l, so \"word\" > \"world\"."),
        Example([["apple", "app"], "abcdefghijklmnopqrstuvwxyz"], "\"app\" is a prefix of \"apple\" and must come first."),
    ],
    edge_cases=[[["a"], "abcdefghijklmnopqrstuvwxyz"], [["app", "app"], "zyxwvutsrqponmlkjihgfedcba"], [["ba", "ab"], "bacdefghijklmnopqrstuvwxyz"]],
    generator=_verify_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Course Schedule II


def _find_order(numCourses: int, prerequisites: list[list[int]]) -> list[int]:
    return _kahn(list(range(numCourses)), [(b, a) for a, b in prerequisites])


def _find_order_brute(numCourses: int, prerequisites: list[list[int]]) -> list[int]:
    if numCourses > 7:
        return NotImplemented
    return _first_valid_permutation(list(range(numCourses)), [(b, a) for a, b in prerequisites])


COURSE_SCHEDULE_II = ProblemSource(
    title="Course Schedule II",
    statement="""
There are `numCourses` courses labelled `0` to `numCourses - 1`, and `prerequisites[i] = [a, b]` means course `b` must be taken before course `a`.
Return an order in which all courses can be taken. If that's impossible, return an empty array. Any valid order is accepted.
""",
    constraints="""
- `1 <= numCourses <= 2000`
- `0 <= prerequisites.length <= numCourses * (numCourses - 1)`
- `prerequisites[i] = [a, b]`, `a != b`, all pairs distinct
""",
    signature=function("findOrder", [("numCourses", "int"), ("prerequisites", "int[][]")], "int[]"),
    reference=_find_order,
    brute=_find_order_brute,
    compare="checker",
    checker="course_order",
    examples=[
        Example([2, [[1, 0]]], "0 then 1."),
        Example([4, [[1, 0], [2, 0], [3, 1], [3, 2]]], "[0,1,2,3] and [0,2,1,3] are both valid."),
        Example([1, []]),
    ],
    edge_cases=[[2, [[0, 1], [1, 0]]], [3, []], [3, [[1, 0], [2, 1], [0, 2]]]],
    generator=lambda rng: [(n := pick_n(rng, 1, 7, big=2000)), _random_dag_pairs(rng, n, rng.randint(0, min(3 * n, 5000)), 0.3)],
    random_count=8,
)


# ---------------------------------------------------------------- Find All Possible Recipes from Given Supplies


def _find_all_recipes(recipes: list[str], ingredients: list[list[str]], supplies: list[str]) -> list[str]:
    recipe_set = set(recipes)
    waiting: dict[str, list[str]] = {}
    missing = {}
    for recipe, needs in zip(recipes, ingredients, strict=True):
        missing[recipe] = len(needs)
        for item in needs:
            waiting.setdefault(item, []).append(recipe)
    ready = deque(supplies)
    made = []
    while ready:
        item = ready.popleft()
        if item in recipe_set:
            made.append(item)
        for recipe in waiting.get(item, []):
            missing[recipe] -= 1
            if missing[recipe] == 0:
                ready.append(recipe)
    return made


def _recipes_brute(recipes: list[str], ingredients: list[list[str]], supplies: list[str]) -> list[str]:
    have = set(supplies)
    changed = True
    while changed:
        changed = False
        for recipe, needs in zip(recipes, ingredients, strict=True):
            if recipe not in have and all(x in have for x in needs):
                have.add(recipe)
                changed = True
    return [r for r in recipes if r in have]


def _recipes_gen(rng: random.Random) -> list:
    names = [f"r{i}" for i in range(rng.randint(1, rng.choice([6, 60])))]
    base = [f"s{i}" for i in range(rng.randint(1, 8))]
    supplies = sample(rng, base, rng.randint(1, len(base)))
    ingredients = []
    for i in range(len(names)):
        pool = base + [n for j, n in enumerate(names) if j != i and (j < i or rng.random() < 0.1)]
        ingredients.append(sample(rng, pool, rng.randint(1, min(4, len(pool)))))
    return [names, ingredients, supplies]


FIND_RECIPES = ProblemSource(
    title="Find All Possible Recipes from Given Supplies",
    statement="""
`recipes[i]` can be cooked once you have every item in `ingredients[i]`. An ingredient may itself be another recipe. You start with an unlimited
amount of every item in `supplies`. Return all recipes you can eventually cook, in any order.
""",
    constraints="""
- `1 <= recipes.length == ingredients.length <= 100`
- `1 <= ingredients[i].length, supplies.length <= 100`
- all names are distinct within each list; no recipe is also a supply
""",
    signature=function(
        "findAllRecipes", [("recipes", "string[]"), ("ingredients", "string[][]"), ("supplies", "string[]")], "string[]"
    ),
    reference=_find_all_recipes,
    brute=_recipes_brute,
    compare="unordered",
    examples=[
        Example([["bread"], [["yeast", "flour"]], ["yeast", "flour", "corn"]]),
        Example([["bread", "sandwich"], [["yeast", "flour"], ["bread", "meat"]], ["yeast", "flour", "meat"]], "Bread first, then the sandwich."),
        Example([["bread", "sandwich", "burger"], [["yeast", "flour"], ["bread", "meat"], ["sandwich", "meat", "bread"]], ["yeast", "flour", "meat"]]),
    ],
    edge_cases=[[["a"], [["b"]], ["c"]], [["a", "b"], [["b"], ["a"]], ["x"]], [["a", "b"], [["x"], ["a", "x"]], ["x"]]],
    generator=_recipes_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Build a Matrix with Conditions


def _build_matrix(k: int, rowConditions: list[list[int]], colConditions: list[list[int]]) -> list[list[int]]:
    rows = _kahn(list(range(1, k + 1)), [tuple(c) for c in rowConditions])
    cols = _kahn(list(range(1, k + 1)), [tuple(c) for c in colConditions])
    if not rows or not cols:
        return []
    col_of = {v: j for j, v in enumerate(cols)}
    matrix = [[0] * k for _ in range(k)]
    for i, v in enumerate(rows):
        matrix[i][col_of[v]] = v
    return matrix


def _build_matrix_brute(k: int, rowConditions: list[list[int]], colConditions: list[list[int]]) -> list[list[int]]:
    if k > 6:
        return NotImplemented
    nodes = list(range(1, k + 1))
    rows = _first_valid_permutation(nodes, [tuple(c) for c in rowConditions])
    cols = _first_valid_permutation(nodes, [tuple(c) for c in colConditions])
    if not rows or not cols:
        return []
    return [[v if cols[j] == v else 0 for j in range(k)] for v in rows]


def _matrix_conditions_gen(rng: random.Random) -> list:
    k = pick_n(rng, 2, 6, big=60)

    def conditions() -> list[list[int]]:
        return [[a + 1, b + 1] for a, b in _random_dag_pairs(rng, k, rng.randint(1, 2 * k), 0.15)]

    return [k, conditions(), conditions()]


BUILD_MATRIX = ProblemSource(
    title="Build a Matrix with Conditions",
    statement="""
Build a `k x k` matrix that contains each number from `1` to `k` exactly once, with every other cell `0`, such that:

- for each `rowConditions[i] = [above, below]`, `above` sits in a strictly higher row than `below`;
- for each `colConditions[i] = [left, right]`, `left` sits in a strictly earlier column than `right`.

Return any such matrix, or an empty matrix if none exists.
""",
    constraints="""
- `2 <= k <= 400`
- `1 <= rowConditions.length, colConditions.length <= 10^4`
- each condition has two different numbers in `1..k`
""",
    signature=function(
        "buildMatrix", [("k", "int"), ("rowConditions", "int[][]"), ("colConditions", "int[][]")], "int[][]"
    ),
    reference=_build_matrix,
    brute=_build_matrix_brute,
    compare="checker",
    checker="matrix_conditions",
    examples=[
        Example([3, [[1, 2], [3, 2]], [[2, 1], [3, 2]]], "e.g. [[3,0,0],[0,0,1],[0,2,0]]."),
        Example([3, [[1, 2], [2, 3], [3, 1], [2, 3]], [[2, 1]]], "The row conditions form a cycle."),
    ],
    edge_cases=[[2, [[1, 2]], [[1, 2]]], [2, [[1, 2]], [[1, 2], [2, 1]]], [4, [[1, 2], [3, 4]], [[4, 3]]]],
    generator=_matrix_conditions_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Longest Path With Different Adjacent Characters


def _longest_path(parent: list[int], s: str) -> int:
    n = len(parent)
    children = [0] * n
    for p in parent[1:]:
        children[p] += 1
    best_down = [1] * n  # longest valid downward chain starting at v
    top_two = [[0, 0] for _ in range(n)]
    ready = deque(v for v in range(n) if children[v] == 0)
    answer = 1
    while ready:  # leaves first, like Kahn's algorithm on the child -> parent edges
        v = ready.popleft()
        a, b = top_two[v]
        best_down[v] = 1 + a
        answer = max(answer, 1 + a + b)
        p = parent[v]
        if p == -1:
            continue
        if s[p] != s[v]:
            pair = top_two[p]
            if best_down[v] > pair[0]:
                pair[0], pair[1] = best_down[v], pair[0]
            elif best_down[v] > pair[1]:
                pair[1] = best_down[v]
        children[p] -= 1
        if children[p] == 0:
            ready.append(p)
    return answer


def _longest_path_brute(parent: list[int], s: str) -> int:
    n = len(parent)
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for v in range(1, n):
        adjacent[v].append(parent[v])
        adjacent[parent[v]].append(v)
    best = 1
    for start in range(n):
        stack = [(start, -1, 1)]
        while stack:
            v, prev, length = stack.pop()
            best = max(best, length)
            stack += [(w, v, length + 1) for w in adjacent[v] if w != prev and s[w] != s[v]]
    return best


def _longest_path_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 12, big=10**4)
    parent = [-1] + [rng.randint(max(0, i - rng.choice([1, 3, i])), i - 1) for i in range(1, n)]
    return [parent, word(rng, n, rng.choice(["ab", "abc", "abcd", "abcdefghijklmnopqrstuvwxyz"]))]


LONGEST_DIFFERENT_PATH = ProblemSource(
    title="Longest Path With Different Adjacent Characters",
    statement="""
A tree of `n` nodes is rooted at node `0`; `parent[i]` is the parent of node `i` and `parent[0] == -1`. Node `i` carries the letter `s[i]`.

Return the number of nodes on the longest path in the tree in which no two neighbouring nodes carry the same letter.
""",
    constraints="""
- `1 <= n <= 10^5`
- `parent` describes a valid tree rooted at `0`
- `s` consists of lowercase English letters
""",
    signature=function("longestPath", [("parent", "int[]"), ("s", "string")], "int"),
    reference=_longest_path,
    brute=_longest_path_brute,
    brute_input_limit=400,
    examples=[
        Example([[-1, 0, 0, 1, 1, 2], "abacbe"], "3 -> 1 -> 0 (c, b, a); node 2 repeats node 0's letter."),
        Example([[-1, 0, 0, 0], "aabc"], "2 -> 0 -> 3 (b, a, c)."),
    ],
    edge_cases=[[[-1], "z"], [[-1, 0], "aa"], [[-1, 0, 1, 2, 3], "ababa"]],
    generator=_longest_path_gen,
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Parallel Courses III


def _minimum_time(n: int, relations: list[list[int]], time: list[int]) -> int:
    order = _kahn(list(range(1, n + 1)), [tuple(r) for r in relations])
    earliest_finish = {v: time[v - 1] for v in order}
    successors: dict[int, list[int]] = {v: [] for v in order}
    for a, b in relations:
        successors[a].append(b)
    for v in order:
        for w in successors[v]:
            earliest_finish[w] = max(earliest_finish[w], earliest_finish[v] + time[w - 1])
    return max(earliest_finish.values())


def _minimum_time_brute(n: int, relations: list[list[int]], time: list[int]) -> int:
    if n > 800:
        return NotImplemented  # recursion depth
    before: dict[int, list[int]] = {v: [] for v in range(1, n + 1)}
    for a, b in relations:
        before[b].append(a)

    @cache
    def finish(v: int) -> int:
        return time[v - 1] + max((finish(u) for u in before[v]), default=0)

    return max(finish(v) for v in range(1, n + 1))


PARALLEL_COURSES_III = ProblemSource(
    title="Parallel Courses III",
    statement="""
There are `n` courses labelled `1` to `n`. `relations[j] = [prev, next]` means course `prev` must be finished before course `next` starts, and
course `i` takes `time[i - 1]` months. Any number of courses may run at the same time. Return the minimum number of months to finish every course.
The relations are guaranteed to be acyclic.
""",
    constraints="""
- `1 <= n <= 5 * 10^4`
- `0 <= relations.length <= 5 * 10^4`, pairs distinct, no cycles
- `1 <= time[i] <= 10^4`
""",
    signature=function("minimumTime", [("n", "int"), ("relations", "int[][]"), ("time", "int[]")], "int"),
    reference=_minimum_time,
    brute=_minimum_time_brute,
    examples=[
        Example([3, [[1, 3], [2, 3]], [3, 2, 5]], "Courses 1 and 2 start together; 3 starts at month 3 and ends at 8."),
        Example([5, [[1, 5], [2, 5], [3, 5], [3, 4], [4, 5]], [1, 2, 3, 4, 5]], "3 -> 4 -> 5 takes 3 + 4 + 5 = 12."),
    ],
    edge_cases=[[1, [], [7]], [3, [], [5, 1, 9]], [4, [[1, 2], [2, 3], [3, 4]], [1, 1, 1, 1]]],
    generator=lambda rng: [
        (n := pick_n(rng, 1, 12, big=3000)),
        [[a + 1, b + 1] for a, b in _random_dag_pairs(rng, n, rng.randint(0, 2 * n), 0.0)],
        ints(rng, n, 1, 10**4),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Parallel Courses


def _minimum_semesters(n: int, relations: list[list[int]]) -> int:
    indegree = [0] * (n + 1)
    successors: list[list[int]] = [[] for _ in range(n + 1)]
    for a, b in relations:
        successors[a].append(b)
        indegree[b] += 1
    layer = [v for v in range(1, n + 1) if indegree[v] == 0]
    semesters = taken = 0
    while layer:
        semesters += 1
        taken += len(layer)
        nxt = []
        for v in layer:
            for w in successors[v]:
                indegree[w] -= 1
                if indegree[w] == 0:
                    nxt.append(w)
        layer = nxt
    return semesters if taken == n else -1


def _semesters_brute(n: int, relations: list[list[int]]) -> int:
    done: set[int] = set()
    semesters = 0
    while len(done) < n:
        can_take = {v for v in range(1, n + 1) if v not in done and all(a in done for a, b in relations if b == v)}
        if not can_take:
            return -1
        done |= can_take
        semesters += 1
    return semesters


PARALLEL_COURSES = ProblemSource(
    title="Parallel Courses",
    statement="""
There are `n` courses labelled `1` to `n`. `relations[i] = [prev, next]` means `prev` must be completed in an earlier semester than `next`. In one
semester you may take any number of courses whose prerequisites were all completed in earlier semesters.

Return the minimum number of semesters needed to take every course, or `-1` if it's impossible.
""",
    constraints="""
- `1 <= n <= 5000`
- `1 <= relations.length <= 5000`, pairs distinct, `prev != next`
""",
    signature=function("minimumSemesters", [("n", "int"), ("relations", "int[][]")], "int"),
    reference=_minimum_semesters,
    brute=_semesters_brute,
    brute_input_limit=600,
    examples=[Example([3, [[1, 3], [2, 3]]], "Courses 1 and 2 first, then 3."), Example([3, [[1, 2], [2, 3], [3, 1]]], "A cycle.")],
    edge_cases=[[2, [[1, 2]]], [4, [[1, 2], [2, 3], [3, 4]]], [3, [[1, 2]]]],
    generator=lambda rng: [
        (n := pick_n(rng, 2, 10, big=3000)),
        [[a + 1, b + 1] for a, b in _random_dag_pairs(rng, n, rng.randint(1, 2 * n), 0.3)],
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Sort Items by Groups Respecting Dependencies


def _sort_items(n: int, m: int, group: list[int], beforeItems: list[list[int]]) -> list[int]:
    group = [g if g != -1 else m + i for i, g in enumerate(group)]  # lone items get their own group
    group_ids = sorted(set(group))
    item_edges, group_edges = [], set()
    for item, befores in enumerate(beforeItems):
        for prior in befores:
            if group[prior] == group[item]:
                item_edges.append((prior, item))
            else:
                group_edges.add((group[prior], group[item]))
    group_order = _kahn(group_ids, sorted(group_edges))
    item_order = _kahn(list(range(n)), item_edges)
    if not group_order or not item_order:
        return []
    members: dict[int, list[int]] = {g: [] for g in group_ids}
    for item in item_order:
        members[group[item]].append(item)
    return [item for g in group_order for item in members[g]]


def _sort_items_brute(n: int, m: int, group: list[int], beforeItems: list[list[int]]) -> list[int]:
    if n > 7:
        return NotImplemented
    edges = [(prior, item) for item in range(n) for prior in beforeItems[item]]
    for order in itertools.permutations(range(n)):
        if not _respects(list(order), edges):
            continue
        first: dict[int, int] = {}
        last: dict[int, int] = {}
        for pos, item in enumerate(order):
            if group[item] != -1:
                first.setdefault(group[item], pos)
                last[group[item]] = pos
        if all(last[g] - first[g] + 1 == group.count(g) for g in first):  # each group occupies one contiguous block
            return list(order)
    return []


def _sort_items_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 7, big=300)
    m = rng.randint(1, n)
    group = [rng.randint(-1, m - 1) for _ in range(n)]
    before: list[list[int]] = [[] for _ in range(n)]
    for a, b in _random_dag_pairs(rng, n, rng.randint(0, 2 * n), 0.2):
        before[b].append(a)
    return [n, m, group, [sorted(set(x)) for x in before]]


SORT_ITEMS_GROUPS = ProblemSource(
    title="Sort Items by Groups Respecting Dependencies",
    statement="""
There are `n` items, each in at most one of `m` groups: `group[i]` is item `i`'s group, or `-1` if it belongs to none. `beforeItems[i]` lists the
items that must appear before item `i`.

Return an ordering of all `n` items in which items of the same group are next to each other and every `beforeItems` constraint holds. Return an
empty list if no such ordering exists. Any valid ordering is accepted.
""",
    constraints="""
- `1 <= m <= n <= 3 * 10^4`
- `-1 <= group[i] <= m - 1`
- `beforeItems[i]` holds distinct items other than `i`
""",
    signature=function(
        "sortItems", [("n", "int"), ("m", "int"), ("group", "int[]"), ("beforeItems", "int[][]")], "int[]"
    ),
    reference=_sort_items,
    brute=_sort_items_brute,
    compare="checker",
    checker="sort_items_groups",
    examples=[
        Example([8, 2, [-1, -1, 1, 0, 0, 1, 0, -1], [[], [6], [5], [6], [3, 6], [], [], []]], "e.g. [6,3,4,1,5,2,0,7]."),
        Example([8, 2, [-1, -1, 1, 0, 0, 1, 0, -1], [[], [6], [5], [6], [3], [], [4], []]], "4 must precede 6 and 6 must precede 4 via 3."),
    ],
    edge_cases=[[1, 1, [-1], [[]]], [2, 1, [0, 0], [[1], [0]]], [3, 1, [0, -1, 0], [[], [0], [1]]]],
    generator=_sort_items_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Collect Coins in a Tree


def _collect_the_coins(coins: list[int], edges: list[list[int]]) -> int:
    n = len(coins)
    adjacent: list[set[int]] = [set() for _ in range(n)]
    for a, b in edges:
        adjacent[a].add(b)
        adjacent[b].add(a)
    alive = n
    leaves = deque(v for v in range(n) if len(adjacent[v]) == 1 and coins[v] == 0)
    while leaves:  # strip coinless leaves until every leaf holds a coin
        v = leaves.popleft()
        if not adjacent[v]:
            continue
        (u,) = adjacent[v]
        adjacent[u].discard(v)
        adjacent[v].clear()
        alive -= 1
        if len(adjacent[u]) == 1 and coins[u] == 0:
            leaves.append(u)
    for _ in range(2):  # coins within distance 2 are collected without visiting their leaves
        layer = [v for v in range(n) if len(adjacent[v]) == 1]
        for v in layer:
            if adjacent[v]:
                (u,) = adjacent[v]
                adjacent[u].discard(v)
                adjacent[v].clear()
                alive -= 1
    return max(0, 2 * (alive - 1))


def _collect_coins_brute(coins: list[int], edges: list[list[int]]) -> int:
    n = len(coins)
    coin_ids = [v for v in range(n) if coins[v]]
    if n > 12:
        return NotImplemented
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    dist = [[n] * n for _ in range(n)]
    for s in range(n):
        dist[s][s] = 0
        queue = deque([s])
        while queue:
            v = queue.popleft()
            for w in adjacent[v]:
                if dist[s][w] == n:
                    dist[s][w] = dist[s][v] + 1
                    queue.append(w)
    reach = [sum(1 << i for i, c in enumerate(coin_ids) if dist[v][c] <= 2) for v in range(n)]
    full = (1 << len(coin_ids)) - 1
    best = None
    for start in range(n):
        seen = {(start, reach[start])}
        queue = deque([(start, reach[start], 0)])
        while queue:
            v, mask, steps = queue.popleft()
            if v == start and mask == full:
                best = steps if best is None else min(best, steps)
                break
            for w in adjacent[v]:
                state = (w, mask | reach[w])
                if state not in seen:
                    seen.add(state)
                    queue.append((w, state[1], steps + 1))
    return best


def _collect_coins_gen(rng: random.Random) -> list:
    n = rng.choice([rng.randint(6, 12), rng.randint(13, 60), rng.randint(200, 3000)])  # the brute covers n <= 12
    density = rng.choice([0.1, 0.3, 0.5])
    labels = sample(rng, range(n), n)
    spread = rng.choice([1, 2, n])  # small spread = long, path-like trees, so coins are far apart
    edges = [[labels[rng.randint(max(0, i - spread), i - 1)], labels[i]] for i in range(1, n)]
    return [[int(rng.random() < density) for _ in range(n)], edges]


COLLECT_COINS = ProblemSource(
    title="Collect Coins in a Tree",
    statement="""
An undirected tree has `n` nodes labelled `0` to `n - 1`, given by `edges`. `coins[i]` is `1` if node `i` holds a coin and `0` otherwise.

Pick any starting node. You may then repeatedly either move to an adjacent node, or collect **every** coin within distance `2` of your current
node. Return the minimum number of edge moves needed to collect all the coins and return to the starting node. (Traversing an edge twice counts
twice.)
""",
    constraints="""
- `1 <= n <= 3 * 10^4`
- `coins[i]` is `0` or `1`
- `edges` describes a valid tree
""",
    signature=function("collectTheCoins", [("coins", "int[]"), ("edges", "int[][]")], "int"),
    reference=_collect_the_coins,
    brute=_collect_coins_brute,
    examples=[
        Example([[1, 0, 0, 0, 0, 1], [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]]], "Start at 2: collect coin 0, walk to 3, collect coin 5, walk back."),
        Example([[0, 0, 0, 1, 1, 0, 0, 1], [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [5, 6], [5, 7]]]),
    ],
    edge_cases=[[[1], []], [[0, 0], [[0, 1]]], [[1, 1, 1, 1, 1], [[0, 1], [1, 2], [2, 3], [3, 4]]], [[1, 0, 0, 0, 0, 0, 0, 1], [[i, i + 1] for i in range(7)]]],
    generator=_collect_coins_gen,
    random_count=14,
)


PROBLEMS = [
    ALIEN_DICTIONARY,
    COURSE_SCHEDULE,
    COMPILATION_ORDER,
    VERIFY_ALIEN,
    COURSE_SCHEDULE_II,
    FIND_RECIPES,
    BUILD_MATRIX,
    LONGEST_DIFFERENT_PATH,
    PARALLEL_COURSES_III,
    PARALLEL_COURSES,
    SORT_ITEMS_GROUPS,
    COLLECT_COINS,
]
