"""Pattern 17: Matrices. Original statements; outputs come from `reference`."""

from __future__ import annotations

import bisect
import heapq
import itertools
import random
from collections import deque
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, matrix, pick_n, sample

PATTERN_NUMBER = 17
_STEPS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def _dims(rng: random.Random, lo: int, hi: int, big: int) -> tuple[int, int]:
    return pick_n(rng, lo, hi, big=big), pick_n(rng, lo, hi, big=big)


def _binary_grid(rng: random.Random, m: int, n: int, density: float) -> list[list[int]]:
    return [[int(rng.random() < density) for _ in range(n)] for _ in range(m)]


def _sorted_grid(rng: random.Random, m: int, n: int, lo: int, hi: int, descending: bool) -> list[list[int]]:
    """Rows and columns both sorted (sorting rows, then columns, keeps the rows sorted)."""
    grid = [sorted(row, reverse=descending) for row in matrix(rng, m, n, lo, hi)]
    columns = [sorted(col, reverse=descending) for col in zip(*grid, strict=True)]
    return [list(row) for row in zip(*columns, strict=True)]


def _distinct_grid(rng: random.Random, m: int, n: int, population: range) -> list[list[int]]:
    values = sample(rng, population, m * n)
    return [values[i * n : (i + 1) * n] for i in range(m)]


# ---------------------------------------------------------------- Set Matrix Zeros


def _set_zeroes(matrix: list[list[int]]) -> None:
    rows = {i for i, row in enumerate(matrix) for v in row if v == 0}
    cols = {j for row in matrix for j, v in enumerate(row) if v == 0}
    for i, row in enumerate(matrix):
        for j in range(len(row)):
            if i in rows or j in cols:
                row[j] = 0


def _set_zeroes_brute(matrix: list[list[int]]) -> None:
    original = [row[:] for row in matrix]
    for i, row in enumerate(original):
        for j, v in enumerate(row):
            if v == 0:
                for k in range(len(row)):
                    matrix[i][k] = 0
                for k in range(len(original)):
                    matrix[k][j] = 0


SET_MATRIX_ZEROS = ProblemSource(
    title="Set Matrix Zeros",
    statement="""
For every cell of `matrix` that holds `0`, set its entire row and entire column to `0`. Do it **in place**; nothing is returned.

Try to use only `O(1)` extra space.
""",
    constraints="""
- `1 <= m, n <= 200`
- `-2^31 <= matrix[i][j] <= 2^31 - 1`
""",
    signature=function("setZeroes", [("matrix", "int[][]")], "void", mutates="matrix"),
    reference=_set_zeroes,
    brute=_set_zeroes_brute,
    examples=[Example([[[1, 1, 1], [1, 0, 1], [1, 1, 1]]], "The centre zero clears the middle row and column."), Example([[[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]]])],
    edge_cases=[[[[0]]], [[[5]]], [[[1, 0]]], [[[1], [0], [2]]]],
    generator=lambda rng: [[[0 if rng.random() < 0.08 else rng.randint(1, 99) for _ in range(n)] for _ in range(m)] for m, n in [_dims(rng, 1, 7, 200)]],
    random_count=8,
)


# ---------------------------------------------------------------- Rotate Image


def _rotate(matrix: list[list[int]]) -> None:
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()


def _rotate_brute(matrix: list[list[int]]) -> None:
    rotated = [list(row) for row in zip(*matrix[::-1], strict=True)]
    matrix[:] = rotated


