"""Pattern 12: Backtracking (part 1 of 2). Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import itertools
from collections import deque

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, random_tree, word

PATTERN_NUMBER = 12


# ---------------------------------------------------------------- Word Search


def _exist(board: list[list[str]], word_: str) -> bool:
    m, n = len(board), len(board[0])

    def dfs(i: int, j: int, k: int) -> bool:
        if k == len(word_):
            return True
        if not (0 <= i < m and 0 <= j < n) or board[i][j] != word_[k]:
            return False
        board[i][j] = "#"
        found = any(dfs(i + di, j + dj, k + 1) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        board[i][j] = word_[k]
        return found

    return any(dfs(i, j, 0) for i in range(m) for j in range(n))


def _exist_brute(board: list[list[str]], word_: str) -> bool:
    m, n = len(board), len(board[0])
    paths = [[(i, j)] for i in range(m) for j in range(n) if board[i][j] == word_[0]]
    for ch in word_[1:]:
        paths = [
            p + [(x, y)]
            for p in paths
            for x, y in ((p[-1][0] + 1, p[-1][1]), (p[-1][0] - 1, p[-1][1]), (p[-1][0], p[-1][1] + 1), (p[-1][0], p[-1][1] - 1))
            if 0 <= x < m and 0 <= y < n and board[x][y] == ch and (x, y) not in p
        ]
    return bool(paths)


def _word_search_gen(rng):
    m, n = rng.randint(1, 5), rng.randint(1, 5)
    board = [[rng.choice("ABCE") for _ in range(n)] for _ in range(m)]
    if rng.random() < 0.6:
        i, j, path = rng.randrange(m), rng.randrange(n), []
        for _ in range(rng.randint(1, 6)):
            path.append(board[i][j])
            moves = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= i + di < m and 0 <= j + dj < n]
            i, j = rng.choice(moves) if moves else (i, j)
        return [board, "".join(path)]
    return [board, word(rng, rng.randint(1, 6), "ABCE")]


WORD_SEARCH = ProblemSource(
    title="Word Search",
    statement="""
Given an `m x n` grid of letters and a string `word`, return `true` if `word` can be traced through the grid by moving between horizontally or
vertically adjacent cells, using each cell at most once.
""",
    constraints="""
- `1 <= m, n <= 6`
- `1 <= word.length <= 15`
- `board` and `word` consist of English letters
""",
    signature=function("exist", [("board", "char[][]"), ("word", "string")], "bool"),
    reference=_exist,
    brute=_exist_brute,
    examples=[
        Example([[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCCED"]),
        Example([[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "SEE"]),
        Example([[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCB"], "The B can't be reused."),
    ],
    edge_cases=[[[["A"]], "A"], [[["A"]], "AA"], [[["A", "A"]], "AAA"], [[["C", "A", "A"], ["A", "A", "A"], ["B", "C", "D"]], "AAB"]],
    generator=_word_search_gen,
    random_count=9,
)


# ---------------------------------------------------------------- House Robber III


def _rob_iii(root) -> int:
    def best(node) -> tuple[int, int]:
        if node is None:
            return 0, 0
        left, right = best(node.left), best(node.right)
        take = node.val + left[1] + right[1]
        skip = max(left) + max(right)
        return take, skip

    return max(best(root))


def _rob_iii_brute(root) -> int:
    nodes, parent_of = [], {}
    stack = [(root, None)]
    while stack:
        node, parent = stack.pop()
        if node:
            parent_of[id(node)] = parent
            nodes.append(node)
            stack += [(node.left, node), (node.right, node)]
    best = 0
    for mask in range(1 << len(nodes)):
        chosen = {id(nodes[i]) for i in range(len(nodes)) if mask >> i & 1}
        if all(parent_of[c] is None or id(parent_of[c]) not in chosen for c in chosen):
            best = max(best, sum(n.val for n in nodes if id(n) in chosen))
    return best


HOUSE_ROBBER_III = ProblemSource(
    title="House Robber III",
    statement="""
Houses form a binary tree; each node's value is the money in that house. A thief can't rob two houses that are directly linked (a parent and
its child) on the same night. Return the maximum amount the thief can rob.
""",
    constraints="""
