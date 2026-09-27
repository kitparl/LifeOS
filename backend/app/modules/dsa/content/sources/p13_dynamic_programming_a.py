"""Pattern 13: Dynamic Programming (part 1 of 3). Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
from collections import Counter, deque
from functools import cache
from math import comb

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, random_tree, word

PATTERN_NUMBER = 13
_MOD = 10**9 + 7


# ---------------------------------------------------------------- Coin Change


def _coin_change(coins: list[int], amount: int) -> int:
    best = [0] + [amount + 1] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                best[a] = min(best[a], best[a - c] + 1)
    return best[amount] if best[amount] <= amount else -1


def _coin_change_brute(coins: list[int], amount: int) -> int:
    seen, frontier = {0}, deque([(0, 0)])
    while frontier:
        total, n = frontier.popleft()
        if total == amount:
            return n
        for c in coins:
            if total + c <= amount and total + c not in seen:
                seen.add(total + c)
                frontier.append((total + c, n + 1))
    return -1


COIN_CHANGE = ProblemSource(
    title="Coin Change",
    statement="""
You have unlimited coins of each denomination in `coins`. Return the fewest coins that add up to exactly `amount`, or `-1` if it can't be done.
""",
    constraints="""
- `1 <= coins.length <= 12`
- `1 <= coins[i] <= 2^31 - 1`
- `0 <= amount <= 10^4`
""",
    signature=function("coinChange", [("coins", "int[]"), ("amount", "int")], "int"),
    reference=_coin_change,
    brute=_coin_change_brute,
    examples=[Example([[1, 2, 5], 11], "5 + 5 + 1."), Example([[2], 3], "Odd amounts can't be made from 2s."), Example([[1], 0])],
    edge_cases=[[[7], 7], [[2, 5, 10, 1], 27], [[186, 419, 83, 408], 6249], [[2147483647], 2]],
    generator=lambda rng: [sorted(set(ints(rng, rng.randint(1, 12), 1, rng.choice([10, 500])))), rng.randint(0, rng.choice([50, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Counting Bits


def _count_bits(n: int) -> list[int]:
    bits = [0] * (n + 1)
    for i in range(1, n + 1):
        bits[i] = bits[i >> 1] + (i & 1)
    return bits


COUNTING_BITS = ProblemSource(
    title="Counting Bits",
    statement="""
For every integer `i` from `0` to `n`, count the `1` bits in its binary representation. Return the counts as an array of length `n + 1`.
Can you do it in `O(n)` time without a built-in popcount?
""",
    constraints="""
- `0 <= n <= 10^5` (tests use up to `10^4`)
""",
    signature=function("countBits", [("n", "int")], "int[]"),
    reference=_count_bits,
    brute=lambda n: [bin(i).count("1") for i in range(n + 1)],
    examples=[Example([2], "0 -> 0, 1 -> 1, 10 -> 1."), Example([5])],
    edge_cases=[[0], [1], [1024]],
    generator=lambda rng: [rng.randint(0, rng.choice([64, 10**4]))],
    random_count=6,
)


# ---------------------------------------------------------------- Maximum Product Subarray


def _max_product(nums: list[int]) -> int:
    best = hi = lo = nums[0]
    for x in nums[1:]:
        candidates = (x, hi * x, lo * x)
        hi, lo = max(candidates), min(candidates)
        best = max(best, hi)
    return best


def _max_product_brute(nums: list[int]) -> int:
    best = nums[0]
    for i in range(len(nums)):
        product = 1
        for j in range(i, len(nums)):
            product *= nums[j]
            best = max(best, product)
    return best


MAX_PRODUCT_SUBARRAY = ProblemSource(
    title="Maximum Product Subarray",
    statement="""
Return the largest product of a non-empty contiguous subarray of `nums`. The answer is guaranteed to fit in a 32-bit integer.
""",
    constraints="""
