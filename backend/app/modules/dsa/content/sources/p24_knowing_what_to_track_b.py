"""Pattern 24: Knowing What to Track (part 2 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import random
from collections import Counter

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sample, word

PATTERN_NUMBER = 24


# ---------------------------------------------------------------- Find Words That Can Be Formed by Characters


def _count_characters(words: list[str], chars: str) -> int:
    available = Counter(chars)
    return sum(len(w) for w in words if not Counter(w) - available)


def _formed_brute(words: list[str], chars: str) -> int:
    total = 0
    for w in words:
        pool = list(chars)
        ok = True
        for ch in w:
            if ch in pool:
                pool.remove(ch)
            else:
                ok = False
                break
        total += len(w) if ok else 0
    return total


FORMED_BY_CHARACTERS = ProblemSource(
    title="Find Words That Can Be Formed by Characters",
    statement="""
A word is *good* if it can be spelled with the letters of `chars`, using each letter of `chars` at most once (independently for every word).
Return the total length of all good words in `words`.
""",
    constraints="""
- `1 <= words.length <= 1000`
- `1 <= words[i].length, chars.length <= 100`, lowercase letters
""",
    signature=function("countCharacters", [("words", "string[]"), ("chars", "string")], "int"),
    reference=_count_characters,
    brute=_formed_brute,
    examples=[Example([["cat", "bt", "hat", "tree"], "atach"], "\"cat\" and \"hat\": 3 + 3."), Example([["hello", "world", "leetcode"], "welldonehoneyr"])],
    edge_cases=[[["a"], "a"], [["aa"], "a"], [["abc"], "cba"]],
    generator=lambda rng: [[word(rng, rng.randint(1, 5), "abcd") for _ in range(rng.randint(1, 12))], word(rng, rng.randint(1, 10), "abcd")],
    random_count=8,
)


# ---------------------------------------------------------------- Check if One String Swap Can Make Strings Equal


def _are_almost_equal(s1: str, s2: str) -> bool:
    diff = [i for i in range(len(s1)) if s1[i] != s2[i]]
    return not diff or (len(diff) == 2 and s1[diff[0]] == s2[diff[1]] and s1[diff[1]] == s2[diff[0]])


def _one_swap_brute(s1: str, s2: str) -> bool:
    if s1 == s2:
        return True
    for i, j in itertools.combinations(range(len(s1)), 2):
        chars = list(s1)
        chars[i], chars[j] = chars[j], chars[i]
        if "".join(chars) == s2:
            return True
    return False


def _one_swap_gen(rng: random.Random) -> list:
    s1 = word(rng, rng.randint(1, 12), "abc")
    chars = list(s1)
    for _ in range(rng.choice([0, 1, 1, 2, 3])):
        i, j = rng.randrange(len(chars)), rng.randrange(len(chars))
        chars[i], chars[j] = chars[j], chars[i]
    if rng.random() < 0.2:
        chars[rng.randrange(len(chars))] = "z"  # not even a permutation
    return [s1, "".join(chars)]


ONE_SWAP = ProblemSource(
    title="Check if One String Swap Can Make Strings Equal",
    statement="""
`s1` and `s2` have equal length. A *string swap* exchanges the characters at two positions of one string. Return `true` if the strings can be
made equal by performing **at most one** swap on exactly one of them.
""",
    constraints="""
- `1 <= s1.length == s2.length <= 100`
- lowercase English letters
""",
    signature=function("areAlmostEqual", [("s1", "string"), ("s2", "string")], "bool"),
    reference=_are_almost_equal,
    brute=_one_swap_brute,
    examples=[Example(["bank", "kanb"]), Example(["attack", "defend"]), Example(["kelb", "kelb"], "No swap needed.")],
    edge_cases=[["a", "a"], ["ab", "ba"], ["abc", "bca"], ["aa", "ac"]],
    generator=_one_swap_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find Pivot Index


def _pivot_index(nums: list[int]) -> int:
    total, left = sum(nums), 0
    for i, x in enumerate(nums):
        if left == total - left - x:
            return i
        left += x
    return -1


PIVOT_INDEX = ProblemSource(
    title="Find Pivot Index",
    statement="""