- the tree has between `1` and `10^4` nodes
- `0 <= Node.val <= 10^4`
""",
    signature=function("rob", [("root", "TreeNode")], "int"),
    reference=_rob_iii,
    brute=_rob_iii_brute,
    brute_input_limit=45,
    examples=[Example([[3, 2, 3, None, 3, None, 1]], "Rob 3 + 3 + 1 = 7."), Example([[3, 4, 5, 1, 3, None, 1]], "Rob 4 + 5 = 9.")],
    edge_cases=[[[5]], [[1, 10]], [[4, 1, None, 2, None, 3]], [[0, 0, 0]]],
    generator=lambda rng: [random_tree(rng, pick_n(rng, 1, 12, big=3000), 0, rng.choice([9, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- N-Queens II


def _total_n_queens(n: int) -> int:
    count = 0

    def place(row: int, cols: int, diag1: int, diag2: int) -> None:
        nonlocal count
        if row == n:
            count += 1
            return
        free = ~(cols | diag1 | diag2) & ((1 << n) - 1)
        while free:
            bit = free & -free
            free ^= bit
            place(row + 1, cols | bit, (diag1 | bit) << 1, (diag2 | bit) >> 1)

    place(0, 0, 0, 0)
    return count


def _n_queens_brute(n: int) -> int:
    return sum(
        all(abs(p[i] - p[j]) != j - i for i in range(n) for j in range(i + 1, n)) for p in itertools.permutations(range(n))
    )


N_QUEENS_II = ProblemSource(
    title="N-Queens II",
    statement="""
Place `n` queens on an `n x n` chessboard so that no two queens attack each other (no two share a row, column or diagonal). Return the number
of distinct placements.
""",
    constraints="""
- `1 <= n <= 9`
""",
    signature=function("totalNQueens", [("n", "int")], "int"),
    reference=_total_n_queens,
    brute=lambda n: _n_queens_brute(n) if n <= 7 else NotImplemented,
    examples=[Example([4], "There are two solutions."), Example([1])],
    edge_cases=[[2], [3], [5], [6], [8], [9]],
    generator=lambda rng: [rng.randint(1, 9)],
    random_count=3,
)


# ---------------------------------------------------------------- Restore IP Addresses


def _restore_ip(s: str) -> list[str]:
    out = []

    def build(i: int, parts: list[str]) -> None:
        if len(parts) == 4:
            if i == len(s):
                out.append(".".join(parts))
            return
        for size in (1, 2, 3):
            part = s[i : i + size]
            if len(part) < size or (size > 1 and part[0] == "0") or int(part) > 255:
                break
            build(i + size, parts + [part])

    build(0, [])
    return out


def _restore_ip_brute(s: str) -> list[str]:
    out = []
    for cuts in itertools.combinations(range(1, len(s)), 3):
        parts = [s[a:b] for a, b in itertools.pairwise((0, *cuts, len(s)))]
        if all(p and str(int(p)) == p and int(p) <= 255 for p in parts):
            out.append(".".join(parts))
    return out


RESTORE_IP = ProblemSource(
    title="Restore IP Addresses",
    statement="""
A valid IPv4 address has four integers between `0` and `255` separated by dots, with no leading zeros (`"0.1.2.201"` is valid,
`"01.1.2.3"` isn't). Given a string of digits `s`, return every valid address that can be formed by inserting three dots into `s` (without
reordering or removing digits), in any order.
""",
    constraints="""
- `1 <= s.length <= 20`
- `s` consists of digits
""",
    signature=function("restoreIpAddresses", [("s", "string")], "string[]"),
    reference=_restore_ip,
    brute=_restore_ip_brute,
    compare="unordered",
    examples=[Example(["25525511135"], "\"255.255.11.135\" and \"255.255.111.35\"."), Example(["0000"]), Example(["101023"])],
    edge_cases=[["1"], ["1111"], ["010010"], ["255255255255"], ["256256256256"], ["11111111111111111111"]],
    generator=lambda rng: [word(rng, rng.randint(1, 13), rng.choice(["0123456789", "012", "25"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Flood Fill


def _flood_fill(image: list[list[int]], sr: int, sc: int, color: int) -> list[list[int]]:
    start = image[sr][sc]
    if start == color:
        return image
    stack = [(sr, sc)]
    while stack:
        i, j = stack.pop()
        if 0 <= i < len(image) and 0 <= j < len(image[0]) and image[i][j] == start:
            image[i][j] = color
            stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
    return image


def _flood_fill_brute(image: list[list[int]], sr: int, sc: int, color: int) -> list[list[int]]:
    start, region, frontier = image[sr][sc], {(sr, sc)}, deque([(sr, sc)])
    while frontier:
        i, j = frontier.popleft()
        for x, y in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= x < len(image) and 0 <= y < len(image[0]) and (x, y) not in region and image[x][y] == start:
                region.add((x, y))
                frontier.append((x, y))
    return [[color if (i, j) in region else v for j, v in enumerate(row)] for i, row in enumerate(image)]


def _flood_gen(rng):
    m, n = pick_n(rng, 1, 6, big=50), pick_n(rng, 1, 6, big=50)
    image = [ints(rng, n, 0, 2) for _ in range(m)]
    return [image, rng.randrange(m), rng.randrange(n), rng.randint(0, 3)]


FLOOD_FILL = ProblemSource(
    title="Flood Fill",
    statement="""