- `1 <= nums.length <= 2 * 10^4`
- `-10 <= nums[i] <= 10`
- every subarray product fits in a 32-bit integer
""",
    signature=function("maxProduct", [("nums", "int[]")], "int"),
    reference=_max_product,
    brute=_max_product_brute,
    brute_input_limit=300,
    examples=[Example([[2, 3, -2, 4]], "[2, 3] gives 6."), Example([[-2, 0, -1]], "0 is the best; [-2, -1] isn't contiguous.")],
    edge_cases=[[[-2]], [[0, 2]], [[-2, 3, -4]], [[-1, -1]]],
    generator=lambda rng: [[rng.choice([-2, -1, 0, 1, 1, 2, 3]) for _ in range(pick_n(rng, 1, 18))]],
    random_count=8,
)


# ---------------------------------------------------------------- Combination Sum


def _combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    candidates = sorted(candidates)
    out: list[list[int]] = []

    def build(start: int, chosen: list[int], remaining: int) -> None:
        if remaining == 0:
            out.append(chosen[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break
            chosen.append(candidates[i])
            build(i, chosen, remaining - candidates[i])
            chosen.pop()

    build(0, [], target)
    return out


def _combination_sum_brute(candidates: list[int], target: int) -> list[list[int]]:
    out = []
    for r in range(1, target // min(candidates) + 1):
        for combo in itertools.combinations_with_replacement(sorted(candidates), r):
            if sum(combo) == target:
                out.append(list(combo))
    return out


COMBINATION_SUM = ProblemSource(
    title="Combination Sum",
    statement="""
`candidates` holds distinct positive integers and each may be used **any number of times**. Return every distinct combination that adds up to
`target` (combinations are compared as multisets), in any order.
""",
    constraints="""
- `1 <= candidates.length <= 30`
- `2 <= candidates[i] <= 40`, all distinct
- `1 <= target <= 40`
""",
    signature=function("combinationSum", [("candidates", "int[]"), ("target", "int")], "int[][]"),
    reference=_combination_sum,
    brute=lambda candidates, target: _combination_sum_brute(candidates, target) if target // min(candidates) <= 8 else NotImplemented,
    compare="unordered_nested",
    examples=[Example([[2, 3, 6, 7], 7], "[2, 2, 3] and [7]."), Example([[2, 3, 5], 8]), Example([[2], 1])],
    edge_cases=[[[7], 7], [[3, 4], 2], [[2, 3], 12]],
    generator=lambda rng: [sorted(set(ints(rng, rng.randint(1, 6), 2, 12))), rng.randint(1, 24)],
    random_count=8,
)


# ---------------------------------------------------------------- Word Break


def _word_break(s: str, wordDict: list[str]) -> bool:
    words = set(wordDict)
    ok = [True] + [False] * len(s)
    for i in range(1, len(s) + 1):
        ok[i] = any(ok[j] and s[j:i] in words for j in range(max(0, i - 20), i))
    return ok[-1]


def _word_break_brute(s: str, wordDict: list[str]) -> bool:
    @cache
    def can(i: int) -> bool:
        return i == len(s) or any(s.startswith(w, i) and can(i + len(w)) for w in wordDict)

    return can(0)


def _break_gen(rng):
    words = sorted({word(rng, rng.randint(1, 4), "ab") for _ in range(rng.randint(1, 6))})
    s = "".join(rng.choice(words) for _ in range(rng.randint(1, 12)))
    if rng.random() < 0.4:
        s += rng.choice("abc")
    return [s[:300], words]


WORD_BREAK = ProblemSource(
    title="Word Break",
    statement="""
Return `true` if `s` can be split into a sequence of one or more words from `wordDict` (the same word may be reused).
""",
    constraints="""
