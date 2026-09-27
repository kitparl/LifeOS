"""Pattern 28: Math and Geometry (part 1 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import math
import random
from collections import Counter, deque
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, function, pick_n, sample

PATTERN_NUMBER = 28
_MOD = 10**9 + 7


def _points(rng: random.Random, n: int, lo: int, hi: int, distinct: bool = True) -> list[list[int]]:
    if distinct:
        cells = sample(rng, [(x, y) for x in range(lo, hi + 1) for y in range(lo, hi + 1)], n) if (hi - lo + 1) ** 2 <= 4000 else list({(rng.randint(lo, hi), rng.randint(lo, hi)) for _ in range(n)})
        return [list(c) for c in cells]
    return [[rng.randint(lo, hi), rng.randint(lo, hi)] for _ in range(n)]


def _cross(o: list[int], a: list[int], b: list[int]) -> int:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


# ---------------------------------------------------------------- Minimum Area Rectangle


def _min_area_rect(points: list[list[int]]) -> int:
    present = {tuple(p) for p in points}
    best = 0
    for (x1, y1), (x2, y2) in itertools.combinations(points, 2):  # treat each pair as a diagonal
        if x1 != x2 and y1 != y2 and (x1, y2) in present and (x2, y1) in present:
            area = abs(x1 - x2) * abs(y1 - y2)
            best = area if not best else min(best, area)
    return best


def _min_rect_brute(points: list[list[int]]) -> int:
    present = {tuple(p) for p in points}
    xs, ys = sorted({x for x, _ in points}), sorted({y for _, y in points})
    best = 0
    for x1, x2 in itertools.combinations(xs, 2):
        for y1, y2 in itertools.combinations(ys, 2):
            if {(x1, y1), (x1, y2), (x2, y1), (x2, y2)} <= present:
                area = (x2 - x1) * (y2 - y1)
                best = area if not best else min(best, area)
    return best


MIN_AREA_RECTANGLE = ProblemSource(
    title="Minimum Area Rectangle",
    statement="""
Given distinct points in the plane, return the minimum area of a rectangle with sides parallel to the axes whose four corners are all among the
points, or `0` if no such rectangle exists.
""",
    constraints="""
- `1 <= points.length <= 500`
- `0 <= x, y <= 4 * 10^4`; all points distinct
""",
    signature=function("minAreaRect", [("points", "int[][]")], "int"),
    reference=_min_area_rect,
    brute=_min_rect_brute,
    brute_input_limit=3000,
    examples=[Example([[[1, 1], [1, 3], [3, 1], [3, 3], [2, 2]]]), Example([[[1, 1], [1, 3], [3, 1], [3, 3], [4, 1], [4, 3]]], "The 1 x 2 rectangle on x = 3..4.")],
    edge_cases=[[[[0, 0]]], [[[0, 0], [0, 1], [1, 0], [1, 1]]], [[[0, 0], [1, 1], [2, 2]]]],
    generator=lambda rng: [_points(rng, pick_n(rng, 1, 20, big=500), 0, rng.choice([4, 8, 4 * 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Area Rectangle With Point Constraints I


def _max_rectangle_area(points: list[list[int]]) -> int:
    present = {tuple(p) for p in points}
    best = -1
    for (x1, y1), (x2, y2) in itertools.combinations(points, 2):
        if x1 == x2 or y1 == y2 or (x1, y2) not in present or (x2, y1) not in present:
            continue
        lo_x, hi_x, lo_y, hi_y = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
        inside = sum(lo_x <= x <= hi_x and lo_y <= y <= hi_y for x, y in points)
        if inside == 4:
            best = max(best, (hi_x - lo_x) * (hi_y - lo_y))
    return best


def _max_rect_brute(points: list[list[int]]) -> int:
    best = -1
    for quad in itertools.combinations(points, 4):
        xs, ys = sorted({x for x, _ in quad}), sorted({y for _, y in quad})
        if len(xs) != 2 or len(ys) != 2 or {tuple(p) for p in quad} != {(x, y) for x in xs for y in ys}:
            continue
        others = [p for p in points if list(p) not in [list(q) for q in quad]]
        if all(not (xs[0] <= x <= xs[1] and ys[0] <= y <= ys[1]) for x, y in others):
            best = max(best, (xs[1] - xs[0]) * (ys[1] - ys[0]))
    return best


MAX_RECTANGLE_CONSTRAINTS = ProblemSource(
    title="Maximum Area Rectangle With Point Constraints I",
    statement="""
Choose four of the given points as the corners of a rectangle with sides parallel to the axes, such that **no other point** lies inside the
rectangle or on its border. Return the largest possible area, or `-1` if no such rectangle exists.
""",
    constraints="""
- `1 <= points.length <= 10`
- `0 <= x, y <= 100`; all points distinct
""",
    signature=function("maxRectangleArea", [("points", "int[][]")], "int"),
    reference=_max_rectangle_area,
    brute=_max_rect_brute,
    examples=[Example([[[1, 1], [1, 3], [3, 1], [3, 3]]]), Example([[[1, 1], [1, 3], [3, 1], [3, 3], [2, 2]]], "[2,2] lies inside the only rectangle."), Example([[[1, 1], [1, 3], [3, 1], [3, 3], [1, 2], [3, 2]]])],
    edge_cases=[[[[0, 0]]], [[[0, 0], [0, 100], [100, 0], [100, 100]]]],
    generator=lambda rng: [_points(rng, rng.randint(1, 10), 0, rng.choice([3, 5, 100]))],
    random_count=10,
)


# ---------------------------------------------------------------- Reverse Integer


def _reverse(x: int) -> int:
    sign = -1 if x < 0 else 1
    result = 0
    x = abs(x)
    while x:
        result = result * 10 + x % 10
        x //= 10
    result *= sign
    return result if -(2**31) <= result <= 2**31 - 1 else 0


REVERSE_INTEGER = ProblemSource(
    title="Reverse Integer",
    statement="""