`image` is a grid of pixel colours. Starting from pixel `(sr, sc)`, repaint it and every pixel connected to it horizontally or vertically
through pixels of the **same original colour** with `color`. Return the modified image.
""",
    constraints="""
- `1 <= m, n <= 50`
- `0 <= image[i][j], color < 2^16`
- `0 <= sr < m`, `0 <= sc < n`
""",
    signature=function("floodFill", [("image", "int[][]"), ("sr", "int"), ("sc", "int"), ("color", "int")], "int[][]"),
    reference=_flood_fill,
    brute=_flood_fill_brute,
    examples=[Example([[[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2], "The bottom-right 1 isn't connected."), Example([[[0, 0, 0], [0, 0, 0]], 0, 0, 0], "Same colour: nothing changes.")],
    edge_cases=[[[[5]], 0, 0, 7], [[[1, 2], [2, 1]], 0, 0, 3]],
    generator=_flood_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Moves to Spread Stones Over Grid


def _minimum_moves_stones(grid: list[list[int]]) -> int:
    empty = [(i, j) for i in range(3) for j in range(3) if grid[i][j] == 0]
    extra = [(i, j) for i in range(3) for j in range(3) for _ in range(grid[i][j] - 1)]
    return min(
        sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(empty, perm, strict=True)) for perm in itertools.permutations(extra)
    )


def _stones_brute(grid: list[list[int]]) -> int:
    start = tuple(v for row in grid for v in row)
    goal = (1,) * 9
    seen, frontier = {start}, deque([(start, 0)])
    while frontier:
        state, d = frontier.popleft()
        if state == goal:
            return d
        for cell in range(9):
            if state[cell] > 1:
                i, j = divmod(cell, 3)
                for x, y in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                    if 0 <= x < 3 and 0 <= y < 3:
                        nxt = list(state)
                        nxt[cell] -= 1
                        nxt[x * 3 + y] += 1
                        t = tuple(nxt)
                        if t not in seen:
                            seen.add(t)
                            frontier.append((t, d + 1))
    raise AssertionError


def _stones_gen(rng):
    cells = [0] * 9
    for _ in range(9):
        cells[rng.randrange(9)] += 1
    return [[cells[0:3], cells[3:6], cells[6:9]]]


SPREAD_STONES = ProblemSource(
    title="Minimum Moves to Spread Stones Over Grid",
    statement="""
A `3 x 3` grid holds exactly 9 stones in total; `grid[i][j]` is the number of stones in a cell (a cell may hold several). In one move you may
take a single stone and move it to an adjacent cell (sharing a side). Return the minimum number of moves needed so that every cell holds
exactly one stone.
""",
    constraints="""