- `1 <= s.length <= 300`
- `1 <= wordDict.length <= 1000`, `1 <= wordDict[i].length <= 20`
- all strings are lowercase; dictionary words are distinct
""",
    signature=function("wordBreak", [("s", "string"), ("wordDict", "string[]")], "bool"),
    reference=_word_break,
    brute=_word_break_brute,
    examples=[Example(["leetcode", ["leet", "code"]]), Example(["applepenapple", ["apple", "pen"]], "\"apple\" is reused."), Example(["catsandog", ["cats", "dog", "sand", "and", "cat"]])],
    edge_cases=[["a", ["a"]], ["a", ["b"]], ["aaaaaaab", ["a", "aa", "aaa"]]],
    generator=_break_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Palindromic Substrings


def _count_substrings(s: str) -> int:
    count = 0
    for center in range(2 * len(s) - 1):
        lo, hi = center // 2, center // 2 + center % 2
        while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
            count += 1
            lo, hi = lo - 1, hi + 1
    return count


PALINDROMIC_SUBSTRINGS = ProblemSource(
    title="Palindromic Substrings",
    statement="""
Count the substrings of `s` that are palindromes. Substrings at different positions count separately even if they're equal.
""",
    constraints="""
- `1 <= s.length <= 1000`
- `s` consists of lowercase English letters
""",
    signature=function("countSubstrings", [("s", "string")], "int"),
    reference=_count_substrings,
    brute=lambda s: sum(s[i:j] == s[i:j][::-1] for i in range(len(s)) for j in range(i + 1, len(s) + 1)),
    brute_input_limit=150,
    examples=[Example(["abc"], "a, b, c."), Example(["aaa"], "a, a, a, aa, aa, aaa.")],
    edge_cases=[["a"], ["ab"], ["abba"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 30, big=1000), rng.choice(["ab", "abc"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Common Subsequence


def _lcs(text1: str, text2: str) -> int:
    prev = [0] * (len(text2) + 1)
    for a in text1:
        cur = [0]
        for j, b in enumerate(text2):
            cur.append(prev[j] + 1 if a == b else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def _lcs_brute(text1: str, text2: str) -> int:
    @cache
    def best(i: int, j: int) -> int:
        if i == len(text1) or j == len(text2):
            return 0
        if text1[i] == text2[j]:
            return 1 + best(i + 1, j + 1)
        return max(best(i + 1, j), best(i, j + 1))

    return best(0, 0)


LCS = ProblemSource(
    title="Longest Common Subsequence",
    statement="""
Return the length of the longest string that is a subsequence of both `text1` and `text2` (characters in order, not necessarily contiguous),
or `0` if they share no characters.
""",
    constraints="""
- `1 <= text1.length, text2.length <= 1000`
- lowercase English letters only
""",
    signature=function("longestCommonSubsequence", [("text1", "string"), ("text2", "string")], "int"),
    reference=_lcs,
    brute=_lcs_brute,
    brute_input_limit=300,
    examples=[Example(["abcde", "ace"], "\"ace\"."), Example(["abc", "abc"]), Example(["abc", "def"])],
    edge_cases=[["a", "a"], ["a", "b"], ["abcba", "abcbcba"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 20, big=1000), "abc"), word(rng, pick_n(rng, 1, 20, big=1000), "abcd")],
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Decode Ways


def _num_decodings(s: str) -> int:
    prev, cur = 1, int(s[0] != "0")
    for i in range(1, len(s)):
        nxt = cur if s[i] != "0" else 0
        if 10 <= int(s[i - 1 : i + 1]) <= 26:
            nxt += prev
        prev, cur = cur, nxt
    return cur


def _decodings_brute(s: str) -> int:
    @cache
    def ways(i: int) -> int:
        if i == len(s):
            return 1
        total = 0
        for size in (1, 2):
            part = s[i : i + size]
            if len(part) == size and part[0] != "0" and 1 <= int(part) <= 26:
                total += ways(i + size)
        return total

    return ways(0)


DECODE_WAYS = ProblemSource(
    title="Decode Ways",
    statement="""