The *pivot index* is where the sum of all elements strictly to its left equals the sum of all elements strictly to its right (an empty side sums
to `0`). Return the leftmost pivot index, or `-1` if none exists.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-1000 <= nums[i] <= 1000`
""",
    signature=function("pivotIndex", [("nums", "int[]")], "int"),
    reference=_pivot_index,
    brute=lambda nums: next((i for i in range(len(nums)) if sum(nums[:i]) == sum(nums[i + 1 :])), -1),
    brute_input_limit=3000,
    examples=[Example([[1, 7, 3, 6, 5, 6]], "1 + 7 + 3 = 5 + 6."), Example([[1, 2, 3]]), Example([[2, 1, -1]], "Index 0: left is empty, right sums to 0.")],
    edge_cases=[[[0]], [[5]], [[0, 0, 0]], [[-1, -1, 0, 1, 1, 0]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 12, big=3000), -rng.choice([2, 1000]), rng.choice([2, 1000]))],
    random_count=10,
)


# ---------------------------------------------------------------- Sort Array by Increasing Frequency


def _frequency_sort(nums: list[int]) -> list[int]:
    counts = Counter(nums)
    return sorted(nums, key=lambda x: (counts[x], -x))


def _frequency_brute(nums: list[int]) -> list[int]:
    out: list[int] = []
    remaining = list(nums)
    while remaining:
        best = min(set(remaining), key=lambda x: (remaining.count(x), -x))
        out += [best] * remaining.count(best)
        remaining = [x for x in remaining if x != best]
    return out


FREQUENCY_SORT = ProblemSource(
    title="Sort Array by Increasing Frequency",
    statement="""
Sort `nums` by how often each value occurs, least frequent first. Values that occur equally often are sorted in **decreasing** order. Return the
sorted array.
""",
    constraints="""
- `1 <= nums.length <= 100`
- `-100 <= nums[i] <= 100`
""",
    signature=function("frequencySort", [("nums", "int[]")], "int[]"),
    reference=_frequency_sort,
    brute=_frequency_brute,
    examples=[Example([[1, 1, 2, 2, 2, 3]], "[3,1,1,2,2,2]."), Example([[2, 3, 1, 3, 2]], "2 and 3 both occur twice: 3 comes first."), Example([[-1, 1, -6, 4, 5, -6, 1, 4, 1]])],
    edge_cases=[[[7]], [[1, 2, 3]], [[5, 5, -5, -5]]],
    generator=lambda rng: [ints(rng, rng.randint(1, 100), -(hi := rng.choice([4, 100])), hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Concatenation of Array


def _get_concatenation(nums: list[int]) -> list[int]:
    n = len(nums)
    out = [0] * (2 * n)
    for i, x in enumerate(nums):
        out[i] = out[i + n] = x
    return out


CONCATENATION = ProblemSource(
    title="Concatenation of Array",
    statement="""
Return an array `ans` of length `2n` with `ans[i] == nums[i]` and `ans[i + n] == nums[i]` for every `0 <= i < n` — that is, `nums` followed by
itself.
""",
    constraints="""
- `1 <= n <= 1000`
- `1 <= nums[i] <= 1000`
""",
    signature=function("getConcatenation", [("nums", "int[]")], "int[]"),
    reference=_get_concatenation,
    brute=lambda nums: nums + nums,
    examples=[Example([[1, 2, 1]]), Example([[1, 3, 2, 1]])],
    edge_cases=[[[1000]]],
    generator=lambda rng: [ints(rng, rng.randint(1, rng.choice([10, 1000])), 1, 1000)],
    random_count=6,
)


# ---------------------------------------------------------------- Zigzag Conversion


def _convert(s: str, numRows: int) -> str:
    if numRows == 1:
        return s
    rows = [""] * numRows
    row, step = 0, 1
    for ch in s:
        rows[row] += ch
        if row == 0:
            step = 1
        elif row == numRows - 1:
            step = -1
        row += step
    return "".join(rows)


def _zigzag_brute(s: str, numRows: int) -> str:
    if numRows == 1:
        return s
    cycle = 2 * numRows - 2
    return "".join(ch for r in range(numRows) for i, ch in enumerate(s) if i % cycle in (r, cycle - r))


ZIGZAG_CONVERSION = ProblemSource(
    title="Zigzag Conversion",
    statement="""
Write `s` in a zigzag over `numRows` rows — down the rows, then diagonally back up, and so on — and then read it row by row. For example
`"PAYPALISHIRING"` on 3 rows is written as

```
P   A   H   N
A P L S I I G
Y   I   R
```

and read as `"PAHNAPLSIIGYIR"`. Return the row-by-row reading.
""",
    constraints="""
- `1 <= s.length <= 1000`
- `1 <= numRows <= 1000`
- English letters, `,` and `.`
""",
    signature=function("convert", [("s", "string"), ("numRows", "int")], "string"),
    reference=_convert,
    brute=_zigzag_brute,
    examples=[Example(["PAYPALISHIRING", 3]), Example(["PAYPALISHIRING", 4], "\"PINALSIGYAHRPI\"."), Example(["A", 1])],
    edge_cases=[["AB", 1], ["AB", 5], ["ABCDE", 2]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([20, 1000])), "abcdefghXYZ,."), rng.randint(1, rng.choice([6, 1000]))],
    random_count=8,
)


# ---------------------------------------------------------------- Zero Array Transformation I


def _is_zero_array(nums: list[int], queries: list[list[int]]) -> bool:
    delta = [0] * (len(nums) + 1)
    for left, right in queries:
        delta[left] += 1
        delta[right + 1] -= 1
    coverage = 0
    for i, x in enumerate(nums):
        coverage += delta[i]
        if coverage < x:
            return False
    return True


def _zero_array_brute(nums: list[int], queries: list[list[int]]) -> bool:
    if len(nums) * len(queries) > 20000:
        return NotImplemented
    values = list(nums)
    for left, right in queries:
        for i in range(left, right + 1):
            values[i] = max(0, values[i] - 1)
    return not any(values)


def _zero_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 10, big=10**4)
    queries = [sorted([rng.randrange(n), rng.randrange(n)]) for _ in range(rng.randint(1, rng.choice([8, 500])))]
    cover = [sum(a <= i <= b for a, b in queries) for i in range(n)] if n * len(queries) <= 200_000 else [len(queries)] * n
    nums = [max(0, c - rng.choice([0, 0, 1, -1])) for c in cover]
    return [nums, queries]


ZERO_ARRAY_I = ProblemSource(
    title="Zero Array Transformation I",
    statement="""
Process `queries` in order. For `queries[i] = [l, r]`, choose any subset of the indices in `[l, r]` and decrement each chosen element by `1`.
Return `true` if some choice of subsets turns `nums` into all zeros.
""",
    constraints="""
- `1 <= nums.length <= 10^5`, `0 <= nums[i] <= 10^5`
- `1 <= queries.length <= 10^5`, `0 <= l <= r < nums.length`
""",
    signature=function("isZeroArray", [("nums", "int[]"), ("queries", "int[][]")], "bool"),
    reference=_is_zero_array,
    brute=_zero_array_brute,
    examples=[Example([[1, 0, 1], [[0, 2]]]), Example([[4, 3, 2, 1], [[1, 3], [0, 2]]], "Index 0 is covered only once but needs 4.")],
    edge_cases=[[[0], [[0, 0]]], [[2], [[0, 0]]], [[1, 1], [[0, 0], [1, 1]]]],
    generator=_zero_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Count Binary Substrings


def _count_binary_substrings(s: str) -> int:
    runs = [len(list(group)) for _, group in itertools.groupby(s)]
    return sum(min(a, b) for a, b in itertools.pairwise(runs))


def _binary_substrings_brute(s: str) -> int:
    n = len(s)
    count = 0
    for i in range(n):
        for length in range(2, n - i + 1, 2):
            half = length // 2
            left, right = s[i : i + half], s[i + half : i + length]
            count += len(set(left)) == 1 and len(set(right)) == 1 and left[0] != right[0]
    return count


def _runs_gen(rng: random.Random) -> list:
    first = rng.choice("01")
    runs = rng.randint(1, rng.choice([10, 3000]))
    return ["".join(("01" if first == "0" else "10")[k % 2] * rng.randint(1, 4) for k in range(runs))]


COUNT_BINARY_SUBSTRINGS = ProblemSource(
    title="Count Binary Substrings",
    statement="""
Count the non-empty substrings of the binary string `s` that have the same number of `0`s and `1`s, with all the `0`s grouped together and all
the `1`s grouped together (like `"0011"` or `"10"`). Substrings at different positions count separately.
""",
    constraints="""
- `1 <= s.length <= 10^5`
- `s[i]` is `0` or `1`
""",
    signature=function("countBinarySubstrings", [("s", "string")], "int"),
    reference=_count_binary_substrings,
    brute=lambda s: _binary_substrings_brute(s) if len(s) <= 120 else NotImplemented,
    examples=[Example(["00110011"], "0011, 01, 1100, 10, 0011, 01."), Example(["10101"])],
    edge_cases=[["0"], ["01"], ["000111"], ["0001"]],
    generator=_runs_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find the Celebrity


def _find_celebrity(graph: list[list[int]]) -> int:
    n = len(graph)
    candidate = 0
    for i in range(1, n):  # whoever knows someone can't be the celebrity
        if graph[candidate][i]:
            candidate = i
    if all(i == candidate or (graph[i][candidate] and not graph[candidate][i]) for i in range(n)):
        return candidate
    return -1


def _celebrity_brute(graph: list[list[int]]) -> int:
    n = len(graph)
    found = [c for c in range(n) if all(graph[i][c] for i in range(n) if i != c) and not any(graph[c][i] for i in range(n) if i != c)]
    return found[0] if found else -1


def _celebrity_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 8, big=100)
    graph = [[1 if i == j else int(rng.random() < 0.5) for j in range(n)] for i in range(n)]
    if rng.random() < 0.8:
        c = rng.randrange(n)
        for i in range(n):
            if i != c:
                graph[i][c], graph[c][i] = 1, 0
        if rng.random() < 0.25:
            graph[rng.choice([i for i in range(n) if i != c])][c] = 0  # spoil it
    return [graph]


FIND_CELEBRITY = ProblemSource(
    title="Find the Celebrity",
    statement="""
At a party of `n` people (labelled `0` to `n - 1`), a *celebrity* is someone whom everyone else knows but who knows none of them.

*Adapted I/O:* the original problem only lets you ask `knows(a, b)`. Here you receive the answers as a matrix: `graph[a][b] == 1` means `a` knows
`b` (everyone knows themselves). Return the celebrity's label, or `-1` if there is none. Aim to look at only `O(n)` entries of `graph`.
""",
    constraints="""
- `2 <= n <= 100`
- `graph[i][j]` is `0` or `1`; `graph[i][i] == 1`
""",
    signature=function("findCelebrity", [("graph", "int[][]")], "int"),
    reference=_find_celebrity,
    brute=_celebrity_brute,
    is_variant=True,
    examples=[Example([[[1, 1, 0], [0, 1, 0], [1, 1, 1]]], "Everyone knows 1, and 1 knows nobody else."), Example([[[1, 0, 1], [1, 1, 0], [0, 1, 1]]])],
    edge_cases=[[[[1, 1], [0, 1]]], [[[1, 1], [1, 1]]], [[[1, 0], [0, 1]]]],
    generator=_celebrity_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Operations to Write the Letter Y on a Grid


def _y_cells(n: int) -> set[tuple[int, int]]:
    mid = n // 2
    cells = {(i, i) for i in range(mid + 1)} | {(i, n - 1 - i) for i in range(mid + 1)}
    return cells | {(i, mid) for i in range(mid, n)}


def _minimum_operations_to_write_y(grid: list[list[int]]) -> int:
    n = len(grid)
    y = _y_cells(n)
    inside, outside = Counter(), Counter()
    for i in range(n):
        for j in range(n):
            (inside if (i, j) in y else outside)[grid[i][j]] += 1
    keep = max(inside[a] + outside[b] for a in range(3) for b in range(3) if a != b)
    return n * n - keep


def _write_y_brute(grid: list[list[int]]) -> int:
    n = len(grid)
    mid = n // 2
    best = None
    for a in range(3):
        for b in range(3):
            if a == b:
                continue
            cost = 0
            for i in range(n):
                for j in range(n):
                    on_y = (i <= mid and (j == i or j == n - 1 - i)) or (i >= mid and j == mid)
                    cost += grid[i][j] != (a if on_y else b)
            best = cost if best is None else min(best, cost)
    return best


WRITE_Y = ProblemSource(
    title="Minimum Operations to Write the Letter Y on a Grid",
    statement="""
`grid` is `n x n` with `n` odd, and every cell holds `0`, `1` or `2`. The cells of the letter **Y** are the two diagonals from the top corners
down to the centre, plus the vertical line from the centre down to the bottom edge. The Y is *written* when every Y cell holds the same value,
every other cell holds the same value, and those two values differ. One operation changes a cell to any of `0`, `1` or `2`. Return the minimum
number of operations to write the Y.
""",
    constraints="""
- `3 <= n <= 49`, `n` odd
- `grid[i][j]` is `0`, `1` or `2`
""",
    signature=function("minimumOperationsToWriteY", [("grid", "int[][]")], "int"),
    reference=_minimum_operations_to_write_y,
    brute=_write_y_brute,
    examples=[Example([[[1, 2, 2], [1, 1, 0], [0, 1, 0]]]), Example([[[0, 1, 0, 1, 0], [2, 1, 0, 1, 2], [2, 2, 2, 0, 1], [2, 2, 2, 2, 2], [2, 1, 2, 2, 2]]])],
    edge_cases=[[[[0, 0, 0], [0, 0, 0], [0, 0, 0]]], [[[1, 0, 1], [0, 1, 0], [0, 1, 0]]]],
    generator=lambda rng: [[[rng.randint(0, 2) for _ in range(n)] for _ in range(n)] for n in [2 * rng.randint(1, rng.choice([3, 24])) + 1]],
    random_count=8,
)


# ---------------------------------------------------------------- Fruits Into Baskets II


def _num_of_unplaced_fruits(fruits: list[int], baskets: list[int]) -> int:
    used = [False] * len(baskets)
    unplaced = 0
    for f in fruits:
        for j, capacity in enumerate(baskets):
            if not used[j] and capacity >= f:
                used[j] = True
                break
        else:
            unplaced += 1
    return unplaced


def _unplaced_brute(fruits: list[int], baskets: list[int]) -> int:
    free = list(enumerate(baskets))
    unplaced = 0
    for f in fruits:
        fits = [pair for pair in free if pair[1] >= f]
        if fits:
            free.remove(min(fits))  # the leftmost fitting basket
        else:
            unplaced += 1
    return unplaced


FRUITS_BASKETS_II = ProblemSource(
    title="Fruits Into Baskets II",
    statement="""
`fruits[i]` is the quantity of the `i`-th fruit type and `baskets[j]` the capacity of the `j`-th basket (both arrays have length `n`). Place
fruit types from left to right: each goes into the **leftmost** unused basket whose capacity is at least its quantity; if none fits, it stays
unplaced. Each basket holds one fruit type. Return the number of unplaced fruit types.
""",
    constraints="""
- `1 <= n <= 100`
- `1 <= fruits[i], baskets[i] <= 1000`
""",
    signature=function("numOfUnplacedFruits", [("fruits", "int[]"), ("baskets", "int[]")], "int"),
    reference=_num_of_unplaced_fruits,
    brute=_unplaced_brute,
    examples=[Example([[4, 2, 5], [3, 5, 4]], "4 -> basket 1, 2 -> basket 0, 5 has no basket left."), Example([[3, 6, 1], [6, 4, 7]])],
    edge_cases=[[[1], [1]], [[2], [1]], [[1, 1, 1], [1, 1, 1]]],
    generator=lambda rng: [ints(rng, (n := rng.randint(1, rng.choice([8, 100]))), 1, (hi := rng.choice([10, 1000]))), ints(rng, n, 1, hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Good Pairs


def _num_identical_pairs(nums: list[int]) -> int:
    return sum(c * (c - 1) // 2 for c in Counter(nums).values())


GOOD_PAIRS = ProblemSource(
    title="Number of Good Pairs",
    statement="""
A pair of indices `(i, j)` is *good* if `nums[i] == nums[j]` and `i < j`. Return the number of good pairs.
""",
    constraints="""
- `1 <= nums.length <= 100`
- `1 <= nums[i] <= 100`
""",
    signature=function("numIdenticalPairs", [("nums", "int[]")], "int"),
    reference=_num_identical_pairs,
    brute=lambda nums: sum(a == b for a, b in itertools.combinations(nums, 2)),
    examples=[Example([[1, 2, 3, 1, 1, 3]]), Example([[1, 1, 1, 1]], "Every pair: 6."), Example([[1, 2, 3]])],
    edge_cases=[[[5]], [[5, 5]]],
    generator=lambda rng: [ints(rng, rng.randint(1, 100), 1, rng.choice([3, 100]))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Product of Three Numbers


def _maximum_product(nums: list[int]) -> int:
    low = sorted(nums)
    return max(low[-1] * low[-2] * low[-3], low[0] * low[1] * low[-1])


MAX_PRODUCT_THREE = ProblemSource(
    title="Maximum Product of Three Numbers",
    statement="""
Return the maximum product of three numbers taken from three different positions of `nums`.
""",
    constraints="""
- `3 <= nums.length <= 10^4`
- `-1000 <= nums[i] <= 1000`
""",
    signature=function("maximumProduct", [("nums", "int[]")], "int"),
    reference=_maximum_product,
    brute=lambda nums: max(a * b * c for a, b, c in itertools.combinations(nums, 3)) if len(nums) <= 60 else NotImplemented,
    examples=[Example([[1, 2, 3]]), Example([[1, 2, 3, 4]]), Example([[-100, -98, -1, 2, 3, 4]], "Two negatives times the largest: 39200.")],
    edge_cases=[[[-1, -2, -3]], [[0, 0, 0]], [[-5, 0, 5]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 3, 15, big=10**4), -1000, 1000)],
    random_count=8,
)


# ---------------------------------------------------------------- Shortest Unsorted Continuous Subarray


def _find_unsorted_subarray(nums: list[int]) -> int:
    n = len(nums)
    end, high = -1, nums[0]
    for i in range(n):  # the last index smaller than the running maximum
        high = max(high, nums[i])
        if nums[i] < high:
            end = i
    start, low = 0, nums[-1]
    for i in range(n - 1, -1, -1):  # the first index larger than the running minimum from the right
        low = min(low, nums[i])
        if nums[i] > low:
            start = i
    return end - start + 1 if end != -1 else 0


def _unsorted_brute(nums: list[int]) -> int:
    ordered = sorted(nums)
    diff = [i for i in range(len(nums)) if nums[i] != ordered[i]]
    return diff[-1] - diff[0] + 1 if diff else 0


def _unsorted_gen(rng: random.Random) -> list:
    values = sorted(ints(rng, pick_n(rng, 2, 15, big=5000), -(10**5), 10**5))
    i = rng.randint(0, len(values))
    j = rng.randint(i, len(values))
    return [values[:i] + sample(rng, values[i:j], j - i) + values[j:]]  # shuffle one window


SHORTEST_UNSORTED = ProblemSource(
    title="Shortest Unsorted Continuous Subarray",
    statement="""
Find the shortest contiguous subarray which, if sorted in non-decreasing order, makes the whole array sorted. Return its length (`0` if the array
is already sorted). Aim for `O(n)` time.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-10^5 <= nums[i] <= 10^5`
""",
    signature=function("findUnsortedSubarray", [("nums", "int[]")], "int"),
    reference=_find_unsorted_subarray,
    brute=_unsorted_brute,
    examples=[Example([[2, 6, 4, 8, 10, 9, 15]], "Sort [6, 4, 8, 10, 9]."), Example([[1, 2, 3, 4]]), Example([[1]])],
    edge_cases=[[[2, 1]], [[1, 3, 2, 2, 2]], [[1, 1, 1]]],
    generator=_unsorted_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Bitwise ORs of Subarrays


def _subarray_bitwise_ors(arr: list[int]) -> int:
    seen: set[int] = set()
    ending_here: set[int] = set()
    for x in arr:
        ending_here = {x | y for y in ending_here} | {x}  # at most ~30 distinct values
        seen |= ending_here
    return len(seen)


def _ors_brute(arr: list[int]) -> int:
    n = len(arr)
    if n > 200:
        return NotImplemented
    values = set()
    for i in range(n):
        acc = 0
        for j in range(i, n):
            acc |= arr[j]
            values.add(acc)
    return len(values)


BITWISE_ORS = ProblemSource(
    title="Bitwise ORs of Subarrays",
    statement="""