- `grid` is `3 x 3`
- `0 <= grid[i][j] <= 9`, and the values add up to 9
""",
    signature=function("minimumMoves", [("grid", "int[][]")], "int"),
    reference=_minimum_moves_stones,
    brute=_stones_brute,
    examples=[Example([[[1, 1, 0], [1, 1, 1], [1, 2, 1]]], "Moving one stone from (2,1) up and right takes 3 moves."), Example([[[1, 3, 0], [1, 0, 0], [1, 0, 3]]])],
    edge_cases=[[[[1, 1, 1], [1, 1, 1], [1, 1, 1]]], [[[9, 0, 0], [0, 0, 0], [0, 0, 0]]], [[[0, 0, 0], [0, 9, 0], [0, 0, 0]]]],
    generator=_stones_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Sudoku Solver


def _candidates(board: list[list[str]], i: int, j: int) -> list[str]:
    used = set(board[i]) | {board[r][j] for r in range(9)}
    bi, bj = 3 * (i // 3), 3 * (j // 3)
    used |= {board[r][c] for r in range(bi, bi + 3) for c in range(bj, bj + 3)}
    return [d for d in "123456789" if d not in used]


def _solve_sudoku(board: list[list[str]]) -> None:
    empties = [(i, j) for i in range(9) for j in range(9) if board[i][j] == "."]

    def solve(k: int) -> bool:
        if k == len(empties):
            return True
        i, j = empties[k]
        for d in _candidates(board, i, j):
            board[i][j] = d
            if solve(k + 1):
                return True
        board[i][j] = "."
        return False

    solve(0)


def _count_solutions(board: list[list[str]], limit: int = 2) -> int:
    best = None
    for i in range(9):
        for j in range(9):
            if board[i][j] == ".":
                options = _candidates(board, i, j)
                if best is None or len(options) < len(best[2]):
                    best = (i, j, options)
    if best is None:
        return 1
    i, j, options = best
    total = 0
    for d in options:
        board[i][j] = d
        total += _count_solutions(board, limit)
        board[i][j] = "."
        if total >= limit:
            break
    return total


def _sudoku_brute(board: list[list[str]]) -> None:
    # Most-constrained-cell search (different order from the reference).
    def solve() -> bool:
        best = None
        for i in range(9):
            for j in range(9):
                if board[i][j] == ".":
                    options = _candidates(board, i, j)
                    if best is None or len(options) < len(best[2]):
                        best = (i, j, options)
        if best is None:
            return True
        i, j, options = best
        for d in options:
            board[i][j] = d
            if solve():
                return True
        board[i][j] = "."
        return False

    solve()


def _sudoku_gen(rng):
    board = [["."] * 9 for _ in range(9)]
    for box in range(3):
        digits = list("123456789")
        rng.shuffle(digits)
        for k, d in enumerate(digits):
            board[3 * box + k // 3][3 * box + k % 3] = d
    _sudoku_brute(board)
    cells = [(i, j) for i in range(9) for j in range(9)]
    rng.shuffle(cells)
    removed = 0
    for i, j in cells:
        if removed >= rng.randint(40, 55):
            break
        keep = board[i][j]
        board[i][j] = "."
        if _count_solutions(board) != 1:
            board[i][j] = keep
        else:
            removed += 1
    return [board]


_EXAMPLE_SUDOKU = [
    ["5", "3", ".", ".", "7", ".", ".", ".", "."],
    ["6", ".", ".", "1", "9", "5", ".", ".", "."],
    [".", "9", "8", ".", ".", ".", ".", "6", "."],
    ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
    ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
    ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
    [".", "6", ".", ".", ".", ".", "2", "8", "."],
    [".", ".", ".", "4", "1", "9", ".", ".", "5"],
    [".", ".", ".", ".", "8", ".", ".", "7", "9"],
]

_SECOND_SUDOKU = [
    [".", ".", "4", "6", "7", ".", "9", "1", "2"],
    ["6", ".", "2", "1", ".", "5", ".", ".", "8"],
    ["1", "9", ".", ".", ".", "2", ".", "6", "7"],
    ["8", ".", ".", "7", ".", ".", ".", "2", "3"],
    ["4", "2", ".", ".", "5", "3", ".", ".", "."],
    ["7", "1", ".", ".", ".", "4", "8", "5", "6"],
    ["9", "6", "1", "5", "3", "7", "2", ".", "4"],
    ["2", "8", "7", "4", "1", "9", ".", "3", "."],
    ["3", ".", "5", "2", "8", "6", ".", "7", "."],
]

SUDOKU_SOLVER = ProblemSource(
    title="Sudoku Solver",
    statement="""
Fill in the empty cells (`'.'`) of the `9 x 9` Sudoku `board` **in place** so that every row, every column and every one of the nine `3 x 3`
boxes contains each digit `1`-`9` exactly once. Every test puzzle has exactly one solution.
""",
    constraints="""