ROTATE_IMAGE = ProblemSource(
    title="Rotate Image",
    statement="""
Rotate the `n x n` matrix by 90 degrees clockwise **in place**, without allocating another matrix. Nothing is returned.
""",
    constraints="""
- `1 <= n <= 20`
- `-1000 <= matrix[i][j] <= 1000`
""",
    signature=function("rotate", [("matrix", "int[][]")], "void", mutates="matrix"),
    reference=_rotate,
    brute=_rotate_brute,
    examples=[Example([[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "Becomes [[7,4,1],[8,5,2],[9,6,3]]."), Example([[[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]])],
    edge_cases=[[[[1]]], [[[1, 2], [3, 4]]]],
    generator=lambda rng: [matrix(rng, (n := rng.randint(1, 20)), n, -1000, 1000)],
    random_count=8,
)


# ---------------------------------------------------------------- Spiral Matrix


def _spiral_order(matrix: list[list[int]]) -> list[int]:
    out: list[int] = []
    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        out += matrix[top][left : right + 1]
        out += [matrix[i][right] for i in range(top + 1, bottom + 1)]
        if top < bottom and left < right:
            out += matrix[bottom][left:right][::-1]
            out += [matrix[i][left] for i in range(bottom - 1, top, -1)]
        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
    return out


def _spiral_brute(matrix: list[list[int]]) -> list[int]:
    m, n = len(matrix), len(matrix[0])
    seen, out = set(), []
    i = j = d = 0
    for _ in range(m * n):
        out.append(matrix[i][j])
        seen.add((i, j))
        di, dj = _STEPS[d]
        if not (0 <= i + di < m and 0 <= j + dj < n) or (i + di, j + dj) in seen:
            d = (d + 1) % 4
            di, dj = _STEPS[d]
        i, j = i + di, j + dj
    return out


SPIRAL_MATRIX = ProblemSource(
    title="Spiral Matrix",
    statement="""
Return all elements of the `m x n` matrix in clockwise spiral order, starting at the top-left corner and moving right.
""",
    constraints="""
- `1 <= m, n <= 10`
- `-100 <= matrix[i][j] <= 100`
""",
    signature=function("spiralOrder", [("matrix", "int[][]")], "int[]"),
    reference=_spiral_order,
    brute=_spiral_brute,
    examples=[Example([[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]), Example([[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]])],
    edge_cases=[[[[7]]], [[[1, 2, 3]]], [[[1], [2], [3]]], [[[1, 2], [3, 4], [5, 6]]]],
    generator=lambda rng: [matrix(rng, rng.randint(1, 10), rng.randint(1, 10), -100, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Where Will the Ball Fall


def _find_ball(grid: list[list[int]]) -> list[int]:
    n = len(grid[0])
    out = []
    for start in range(n):
        col = start
        for row in grid:
            nxt = col + row[col]
            if not 0 <= nxt < n or row[nxt] != row[col]:
                col = -1
                break
            col = nxt
        out.append(col)
    return out


def _ball_brute(grid: list[list[int]]) -> list[int]:
    """Trace the ball through half-cell positions: 2*col+1 is a cell centre, even numbers are walls."""
    n = len(grid[0])
    out = []
    for start in range(n):
        x = 2 * start + 1
        for row in grid:
            board = row[(x - 1) // 2]
            x += 2 * board  # slide to the next cell centre
            if not 1 <= x <= 2 * n - 1 or row[(x - 1) // 2] != board:
                x = -1
                break
        out.append((x - 1) // 2 if x != -1 else -1)
    return out


def _ball_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 8, 100)
    rows = []
    for _ in range(m):  # runs of equal boards, so some balls make it through
        row: list[int] = []
        while len(row) < n:
            row += [rng.choice((1, -1))] * rng.randint(1, 4)
        rows.append(row[:n])
    return [rows]


BALL_FALL = ProblemSource(
    title="Where Will the Ball Fall",
    statement="""
A box is an `m x n` grid of diagonal boards: `1` is a board running from top-left to bottom-right (it deflects balls to the right) and `-1` runs
from top-right to bottom-left (it deflects to the left). One ball is dropped at the top of each column.

A ball gets stuck if it hits the side wall or a "V" formed by two neighbouring boards pointing at each other. For each column, return the column
where its ball leaves the bottom, or `-1` if it gets stuck.
""",
    constraints="""
- `1 <= m, n <= 100`
- `grid[i][j]` is `1` or `-1`
""",
    signature=function("findBall", [("grid", "int[][]")], "int[]"),
    reference=_find_ball,
    brute=_ball_brute,
    examples=[
        Example([[[1, 1, 1, -1, -1], [1, 1, 1, -1, -1], [-1, -1, -1, 1, 1], [1, 1, 1, 1, -1], [-1, -1, -1, -1, -1]]], "Only the ball from column 0 gets through, leaving at column 1."),
        Example([[[-1]]], "It hits the left wall."),
        Example([[[1, 1, 1, 1, 1, 1], [-1, -1, -1, -1, -1, -1], [1, 1, 1, 1, 1, 1], [-1, -1, -1, -1, -1, -1]]]),
    ],
    edge_cases=[[[[1]]], [[[1, -1]]], [[[1, 1], [-1, -1]]]],
    generator=_ball_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Island Perimeter


def _island_perimeter(grid: list[list[int]]) -> int:
    cells = shared = 0
    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            if v:
                cells += 1
                shared += (i > 0 and grid[i - 1][j]) + (j > 0 and row[j - 1])
    return 4 * cells - 2 * shared


def _perimeter_brute(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    return sum(
        1
        for i in range(m)
        for j in range(n)
        if grid[i][j]
        for di, dj in _STEPS
        if not (0 <= i + di < m and 0 <= j + dj < n) or not grid[i + di][j + dj]
    )


def _island_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 8, 100)
    grid = [[0] * n for _ in range(m)]
    i, j = rng.randrange(m), rng.randrange(n)
    grid[i][j] = 1
    frontier = [(i, j)]
    for _ in range(rng.randint(0, m * n)):  # grow one connected island without lakes being required
        ci, cj = rng.choice(frontier)
        di, dj = rng.choice(_STEPS)
        if 0 <= ci + di < m and 0 <= cj + dj < n and not grid[ci + di][cj + dj]:
            grid[ci + di][cj + dj] = 1
            frontier.append((ci + di, cj + dj))
    return [grid]


ISLAND_PERIMETER = ProblemSource(
    title="Island Perimeter",
    statement="""
`grid` is a map where `1` is land and `0` is water; cells connect horizontally and vertically. It contains exactly one island (one connected group
of land cells), the area outside the grid is water, and the island may contain lakes. Return the island's perimeter.
""",
    constraints="""
- `1 <= m, n <= 100`
- `grid[i][j]` is `0` or `1`; exactly one island
""",
    signature=function("islandPerimeter", [("grid", "int[][]")], "int"),
    reference=_island_perimeter,
    brute=_perimeter_brute,
    examples=[Example([[[0, 1, 0, 0], [1, 1, 1, 0], [0, 1, 0, 0], [1, 1, 0, 0]]]), Example([[[1]]]), Example([[[1, 0]]])],
    edge_cases=[[[[1, 1], [1, 1]]], [[[1, 1, 1], [1, 0, 1], [1, 1, 1]]]],
    generator=_island_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Convert 1D Array Into 2D Array


def _construct_2d(original: list[int], m: int, n: int) -> list[list[int]]:
    if m * n != len(original):
        return []
    return [original[i * n : (i + 1) * n] for i in range(m)]


def _construct_brute(original: list[int], m: int, n: int) -> list[list[int]]:
    if m * n != len(original):
        return []
    out = [[0] * n for _ in range(m)]
    for k, v in enumerate(original):
        out[k // n][k % n] = v
    return out


def _convert_gen(rng: random.Random) -> list:
    m, n = rng.randint(1, 10), rng.randint(1, 10)
    size = m * n if rng.random() < 0.7 else m * n + rng.choice([-1, 1])
    return [ints(rng, max(1, size), 1, 10**5), m, n]


CONVERT_1D_2D = ProblemSource(
    title="Convert 1D Array Into 2D Array",
    statement="""
Arrange all elements of `original`, in order, into an `m x n` matrix filled row by row. Return an empty matrix if that's impossible.
""",
    constraints="""
- `1 <= original.length <= 5 * 10^4`
- `1 <= original[i] <= 10^5`
- `1 <= m, n <= 4 * 10^4`
""",
    signature=function("construct2DArray", [("original", "int[]"), ("m", "int"), ("n", "int")], "int[][]"),
    reference=_construct_2d,
    brute=_construct_brute,
    examples=[Example([[1, 2, 3, 4], 2, 2]), Example([[1, 2, 3], 1, 3]), Example([[1, 2], 1, 1], "2 elements can't fill a 1 x 1 matrix.")],
    edge_cases=[[[5], 1, 1], [[5], 40000, 40000], [[1, 2, 3, 4, 5, 6], 3, 2]],
    generator=_convert_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Spiral Matrix II


def _generate_matrix(n: int) -> list[list[int]]:
    grid = [[0] * n for _ in range(n)]
    i = j = d = 0
    for value in range(1, n * n + 1):
        grid[i][j] = value
        di, dj = _STEPS[d]
        if not (0 <= i + di < n and 0 <= j + dj < n) or grid[i + di][j + dj]:
            d = (d + 1) % 4
            di, dj = _STEPS[d]
        i, j = i + di, j + dj
    return grid


def _generate_brute(n: int) -> list[list[int]]:
    grid = [[0] * n for _ in range(n)]
    order = _spiral_order([[(i, j) for j in range(n)] for i in range(n)])  # type: ignore[list-item]
    for value, (i, j) in enumerate(order, start=1):
        grid[i][j] = value
    return grid


SPIRAL_MATRIX_II = ProblemSource(
    title="Spiral Matrix II",
    statement="""
Return an `n x n` matrix filled with the numbers `1` to `n^2` in clockwise spiral order, starting at the top-left corner and moving right.
""",
    constraints="""
- `1 <= n <= 20`
""",
    signature=function("generateMatrix", [("n", "int")], "int[][]"),
    reference=_generate_matrix,
    brute=_generate_brute,
    examples=[Example([3], "[[1,2,3],[8,9,4],[7,6,5]]."), Example([1])],
    edge_cases=[[2], [4], [20]],
    generator=lambda rng: [rng.randint(1, 20)],
    random_count=6,
)


# ---------------------------------------------------------------- Flip Columns For Maximum Number of Equal Rows


def _max_equal_rows(matrix: list[list[int]]) -> int:
    patterns: dict[tuple[int, ...], int] = {}
    for row in matrix:
        key = tuple(v ^ row[0] for v in row)
        patterns[key] = patterns.get(key, 0) + 1
    return max(patterns.values())


def _equal_rows_brute(matrix: list[list[int]]) -> int:
    n = len(matrix[0])
    if n > 10:
        return NotImplemented
    best = 0
    for mask in range(1 << n):
        flipped = [[v ^ (mask >> j & 1) for j, v in enumerate(row)] for row in matrix]
        best = max(best, sum(len(set(row)) == 1 for row in flipped))
    return best


def _flip_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 8, 300)
    bases = [[rng.randint(0, 1) for _ in range(n)] for _ in range(rng.randint(1, 3))]
    rows = []
    for _ in range(m):
        base = rng.choice(bases)
        rows.append([1 - v for v in base] if rng.random() < 0.5 else base[:])
        if rng.random() < 0.2:
            rows[-1][rng.randrange(n)] ^= 1
    return [rows]


FLIP_COLUMNS = ProblemSource(
    title="Flip Columns For Maximum Number of Equal Rows",
    statement="""
`matrix` is a binary matrix. You may flip any set of columns (flipping turns every `0` in the column into `1` and vice versa). Return the
maximum number of rows that can have all their values equal after some set of flips.
""",
    constraints="""
- `1 <= m, n <= 300`
- `matrix[i][j]` is `0` or `1`
""",
    signature=function("maxEqualRowsAfterFlips", [("matrix", "int[][]")], "int"),
    reference=_max_equal_rows,
    brute=_equal_rows_brute,
    examples=[Example([[[0, 1], [1, 1]]]), Example([[[0, 1], [1, 0]]], "Flip the first column."), Example([[[0, 0, 0], [0, 0, 1], [1, 1, 0]]])],
    edge_cases=[[[[1]]], [[[0], [1], [0]]], [[[0, 1, 0], [0, 1, 0], [1, 0, 1]]]],
    generator=_flip_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Number of Spaces Cleaning Robot Cleaned


def _number_of_clean_rooms(room: list[list[int]]) -> int:
    m, n = len(room), len(room[0])
    i = j = d = 0
    cleaned = {(0, 0)}
    states = {(0, 0, 0)}
    while True:
        di, dj = _STEPS[d]
        ni, nj = i + di, j + dj
        if 0 <= ni < m and 0 <= nj < n and room[ni][nj] == 0:
            i, j = ni, nj
            cleaned.add((i, j))
        else:
            d = (d + 1) % 4
        if (i, j, d) in states:
            return len(cleaned)
        states.add((i, j, d))


def _clean_rooms_brute(room: list[list[int]]) -> int:
    m, n = len(room), len(room[0])
    i = j = d = 0
    cleaned = {(0, 0)}
    for _ in range(4 * m * n * 4 + 8):  # more steps than there are (cell, direction) states
        di, dj = _STEPS[d]
        if 0 <= i + di < m and 0 <= j + dj < n and room[i + di][j + dj] == 0:
            i, j = i + di, j + dj
            cleaned.add((i, j))
        else:
            d = (d + 1) % 4
    return len(cleaned)


def _room_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 8, 300)
    grid = _binary_grid(rng, m, n, rng.choice([0.1, 0.3]))
    grid[0][0] = 0
    return [grid]


CLEANING_ROBOT = ProblemSource(
    title="Number of Spaces Cleaning Robot Cleaned",
    statement="""
`room` is a grid where `0` is an empty space and `1` is an object. A cleaning robot starts at the top-left cell (always empty) facing right. It
repeatedly moves straight ahead; whenever the next cell is outside the room or holds an object, it turns 90 degrees clockwise instead of moving.
The robot cleans every space it visits, including the starting one. It runs forever; return the number of distinct spaces it cleans.
""",
    constraints="""
- `1 <= m, n <= 300`
- `room[i][j]` is `0` or `1`; `room[0][0] == 0`
""",
    signature=function("numberOfCleanRooms", [("room", "int[][]")], "int"),
    reference=_number_of_clean_rooms,
    brute=_clean_rooms_brute,
    brute_input_limit=400,
    examples=[Example([[[0, 0, 0], [1, 1, 0], [0, 0, 0]]], "It cleans the whole ring of 7 spaces."), Example([[[0, 1, 0], [1, 0, 0], [0, 0, 0]]], "Boxed in at the start: 1 space.")],
    edge_cases=[[[[0]]], [[[0, 0, 0, 0]]], [[[0], [0], [0]]]],
    generator=_room_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Transpose Matrix


def _transpose(matrix: list[list[int]]) -> list[list[int]]:
    return [list(col) for col in zip(*matrix, strict=True)]


TRANSPOSE = ProblemSource(
    title="Transpose Matrix",
    statement="""
Return the transpose of `matrix`: the matrix flipped over its main diagonal, so rows become columns.
""",
    constraints="""
- `1 <= m, n <= 1000`, `1 <= m * n <= 10^5`
- `-10^9 <= matrix[i][j] <= 10^9`
""",
    signature=function("transpose", [("matrix", "int[][]")], "int[][]"),
    reference=_transpose,
    brute=lambda matrix: [[matrix[i][j] for i in range(len(matrix))] for j in range(len(matrix[0]))],
    examples=[Example([[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]), Example([[[1, 2, 3], [4, 5, 6]]], "A 2 x 3 matrix becomes 3 x 2.")],
    edge_cases=[[[[1]]], [[[1, 2, 3]]], [[[1], [2]]]],
    generator=lambda rng: [matrix(rng, *_dims(rng, 1, 8, 40), -(10**9), 10**9)],
    random_count=8,
)


# ---------------------------------------------------------------- Count Negative Numbers in a Sorted Matrix


def _count_negatives(grid: list[list[int]]) -> int:
    n = len(grid[0])
    count, j = 0, n - 1
    for row in grid:  # the first negative moves left as we go down
        while j >= 0 and row[j] < 0:
            j -= 1
        count += n - 1 - j
    return count


COUNT_NEGATIVES = ProblemSource(
    title="Count Negative Numbers in a Sorted Matrix",
    statement="""
Every row and every column of `grid` is sorted in non-increasing order. Return the number of negative values.

Aim for `O(m + n)` time.
""",
    constraints="""
- `1 <= m, n <= 100`
- `-100 <= grid[i][j] <= 100`
""",
    signature=function("countNegatives", [("grid", "int[][]")], "int"),
    reference=_count_negatives,
    brute=lambda grid: sum(v < 0 for row in grid for v in row),
    examples=[Example([[[4, 3, 2, -1], [3, 2, 1, -1], [1, 1, -1, -2], [-1, -1, -2, -3]]]), Example([[[3, 2], [1, 0]]])],
    edge_cases=[[[[-1]]], [[[0]]], [[[5, 1, 0], [-1, -2, -3]]]],
    generator=lambda rng: [_sorted_grid(rng, *_dims(rng, 1, 8, 100), -100, 100, descending=True)],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Time Takes to Reach Destination Without Drowning


def _minimum_seconds(land: list[list[str]]) -> int:
    m, n = len(land), len(land[0])
    inf = float("inf")
    flood = [[inf] * n for _ in range(m)]
    queue = deque()
    for i in range(m):
        for j in range(n):
            if land[i][j] == "*":
                flood[i][j] = 0
                queue.append((i, j))
    while queue:
        i, j = queue.popleft()
        for di, dj in _STEPS:
            a, b = i + di, j + dj
            if 0 <= a < m and 0 <= b < n and land[a][b] in ".S" and flood[a][b] == inf:
                flood[a][b] = flood[i][j] + 1
                queue.append((a, b))
    start = next((i, j) for i in range(m) for j in range(n) if land[i][j] == "S")
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        (i, j), t = queue.popleft()
        if land[i][j] == "D":
            return t
        for di, dj in _STEPS:
            a, b = i + di, j + dj
            if 0 <= a < m and 0 <= b < n and (a, b) not in seen and land[a][b] in ".D" and t + 1 < flood[a][b]:
                seen.add((a, b))
                queue.append(((a, b), t + 1))
    return -1


def _drowning_brute(land: list[list[str]]) -> int:
    m, n = len(land), len(land[0])
    flooded = {(i, j) for i in range(m) for j in range(n) if land[i][j] == "*"}
    here = {(i, j) for i in range(m) for j in range(n) if land[i][j] == "S"}
    for t in range(1, m * n + 2):
        flooded |= {
            (i + di, j + dj)
            for i, j in flooded
            for di, dj in _STEPS
            if 0 <= i + di < m and 0 <= j + dj < n and land[i + di][j + dj] in ".S"
        }
        here = {
            (i + di, j + dj)
            for i, j in here
            for di, dj in _STEPS
            if 0 <= i + di < m and 0 <= j + dj < n and land[i + di][j + dj] in ".DS" and (i + di, j + dj) not in flooded
        }
        if any(land[i][j] == "D" for i, j in here):
            return t
        if not here:
            return -1
    return -1


def _drowning_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 7, 100)
    if m * n < 2:
        n = 2
    cells = [rng.choice(".....XX*" if rng.random() < 0.5 else "......X*") for _ in range(m * n)]
    s, d = sample(rng, range(m * n), 2)
    cells[s], cells[d] = "S", "D"
    return [[cells[i * n : (i + 1) * n] for i in range(m)]]


DROWNING = ProblemSource(
    title="Minimum Time Takes to Reach Destination Without Drowning",
    statement="""
`land` is a grid of single-character strings: `"S"` is your start, `"D"` the destination, `"."` an empty cell, `"X"` a stone and `"*"` a flooded
cell. Every second you must move to a side-adjacent cell; in the same second, every empty cell (or the start cell) adjacent to a flooded cell
becomes flooded too. You can't enter stones, and you can't enter a cell that is flooded — including one that becomes flooded in the second you
arrive. The destination never floods.

Return the minimum number of seconds needed to reach `"D"`, or `-1` if it's impossible.
""",
    constraints="""
- `2 <= m * n`, `1 <= m, n <= 100`
- exactly one `"S"` and one `"D"`; the other cells are `"."`, `"X"` or `"*"`
""",
    signature=function("minimumSeconds", [("land", "string[][]")], "int"),
    reference=_minimum_seconds,
    brute=_drowning_brute,
    brute_input_limit=1200,
    examples=[
        Example([[["D", ".", "*"], [".", ".", "."], [".", "S", "."]]], "Up to the middle, then left and up: 3 seconds."),
        Example([[["D", "X", "*"], [".", ".", "."], [".", ".", "S"]]], "The flood cuts off every route."),
        Example([[["D", ".", ".", ".", "*", "."], [".", "X", ".", "X", ".", "."], [".", ".", ".", ".", "S", "."]]]),
    ],
    edge_cases=[[[["S", "D"]]], [[["S", "X", "D"]]], [[["S"], ["*"], ["D"]]]],
    generator=_drowning_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Smallest Rectangle Enclosing Black Pixels


def _min_area(image: list[list[str]], x: int, y: int) -> int:
    m, n = len(image), len(image[0])

    def row_has(i: int) -> bool:
        return "1" in image[i]

    def col_has(j: int) -> bool:
        return any(image[i][j] == "1" for i in range(m))

    def first_true(lo: int, hi: int, has: object, want: bool) -> int:
        """First index in [lo, hi) where has(index) == want (monotone on that range)."""
        while lo < hi:
            mid = (lo + hi) // 2
            if has(mid) == want:  # type: ignore[operator]
                hi = mid
            else:
                lo = mid + 1
        return lo

    top = first_true(0, x, row_has, True)
    bottom = first_true(x + 1, m, row_has, False)
    left = first_true(0, y, col_has, True)
    right = first_true(y + 1, n, col_has, False)
    return (bottom - top) * (right - left)


def _min_area_brute(image: list[list[str]], x: int, y: int) -> int:
    rows = [i for i, row in enumerate(image) if "1" in row]
    cols = [j for row in image for j, c in enumerate(row) if c == "1"]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _blob_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 8, 100)
    grid = [["0"] * n for _ in range(m)]
    x, y = rng.randrange(m), rng.randrange(n)
    grid[x][y] = "1"
    blob = [(x, y)]
    for _ in range(rng.randint(0, 2 * m * n)):
        i, j = rng.choice(blob)
        di, dj = rng.choice(_STEPS)
        if 0 <= i + di < m and 0 <= j + dj < n and grid[i + di][j + dj] == "0":
            grid[i + di][j + dj] = "1"
            blob.append((i + di, j + dj))
    px, py = rng.choice(blob)
    return [grid, px, py]


SMALLEST_RECTANGLE = ProblemSource(
    title="Smallest Rectangle Enclosing Black Pixels",
    statement="""
`image` is a binary matrix where `"0"` is white and `"1"` is black. All black pixels form one connected region (connected horizontally and
vertically), and `image[x][y]` is one of them. Return the area of the smallest axis-aligned rectangle that encloses every black pixel.

Aim for better than `O(m * n)` time.
""",
    constraints="""
- `1 <= m, n <= 100`
- `image[i][j]` is `"0"` or `"1"`; `image[x][y] == "1"`; the black pixels are connected
""",
    signature=function("minArea", [("image", "char[][]"), ("x", "int"), ("y", "int")], "int"),
    reference=_min_area,
    brute=_min_area_brute,
    examples=[Example([[["0", "0", "1", "0"], ["0", "1", "1", "0"], ["0", "1", "0", "0"]], 0, 2], "Rows 0-2, columns 1-2: 3 x 2."), Example([[["1"]], 0, 0])],
    edge_cases=[[[["0", "1"]], 0, 1], [[["1", "1", "1"]], 0, 1], [[["0"], ["1"], ["0"]], 1, 0]],
    generator=_blob_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimize Maximum Value in a Grid


def _min_score(grid: list[list[int]]) -> list[list[int]]:
    m, n = len(grid), len(grid[0])
    row_max, col_max = [0] * m, [0] * n
    out = [[0] * n for _ in range(m)]
    for _, i, j in sorted((grid[i][j], i, j) for i in range(m) for j in range(n)):
        out[i][j] = max(row_max[i], col_max[j]) + 1
        row_max[i] = col_max[j] = out[i][j]
    return out


def _min_score_brute(grid: list[list[int]]) -> list[list[int]]:
    m, n = len(grid), len(grid[0])

    @cache
    def rank(i: int, j: int) -> int:
        smaller = [rank(i, k) for k in range(n) if grid[i][k] < grid[i][j]]
        smaller += [rank(k, j) for k in range(m) if grid[k][j] < grid[i][j]]
        return 1 + max(smaller, default=0)

    return [[rank(i, j) for j in range(n)] for i in range(m)]


MINIMIZE_MAX_GRID = ProblemSource(
    title="Minimize Maximum Value in a Grid",
    statement="""
`grid` holds distinct positive integers. Replace every value with a positive integer so that the relative order of values in every row and in
every column is unchanged (if `grid[r][c1] > grid[r][c2]` before, it still is afterwards, and likewise within columns), and the largest value in
the new grid is as small as possible. Return the new grid; if several are optimal, any of them is accepted.
""",
    constraints="""
- `1 <= m, n <= 1000`, `1 <= m * n <= 10^5`
- `1 <= grid[i][j] <= 10^9`, all distinct
""",
    signature=function("minScore", [("grid", "int[][]")], "int[][]"),
    reference=_min_score,
    brute=_min_score_brute,
    brute_input_limit=600,
    compare="checker",
    checker="min_max_grid",
    examples=[Example([[[3, 1], [2, 5]]], "[[2,1],[1,2]] keeps every order; the maximum 2 is optimal."), Example([[[10]]])],
    edge_cases=[[[[1, 2, 3]]], [[[3], [2], [1]]], [[[1, 4], [2, 3]]]],
    generator=lambda rng: [_distinct_grid(rng, *_dims(rng, 1, 6, 300), range(1, 10**9))],
    random_count=8,
)


# ---------------------------------------------------------------- Kth Smallest Number in Multiplication Table


def _find_kth_number(m: int, n: int, k: int) -> int:
    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if sum(min(mid // i, n) for i in range(1, m + 1)) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


MULTIPLICATION_TABLE = ProblemSource(
    title="Kth Smallest Number in Multiplication Table",
    statement="""
The `m x n` multiplication table has `i * j` in row `i`, column `j` (both 1-indexed). Return the `k`-th smallest number in the table, counting
repeated values separately.
""",
    constraints="""
- `1 <= m, n <= 3 * 10^4`
- `1 <= k <= m * n`
""",
    signature=function("findKthNumber", [("m", "int"), ("n", "int"), ("k", "int")], "int"),
    reference=_find_kth_number,
    brute=lambda m, n, k: sorted(i * j for i in range(1, m + 1) for j in range(1, n + 1))[k - 1] if m * n <= 40000 else NotImplemented,
    examples=[Example([3, 3, 5], "1,2,2,3,3,4,6,6,9: the 5th is 3."), Example([2, 3, 6])],
    edge_cases=[[1, 1, 1], [1, 30000, 30000], [30000, 30000, 1], [30000, 30000, 900000000]],
    generator=lambda rng: [(m := pick_n(rng, 1, 40, big=30000)), (n := pick_n(rng, 1, 40, big=30000)), rng.randint(1, m * n)],
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Swim in Rising Water


def _swim_in_water(grid: list[list[int]]) -> int:
    n = len(grid)
    heap = [(grid[0][0], 0, 0)]
    seen = {(0, 0)}
    while heap:
        t, i, j = heapq.heappop(heap)
        if (i, j) == (n - 1, n - 1):
            return t
        for di, dj in _STEPS:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < n and (a, b) not in seen:
                seen.add((a, b))
                heapq.heappush(heap, (max(t, grid[a][b]), a, b))
    raise AssertionError("unreachable")


def _swim_brute(grid: list[list[int]]) -> int:
    n = len(grid)
    for t in range(n * n):
        if grid[0][0] > t:
            continue
        seen, stack = {(0, 0)}, [(0, 0)]
        while stack:
            i, j = stack.pop()
            for di, dj in _STEPS:
                a, b = i + di, j + dj
                if 0 <= a < n and 0 <= b < n and (a, b) not in seen and grid[a][b] <= t:
                    seen.add((a, b))
                    stack.append((a, b))
        if (n - 1, n - 1) in seen:
            return t
    raise AssertionError("unreachable")


SWIM_RISING_WATER = ProblemSource(
    title="Swim in Rising Water",
    statement="""
`grid` is an `n x n` elevation map holding each of the values `0` to `n^2 - 1` exactly once. At time `t` the water everywhere is at depth `t`, and
you can swim between side-adjacent cells only if both elevations are at most `t`; swimming itself takes no time. Starting at the top-left cell,
return the least time at which you can reach the bottom-right cell.
""",
    constraints="""
- `1 <= n <= 50`
- `grid` is a permutation of `0..n^2 - 1`
""",
    signature=function("swimInWater", [("grid", "int[][]")], "int"),
    reference=_swim_in_water,
    brute=_swim_brute,
    brute_input_limit=3000,
    examples=[Example([[[0, 2], [1, 3]]], "At time 3 every cell is reachable."), Example([[[0, 1, 2, 3, 4], [24, 23, 22, 21, 5], [12, 13, 14, 15, 16], [11, 17, 18, 19, 20], [10, 9, 8, 7, 6]]])],
    edge_cases=[[[[0]]], [[[3, 2], [0, 1]]]],
    generator=lambda rng: [_distinct_grid(rng, (n := rng.randint(1, rng.choice([8, 50]))), n, range(n * n))],
    random_count=8,
)


# ---------------------------------------------------------------- Best Meeting Point


def _min_total_distance(grid: list[list[int]]) -> int:
    rows = [i for i, row in enumerate(grid) for v in row if v]
    cols = sorted(j for row in grid for j, v in enumerate(row) if v)
    mid_r, mid_c = rows[len(rows) // 2], cols[len(cols) // 2]
    return sum(abs(r - mid_r) for r in rows) + sum(abs(c - mid_c) for c in cols)


def _meeting_brute(grid: list[list[int]]) -> int:
    homes = [(i, j) for i, row in enumerate(grid) for j, v in enumerate(row) if v]
    return min(sum(abs(i - a) + abs(j - b) for a, b in homes) for i in range(len(grid)) for j in range(len(grid[0])))


def _meeting_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 8, 200)
    grid = _binary_grid(rng, m, n, rng.choice([0.1, 0.4]))
    grid[rng.randrange(m)][rng.randrange(n)] = 1
    return [grid]


BEST_MEETING = ProblemSource(
    title="Best Meeting Point",
    statement="""
In the binary grid, each `1` marks the home of one friend. Choose a meeting cell (any cell, possibly a home) that minimises the total Manhattan
distance from every home to it, and return that minimum total distance.
""",
    constraints="""
- `1 <= m, n <= 200`
- `grid[i][j]` is `0` or `1`; there is at least one `1`
""",
    signature=function("minTotalDistance", [("grid", "int[][]")], "int"),
    reference=_min_total_distance,
    brute=_meeting_brute,
    brute_input_limit=1500,
    examples=[Example([[[1, 0, 0, 0, 1], [0, 0, 0, 0, 0], [0, 0, 1, 0, 0]]], "Meeting at (0, 2) costs 2 + 2 + 2 = 6."), Example([[[1, 1]]])],
    edge_cases=[[[[1]]], [[[1, 0, 0, 0, 0, 1]]], [[[1], [0], [1], [1]]]],
    generator=_meeting_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Game of Life


def _game_of_life(board: list[list[int]]) -> None:
    m, n = len(board), len(board[0])
    for i in range(m):  # bit 0 = current state, bit 1 = next state
        for j in range(n):
            live = sum(board[a][b] & 1 for a in range(i - 1, i + 2) for b in range(j - 1, j + 2) if (a, b) != (i, j) and 0 <= a < m and 0 <= b < n)
            if live == 3 or (board[i][j] & 1 and live == 2):
                board[i][j] |= 2
    for row in board:
        for j in range(n):
            row[j] >>= 1


def _life_brute(board: list[list[int]]) -> None:
    old = [row[:] for row in board]
    m, n = len(old), len(old[0])
    for i in range(m):
        for j in range(n):
            live = sum(old[a][b] for a in range(m) for b in range(n) if max(abs(a - i), abs(b - j)) == 1)
            board[i][j] = int(live == 3 or (old[i][j] == 1 and live == 2))


GAME_OF_LIFE = ProblemSource(
    title="Game of Life",
    statement="""
`board` is a grid of cells, each live (`1`) or dead (`0`). Every cell interacts with its eight neighbours (horizontal, vertical, diagonal):

1. a live cell with fewer than two live neighbours dies;
2. a live cell with two or three live neighbours lives on;
3. a live cell with more than three live neighbours dies;
4. a dead cell with exactly three live neighbours becomes live.

All cells update simultaneously, based on the current generation. Update `board` **in place** to the next generation; nothing is returned.
""",
    constraints="""
- `1 <= m, n <= 25`
- `board[i][j]` is `0` or `1`
""",
    signature=function("gameOfLife", [("board", "int[][]")], "void", mutates="board"),
    reference=_game_of_life,
    brute=_life_brute,
    examples=[Example([[[0, 1, 0], [0, 0, 1], [1, 1, 1], [0, 0, 0]]]), Example([[[1, 1], [1, 0]]], "The dead corner has three live neighbours.")],
    edge_cases=[[[[1]]], [[[0]]], [[[0, 1, 0], [0, 1, 0], [0, 1, 0]]]],
    generator=lambda rng: [_binary_grid(rng, *_dims(rng, 1, 10, 25), rng.choice([0.2, 0.4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Toeplitz Matrix


def _is_toeplitz(matrix: list[list[int]]) -> bool:
    return all(a[:-1] == b[1:] for a, b in itertools.pairwise(matrix))


def _toeplitz_brute(matrix: list[list[int]]) -> bool:
    diagonals: dict[int, set[int]] = {}
    for i, row in enumerate(matrix):
        for j, v in enumerate(row):
            diagonals.setdefault(i - j, set()).add(v)
    return all(len(values) == 1 for values in diagonals.values())


def _toeplitz_gen(rng: random.Random) -> list:
    m, n = _dims(rng, 1, 7, 20)
    diagonal = {d: rng.randint(0, 9) for d in range(-n, m)}
    grid = [[diagonal[i - j] for j in range(n)] for i in range(m)]
    if rng.random() < 0.5:
        grid[rng.randrange(m)][rng.randrange(n)] = rng.randint(0, 9)
    return [grid]


TOEPLITZ = ProblemSource(
    title="Toeplitz Matrix",
    statement="""
A matrix is *Toeplitz* if every diagonal running from top-left to bottom-right holds a single repeated value. Return `true` if `matrix` is
Toeplitz.
""",
    constraints="""
- `1 <= m, n <= 20`
- `0 <= matrix[i][j] <= 99`
""",
    signature=function("isToeplitzMatrix", [("matrix", "int[][]")], "bool"),
    reference=_is_toeplitz,
    brute=_toeplitz_brute,
    examples=[Example([[[1, 2, 3, 4], [5, 1, 2, 3], [9, 5, 1, 2]]]), Example([[[1, 2], [2, 2]]], "The main diagonal holds 1 and 2.")],
    edge_cases=[[[[7]]], [[[1, 2, 3]]], [[[1], [2]]]],
    generator=_toeplitz_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Diagonal Traverse


def _find_diagonal_order(mat: list[list[int]]) -> list[int]:
    m, n = len(mat), len(mat[0])
    out = []
    for d in range(m + n - 1):
        cells = [(i, d - i) for i in range(max(0, d - n + 1), min(m, d + 1))]
        out += [mat[i][j] for i, j in (reversed(cells) if d % 2 == 0 else cells)]
    return out


def _diagonal_brute(mat: list[list[int]]) -> list[int]:
    m, n = len(mat), len(mat[0])
    cells = sorted(((i, j) for i in range(m) for j in range(n)), key=lambda c: (c[0] + c[1], c[1] if (c[0] + c[1]) % 2 == 0 else c[0]))
    return [mat[i][j] for i, j in cells]


DIAGONAL_TRAVERSE = ProblemSource(
    title="Diagonal Traverse",
    statement="""
Return all elements of `mat` in zig-zag diagonal order: start at the top-left, walk the first anti-diagonal upward-right, the next one
downward-left, and keep alternating.
""",
    constraints="""
- `1 <= m, n <= 10^4`, `1 <= m * n <= 10^4`
- `-10^5 <= mat[i][j] <= 10^5`
""",
    signature=function("findDiagonalOrder", [("mat", "int[][]")], "int[]"),
    reference=_find_diagonal_order,
    brute=_diagonal_brute,
    examples=[Example([[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "1, 2, 4, 7, 5, 3, 6, 8, 9."), Example([[[1, 2], [3, 4]]])],
    edge_cases=[[[[1]]], [[[1, 2, 3, 4]]], [[[1], [2], [3]]]],
    generator=lambda rng: [matrix(rng, *_dims(rng, 1, 8, 60), -(10**5), 10**5)],
    random_count=8,
)


# ---------------------------------------------------------------- Search a 2D Matrix II


def _search_matrix(matrix: list[list[int]], target: int) -> bool:
    i, j = 0, len(matrix[0]) - 1
    while i < len(matrix) and j >= 0:
        if matrix[i][j] == target:
            return True
        if matrix[i][j] > target:
            j -= 1
        else:
            i += 1
    return False


def _search_brute(matrix: list[list[int]], target: int) -> bool:
    return any((k := bisect.bisect_right(row, target)) > 0 and row[k - 1] == target for row in matrix)


def _search_gen(rng: random.Random) -> list:
    grid = _sorted_grid(rng, *_dims(rng, 1, 8, 300), -(hi := rng.choice([20, 10**9])), hi, descending=False)
    target = rng.choice(rng.choice(grid)) if rng.random() < 0.5 else rng.randint(-hi, hi)
    return [grid, target]


SEARCH_2D_II = ProblemSource(
    title="Search a 2D Matrix II",
    statement="""
Every row of `matrix` is sorted in ascending order from left to right, and every column from top to bottom. Return `true` if `target` occurs in
the matrix.

Aim for `O(m + n)` time.
""",
    constraints="""
- `1 <= m, n <= 300`
- `-10^9 <= matrix[i][j], target <= 10^9`
""",
    signature=function("searchMatrix", [("matrix", "int[][]"), ("target", "int")], "bool"),
    reference=_search_matrix,
    brute=_search_brute,
    examples=[
        Example([[[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22], [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]], 5]),
        Example([[[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22], [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]], 20]),
    ],
    edge_cases=[[[[1]], 1], [[[1]], 2], [[[-5, -3, 0]], -3]],
    generator=_search_gen,
    random_count=8,
)


PROBLEMS = [
    SET_MATRIX_ZEROS,
    ROTATE_IMAGE,
    SPIRAL_MATRIX,
    BALL_FALL,
    ISLAND_PERIMETER,
    CONVERT_1D_2D,
    SPIRAL_MATRIX_II,
    FLIP_COLUMNS,
    CLEANING_ROBOT,
    TRANSPOSE,
    COUNT_NEGATIVES,
    DROWNING,
    SMALLEST_RECTANGLE,
    MINIMIZE_MAX_GRID,
    MULTIPLICATION_TABLE,
    SWIM_RISING_WATER,
    BEST_MEETING,
    GAME_OF_LIFE,
    TOEPLITZ,
    DIAGONAL_TRAVERSE,
    SEARCH_2D_II,
]