For every non-empty contiguous subarray of `arr`, take the bitwise OR of its elements. Return how many distinct results there are.
""",
    constraints="""
- `1 <= arr.length <= 5 * 10^4`
- `0 <= arr[i] <= 10^9`
""",
    signature=function("subarrayBitwiseORs", [("arr", "int[]")], "int"),
    reference=_subarray_bitwise_ors,
    brute=_ors_brute,
    examples=[Example([[0]]), Example([[1, 1, 2]], "Results 1, 1, 2, 1, 3, 3: three distinct."), Example([[1, 2, 4]])],
    edge_cases=[[[0, 0, 0]], [[536870911]], [[1, 2, 4, 8, 16]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=10**4), 0, rng.choice([15, 255, 10**9]))],
    random_count=8,
)


# ---------------------------------------------------------------- Count Hills and Valleys in an Array


def _count_hill_valley(nums: list[int]) -> int:
    values = [k for k, _ in itertools.groupby(nums)]  # merge runs of equal neighbours
    return sum((a < b > c) or (a > b < c) for a, b, c in zip(values, values[1:], values[2:], strict=False))


def _hill_valley_brute(nums: list[int]) -> int:
    counted = 0
    for i in range(1, len(nums) - 1):
        if nums[i] == nums[i - 1]:
            continue  # same hill or valley as the previous index
        left = next((nums[j] for j in range(i - 1, -1, -1) if nums[j] != nums[i]), None)
        right = next((nums[j] for j in range(i + 1, len(nums)) if nums[j] != nums[i]), None)
        if left is not None and right is not None and ((left < nums[i] > right) or (left > nums[i] < right)):
            counted += 1
    return counted


HILLS_AND_VALLEYS = ProblemSource(
    title="Count Hills and Valleys in an Array",
    statement="""