Reverse the decimal digits of the signed 32-bit integer `x` (keeping its sign). If the result falls outside the signed 32-bit range
`[-2^31, 2^31 - 1]`, return `0`. Assume you can't store 64-bit integers.
""",
    constraints="""
- `-2^31 <= x <= 2^31 - 1`
""",
    signature=function("reverse", [("x", "int")], "int"),
    reference=_reverse,
    brute=lambda x: (lambda r: r if -(2**31) <= r <= 2**31 - 1 else 0)(int(str(abs(x))[::-1]) * (-1 if x < 0 else 1)),
    examples=[Example([123]), Example([-123]), Example([120], "Trailing zeros disappear.")],
    edge_cases=[[0], [1534236469], [-2147483648], [2147483641], [-2147483412]],
    generator=lambda rng: [rng.randint(-(2**31), 2**31 - 1) if rng.random() < 0.6 else rng.randint(-99999, 99999)],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Number of Lines to Cover Points


def _minimum_lines(points: list[list[int]]) -> int:
    n = len(points)

    def collinear(a: int, b: int, c: int) -> bool:
        return _cross(points[a], points[b], points[c]) == 0

    lines = []  # every line through two points, as a bitmask of the points on it
    for a, b in itertools.combinations(range(n), 2):
        lines.append(sum(1 << c for c in range(n) if collinear(a, b, c)))

    @cache
    def best(mask: int) -> int:
        if mask == (1 << n) - 1:
            return 0
        first = next(i for i in range(n) if not mask >> i & 1)
        options = [1 + best(mask | 1 << first)]  # a line through this point alone
        options += [1 + best(mask | line) for line in lines if line >> first & 1]
        return min(options)

    return best(0)


def _lines_brute(points: list[list[int]]) -> int:
    n = len(points)
    if n > 8:
        return NotImplemented

    def covered_by(k: int, remaining: tuple[int, ...]) -> bool:
        if not remaining:
            return True
        if k == 0:
            return False
        first, rest = remaining[0], remaining[1:]
        if not rest:
            return True
        for other in rest:  # the line through `first` must pass through some other point, or cover `first` alone
            left = tuple(i for i in rest if _cross(points[first], points[other], points[i]) != 0)
            if covered_by(k - 1, left):
                return True
        return covered_by(k - 1, rest)

    return next(k for k in range(1, n + 1) if covered_by(k, tuple(range(n))))


LINES_COVER_POINTS = ProblemSource(
    title="Minimum Number of Lines to Cover Points",
    statement="""
Return the minimum number of straight lines needed so that every one of the given distinct points lies on at least one line.
""",
    constraints="""
- `1 <= points.length <= 10`
- `-100 <= x, y <= 100`; all points distinct
""",
    signature=function("minimumLines", [("points", "int[][]")], "int"),
    reference=_minimum_lines,
    brute=_lines_brute,
    examples=[Example([[[0, 1], [2, 3], [4, 5], [4, 3]]], "One line through the first three, one through [4,3]."), Example([[[0, 2], [-2, -2], [1, 4]]])],
    edge_cases=[[[[0, 0]]], [[[0, 0], [5, 5]]], [[[0, 0], [1, 1], [2, 2], [0, 1], [0, 2]]]],
    generator=lambda rng: [_points(rng, rng.randint(1, 10), -rng.choice([2, 100]), rng.choice([2, 100]))],
    random_count=10,
)


# ---------------------------------------------------------------- Minimize Manhattan Distances


def _minimum_distance(points: list[list[int]]) -> int:
    sums = sorted((x + y, i) for i, (x, y) in enumerate(points))
    diffs = sorted((x - y, i) for i, (x, y) in enumerate(points))

    def max_without(skip: int) -> int:
        s = [v for v, i in (sums[:2] + sums[-2:]) if i != skip]
        d = [v for v, i in (diffs[:2] + diffs[-2:]) if i != skip]
        return max(max(s) - min(s), max(d) - min(d))

    candidates = {sums[0][1], sums[-1][1], diffs[0][1], diffs[-1][1]}  # only an extreme point can matter
    return min(max_without(i) for i in candidates)


def _manhattan_brute(points: list[list[int]]) -> int:
    n = len(points)
    if n > 60:
        return NotImplemented
    best = None
    for skip in range(n):
        rest = [p for i, p in enumerate(points) if i != skip]
        worst = max((abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in itertools.combinations(rest, 2)), default=0)
        best = worst if best is None else min(best, worst)
    return best


MINIMIZE_MANHATTAN = ProblemSource(
    title="Minimize Manhattan Distances",
    statement="""
Remove exactly one point from `points`, then take the maximum Manhattan distance (`|x1 - x2| + |y1 - y2|`) between any two remaining points.
Return the smallest possible value of that maximum.
""",
    constraints="""
- `3 <= points.length <= 10^5`
- `1 <= x, y <= 10^8`
""",
    signature=function("minimumDistance", [("points", "int[][]")], "int"),
    reference=_minimum_distance,
    brute=_manhattan_brute,
    brute_input_limit=3000,
    examples=[Example([[[3, 10], [5, 15], [10, 2], [4, 4]]], "Removing [10,2] leaves a maximum of 12."), Example([[[1, 1], [1, 1], [1, 1]]])],
    edge_cases=[[[[1, 1], [100000000, 100000000], [1, 100000000]]], [[[5, 5], [5, 5], [6, 6]]]],
    generator=lambda rng: [_points(rng, pick_n(rng, 3, 15, big=5000), 1, rng.choice([10, 10**8]), distinct=False)],
    random_count=8,
)


# ---------------------------------------------------------------- Convex Polygon


def _is_convex(points: list[list[int]]) -> bool:
    n = len(points)
    sign = 0
    for i in range(n):
        turn = _cross(points[i], points[(i + 1) % n], points[(i + 2) % n])
        if turn:
            if sign and (turn > 0) != (sign > 0):
                return False
            sign = turn
    return True


def _convex_brute(points: list[list[int]]) -> bool:
    """Convex iff, for every edge, no vertex lies strictly on the opposite side from any other vertex."""
    n = len(points)
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        sides = {(_cross(a, b, p) > 0) - (_cross(a, b, p) < 0) for p in points} - {0}
        if len(sides) > 1:
            return False
    return True


def _polygon_gen(rng: random.Random) -> list:
    n = rng.randint(3, rng.choice([6, 40]))
    angles = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
    radius = rng.randint(5, 1000)
    pts = []
    for a in angles:
        p = [round(radius * math.cos(a)), round(radius * math.sin(a))]
        if p not in pts:
            pts.append(p)
    while len(pts) < 3:
        pts.append([rng.randint(-1000, 1000), rng.randint(-1000, 1000)])
    if rng.random() < 0.4:  # dent it
        i = rng.randrange(len(pts))
        pts[i] = [pts[i][0] // 3, pts[i][1] // 3]
    return [pts]


CONVEX_POLYGON = ProblemSource(
    title="Convex Polygon",
    statement="""