- `board` is `9 x 9`; each cell is a digit or `'.'`
- the puzzle has exactly one solution
""",
    signature=function("solveSudoku", [("board", "char[][]")], "void", mutates="board"),
    reference=_solve_sudoku,
    brute=_sudoku_brute,
    examples=[Example([_EXAMPLE_SUDOKU], "A classic puzzle; the filled board is the only solution."), Example([_SECOND_SUDOKU], "An easier puzzle with 30 blanks.")],
    generator=_sudoku_gen,
    random_count=5,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Matchsticks to Square


def _makesquare(matchsticks: list[int]) -> bool:
    total = sum(matchsticks)
    if total % 4:
        return False
    side = total // 4
    sticks = sorted(matchsticks, reverse=True)
    if sticks[0] > side:
        return False
    sides = [0] * 4

    def place(i: int) -> bool:
        if i == len(sticks):
            return True
        for k in range(4):
            if sides[k] + sticks[i] <= side and (k == 0 or sides[k] != sides[k - 1]):
                sides[k] += sticks[i]
                if place(i + 1):
                    return True
                sides[k] -= sticks[i]
        return False

    return place(0)


def _makesquare_brute(matchsticks: list[int]) -> bool:
    total = sum(matchsticks)
    if total % 4:
        return False
    side = total // 4
    for assignment in itertools.product(range(4), repeat=len(matchsticks)):
        sums = [0] * 4
        for stick, k in zip(matchsticks, assignment, strict=True):
            sums[k] += stick
        if sums == [side] * 4:
            return True
    return False


MATCHSTICKS = ProblemSource(
    title="Matchsticks to Square",
    statement="""
`matchsticks[i]` is the length of stick `i`. Using **every** stick exactly once, without breaking any, can you form a square? Sticks may be
joined end to end along a side. Return `true` if a square can be made.
""",
    constraints="""
- `1 <= matchsticks.length <= 15`
- `1 <= matchsticks[i] <= 10^8`
""",
    signature=function("makesquare", [("matchsticks", "int[]")], "bool"),
    reference=_makesquare,
    brute=lambda matchsticks: _makesquare_brute(matchsticks) if len(matchsticks) <= 8 else NotImplemented,
    examples=[Example([[1, 1, 2, 2, 2]], "Sides 2, 2, 2 and 1 + 1."), Example([[3, 3, 3, 3, 4]])],
    edge_cases=[[[1]], [[1, 1, 1, 1]], [[5, 5, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3]], [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 102]]],
    generator=lambda rng: [ints(rng, rng.randint(1, rng.choice([8, 15])), 1, rng.choice([4, 8]))],
    random_count=9,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Binary Watch


def _read_binary_watch(turnedOn: int) -> list[str]:
    return [f"{h}:{m:02d}" for h in range(12) for m in range(60) if bin(h).count("1") + bin(m).count("1") == turnedOn]


def _watch_brute(turnedOn: int) -> list[str]:
    out = []
    for leds in itertools.combinations(range(10), turnedOn):
        hours = sum(1 << i for i in leds if i < 4)
        minutes = sum(1 << (i - 4) for i in leds if i >= 4)
        if hours < 12 and minutes < 60:
            out.append(f"{hours}:{minutes:02d}")
    return out


BINARY_WATCH = ProblemSource(
    title="Binary Watch",
    statement="""
A binary watch has 4 LEDs for the hour (0-11) and 6 LEDs for the minute (0-59); each LED is one bit of the value. Given how many LEDs are
on, `turnedOn`, return every time the watch could be showing, in any order. Hours have no leading zero (`"1:00"`, not `"01:00"`) and
minutes always have two digits (`"10:02"`, not `"10:2"`).
""",
    constraints="""
- `0 <= turnedOn <= 10`
""",
    signature=function("readBinaryWatch", [("turnedOn", "int")], "string[]"),
    reference=_read_binary_watch,
    brute=_watch_brute,
    compare="unordered",
    examples=[Example([1]), Example([9], "No valid time uses 9 LEDs.")],
    edge_cases=[[0], [2], [3], [8], [10]],
    generator=lambda rng: [rng.randint(0, 10)],
    random_count=3,
)


# ---------------------------------------------------------------- Optimal Account Balancing


def _min_transfers(transactions: list[list[int]]) -> int:
    balance: dict[int, int] = {}
    for a, b, amount in transactions:
        balance[a] = balance.get(a, 0) - amount
        balance[b] = balance.get(b, 0) + amount
    debts = [v for v in balance.values() if v]

    def settle(i: int) -> int:
        while i < len(debts) and debts[i] == 0:
            i += 1
        if i == len(debts):
            return 0
        best = float("inf")
        for j in range(i + 1, len(debts)):
            if debts[i] * debts[j] < 0:
                debts[j] += debts[i]
                best = min(best, 1 + settle(i + 1))
                debts[j] -= debts[i]
        return int(best)

    return settle(0)


def _transfers_brute(transactions: list[list[int]]) -> int:
    balance: dict[int, int] = {}
    for a, b, amount in transactions:
        balance[a] = balance.get(a, 0) - amount
        balance[b] = balance.get(b, 0) + amount
    debts = [v for v in balance.values() if v]
    n = len(debts)
    sums = [sum(debts[i] for i in range(n) if mask >> i & 1) for mask in range(1 << n)]
    groups = [0] * (1 << n)  # max number of zero-sum groups the mask splits into
    for mask in range(1, 1 << n):
        best = 0
        for i in range(n):
            if mask >> i & 1:
                best = max(best, groups[mask ^ (1 << i)])
        groups[mask] = best + (sums[mask] == 0)
    return n - groups[(1 << n) - 1]


def _transactions_gen(rng):
    people = rng.randint(2, rng.choice([4, 9]))
    out = []
    for _ in range(rng.randint(1, 8)):
        a, b = rng.sample(range(people), 2)
        out.append([a, b, rng.randint(1, rng.choice([5, 100]))])
    return [out]


ACCOUNT_BALANCING = ProblemSource(
    title="Optimal Account Balancing",
    statement="""