Letters are encoded as numbers: `A -> 1`, `B -> 2`, ..., `Z -> 26`. Given a string of digits `s`, return how many ways it can be decoded back
into letters. A group like `"06"` is invalid (it can't be read as 6). The answer fits in a 32-bit integer.
""",
    constraints="""
- `1 <= s.length <= 100`
- `s` consists of digits (it may start with `0`)
""",
    signature=function("numDecodings", [("s", "string")], "int"),
    reference=_num_decodings,
    brute=_decodings_brute,
    examples=[Example(["12"], "\"AB\" or \"L\"."), Example(["226"], "BZ, VF, BBF."), Example(["06"], "No valid decoding.")],
    edge_cases=[["0"], ["10"], ["27"], ["1111111111"], ["2101"], ["100"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([12, 40])), rng.choice(["12", "1203", "0123456789"]))],
    random_count=9,
)


# ---------------------------------------------------------------- Climbing Stairs


def _climb_stairs(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


CLIMBING_STAIRS = ProblemSource(
    title="Climbing Stairs",
    statement="""
A staircase has `n` steps and you climb either 1 or 2 steps at a time. Return how many distinct ways lead to the top.
""",
    constraints="""
- `1 <= n <= 45`
""",
    signature=function("climbStairs", [("n", "int")], "int"),
    reference=_climb_stairs,
    brute=lambda n: sum(comb(n - k, k) for k in range(n // 2 + 1)),
    examples=[Example([2], "1 + 1 or 2."), Example([3])],
    edge_cases=[[1], [10], [45]],
    generator=lambda rng: [rng.randint(1, 45)],
    random_count=5,
)


# ---------------------------------------------------------------- 0/1 Knapsack


def _knapsack(weights: list[int], values: list[int], capacity: int) -> int:
    best = [0] * (capacity + 1)
    for w, v in zip(weights, values, strict=True):
        for c in range(capacity, w - 1, -1):
            best[c] = max(best[c], best[c - w] + v)
    return best[capacity]


def _knapsack_brute(weights: list[int], values: list[int], capacity: int) -> int:
    return max(
        (sum(values[i] for i in chosen) for r in range(len(weights) + 1) for chosen in itertools.combinations(range(len(weights)), r) if sum(weights[i] for i in chosen) <= capacity),
        default=0,
    )


def _knapsack_gen(rng):
    n = pick_n(rng, 1, 10, big=100)
    return [ints(rng, n, 1, rng.choice([10, 1000])), ints(rng, n, 1, 1000), rng.randint(0, rng.choice([30, 1000]))]


KNAPSACK = ProblemSource(
    title="0/1 Knapsack",
    statement="""
Item `i` has weight `weights[i]` and value `values[i]`. Choose a set of items (each at most once) whose total weight is at most `capacity`,
maximising the total value. Return that maximum value.
""",
    constraints="""
- `1 <= n <= 100`, `weights.length == values.length == n`
- `1 <= weights[i], values[i] <= 1000`
- `0 <= capacity <= 1000`
""",
    signature=function("findMaxKnapsackProfit", [("weights", "int[]"), ("values", "int[]"), ("capacity", "int")], "int"),
    reference=_knapsack,
    brute=lambda weights, values, capacity: _knapsack_brute(weights, values, capacity) if len(weights) <= 12 else NotImplemented,
    examples=[Example([[1, 2, 3, 5], [1, 6, 10, 16], 7], "Items with weights 2 and 5 give value 22."), Example([[10], [5], 3], "Nothing fits.")],
    edge_cases=[[[1], [1], 0], [[3, 3, 3], [5, 5, 5], 9], [[5, 4, 6, 3], [10, 40, 30, 50], 10]],
    generator=_knapsack_gen,
    random_count=8,
)


# ---------------------------------------------------------------- N-th Tribonacci Number


def _tribonacci(n: int) -> int:
    a, b, c = 0, 1, 1
    for _ in range(n):
        a, b, c = b, c, a + b + c
    return a


TRIBONACCI = ProblemSource(
    title="N-th Tribonacci Number",
    statement="""
The Tribonacci sequence is `T0 = 0`, `T1 = 1`, `T2 = 1`, and `T(n+3) = T(n) + T(n+1) + T(n+2)`. Return `Tn`.
""",
    constraints="""
- `0 <= n <= 37` (the answer fits in a 32-bit integer)
""",
    signature=function("tribonacci", [("n", "int")], "int"),
    reference=_tribonacci,
    brute=lambda n: (lambda f: f(f, n))(lambda f, k: [0, 1, 1][k] if k < 3 else f(f, k - 1) + f(f, k - 2) + f(f, k - 3)) if n <= 20 else NotImplemented,
    examples=[Example([4], "0, 1, 1, 2, 4."), Example([25])],
    edge_cases=[[0], [1], [2], [37]],
    generator=lambda rng: [rng.randint(0, 37)],
    random_count=5,
)


# ---------------------------------------------------------------- Partition Equal Subset Sum


def _can_partition(nums: list[int]) -> bool:
    total = sum(nums)
    if total % 2:
        return False
    reachable = 1
    for x in nums:
        reachable |= reachable << x
    return bool(reachable >> (total // 2) & 1)


def _partition_brute(nums: list[int]) -> bool:
    total = sum(nums)
    return total % 2 == 0 and any(sum(c) * 2 == total for r in range(len(nums) + 1) for c in itertools.combinations(nums, r))


PARTITION_EQUAL = ProblemSource(
    title="Partition Equal Subset Sum",
    statement="""
Return `true` if `nums` can be split into two groups with equal sums (every element goes into exactly one group).
""",
    constraints="""
- `1 <= nums.length <= 200`
- `1 <= nums[i] <= 100`
""",
    signature=function("canPartition", [("nums", "int[]")], "bool"),
    reference=_can_partition,
    brute=lambda nums: _partition_brute(nums) if len(nums) <= 14 else NotImplemented,
    examples=[Example([[1, 5, 11, 5]], "[1, 5, 5] and [11]."), Example([[1, 2, 3, 5]])],
    edge_cases=[[[1]], [[2, 2]], [[100, 100, 100, 100, 99, 97]], [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 13]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 14, big=200), 1, rng.choice([6, 100]))],
    random_count=9,
)


# ---------------------------------------------------------------- 01 Matrix


def _update_matrix(mat: list[list[int]]) -> list[list[int]]:
    m, n = len(mat), len(mat[0])
    dist = [[0 if mat[i][j] == 0 else -1 for j in range(n)] for i in range(m)]
    frontier = deque((i, j) for i in range(m) for j in range(n) if mat[i][j] == 0)
    while frontier:
        i, j = frontier.popleft()
        for x, y in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= x < m and 0 <= y < n and dist[x][y] < 0:
                dist[x][y] = dist[i][j] + 1
                frontier.append((x, y))
    return dist


def _matrix_brute(mat: list[list[int]]) -> list[list[int]]:
    zeros = [(i, j) for i, row in enumerate(mat) for j, v in enumerate(row) if v == 0]
    return [[min(abs(i - a) + abs(j - b) for a, b in zeros) for j in range(len(mat[0]))] for i in range(len(mat))]


def _zero_one_gen(rng):
    m, n = pick_n(rng, 1, 7, big=60), pick_n(rng, 1, 7, big=60)
    mat = [[int(rng.random() < 0.7) for _ in range(n)] for _ in range(m)]
    mat[rng.randrange(m)][rng.randrange(n)] = 0
    return [mat]


ZERO_ONE_MATRIX = ProblemSource(
    title="01 Matrix",
    statement="""
For each cell of the binary matrix `mat`, find the distance to the nearest `0`, moving up, down, left or right (each move has distance 1).
The matrix contains at least one `0`. Return the matrix of distances.
""",
    constraints="""
- `1 <= m, n`, `m * n <= 10^4`
- `mat[i][j]` is `0` or `1`, with at least one `0`
""",
    signature=function("updateMatrix", [("mat", "int[][]")], "int[][]"),
    reference=_update_matrix,
    brute=_matrix_brute,
    brute_input_limit=1500,
    examples=[Example([[[0, 0, 0], [0, 1, 0], [0, 0, 0]]]), Example([[[0, 0, 0], [0, 1, 0], [1, 1, 1]]])],
    edge_cases=[[[[0]]], [[[1, 0, 1, 1, 1]]], [[[1], [1], [0]]]],
    generator=_zero_one_gen,
    random_count=8,
)


# ---------------------------------------------------------------- House Robber II


def _rob_line(nums: list[int]) -> int:
    take = skip = 0
    for x in nums:
        take, skip = skip + x, max(take, skip)
    return max(take, skip)


def _rob_ii(nums: list[int]) -> int:
    if len(nums) == 1:
        return nums[0]
    return max(_rob_line(nums[1:]), _rob_line(nums[:-1]))


def _rob_ii_brute(nums: list[int]) -> int:
    n, best = len(nums), 0
    for mask in range(1 << n):
        chosen = [i for i in range(n) if mask >> i & 1]
        if all((j - i) % n not in (1, n - 1) for i, j in itertools.combinations(chosen, 2)) or n == 1:
            best = max(best, sum(nums[i] for i in chosen))
    return best


HOUSE_ROBBER_II = ProblemSource(
    title="House Robber II",
    statement="""
Houses stand in a **circle** (the first and last are neighbours); `nums[i]` is the money in house `i`. A thief can't rob two adjacent houses.
Return the most money the thief can rob.
""",
    constraints="""
- `1 <= nums.length <= 100`
- `0 <= nums[i] <= 1000`
""",
    signature=function("rob", [("nums", "int[]")], "int"),
    reference=_rob_ii,
    brute=lambda nums: _rob_ii_brute(nums) if len(nums) <= 14 else NotImplemented,
    examples=[Example([[2, 3, 2]], "Houses 0 and 2 are adjacent in the circle."), Example([[1, 2, 3, 1]]), Example([[1, 2, 3]])],
    edge_cases=[[[5]], [[1, 2]], [[2, 1, 1, 2]], [[0, 0, 0]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 14, big=100), 0, rng.choice([5, 1000]))],
    random_count=8,
)


# ---------------------------------------------------------------- Word Break II


def _word_break_ii(s: str, wordDict: list[str]) -> list[str]:
    words = set(wordDict)

    @cache
    def sentences(i: int) -> list[str]:
        if i == len(s):
            return [""]
        out = []
        for j in range(i + 1, len(s) + 1):
            if s[i:j] in words:
                out += [s[i:j] + ("" if not rest else " " + rest) for rest in sentences(j)]
        return out

    return sentences(0)


def _word_break_ii_brute(s: str, wordDict: list[str]) -> list[str]:
    out = []
    for mask in range(1 << (len(s) - 1)):
        parts, start = [], 0
        for i in range(len(s) - 1):
            if mask >> i & 1:
                parts.append(s[start : i + 1])
                start = i + 1
        parts.append(s[start:])
        if all(p in wordDict for p in parts):
            out.append(" ".join(parts))
    return out


def _break_ii_gen(rng):
    words = sorted({word(rng, rng.randint(1, 3), "ab") for _ in range(rng.randint(2, 6))})
    s = "".join(rng.choice(words) for _ in range(rng.randint(1, 6)))[:20]
    return [s, words]


WORD_BREAK_II = ProblemSource(
    title="Word Break II",
    statement="""
Insert spaces into `s` to split it into words from `wordDict` (words may be reused). Return every possible resulting sentence, in any order.
""",
    constraints="""
- `1 <= s.length <= 20`
- `1 <= wordDict.length <= 1000`, `1 <= wordDict[i].length <= 10`
- lowercase letters only; dictionary words are distinct
""",
    signature=function("wordBreak", [("s", "string"), ("wordDict", "string[]")], "string[]"),
    reference=_word_break_ii,
    brute=_word_break_ii_brute,
    compare="unordered",
    examples=[Example(["catsanddog", ["cat", "cats", "and", "sand", "dog"]], "\"cats and dog\" and \"cat sand dog\"."), Example(["catsandog", ["cats", "dog", "sand", "and", "cat"]])],
    edge_cases=[["a", ["a"]], ["aaaa", ["a", "aa"]], ["ab", ["b"]]],
    generator=_break_ii_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Count the Number of Good Subsequences


def _count_good_subsequences(s: str) -> int:
    counts = Counter(s).values()
    total = 0
    for f in range(1, max(counts) + 1):
        ways = 1
        for c in counts:
            ways = ways * (1 + comb(c, f)) % _MOD
        total = (total + ways - 1) % _MOD
    return total


def _good_subsequences_brute(s: str) -> int:
    count = 0
    for mask in range(1, 1 << len(s)):
        freq = Counter(s[i] for i in range(len(s)) if mask >> i & 1)
        count += len(set(freq.values())) == 1
    return count % _MOD


GOOD_SUBSEQUENCES = ProblemSource(
    title="Count the Number of Good Subsequences",
    statement="""
A subsequence is *good* if it is non-empty and every character in it occurs the same number of times. Return the number of good subsequences
of `s` modulo `10^9 + 7` (subsequences chosen from different positions count separately).
""",
    constraints="""
- `1 <= s.length <= 10^4`
- lowercase English letters only
""",
    signature=function("countGoodSubsequences", [("s", "string")], "int"),
    reference=_count_good_subsequences,
    brute=_good_subsequences_brute,
    brute_input_limit=16,
    examples=[Example(["aabb"], "15 non-empty subsequences; the four with unequal counts (the two \"aab\" and two \"abb\") are not good."), Example(["leet"]), Example(["abcd"], "All 15 non-empty subsequences.")],
    edge_cases=[["a"], ["aa"], ["abc"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 12, big=10**4), rng.choice(["ab", "abc", "abcdefghij"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Binary Tree Cameras


def _min_camera_cover(root) -> int:
    cameras = 0

    def state(node) -> int:  # 0 = needs cover, 1 = has camera, 2 = covered
        nonlocal cameras
        if node is None:
            return 2
        left, right = state(node.left), state(node.right)
        if left == 0 or right == 0:
            cameras += 1
            return 1
        return 2 if left == 1 or right == 1 else 0

    root_state = state(root)  # must run before `cameras` is read
    return cameras + (root_state == 0)


def _cameras_brute(root) -> int:
    nodes, adjacent = [], {}
    stack = [(root, None)]
    while stack:
        node, parent = stack.pop()
        if node:
            nodes.append(node)
            adjacent[id(node)] = {id(parent)} if parent else set()
            if parent:
                adjacent[id(parent)].add(id(node))
            stack += [(node.left, node), (node.right, node)]
    for k in range(len(nodes) + 1):
        for chosen in itertools.combinations([id(n) for n in nodes], k):
            chosen_set = set(chosen)
            if all(i in chosen_set or adjacent[i] & chosen_set for i in adjacent):
                return k
    raise AssertionError


BINARY_TREE_CAMERAS = ProblemSource(
    title="Binary Tree Cameras",
    statement="""
Cameras can be installed on nodes of a binary tree; a camera monitors its own node, its parent and its immediate children. Return the minimum
number of cameras needed to monitor every node.
""",
    constraints="""
- the tree has between `1` and `1000` nodes
- every node's value is `0`
""",
    signature=function("minCameraCover", [("root", "TreeNode")], "int"),
    reference=_min_camera_cover,
    brute=_cameras_brute,
    brute_input_limit=60,
    examples=[Example([[0, 0, None, 0, 0]], "One camera on the middle node."), Example([[0, 0, None, 0, None, 0, None, None, 0]])],
    edge_cases=[[[0]], [[0, 0]], [[0, 0, 0]], [[0, None, 0, None, 0, None, 0]]],
    generator=lambda rng: [[0 if v is not None else None for v in random_tree(rng, pick_n(rng, 1, 12, big=1000), 0, 0)]],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Ways to Form a Target String Given a Dictionary


def _num_ways_target(words: list[str], target: str) -> int:
    length = len(words[0])
    counts = [Counter(w[k] for w in words) for k in range(length)]
    ways = [1] + [0] * len(target)  # ways[i] = ways to build target[:i]
    for k in range(length):
        for i in range(min(k + 1, len(target)), 0, -1):
            ways[i] = (ways[i] + ways[i - 1] * counts[k][target[i - 1]]) % _MOD
    return ways[-1]


def _num_ways_brute(words: list[str], target: str) -> int:
    length = len(words[0])
    total = 0
    for cols in itertools.combinations(range(length), len(target)):
        ways = 1
        for k, ch in zip(cols, target, strict=True):
            ways *= sum(w[k] == ch for w in words)
        total += ways
    return total % _MOD


def _ways_target_gen(rng):
    length = rng.randint(1, rng.choice([6, 200]))
    words = [word(rng, length, "ab") for _ in range(rng.randint(1, rng.choice([4, 50])))]
    return [words, word(rng, rng.randint(1, min(length, rng.choice([4, 40]))), "ab")]


WAYS_FORM_TARGET = ProblemSource(
    title="Number of Ways to Form a Target String Given a Dictionary",
    statement="""
All strings in `words` have the same length. Build `target` from left to right: for each next character `target[i]`, pick any word and any
column `k` of it with `words[j][k] == target[i]`. After using column `k`, you may only use columns **greater than `k`** (in any word) for the
following characters.

Return the number of ways to build `target`, modulo `10^9 + 7`.
""",
    constraints="""
- `1 <= words.length <= 1000`, `1 <= words[i].length <= 1000` (all equal)
- `1 <= target.length <= 1000`
- lowercase English letters only
""",
    signature=function("numWays", [("words", "string[]"), ("target", "string")], "int"),
    reference=_num_ways_target,
    brute=lambda words, target: _num_ways_brute(words, target) if len(words[0]) <= 10 else NotImplemented,
    examples=[Example([["acca", "bbbb", "caca"], "aba"], "Six ways."), Example([["abba", "baab"], "bab"], "Four ways.")],
    edge_cases=[[["a"], "a"], [["a"], "b"], [["ab"], "ab"], [["ab"], "ba"]],
    generator=_ways_target_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Pascal's Triangle


def _pascal(numRows: int) -> list[list[int]]:
    rows = [[1]]
    for _ in range(numRows - 1):
        prev = rows[-1]
        rows.append([1] + [a + b for a, b in itertools.pairwise(prev)] + [1])
    return rows


PASCAL = ProblemSource(
    title="Pascal's Triangle",
    statement="""
Return the first `numRows` rows of Pascal's triangle. Each row starts and ends with `1`, and every inner number is the sum of the two numbers
above it.
""",
    constraints="""
- `1 <= numRows <= 30`
""",
    signature=function("generate", [("numRows", "int")], "int[][]"),
    reference=_pascal,
    brute=lambda numRows: [[comb(r, k) for k in range(r + 1)] for r in range(numRows)],
    examples=[Example([5]), Example([1])],
    edge_cases=[[2], [30]],
    generator=lambda rng: [rng.randint(1, 30)],
    random_count=4,
)


PROBLEMS = [
    COIN_CHANGE,
    COUNTING_BITS,
    MAX_PRODUCT_SUBARRAY,
    COMBINATION_SUM,
    WORD_BREAK,
    PALINDROMIC_SUBSTRINGS,
    LCS,
    DECODE_WAYS,
    CLIMBING_STAIRS,
    KNAPSACK,
    TRIBONACCI,
    PARTITION_EQUAL,
    ZERO_ONE_MATRIX,
    HOUSE_ROBBER_II,
    WORD_BREAK_II,
    GOOD_SUBSEQUENCES,
    BINARY_TREE_CAMERAS,
    WAYS_FORM_TARGET,
    PASCAL,
]