`points` lists the vertices of a simple polygon (its edges don't cross each other) in order, either clockwise or counter-clockwise. Return `true`
if the polygon is convex. Consecutive collinear vertices are allowed.
""",
    constraints="""
- `3 <= points.length <= 10^4`
- `-10^4 <= x, y <= 10^4`; the polygon is simple
""",
    signature=function("isConvex", [("points", "int[][]")], "bool"),
    reference=_is_convex,
    brute=_convex_brute,
    examples=[Example([[[0, 0], [0, 5], [5, 5], [5, 0]]]), Example([[[0, 0], [0, 10], [10, 10], [10, 0], [5, 5]]], "[5,5] dents the square inward.")],
    edge_cases=[[[[0, 0], [1, 0], [0, 1]]], [[[0, 0], [1, 0], [2, 0], [2, 2], [0, 2]]]],
    generator=_polygon_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Check If It Is a Straight Line


def _check_straight_line(coordinates: list[list[int]]) -> bool:
    a, b = coordinates[0], coordinates[1]
    return all(_cross(a, b, c) == 0 for c in coordinates[2:])


def _straight_brute(coordinates: list[list[int]]) -> bool:
    """Every point's direction from the first point, reduced and sign-normalised, must be the same."""
    x0, y0 = coordinates[0]
    directions = set()
    for x, y in coordinates[1:]:
        dx, dy = x - x0, y - y0
        g = math.gcd(dx, dy)
        dx, dy = dx // g, dy // g
        directions.add((dx, dy) if (dx, dy) > (0, 0) else (-dx, -dy))
    return len(directions) == 1


def _line_gen(rng: random.Random) -> list:
    dx, dy = rng.randint(-5, 5), rng.randint(-5, 5)
    if dx == dy == 0:
        dx = 1
    starts = sample(rng, range(-100, 100), rng.randint(2, 12))
    pts = [[3 * dx * t, 3 * dy * t] for t in starts]
    if rng.random() < 0.5:
        pts[rng.randrange(len(pts))][1] += 1
    return [pts]


STRAIGHT_LINE = ProblemSource(
    title="Check If It Is a Straight Line",
    statement="""
`coordinates` holds distinct points. Return `true` if all of them lie on one straight line.
""",
    constraints="""
- `2 <= coordinates.length <= 1000`
- `-10^4 <= x, y <= 10^4`; all points distinct
""",
    signature=function("checkStraightLine", [("coordinates", "int[][]")], "bool"),
    reference=_check_straight_line,
    brute=_straight_brute,
    examples=[Example([[[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]]]), Example([[[1, 1], [2, 2], [3, 4], [4, 5], [5, 6], [7, 7]]])],
    edge_cases=[[[[0, 0], [5, 7]]], [[[1, 0], [1, 5], [1, -3]]], [[[0, 0], [0, 1], [1, 1]]]],
    generator=_line_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Cuts to Divide a Circle


def _number_of_cuts(n: int) -> int:
    if n == 1:
        return 0
    return n // 2 if n % 2 == 0 else n


CIRCLE_CUTS = ProblemSource(
    title="Minimum Cuts to Divide a Circle",
    statement="""
A *valid cut* on a circle is either a straight segment through the centre touching the edge at two points, or a segment from the centre to one
point on the edge. Return the minimum number of valid cuts needed to divide the circle into `n` equal slices.
""",
    constraints="""
- `1 <= n <= 100`
""",
    signature=function("numberOfCuts", [("n", "int")], "int"),
    reference=_number_of_cuts,
    brute=lambda n: 0 if n == 1 else min(c for c in range(1, n + 1) if (n % 2 == 0 and 2 * c == n) or c == n),
    examples=[Example([4], "Two diameters."), Example([3], "Three radii.")],
    edge_cases=[[1], [2], [100], [99]],
    generator=lambda rng: [rng.randint(1, 100)],
    random_count=6,
)


# ---------------------------------------------------------------- Valid Square


def _valid_square(p1: list[int], p2: list[int], p3: list[int], p4: list[int]) -> bool:
    d = sorted((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 for a, b in itertools.combinations([p1, p2, p3, p4], 2))
    return d[0] > 0 and d[0] == d[3] and d[4] == d[5] == 2 * d[0]


def _square_brute(p1: list[int], p2: list[int], p3: list[int], p4: list[int]) -> bool:
    for a, b, c, d in itertools.permutations([p1, p2, p3, p4]):  # try every vertex order a-b-c-d
        side = (b[0] - a[0], b[1] - a[1])
        if side == (0, 0):
            continue
        turned = (-side[1], side[0])
        if [b[0] + turned[0], b[1] + turned[1]] == c and [a[0] + turned[0], a[1] + turned[1]] == d:
            return True
    return False


def _square_gen(rng: random.Random) -> list:
    x, y, dx, dy = (rng.randint(-50, 50) for _ in range(4))
    pts = [[x, y], [x + dx, y + dy], [x + dx - dy, y + dy + dx], [x - dy, y + dx]]
    if rng.random() < 0.4:
        pts[rng.randrange(4)][rng.randrange(2)] += rng.choice([-1, 1])
    rng.shuffle(pts)
    return pts


VALID_SQUARE = ProblemSource(
    title="Valid Square",
    statement="""
Given four points in any order, return `true` if they are the vertices of a square (four equal positive sides and four right angles; the
square may be rotated).
""",
    constraints="""
- `-10^4 <= x, y <= 10^4`
""",
    signature=function("validSquare", [("p1", "int[]"), ("p2", "int[]"), ("p3", "int[]"), ("p4", "int[]")], "bool"),
    reference=_valid_square,
    brute=_square_brute,
    examples=[Example([[0, 0], [1, 1], [1, 0], [0, 1]]), Example([[0, 0], [1, 1], [1, 0], [0, 12]]), Example([[1, 0], [-1, 0], [0, 1], [0, -1]], "A square rotated by 45 degrees.")],
    edge_cases=[[[0, 0], [0, 0], [0, 0], [0, 0]], [[0, 0], [2, 0], [2, 1], [0, 1]], [[0, 0], [1, 1], [0, 0], [1, 1]]],
    generator=_square_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Rectangle Overlap


def _is_rectangle_overlap(rec1: list[int], rec2: list[int]) -> bool:
    return min(rec1[2], rec2[2]) > max(rec1[0], rec2[0]) and min(rec1[3], rec2[3]) > max(rec1[1], rec2[1])


def _overlap_brute(rec1: list[int], rec2: list[int]) -> bool:
    if rec1[2] - rec1[0] > 60 or rec1[3] - rec1[1] > 60:
        return NotImplemented
    cells = {(x, y) for x in range(rec1[0], rec1[2]) for y in range(rec1[1], rec1[3])}  # unit squares covered
    return any(rec2[0] <= x < rec2[2] and rec2[1] <= y < rec2[3] for x, y in cells)


def _rect(rng: random.Random, hi: int) -> list[int]:
    x1, y1 = rng.randint(-hi, hi - 1), rng.randint(-hi, hi - 1)
    return [x1, y1, rng.randint(x1 + 1, min(hi, x1 + rng.choice([5, 40]))), rng.randint(y1 + 1, min(hi, y1 + rng.choice([5, 40])))]


RECTANGLE_OVERLAP = ProblemSource(
    title="Rectangle Overlap",
    statement="""
An axis-aligned rectangle is given as `[x1, y1, x2, y2]` (bottom-left and top-right corners, with positive width and height). Return `true` if
the two rectangles overlap with **positive area**; touching edges or corners don't count.
""",
    constraints="""
- `-10^9 <= coordinates <= 10^9`; each rectangle has positive area
""",
    signature=function("isRectangleOverlap", [("rec1", "int[]"), ("rec2", "int[]")], "bool"),
    reference=_is_rectangle_overlap,
    brute=_overlap_brute,
    examples=[Example([[0, 0, 2, 2], [1, 1, 3, 3]]), Example([[0, 0, 1, 1], [1, 0, 2, 1]], "They only share an edge."), Example([[0, 0, 1, 1], [2, 2, 3, 3]])],
    edge_cases=[[[0, 0, 1, 1], [0, 0, 1, 1]], [[0, 0, 10, 10], [2, 2, 3, 3]], [[-1000000000, -1000000000, 1000000000, 1000000000], [0, 0, 1, 1]]],
    generator=lambda rng: [_rect(rng, (hi := rng.choice([6, 30]))), _rect(rng, hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Time Visiting All Points


def _min_time_to_visit_all_points(points: list[list[int]]) -> int:
    return sum(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for a, b in itertools.pairwise(points))


def _visit_brute(points: list[list[int]]) -> int:
    total = 0
    for (x, y), (tx, ty) in itertools.pairwise(points):
        while (x, y) != (tx, ty):  # walk one second at a time, diagonally when both axes still differ
            x += (tx > x) - (tx < x)
            y += (ty > y) - (ty < y)
            total += 1
    return total


VISIT_ALL_POINTS = ProblemSource(
    title="Minimum Time Visiting All Points",
    statement="""
Visit the points in the given order. In one second you can move one unit vertically, one unit horizontally, or one unit diagonally (both at
once). Return the minimum number of seconds.
""",
    constraints="""
- `1 <= points.length <= 100`
- `-1000 <= x, y <= 1000`
""",
    signature=function("minTimeToVisitAllPoints", [("points", "int[][]")], "int"),
    reference=_min_time_to_visit_all_points,
    brute=_visit_brute,
    examples=[Example([[[1, 1], [3, 4], [-1, 0]]]), Example([[[3, 2], [-2, 2]]])],
    edge_cases=[[[[0, 0]]], [[[0, 0], [0, 0]]], [[[-1000, -1000], [1000, 1000]]]],
    generator=lambda rng: [_points(rng, rng.randint(1, 20), -rng.choice([5, 1000]), rng.choice([5, 1000]), distinct=False)],
    random_count=8,
)


# ---------------------------------------------------------------- Rectangle Area


def _compute_area(ax1: int, ay1: int, ax2: int, ay2: int, bx1: int, by1: int, bx2: int, by2: int) -> int:
    overlap = max(0, min(ax2, bx2) - max(ax1, bx1)) * max(0, min(ay2, by2) - max(ay1, by1))
    return (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - overlap


def _area_brute(ax1: int, ay1: int, ax2: int, ay2: int, bx1: int, by1: int, bx2: int, by2: int) -> int:
    if max(ax2 - ax1, ay2 - ay1, bx2 - bx1, by2 - by1) > 40:
        return NotImplemented
    cells = {(x, y) for x in range(ax1, ax2) for y in range(ay1, ay2)} | {(x, y) for x in range(bx1, bx2) for y in range(by1, by2)}
    return len(cells)


def _area_gen(rng: random.Random) -> list:
    hi = rng.choice([10, 10**4])
    a = _rect(rng, hi)
    b = _rect(rng, hi)
    return [*a, *b]


RECTANGLE_AREA = ProblemSource(
    title="Rectangle Area",
    statement="""
Two axis-aligned rectangles are given by their bottom-left and top-right corners: `(ax1, ay1)-(ax2, ay2)` and `(bx1, by1)-(bx2, by2)`. Return the
total area covered by the two rectangles (overlapping area is counted once).
""",
    constraints="""
- `-10^4 <= all coordinates <= 10^4`
- `ax1 <= ax2`, `ay1 <= ay2`, `bx1 <= bx2`, `by1 <= by2`
""",
    signature=function("computeArea", [("ax1", "int"), ("ay1", "int"), ("ax2", "int"), ("ay2", "int"), ("bx1", "int"), ("by1", "int"), ("bx2", "int"), ("by2", "int")], "int"),
    reference=_compute_area,
    brute=_area_brute,
    examples=[Example([-3, 0, 3, 4, 0, -1, 9, 2], "24 + 27 - 6 = 45."), Example([-2, -2, 2, 2, -2, -2, 2, 2])],
    edge_cases=[[0, 0, 0, 0, -1, -1, 1, 1], [0, 0, 1, 1, 1, 1, 2, 2]],
    generator=_area_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Queries on Number of Points Inside a Circle


def _count_points(points: list[list[int]], queries: list[list[int]]) -> list[int]:
    return [sum((x - cx) ** 2 + (y - cy) ** 2 <= r * r for x, y in points) for cx, cy, r in queries]


def _count_points_brute(points: list[list[int]], queries: list[list[int]]) -> list[int]:
    return [sum(math.dist((x, y), (cx, cy)) <= r + 1e-9 for x, y in points) for cx, cy, r in queries]


POINTS_IN_CIRCLE = ProblemSource(
    title="Queries on Number of Points Inside a Circle",
    statement="""
For each query `[cx, cy, r]`, count the points of `points` that lie inside the circle of radius `r` centred at `(cx, cy)`; points exactly on the
circle count as inside. Return the counts.
""",
    constraints="""
- `1 <= points.length, queries.length <= 500`
- `0 <= coordinates <= 500`, `1 <= r <= 500`
""",
    signature=function("countPoints", [("points", "int[][]"), ("queries", "int[][]")], "int[]"),
    reference=_count_points,
    brute=_count_points_brute,
    examples=[Example([[[1, 3], [3, 3], [5, 3], [2, 2]], [[2, 3, 1], [4, 3, 1], [1, 1, 2]]]), Example([[[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], [[1, 2, 2], [2, 2, 2], [4, 3, 2], [4, 3, 3]]])],
    edge_cases=[[[[0, 0]], [[3, 4, 5]]], [[[0, 0]], [[3, 4, 4]]]],
    generator=lambda rng: [_points(rng, rng.randint(1, 30), 0, (hi := rng.choice([10, 500])), distinct=False), [[rng.randint(0, hi), rng.randint(0, hi), rng.randint(1, hi)] for _ in range(rng.randint(1, 20))]],
    random_count=8,
)


# ---------------------------------------------------------------- Max Points on a Line


def _max_points(points: list[list[int]]) -> int:
    best = 1
    for i, (x1, y1) in enumerate(points):
        slopes: Counter[tuple[int, int]] = Counter()
        for x2, y2 in points[i + 1 :]:
            dx, dy = x2 - x1, y2 - y1
            g = math.gcd(dx, dy)
            dx, dy = dx // g, dy // g
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            slopes[(dx, dy)] += 1
        best = max(best, 1 + max(slopes.values(), default=0))
    return best


def _max_points_brute(points: list[list[int]]) -> int:
    if len(points) < 3:
        return len(points)
    return max(sum(_cross(a, b, c) == 0 for c in points) for a, b in itertools.combinations(points, 2))


MAX_POINTS_LINE = ProblemSource(
    title="Max Points on a Line",
    statement="""
Given distinct points in the plane, return the maximum number of them that lie on one straight line.
""",
    constraints="""
- `1 <= points.length <= 300`
- `-10^4 <= x, y <= 10^4`; all points distinct
""",
    signature=function("maxPoints", [("points", "int[][]")], "int"),
    reference=_max_points,
    brute=_max_points_brute,
    brute_input_limit=1500,
    examples=[Example([[[1, 1], [2, 2], [3, 3]]]), Example([[[1, 1], [3, 2], [5, 3], [4, 1], [2, 3], [1, 4]]])],
    edge_cases=[[[[0, 0]]], [[[0, 0], [1, 1]]], [[[0, 0], [0, 1], [0, 2], [1, 0]]]],
    generator=lambda rng: [_points(rng, pick_n(rng, 1, 20, big=300), -rng.choice([4, 10**4]), rng.choice([4, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Number of Visible Points


def _visible_points(points: list[list[int]], angle: int, location: list[int]) -> int:
    here = sum(p == location for p in points)
    angles = sorted(math.degrees(math.atan2(y - location[1], x - location[0])) for x, y in points if [x, y] != location)
    doubled = angles + [a + 360 for a in angles]
    best = left = 0
    for right, a in enumerate(doubled):
        while a - doubled[left] > angle + 1e-9:
            left += 1
        best = max(best, right - left + 1)
    return here + min(best, len(angles))


def _visible_brute(points: list[list[int]], angle: int, location: list[int]) -> int:
    if len(points) > 80:
        return NotImplemented
    here = sum(p == location for p in points)
    angles = [math.degrees(math.atan2(y - location[1], x - location[0])) % 360 for x, y in points if [x, y] != location]
    best = 0
    for start in angles:  # an optimal view can always start exactly at some point
        best = max(best, sum((a - start) % 360 <= angle + 1e-9 or abs((a - start) % 360 - 360) <= 1e-9 for a in angles))
    return here + best


VISIBLE_POINTS = ProblemSource(
    title="Maximum Number of Visible Points",
    statement="""
You stand at `location` and can turn to face any direction; you see every point within an angle of `angle` degrees (inclusive at both edges)
around your facing direction. Points exactly at your location are always visible, and points never block each other. Return the maximum number of
points you can see at once.
""",
    constraints="""
- `1 <= points.length <= 10^5`
- `0 <= angle < 360`
- `0 <= coordinates <= 100`
""",
    signature=function("visiblePoints", [("points", "int[][]"), ("angle", "int"), ("location", "int[]")], "int"),
    reference=_visible_points,
    brute=_visible_brute,
    examples=[Example([[[2, 1], [2, 2], [3, 3]], 90, [1, 1]]), Example([[[2, 1], [2, 2], [3, 4], [1, 1]], 90, [1, 1]], "[1,1] is at your location."), Example([[[1, 0], [2, 1]], 13, [1, 1]])],
    edge_cases=[[[[1, 1]], 0, [1, 1]], [[[0, 0], [2, 2]], 0, [1, 1]], [[[0, 0], [2, 2]], 180, [1, 1]]],
    generator=lambda rng: [_points(rng, rng.randint(1, 30), 0, (hi := rng.choice([6, 100])), distinct=False), rng.choice([0, 45, 90, 180, rng.randint(0, 359)]), [rng.randint(0, hi), rng.randint(0, hi)]],
    random_count=10,
)


# ---------------------------------------------------------------- Detonate the Maximum Bombs


def _maximum_detonation(bombs: list[list[int]]) -> int:
    n = len(bombs)
    reaches = [[j for j in range(n) if j != i and (bombs[i][0] - bombs[j][0]) ** 2 + (bombs[i][1] - bombs[j][1]) ** 2 <= bombs[i][2] ** 2] for i in range(n)]
    best = 0
    for start in range(n):
        seen, queue = {start}, deque([start])
        while queue:
            for j in reaches[queue.popleft()]:
                if j not in seen:
                    seen.add(j)
                    queue.append(j)
        best = max(best, len(seen))
    return best


def _bombs_brute(bombs: list[list[int]]) -> int:
    n = len(bombs)
    best = 0
    for start in range(n):
        exploded = {start}
        changed = True
        while changed:  # fixpoint: keep adding bombs inside any exploded bomb's radius
            grown = {j for i in exploded for j in range(n) if math.dist(bombs[i][:2], bombs[j][:2]) <= bombs[i][2] + 1e-9}
            changed = not grown <= exploded
            exploded |= grown
        best = max(best, len(exploded))
    return best


DETONATE_BOMBS = ProblemSource(
    title="Detonate the Maximum Bombs",
    statement="""
`bombs[i] = [x, y, r]` is a bomb at `(x, y)` with blast radius `r`. When a bomb explodes it detonates every bomb whose centre is within distance
`r` (inclusive), which may trigger further explosions. You may detonate exactly one bomb by hand. Return the maximum number of bombs that can
end up exploding.
""",
    constraints="""
- `1 <= bombs.length <= 100`
- `1 <= x, y, r <= 10^5`
""",
    signature=function("maximumDetonation", [("bombs", "int[][]")], "int"),
    reference=_maximum_detonation,
    brute=_bombs_brute,
    examples=[Example([[[2, 1, 3], [6, 1, 4]]], "The second bomb reaches the first but not the other way round."), Example([[[1, 1, 5], [10, 10, 5]]]), Example([[[1, 2, 3], [2, 3, 1], [3, 4, 2], [4, 5, 3], [5, 6, 4]]])],
    edge_cases=[[[[1, 1, 1]]], [[[1, 1, 3], [4, 5, 5]]]],
    generator=lambda rng: [[[rng.randint(1, hi), rng.randint(1, hi), rng.randint(1, hi // 2)] for _ in range(rng.randint(1, rng.choice([8, 60])))] for hi in [rng.choice([20, 10**5])]],
    random_count=8,
)


# ---------------------------------------------------------------- Self Crossing


def _is_self_crossing(distance: list[int]) -> bool:
    d = distance
    for i in range(3, len(d)):
        if d[i] >= d[i - 2] and d[i - 1] <= d[i - 3]:
            return True  # crosses the segment three steps back
        if i >= 4 and d[i - 1] == d[i - 3] and d[i] + d[i - 4] >= d[i - 2]:
            return True  # meets the segment four steps back
        if i >= 5 and d[i - 2] >= d[i - 4] and d[i] + d[i - 4] >= d[i - 2] and d[i - 1] <= d[i - 3] and d[i - 1] + d[i - 5] >= d[i - 3]:
            return True  # crosses the segment five steps back
    return False


def _self_crossing_brute(distance: list[int]) -> bool:
    if len(distance) > 40 or max(distance) > 30:
        return NotImplemented
    x = y = 0
    visited = {(0, 0)}
    for k, step in enumerate(distance):
        dx, dy = ((0, 1), (-1, 0), (0, -1), (1, 0))[k % 4]
        for _ in range(step):
            x, y = x + dx, y + dy
            if (x, y) in visited:
                return True
            visited.add((x, y))
    return False


SELF_CROSSING = ProblemSource(
    title="Self Crossing",
    statement="""
Starting at `(0, 0)`, move `distance[0]` units north, then `distance[1]` west, `distance[2]` south, `distance[3]` east, and keep turning
counter-clockwise. Return `true` if the path ever crosses or touches itself.
""",
    constraints="""
- `1 <= distance.length <= 10^5`
- `1 <= distance[i] <= 10^5`
""",
    signature=function("isSelfCrossing", [("distance", "int[]")], "bool"),
    reference=_is_self_crossing,
    brute=_self_crossing_brute,
    examples=[Example([[2, 1, 1, 2]], "It crosses at (0, 1)."), Example([[1, 2, 3, 4]], "An outward spiral."), Example([[1, 1, 1, 2, 1]], "It returns to the origin.")],
    edge_cases=[[[1]], [[1, 1, 1, 1]], [[3, 3, 4, 2, 2]], [[1, 1, 2, 2, 1, 1]]],
    generator=lambda rng: [[rng.randint(1, rng.choice([3, 30])) for _ in range(rng.randint(1, 20))] if rng.random() < 0.6 else sorted(rng.randint(1, 30) for _ in range(rng.randint(1, 12)))],
    random_count=12,
)


# ---------------------------------------------------------------- Erect the Fence


def _outer_trees(trees: list[list[int]]) -> list[list[int]]:
    pts = sorted(map(tuple, trees))
    if len(pts) <= 2:
        return [list(p) for p in pts]

    def chain(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
        hull: list[tuple[int, int]] = []
        for p in points:
            while len(hull) >= 2 and _cross(list(hull[-2]), list(hull[-1]), list(p)) < 0:  # keep collinear points
                hull.pop()
            hull.append(p)
        return hull

    return [list(p) for p in sorted(set(chain(pts) + chain(pts[::-1])))]


def _fence_brute(trees: list[list[int]]) -> list[list[int]]:
    """A tree is on the fence if some line through it has every tree on one (closed) side."""
    pts = [tuple(t) for t in trees]
    if len(pts) <= 2:
        return [list(p) for p in pts]
    out = []
    for p in pts:
        on_hull = False
        for q in pts:
            if q == p:
                continue
            sides = {(_cross(list(p), list(q), list(r)) > 0) - (_cross(list(p), list(q), list(r)) < 0) for r in pts} - {0}
            if len(sides) <= 1:
                on_hull = True
                break
        if on_hull:
            out.append(list(p))
    return out


FENCE = ProblemSource(
    title="Erect the Fence",
    statement="""
`trees[i] = [x, y]` is the position of a tree (all positions distinct). Fence the whole garden with the shortest possible rope: the fence is the
convex hull of the trees. Return every tree lying **on** the fence (including trees in the middle of a straight fence segment), in any order.
""",
    constraints="""
- `1 <= trees.length <= 3000`
- `0 <= x, y <= 100`; all positions distinct
""",
    signature=function("outerTrees", [("trees", "int[][]")], "int[][]"),
    reference=_outer_trees,
    brute=_fence_brute,
    brute_input_limit=1500,
    compare="unordered",
    examples=[Example([[[1, 1], [2, 2], [2, 0], [2, 4], [3, 3], [4, 2]]], "Everything except [2,2]."), Example([[[4, 2], [2, 2], [4, 4], [2, 4]]]), Example([[[0, 0], [1, 1], [2, 2]]], "Collinear trees are all on the fence.")],
    edge_cases=[[[[5, 5]]], [[[0, 0], [3, 0]]], [[[0, 0], [2, 0], [1, 0], [1, 1]]]],
    generator=lambda rng: [_points(rng, pick_n(rng, 1, 20, big=500), 0, rng.choice([4, 10, 100]))],
    random_count=10,
)


# ---------------------------------------------------------------- Nth Magical Number


def _nth_magical_number(n: int, a: int, b: int) -> int:
    lcm = a * b // math.gcd(a, b)
    lo, hi = 1, n * min(a, b)
    while lo < hi:
        mid = (lo + hi) // 2
        if mid // a + mid // b - mid // lcm >= n:
            hi = mid
        else:
            lo = mid + 1
    return lo % _MOD


def _magical_brute(n: int, a: int, b: int) -> int:
    if n > 3000:
        return NotImplemented
    count, x = 0, 0
    while count < n:
        x += 1
        count += x % a == 0 or x % b == 0
    return x % _MOD


NTH_MAGICAL = ProblemSource(
    title="Nth Magical Number",
    statement="""
A positive integer is *magical* if it is divisible by `a` or by `b`. Return the `n`-th magical number, modulo `10^9 + 7`.
""",
    constraints="""
- `1 <= n <= 10^9`
- `2 <= a, b <= 4 * 10^4`
""",
    signature=function("nthMagicalNumber", [("n", "int"), ("a", "int"), ("b", "int")], "int"),
    reference=_nth_magical_number,
    brute=_magical_brute,
    examples=[Example([1, 2, 3]), Example([4, 2, 3], "2, 3, 4, 6."), Example([5, 2, 4])],
    edge_cases=[[1000000000, 40000, 40000], [3, 7, 7], [1000000000, 2, 3]],
    generator=lambda rng: [rng.randint(1, rng.choice([3000, 10**9])), rng.randint(2, rng.choice([10, 4 * 10**4])), rng.randint(2, rng.choice([10, 4 * 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Add Strings


def _add_strings(num1: str, num2: str) -> str:
    i, j, carry, out = len(num1) - 1, len(num2) - 1, 0, []
    while i >= 0 or j >= 0 or carry:
        total = carry + (int(num1[i]) if i >= 0 else 0) + (int(num2[j]) if j >= 0 else 0)
        out.append(str(total % 10))
        carry = total // 10
        i, j = i - 1, j - 1
    return "".join(reversed(out))


def _digits(rng: random.Random, n: int) -> str:
    return str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(n - 1)) if n > 1 else str(rng.randint(0, 9))


ADD_STRINGS = ProblemSource(
    title="Add Strings",
    statement="""
`num1` and `num2` are non-negative integers written as decimal strings (no leading zeros except for `"0"`). Return their sum as a string, without
converting the inputs to integers directly or using big-integer libraries.
""",
    constraints="""
- `1 <= num1.length, num2.length <= 10^4`
""",
    signature=function("addStrings", [("num1", "string"), ("num2", "string")], "string"),
    reference=_add_strings,
    brute=lambda num1, num2: str(int(num1) + int(num2)),
    examples=[Example(["11", "123"]), Example(["456", "77"]), Example(["0", "0"])],
    edge_cases=[["9", "1"], ["999999", "1"], ["1", "99999999999999999999"]],
    generator=lambda rng: [_digits(rng, rng.randint(1, rng.choice([5, 3000]))), _digits(rng, rng.randint(1, rng.choice([5, 3000])))],
    random_count=8,
)


# ---------------------------------------------------------------- Perfect Squares


def _num_squares(n: int) -> int:
    """Lagrange: every n is a sum of 4 squares; Legendre tells when 4 are needed."""
    if math.isqrt(n) ** 2 == n:
        return 1
    m = n
    while m % 4 == 0:
        m //= 4
    if m % 8 == 7:
        return 4
    if any(math.isqrt(n - i * i) ** 2 == n - i * i for i in range(1, math.isqrt(n) + 1)):
        return 2
    return 3


def _squares_brute(n: int) -> int:
    if n > 3000:
        return NotImplemented
    best = [0] + [n] * n
    for x in range(1, n + 1):
        best[x] = 1 + min(best[x - k * k] for k in range(1, math.isqrt(x) + 1))
    return best[n]


PERFECT_SQUARES = ProblemSource(
    title="Perfect Squares",
    statement="""
Return the least number of perfect squares (`1, 4, 9, 16, ...`) that add up to `n`.
""",
    constraints="""
- `1 <= n <= 10^4`
""",
    signature=function("numSquares", [("n", "int")], "int"),
    reference=_num_squares,
    brute=_squares_brute,
    examples=[Example([12], "4 + 4 + 4."), Example([13], "4 + 9.")],
    edge_cases=[[1], [7], [10000], [9999]],
    generator=lambda rng: [rng.randint(1, rng.choice([3000, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Palindrome Number


def _is_palindrome_number(x: int) -> bool:
    if x < 0 or (x % 10 == 0 and x):
        return False
    reverted = 0
    while x > reverted:  # reverse only half of the digits
        reverted = reverted * 10 + x % 10
        x //= 10
    return x in (reverted, reverted // 10)


def _palindrome_number_gen(rng: random.Random) -> list:
    half = str(rng.randint(1, 9999))  # mirrored result stays within int32
    roll = rng.random()
    if roll < 0.4:
        return [int(half + half[::-1][rng.randint(0, 1) :])]
    return [rng.randint(-(2**31), 2**31 - 1) if roll < 0.7 else rng.randint(0, 1000)]


PALINDROME_NUMBER = ProblemSource(
    title="Palindrome Number",
    statement="""
Return `true` if the integer `x` reads the same forwards and backwards in decimal (a minus sign breaks the symmetry). Try it without converting
`x` to a string.
""",
    constraints="""
- `-2^31 <= x <= 2^31 - 1`
""",
    signature=function("isPalindrome", [("x", "int")], "bool"),
    reference=_is_palindrome_number,
    brute=lambda x: str(x) == str(x)[::-1],
    examples=[Example([121]), Example([-121], "\"-121\" reversed is \"121-\"."), Example([10])],
    edge_cases=[[0], [7], [1000000001], [2147483647]],
    generator=_palindrome_number_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Fibonacci Number


def _fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _fib_brute(n: int) -> int:
    phi = (1 + math.sqrt(5)) / 2
    return round(phi**n / math.sqrt(5))


FIBONACCI = ProblemSource(
    title="Fibonacci Number",
    statement="""
The Fibonacci numbers are `F(0) = 0`, `F(1) = 1` and `F(n) = F(n - 1) + F(n - 2)`. Return `F(n)`.
""",
    constraints="""
- `0 <= n <= 30`
""",
    signature=function("fib", [("n", "int")], "int"),
    reference=_fib,
    brute=_fib_brute,
    examples=[Example([2]), Example([3]), Example([4])],
    edge_cases=[[0], [1], [30]],
    generator=lambda rng: [rng.randint(0, 30)],
    random_count=6,
)


# ---------------------------------------------------------------- Integer to English Words


_ONES = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["_", "_", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _number_to_words(num: int) -> str:
    if num == 0:
        return "Zero"

    def below_thousand(n: int) -> list[str]:
        words: list[str] = []
        if n >= 100:
            words += [_ONES[n // 100], "Hundred"]
            n %= 100
        if n >= 20:
            words.append(_TENS[n // 10])
            n %= 10
        if n:
            words.append(_ONES[n])
        return words

    words: list[str] = []
    for value, name in ((10**9, "Billion"), (10**6, "Million"), (10**3, "Thousand"), (1, "")):
        chunk, num = divmod(num, value)
        if chunk:
            words += below_thousand(chunk) + ([name] if name else [])
    return " ".join(words)


def _words_brute(num: int) -> str:
    def say(n: int) -> str:
        if n < 20:
            return _ONES[n]
        if n < 100:
            return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
        if n < 1000:
            return _ONES[n // 100] + " Hundred" + ("" if n % 100 == 0 else " " + say(n % 100))
        for value, name in ((10**9, "Billion"), (10**6, "Million"), (10**3, "Thousand")):
            if n >= value:
                return say(n // value) + " " + name + ("" if n % value == 0 else " " + say(n % value))
        raise AssertionError

    return say(num)


INTEGER_TO_WORDS = ProblemSource(
    title="Integer to English Words",
    statement="""
Write the non-negative integer `num` in English words, capitalising each word (for example `12345` is `"Twelve Thousand Three Hundred Forty
Five"`). Use single spaces, no `"and"` and no hyphens.
""",
    constraints="""
- `0 <= num <= 2^31 - 1`
""",
    signature=function("numberToWords", [("num", "int")], "string"),
    reference=_number_to_words,
    brute=_words_brute,
    examples=[Example([123]), Example([12345]), Example([1234567])],
    edge_cases=[[0], [100], [1000000], [1000010], [2147483647], [20], [19]],
    generator=lambda rng: [rng.choice([rng.randint(0, 2**31 - 1), rng.randint(0, 1000), rng.randint(0, 20) * 10 ** rng.randint(0, 8)])],
    random_count=10,
)


PROBLEMS = [
    MIN_AREA_RECTANGLE,
    MAX_RECTANGLE_CONSTRAINTS,
    REVERSE_INTEGER,
    LINES_COVER_POINTS,
    MINIMIZE_MANHATTAN,
    CONVEX_POLYGON,
    STRAIGHT_LINE,
    CIRCLE_CUTS,
    VALID_SQUARE,
    RECTANGLE_OVERLAP,
    VISIT_ALL_POINTS,
    RECTANGLE_AREA,
    POINTS_IN_CIRCLE,
    MAX_POINTS_LINE,
    VISIBLE_POINTS,
    DETONATE_BOMBS,
    SELF_CROSSING,
    FENCE,
    NTH_MAGICAL,
    ADD_STRINGS,
    PERFECT_SQUARES,
    PALINDROME_NUMBER,
    FIBONACCI,
    INTEGER_TO_WORDS,
]