Index `i` is part of a *hill* if its closest non-equal neighbours on both sides are smaller than `nums[i]`, and part of a *valley* if both are
larger. Adjacent equal indices belong to the same hill or valley, and an index needs a non-equal neighbour on **both** sides to count. Return the
number of hills and valleys.
""",
    constraints="""
- `3 <= nums.length <= 100`
- `1 <= nums[i] <= 100`
""",
    signature=function("countHillValley", [("nums", "int[]")], "int"),
    reference=_count_hill_valley,
    brute=_hill_valley_brute,
    examples=[Example([[2, 4, 1, 1, 6, 5]], "4 is a hill, the 1s a valley, 6 a hill."), Example([[6, 6, 5, 5, 4, 1]])],
    edge_cases=[[[1, 2, 1]], [[1, 1, 1]], [[3, 1, 1, 3]]],
    generator=lambda rng: [ints(rng, rng.randint(3, 100), 1, rng.choice([3, 100]))],
    random_count=8,
)


PROBLEMS = [
    FORMED_BY_CHARACTERS,
    ONE_SWAP,
    PIVOT_INDEX,
    FREQUENCY_SORT,
    CONCATENATION,
    ZIGZAG_CONVERSION,
    ZERO_ARRAY_I,
    COUNT_BINARY_SUBSTRINGS,
    FIND_CELEBRITY,
    WRITE_Y,
    FRUITS_BASKETS_II,
    GOOD_PAIRS,
    MAX_PRODUCT_THREE,
    SHORTEST_UNSORTED,
    BITWISE_ORS,
    HILLS_AND_VALLEYS,
]