`transactions[i] = [from_i, to_i, amount_i]` means person `from_i` gave `amount_i` dollars to person `to_i`. Return the minimum number of
new transactions needed so that everyone ends up even (each person has received exactly as much as they gave).
""",
    constraints="""
- `1 <= transactions.length <= 8`
- `0 <= from_i, to_i < 12`, `from_i != to_i`
- `1 <= amount_i <= 100`
""",
    signature=function("minTransfers", [("transactions", "int[][]")], "int"),
    reference=_min_transfers,
    brute=_transfers_brute,
    examples=[Example([[[0, 1, 10], [2, 0, 5]]], "Person 1 pays 5 to person 0 and 5 to person 2."), Example([[[0, 1, 10], [1, 0, 1], [1, 2, 5], [2, 0, 5]]], "One transfer: person 1 pays 4 to person 0.")],
    edge_cases=[[[[0, 1, 5], [1, 0, 5]]], [[[0, 1, 1], [1, 2, 1], [2, 3, 1]]]],
    generator=_transactions_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Split a String Into the Max Number of Unique Substrings


def _max_unique_split(s: str) -> int:
    best = 0

    def split(i: int, used: set[str]) -> None:
        nonlocal best
        if len(used) + (len(s) - i) <= best:
            return
        if i == len(s):
            best = max(best, len(used))
            return
        for j in range(i + 1, len(s) + 1):
            part = s[i:j]
            if part not in used:
                used.add(part)
                split(j, used)
                used.remove(part)

    split(0, set())
    return best


def _max_unique_brute(s: str) -> int:
    best = 0
    for mask in range(1 << (len(s) - 1)):
        parts, start = [], 0
        for i in range(len(s) - 1):
            if mask >> i & 1:
                parts.append(s[start : i + 1])
                start = i + 1
        parts.append(s[start:])
        if len(set(parts)) == len(parts):
            best = max(best, len(parts))
    return best


MAX_UNIQUE_SPLIT = ProblemSource(
    title="Split a String Into the Max Number of Unique Substrings",
    statement="""
Split `s` into non-empty substrings that concatenate back to `s`, with all the substrings **distinct**. Return the largest possible number
of substrings.
""",
    constraints="""
- `1 <= s.length <= 16`
- `s` consists of lowercase English letters
""",
    signature=function("maxUniqueSplit", [("s", "string")], "int"),
    reference=_max_unique_split,
    brute=_max_unique_brute,
    examples=[Example(["ababccc"], "a, b, ab, c, cc: five pieces."), Example(["aba"], "a, ba."), Example(["aa"], "\"aa\" can't be split into distinct pieces.")],
    edge_cases=[["a"], ["ab"], ["aaaa"], ["wwwzfvedwfvhsww"]],
    generator=lambda rng: [word(rng, rng.randint(1, 14), rng.choice(["ab", "abc", "abcdefghij"]))],
    random_count=8,
    time_limit_ms=1500,
)


PROBLEMS = [
    WORD_SEARCH,
    HOUSE_ROBBER_III,
    N_QUEENS_II,
    RESTORE_IP,
    FLOOD_FILL,
    SPREAD_STONES,
    SUDOKU_SOLVER,
    MATCHSTICKS,
    BINARY_WATCH,
    ACCOUNT_BALANCING,
    MAX_UNIQUE_SPLIT,
]
