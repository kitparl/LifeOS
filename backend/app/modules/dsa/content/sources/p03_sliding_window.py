"""Pattern 3: Sliding Window. Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import string
from collections import Counter, defaultdict, deque

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, word

PATTERN_NUMBER = 3


def _is_subsequence(small: str, big: str) -> bool:
    it = iter(big)
    return all(c in it for c in small)


# ---------------------------------------------------------------- Longest Repeating Character Replacement


def _character_replacement(s: str, k: int) -> int:
    counts: Counter[str] = Counter()
    best_freq = lo = best = 0
    for hi, c in enumerate(s):
        counts[c] += 1
        best_freq = max(best_freq, counts[c])
        while hi - lo + 1 - best_freq > k:
            counts[s[lo]] -= 1
            lo += 1
        best = max(best, hi - lo + 1)
    return best


def _character_replacement_brute(s: str, k: int) -> int:
    best = 0
    for i in range(len(s)):
        counts: Counter[str] = Counter()
        for j in range(i, len(s)):
            counts[s[j]] += 1
            if j - i + 1 - max(counts.values()) <= k:
                best = max(best, j - i + 1)
    return best


CHARACTER_REPLACEMENT = ProblemSource(
    title="Longest Repeating Character Replacement",
    statement="""
You are given an uppercase string `s` and an integer `k`. You may change any character of `s` into any
other uppercase letter, at most `k` times in total.

Return the length of the longest substring that consists of a single repeated letter after your changes.
""",
    constraints="""
- `1 <= s.length <= 10^5`
- `s` consists of uppercase English letters
- `0 <= k <= s.length`
""",
    signature=function("characterReplacement", [("s", "string"), ("k", "int")], "int"),
    reference=_character_replacement,
    brute=_character_replacement_brute,
    brute_input_limit=300,
    examples=[
        Example(["ABAB", 2], "Change both A's to B (or both B's to A): \"BBBB\"."),
        Example(["AABABBA", 1], 'Changing the middle A gives "AABBBBA" with the run "BBBB".'),
    ],
    edge_cases=[["A", 0], ["A", 1], ["AB", 0], ["ABCDE", 5], ["AAAA", 2], ["ABBB", 0]],
    generator=lambda rng: [
        (s := word(rng, pick_n(rng, 1, 40, big=15000), "ABC" if rng.random() < 0.7 else string.ascii_uppercase)),
        rng.randint(0, min(len(s), 6)),
    ],
    random_count=9,
)


# ---------------------------------------------------------------- Minimum Window Substring


def _min_window(s: str, t: str) -> str:
    need, missing = Counter(t), len(t)
    lo = start = 0
    best = (float("inf"), 0)
    for hi, c in enumerate(s):
        if need[c] > 0:
            missing -= 1
        need[c] -= 1
        if missing == 0:
            while need[s[lo]] < 0:
                need[s[lo]] += 1
                lo += 1
            if hi - lo + 1 < best[0]:
                best = (hi - lo + 1, lo)
            need[s[lo]] += 1
            missing += 1
            lo += 1
    length, start = best
    return "" if length == float("inf") else s[start : start + int(length)]


def _min_window_brute(s: str, t: str) -> str:
    need = Counter(t)
    for length in range(len(t), len(s) + 1):
        for i in range(len(s) - length + 1):
            window = Counter(s[i : i + length])
            if all(window[c] >= n for c, n in need.items()):
                return s[i : i + length]
    return ""


MIN_WINDOW = ProblemSource(
    title="Minimum Window Substring",
    statement="""
Given two strings `s` and `t`, return the shortest substring of `s` that contains every character of `t`,
**including duplicates** (if `t` has two `a`'s, the window needs at least two `a`'s).

If several windows have the minimum length, return the one that starts first. If no window exists,
return the empty string `""`.

Aim for `O(m + n)` time.
""",
    constraints="""
- `1 <= s.length, t.length <= 10^5`
- `s` and `t` consist of uppercase and lowercase English letters
""",
    signature=function("minWindow", [("s", "string"), ("t", "string")], "string"),
    reference=_min_window,
    brute=_min_window_brute,
    brute_input_limit=120,
    examples=[
        Example(["ADOBECODEBANC", "ABC"], '"BANC" is the shortest window containing A, B and C.'),
        Example(["a", "a"]),
        Example(["a", "aa"], "s has only one 'a', so no window works."),
    ],
    edge_cases=[["ab", "b"], ["ab", "c"], ["aa", "aa"], ["bba", "ab"], ["abcabc", "cba"], ["AaBb", "ab"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 40, big=15000), "abcAB"), word(rng, rng.randint(1, 6), "abcAB")],
    random_count=9,
)


# ---------------------------------------------------------------- Longest Substring without Repeating Characters


def _length_of_longest_substring(s: str) -> int:
    last: dict[str, int] = {}
    lo = best = 0
    for hi, c in enumerate(s):
        if last.get(c, -1) >= lo:
            lo = last[c] + 1
        last[c] = hi
        best = max(best, hi - lo + 1)
    return best


def _longest_substring_brute(s: str) -> int:
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if len(set(s[i:j])) == j - i), default=0)


LONGEST_SUBSTRING = ProblemSource(
    title="Longest Substring without Repeating Characters",
    statement="""
Given a string `s`, return the length of the longest substring in which no character appears twice.
""",
    constraints="""
- `0 <= s.length <= 5 * 10^4`
- `s` consists of English letters, digits, symbols and spaces
""",
    signature=function("lengthOfLongestSubstring", [("s", "string")], "int"),
    reference=_length_of_longest_substring,
    brute=_longest_substring_brute,
    brute_input_limit=200,
    examples=[
        Example(["abcabcbb"], '"abc" has length 3.'),
        Example(["bbbbb"], '"b" has length 1.'),
        Example(["pwwkew"], '"wke" has length 3; "pwke" is a subsequence, not a substring.'),
    ],
    edge_cases=[[""], [" "], ["au"], ["dvdf"], ["abba"], ["tmmzuxt"]],
    generator=lambda rng: [
        word(rng, pick_n(rng, 0, 40, big=15000), rng.choice(["abc", "abcdefgh", string.ascii_letters + " !"]))
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Best Time to Buy and Sell Stock


def _max_profit(prices: list[int]) -> int:
    lowest, best = float("inf"), 0
    for p in prices:
        lowest = min(lowest, p)
        best = max(best, p - int(lowest))
    return best


BEST_TIME = ProblemSource(
    title="Best Time to Buy and Sell Stock",
    statement="""
`prices[i]` is a stock's price on day `i`. You may buy one share on one day and sell it on a **later**
day. Return the largest profit you can make, or `0` if no trade makes money.
""",
    constraints="""
- `1 <= prices.length <= 10^5`
- `0 <= prices[i] <= 10^4`
""",
    signature=function("maxProfit", [("prices", "int[]")], "int"),
    reference=_max_profit,
    brute=lambda prices: max(
        [0] + [prices[j] - prices[i] for i in range(len(prices)) for j in range(i + 1, len(prices))]
    ),
    brute_input_limit=300,
    examples=[
        Example([[7, 1, 5, 3, 6, 4]], "Buy at 1, sell at 6: profit 5."),
        Example([[7, 6, 4, 3, 1]], "Prices only fall, so don't trade."),
    ],
    edge_cases=[[[5]], [[1, 2]], [[2, 1]], [[3, 3, 3]], [[2, 4, 1, 7]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 40, big=4500), 0, 10**4)],
    random_count=8,
)


# ---------------------------------------------------------------- Repeated DNA Sequences


def _repeated_dna(s: str) -> list[str]:
    seen, repeated = set(), set()
    for i in range(len(s) - 9):
        chunk = s[i : i + 10]
        if chunk in seen:
            repeated.add(chunk)
        seen.add(chunk)
    return sorted(repeated)


def _dna_gen(rng):
    base = word(rng, rng.randint(10, 30), "ACGT")
    s = word(rng, pick_n(rng, 0, 30, big=4500), "ACGT" if rng.random() < 0.5 else "AC")
    for _ in range(rng.randint(0, 3)):
        i = rng.randint(0, len(s))
        s = s[:i] + base + s[i:]
    return [s]


REPEATED_DNA = ProblemSource(
    title="Repeated DNA Sequences",
    statement="""
A DNA string is made of the letters `A`, `C`, `G` and `T`. Return every 10-letter-long substring that
occurs **more than once** in `s` (occurrences may overlap). Each such substring should be listed once,
in any order.
""",
    constraints="""
- `1 <= s.length <= 10^5`
- `s[i]` is `A`, `C`, `G` or `T`
""",
    signature=function("findRepeatedDnaSequences", [("s", "string")], "string[]"),
    reference=_repeated_dna,
    brute=lambda s: [c for c, n in Counter(s[i : i + 10] for i in range(len(s) - 9)).items() if n > 1],
    compare="unordered",
    examples=[
        Example(["AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT"], '"AAAAACCCCC" and "CCCCCAAAAA" each appear twice.'),
        Example(["AAAAAAAAAAAAA"], 'The overlapping windows give "AAAAAAAAAA" several times.'),
    ],
    edge_cases=[["A"], ["AAAAAAAAAA"], ["AAAAAAAAAAA"], ["ACGTACGTAC"]],
    generator=_dna_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Sliding Window Maximum


def _max_sliding_window(nums: list[int], k: int) -> list[int]:
    window: deque[int] = deque()
    out = []
    for i, x in enumerate(nums):
        while window and nums[window[-1]] <= x:
            window.pop()
        window.append(i)
        if window[0] <= i - k:
            window.popleft()
        if i >= k - 1:
            out.append(nums[window[0]])
    return out


def _window_max_gen(rng):
    nums = ints(rng, pick_n(rng, 1, 40, big=4500), -(10**4), 10**4)
    return [nums, rng.randint(1, len(nums))]


SLIDING_WINDOW_MAX = ProblemSource(
    title="Sliding Window Maximum",
    statement="""
A window of size `k` slides over the integer array `nums` from left to right, one position at a time.
Return the maximum value inside the window at each of its `nums.length - k + 1` positions.

Can you do it in `O(n)` time?
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
- `1 <= k <= nums.length`
""",
    signature=function("maxSlidingWindow", [("nums", "int[]"), ("k", "int")], "int[]"),
    reference=_max_sliding_window,
    brute=lambda nums, k: [max(nums[i : i + k]) for i in range(len(nums) - k + 1)],
    examples=[
        Example([[1, 3, -1, -3, 5, 3, 6, 7], 3], "Window maxima: 3, 3, 5, 5, 6, 7."),
        Example([[1], 1]),
    ],
    edge_cases=[[[4, 2], 2], [[2, 4], 1], [[9, 8, 7, 6], 2], [[1, 1, 1], 3]],
    generator=_window_max_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Window Subsequence


def _min_window_subsequence(s1: str, s2: str) -> str:
    best_start, best_len = -1, float("inf")
    i = 0
    while i < len(s1):
        j = 0
        while i < len(s1):  # forward: find an end where s2 is a subsequence
            if s1[i] == s2[j]:
                j += 1
                if j == len(s2):
                    break
            i += 1
        if i == len(s1):
            break
        end = i
        j = len(s2) - 1
        while j >= 0:  # backward: tighten the start
            if s1[i] == s2[j]:
                j -= 1
            i -= 1
        start = i + 1
        if end - start + 1 < best_len:
            best_start, best_len = start, end - start + 1
        i = start + 1
    return "" if best_start < 0 else s1[best_start : best_start + int(best_len)]


def _min_window_subsequence_brute(s1: str, s2: str) -> str:
    for length in range(len(s2), len(s1) + 1):
        for i in range(len(s1) - length + 1):
            if _is_subsequence(s2, s1[i : i + length]):
                return s1[i : i + length]
    return ""


MIN_WINDOW_SUBSEQUENCE = ProblemSource(
    title="Minimum Window Subsequence",
    statement="""
Given strings `s1` and `s2`, return the shortest **substring** of `s1` in which `s2` appears as a
**subsequence** (its characters in order, not necessarily next to each other).

If several substrings have the minimum length, return the one that starts first; if none exists,
return `""`.
""",
    constraints="""
- `1 <= s1.length <= 2 * 10^4`
- `1 <= s2.length <= 100`
- both strings consist of lowercase English letters
""",
    signature=function("minWindow", [("s1", "string"), ("s2", "string")], "string"),
    reference=_min_window_subsequence,
    brute=_min_window_subsequence_brute,
    brute_input_limit=100,
    examples=[
        Example(["abcdebdde", "bde"], '"bcde" and "bdde" both work; "bcde" starts first.'),
        Example(["jmeqksfrsdcmsiwvaovztaqenprpvnbstl", "u"], "There is no 'u' in s1."),
    ],
    edge_cases=[["a", "a"], ["ab", "b"], ["ab", "ba"], ["aaa", "aa"], ["abcbca", "ca"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 40, big=3000), "abc"), word(rng, rng.randint(1, 5), "abc")],
    random_count=9,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Minimum Size Subarray Sum


def _min_subarray_len(target: int, nums: list[int]) -> int:
    lo = total = 0
    best = float("inf")
    for hi, x in enumerate(nums):
        total += x
        while total >= target:
            best = min(best, hi - lo + 1)
            total -= nums[lo]
            lo += 1
    return 0 if best == float("inf") else int(best)


def _min_subarray_len_brute(target: int, nums: list[int]) -> int:
    lengths = [j - i + 1 for i in range(len(nums)) for j in range(i, len(nums)) if sum(nums[i : j + 1]) >= target]
    return min(lengths, default=0)


MIN_SUBARRAY_SUM = ProblemSource(
    title="Minimum Size Subarray Sum",
    statement="""
Given a positive integer `target` and an array of positive integers `nums`, return the length of the
shortest contiguous subarray whose sum is **at least** `target`, or `0` if there is none.
""",
    constraints="""
- `1 <= target <= 10^9`
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^4`
""",
    signature=function("minSubArrayLen", [("target", "int"), ("nums", "int[]")], "int"),
    reference=_min_subarray_len,
    brute=_min_subarray_len_brute,
    brute_input_limit=200,
    examples=[
        Example([7, [2, 3, 1, 2, 4, 3]], "[4, 3] sums to 7 with length 2."),
        Example([4, [1, 4, 4]]),
        Example([11, [1, 1, 1, 1, 1, 1, 1, 1]], "The whole array sums to only 8."),
    ],
    edge_cases=[[1, [1]], [2, [1]], [15, [1, 2, 3, 4, 5]], [100, [100, 1, 100]]],
    generator=lambda rng: [rng.randint(1, 300), ints(rng, pick_n(rng, 1, 40, big=4500), 1, 30)],
    random_count=8,
)


# ---------------------------------------------------------------- Fruit Into Baskets


def _total_fruit(fruits: list[int]) -> int:
    counts: Counter[int] = Counter()
    lo = best = 0
    for hi, f in enumerate(fruits):
        counts[f] += 1
        while len(counts) > 2:
            counts[fruits[lo]] -= 1
            if counts[fruits[lo]] == 0:
                del counts[fruits[lo]]
            lo += 1
        best = max(best, hi - lo + 1)
    return best


FRUIT_BASKETS = ProblemSource(
    title="Fruit Into Baskets",
    statement="""
Trees stand in a row; `fruits[i]` is the type of fruit tree `i` produces. You carry two baskets, and each
basket holds one type of fruit (as many pieces as you like).

Pick a starting tree and move to the right, taking exactly one fruit from every tree, until you reach a
tree whose fruit fits in neither basket. Return the maximum number of fruits you can collect.
""",
    constraints="""
- `1 <= fruits.length <= 10^5`
- `0 <= fruits[i] < fruits.length`
""",
    signature=function("totalFruit", [("fruits", "int[]")], "int"),
    reference=_total_fruit,
    brute=lambda fruits: max(
        j - i for i in range(len(fruits)) for j in range(i + 1, len(fruits) + 1) if len(set(fruits[i:j])) <= 2
    ),
    brute_input_limit=200,
    examples=[
        Example([[1, 2, 1]], "Every tree can be picked."),
        Example([[0, 1, 2, 2]], "Start at index 1: types 1 and 2 give 3 fruits."),
        Example([[1, 2, 3, 2, 2]], "Start at index 1 to collect [2, 3, 2, 2]."),
    ],
    edge_cases=[[[0]], [[0, 0]], [[0, 1]], [[0, 1, 2]], [[3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4]]],
    generator=lambda rng: [
        (lambda n: ints(rng, n, 0, min(n - 1, rng.choice([2, 3, 5]))))(pick_n(rng, 1, 40, big=4500))
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Frequency of the Most Frequent Element


def _max_frequency(nums: list[int], k: int) -> int:
    nums = sorted(nums)
    lo = total = best = 0
    for hi, x in enumerate(nums):
        total += x
        while x * (hi - lo + 1) - total > k:
            total -= nums[lo]
            lo += 1
        best = max(best, hi - lo + 1)
    return best


def _max_frequency_brute(nums: list[int], k: int) -> int:
    best = 0
    for target in set(nums):
        costs = sorted(target - x for x in nums if x <= target)
        budget, count = k, 0
        for c in costs:
            if c <= budget:
                budget -= c
                count += 1
        best = max(best, count)
    return best


MAX_FREQUENCY = ProblemSource(
    title="Frequency of the Most Frequent Element",
    statement="""
In one operation you may pick an index of `nums` and increase that element by `1`. You may do at most
`k` operations in total.

Return the largest possible number of equal elements (the maximum frequency of any value) you can reach.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^5`
- `1 <= k <= 10^5`
""",
    signature=function("maxFrequency", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_max_frequency,
    brute=_max_frequency_brute,
    brute_input_limit=300,
    examples=[
        Example([[1, 2, 4], 5], "Raise 1 three times and 2 twice: [4, 4, 4]."),
        Example([[1, 4, 8, 13], 5], "For example raise 1 to 4, giving frequency 2."),
        Example([[3, 9, 6], 2], "No two values can be matched with 2 operations."),
    ],
    edge_cases=[[[1], 1], [[5, 5], 1], [[1, 100000], 100000], [[1, 1, 1, 2], 1]],
    generator=lambda rng: [
        ints(rng, pick_n(rng, 1, 40, big=4500), 1, rng.choice([10, 100, 10**5])),
        rng.randint(1, rng.choice([10, 10**5])),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Average Subarray I


def _find_max_average(nums: list[int], k: int) -> float:
    window = best = sum(nums[:k])
    for i in range(k, len(nums)):
        window += nums[i] - nums[i - k]
        best = max(best, window)
    return best / k


def _avg_gen(rng):
    nums = ints(rng, pick_n(rng, 1, 40, big=4500), -(10**4), 10**4)
    return [nums, rng.randint(1, len(nums))]


MAX_AVERAGE = ProblemSource(
    title="Maximum Average Subarray I",
    statement="""
Given an integer array `nums` and an integer `k`, find the contiguous subarray of length exactly `k` with
the largest average and return that average. Answers within `10^-5` of the expected value are accepted.
""",
    constraints="""
- `1 <= k <= nums.length <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
""",
    signature=function("findMaxAverage", [("nums", "int[]"), ("k", "int")], "double"),
    reference=_find_max_average,
    brute=lambda nums, k: max(sum(nums[i : i + k]) / k for i in range(len(nums) - k + 1)),
    compare="float_tolerance",
    brute_input_limit=400,
    examples=[Example([[1, 12, -5, -6, 50, 3], 4], "Best window: [12, -5, -6, 50], average 12.75."), Example([[5], 1])],
    edge_cases=[[[-1], 1], [[0, 4, 0, 3, 2], 1], [[-10000, -10000], 2], [[7, 7, 7], 3]],
    generator=_avg_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Diet Plan Performance


def _diet_plan(calories: list[int], k: int, lower: int, upper: int) -> int:
    window = sum(calories[:k])
    points = 0
    for i in range(k - 1, len(calories)):
        if i >= k:
            window += calories[i] - calories[i - k]
        points += (window > upper) - (window < lower)
    return points


def _diet_gen(rng):
    calories = ints(rng, pick_n(rng, 1, 40, big=4500), 0, 20)
    k = rng.randint(1, len(calories))
    lower = rng.randint(0, 10 * k)
    return [calories, k, lower, rng.randint(lower, 20 * k)]


DIET_PLAN = ProblemSource(
    title="Diet Plan Performance",
    statement="""
A dieter eats `calories[i]` calories on day `i`. For every run of `k` consecutive days, look at the total
calories `T` of that run:

- if `T < lower`, the dieter loses 1 point,
- if `T > upper`, the dieter gains 1 point,
- otherwise nothing changes.

Starting from 0 points, return the total after scoring every run of `k` consecutive days (there are
`calories.length - k + 1` of them). The total may be negative.
""",
    constraints="""
- `1 <= k <= calories.length <= 10^5`
- `0 <= calories[i] <= 20000`
- `0 <= lower <= upper`
""",
    signature=function(
        "dietPlanPerformance", [("calories", "int[]"), ("k", "int"), ("lower", "int"), ("upper", "int")], "int"
    ),
    reference=_diet_plan,
    brute=lambda calories, k, lower, upper: sum(
        (sum(calories[i : i + k]) > upper) - (sum(calories[i : i + k]) < lower) for i in range(len(calories) - k + 1)
    ),
    brute_input_limit=400,
    examples=[
        Example([[1, 2, 3, 4, 5], 1, 3, 3], "Days 1 and 2 are below 3 (-2), days 4 and 5 above (+2): total 0."),
        Example([[3, 2], 2, 0, 1], "The only window totals 5 > 1: +1."),
        Example([[6, 5, 0, 0], 2, 1, 5], "Window totals 11, 5, 0 give +1, 0, -1: total 0."),
    ],
    edge_cases=[[[0], 1, 0, 0], [[0], 1, 1, 2], [[20000] * 5, 5, 0, 99999]],
    generator=_diet_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Subarrays with K Different Integers


def _at_most_distinct(nums: list[int], k: int) -> int:
    counts: Counter[int] = Counter()
    lo = total = 0
    for hi, x in enumerate(nums):
        counts[x] += 1
        while len(counts) > k:
            counts[nums[lo]] -= 1
            if counts[nums[lo]] == 0:
                del counts[nums[lo]]
            lo += 1
        total += hi - lo + 1
    return total


def _subarrays_k_distinct(nums: list[int], k: int) -> int:
    return _at_most_distinct(nums, k) - _at_most_distinct(nums, k - 1)


K_DIFFERENT = ProblemSource(
    title="Subarrays with K Different Integers",
    statement="""
Given an integer array `nums` and an integer `k`, return the number of contiguous subarrays that contain
**exactly** `k` distinct values.
""",
    constraints="""
- `1 <= nums.length <= 2 * 10^4`
- `1 <= nums[i], k <= nums.length`
""",
    signature=function("subarraysWithKDistinct", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_subarrays_k_distinct,
    brute=lambda nums, k: sum(len(set(nums[i:j])) == k for i in range(len(nums)) for j in range(i + 1, len(nums) + 1)),
    brute_input_limit=200,
    examples=[
        Example(
            [[1, 2, 1, 2, 3], 2], "Seven subarrays have exactly two distinct values, e.g. [1,2], [2,1], [1,2,1,2]."
        ),
        Example([[1, 2, 1, 3, 4], 3], "[1,2,1,3], [2,1,3] and [1,3,4]."),
    ],
    edge_cases=[[[1], 1], [[1, 1, 1], 1], [[1, 2], 2], [[1, 2, 3], 3], [[2, 2], 2]],
    generator=lambda rng: [
        (nums := (lambda n: ints(rng, n, 1, min(n, rng.choice([2, 3, 5, n]))))(pick_n(rng, 1, 40, big=4500))),
        rng.randint(1, min(4, len(nums))),
    ],
    random_count=9,
)


# ---------------------------------------------------------------- Count Subarrays With Score Less Than K


def _count_score_less(nums: list[int], k: int) -> int:
    lo = total = count = 0
    for hi, x in enumerate(nums):
        total += x
        while total * (hi - lo + 1) >= k:
            total -= nums[lo]
            lo += 1
        count += hi - lo + 1
    return count


def _count_score_less_brute(nums: list[int], k: int) -> int:
    return sum(sum(nums[i:j]) * (j - i) < k for i in range(len(nums)) for j in range(i + 1, len(nums) + 1))


SCORE_LESS_THAN_K = ProblemSource(
    title="Count Subarrays With Score Less Than K",
    statement="""
The *score* of an array is its sum multiplied by its length. For example the score of `[1, 2, 3, 4, 5]`
is `15 * 5 = 75`.

Given an array of positive integers `nums` and an integer `k`, return how many non-empty contiguous
subarrays have a score **strictly less** than `k`.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^5`
- `1 <= k <= 10^15`
""",
    signature=function("countSubarrays", [("nums", "int[]"), ("k", "long")], "long"),
    reference=_count_score_less,
    brute=_count_score_less_brute,
    brute_input_limit=250,
    examples=[
        Example(
            [[2, 1, 4, 3, 5], 10], "Six subarrays score below 10, e.g. [2] (2), [2,1] (6), [1,4] (10 is not below)."
        ),
        Example([[1, 1, 1], 5], "All single elements and pairs qualify (score 1 or 4); the whole array scores 9."),
    ],
    edge_cases=[[[1], 1], [[1], 2], [[100000], 10**15], [[5, 5, 5, 5], 21]],
    generator=lambda rng: [
        ints(rng, pick_n(rng, 1, 40, big=4500), 1, rng.choice([10, 1000])),
        rng.randint(1, rng.choice([100, 10**6, 10**12])),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Count Substrings With K-Frequency Characters II


def _k_frequency_substrings(s: str, k: int) -> int:
    counts = [0] * 26
    lo = total = 0
    for hi, c in enumerate(s):
        counts[ord(c) - 97] += 1
        while counts[ord(c) - 97] >= k:
            total += len(s) - hi
            counts[ord(s[lo]) - 97] -= 1
            lo += 1
    return total


def _k_frequency_brute(s: str, k: int) -> int:
    count = 0
    for i in range(len(s)):
        seen: Counter[str] = Counter()
        for j in range(i, len(s)):
            seen[s[j]] += 1
            count += max(seen.values()) >= k
    return count


K_FREQUENCY_SUBSTRINGS = ProblemSource(
    title="Count Substrings With K-Frequency Characters II",
    statement="""
Given a lowercase string `s` and an integer `k`, count the substrings of `s` in which **at least one**
character appears `k` or more times.

The input can be long, so aim for linear time.
""",
    constraints="""
- `1 <= s.length <= 3 * 10^5`
- `1 <= k <= s.length`
- `s` consists of lowercase English letters
""",
    signature=function("numberOfSubstrings", [("s", "string"), ("k", "int")], "long"),
    reference=_k_frequency_substrings,
    brute=_k_frequency_brute,
    brute_input_limit=150,
    examples=[
        Example(["abacb", 2], '"aba", "abac", "abacb" and "bacb" each have a letter at least twice.'),
        Example(["abcde", 1], "With k = 1 every one of the 15 substrings counts."),
    ],
    edge_cases=[["a", 1], ["a", 2], ["aa", 2], ["abc", 3], ["zzzz", 3]],
    generator=lambda rng: [
        (s := word(rng, pick_n(rng, 1, 40, big=20000), "abc" if rng.random() < 0.7 else string.ascii_lowercase)),
        rng.randint(1, min(len(s), 5)),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Substring with Concatenation of All Words


def _find_substring(s: str, words: list[str]) -> list[int]:
    size, count = len(words[0]), len(words)
    need = Counter(words)
    out = []
    for offset in range(size):
        lo, seen, used = offset, Counter(), 0
        for hi in range(offset, len(s) - size + 1, size):
            chunk = s[hi : hi + size]
            if chunk not in need:
                lo, seen, used = hi + size, Counter(), 0
                continue
            seen[chunk] += 1
            used += 1
            while seen[chunk] > need[chunk]:
                seen[s[lo : lo + size]] -= 1
                used -= 1
                lo += size
            if used == count:
                out.append(lo)
                seen[s[lo : lo + size]] -= 1
                used -= 1
                lo += size
    return sorted(out)


def _find_substring_brute(s: str, words: list[str]) -> list[int]:
    size, total, need = len(words[0]), len(words[0]) * len(words), Counter(words)
    return [
        i
        for i in range(len(s) - total + 1)
        if Counter(s[i + j * size : i + (j + 1) * size] for j in range(len(words))) == need
    ]


def _concat_gen(rng):
    size = rng.randint(1, 3)
    words = [word(rng, size, "ab") for _ in range(rng.randint(1, 4))]
    pieces = [word(rng, rng.randint(0, 4), "ab")]
    for _ in range(pick_n(rng, 1, 8, big=400)):
        order = words[:]
        rng.shuffle(order)
        pieces.append("".join(order) if rng.random() < 0.6 else word(rng, rng.randint(1, 6), "ab"))
    return ["".join(pieces), words]


CONCATENATION = ProblemSource(
    title="Substring with Concatenation of All Words",
    statement="""
You are given a string `s` and an array `words` of strings that all have the **same length**. A
*concatenated substring* is a substring of `s` formed by joining every word of `words` exactly once, in
any order (a word listed twice must appear twice).

Return the starting indices of all concatenated substrings of `s`, in any order.
""",
    constraints="""
- `1 <= s.length <= 10^4`
- `1 <= words.length <= 5000`
- `1 <= words[i].length <= 30`, all words have the same length
- `s` and `words[i]` consist of lowercase English letters
""",
    signature=function("findSubstring", [("s", "string"), ("words", "string[]")], "int[]"),
    reference=_find_substring,
    brute=_find_substring_brute,
    compare="unordered",
    examples=[
        Example(["barfoothefoobarman", ["foo", "bar"]], '"barfoo" starts at 0 and "foobar" at 9.'),
        Example(
            ["wordgoodgoodgoodbestword", ["word", "good", "best", "word"]], '"word" is needed twice; there is no match.'
        ),
        Example(["barfoofoobarthefoobarman", ["bar", "foo", "the"]], "Matches start at 6, 9 and 12."),
    ],
    edge_cases=[["a", ["a"]], ["a", ["b"]], ["aaa", ["a", "a"]], ["ab", ["ab", "ab"]], ["abab", ["ab", "ba"]]],
    generator=_concat_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Binary Subarrays With Sum


def _num_subarrays_with_sum(nums: list[int], goal: int) -> int:
    prefix: Counter[int] = Counter({0: 1})
    total = count = 0
    for x in nums:
        total += x
        count += prefix[total - goal]
        prefix[total] += 1
    return count


BINARY_SUBARRAYS = ProblemSource(
    title="Binary Subarrays With Sum",
    statement="""
Given a binary array `nums` and an integer `goal`, return the number of non-empty contiguous subarrays
whose elements add up to `goal`.
""",
    constraints="""
- `1 <= nums.length <= 3 * 10^4`
- `nums[i]` is `0` or `1`
- `0 <= goal <= nums.length`
""",
    signature=function("numSubarraysWithSum", [("nums", "int[]"), ("goal", "int")], "int"),
    reference=_num_subarrays_with_sum,
    brute=lambda nums, goal: sum(sum(nums[i:j]) == goal for i in range(len(nums)) for j in range(i + 1, len(nums) + 1)),
    brute_input_limit=200,
    examples=[
        Example([[1, 0, 1, 0, 1], 2], "Four subarrays sum to 2."),
        Example([[0, 0, 0, 0, 0], 0], "All 15 subarrays sum to 0."),
    ],
    edge_cases=[[[1], 1], [[1], 0], [[0], 0], [[1, 1, 1], 3], [[0, 1, 0], 1]],
    generator=lambda rng: [
        (n := [int(rng.random() < 0.4) for _ in range(pick_n(rng, 1, 40, big=5000))]),
        rng.randint(0, min(len(n), 5)),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Permutation in String


def _check_inclusion(s1: str, s2: str) -> bool:
    if len(s1) > len(s2):
        return False
    need, window = Counter(s1), Counter(s2[: len(s1)])
    if need == window:
        return True
    for i in range(len(s1), len(s2)):
        window[s2[i]] += 1
        window[s2[i - len(s1)]] -= 1
        if window[s2[i - len(s1)]] == 0:
            del window[s2[i - len(s1)]]
        if window == need:
            return True
    return False


PERMUTATION_IN_STRING = ProblemSource(
    title="Permutation in String",
    statement="""
Given two strings `s1` and `s2`, return `true` if some rearrangement of `s1` appears in `s2` as a
contiguous substring.
""",
    constraints="""
- `1 <= s1.length, s2.length <= 10^4`
- both strings consist of lowercase English letters
""",
    signature=function("checkInclusion", [("s1", "string"), ("s2", "string")], "bool"),
    reference=_check_inclusion,
    brute=lambda s1, s2: any(Counter(s2[i : i + len(s1)]) == Counter(s1) for i in range(len(s2) - len(s1) + 1)),
    brute_input_limit=400,
    examples=[
        Example(["ab", "eidbaooo"], 's2 contains "ba".'),
        Example(["ab", "eidboaoo"], 'No window of s2 is a rearrangement of "ab".'),
    ],
    edge_cases=[["a", "a"], ["ab", "a"], ["adc", "dcda"], ["hello", "ooolleoooleh"], ["aab", "baba"]],
    generator=lambda rng: [word(rng, rng.randint(1, 5), "abc"), word(rng, pick_n(rng, 1, 40, big=5000), "abcd")],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Substrings Containing All Three Characters


def _all_three(s: str) -> int:
    last = {"a": -1, "b": -1, "c": -1}
    total = 0
    for i, c in enumerate(s):
        last[c] = i
        total += min(last.values()) + 1
    return total


ALL_THREE = ProblemSource(
    title="Number of Substrings Containing All Three Characters",
    statement="""
The string `s` contains only the letters `a`, `b` and `c`. Return how many substrings of `s` contain at
least one `a`, at least one `b` and at least one `c`.
""",
    constraints="""
- `3 <= s.length <= 5 * 10^4`
- `s` consists of the letters `a`, `b` and `c`
""",
    signature=function("numberOfSubstrings", [("s", "string")], "int"),
    reference=_all_three,
    brute=lambda s: sum(set(s[i:j]) >= {"a", "b", "c"} for i in range(len(s)) for j in range(i + 1, len(s) + 1)),
    brute_input_limit=200,
    examples=[
        Example(["abcabc"], 'Ten substrings contain all three letters, e.g. "abc", "abca", "bca".'),
        Example(["aaacb"], '"aaacb", "aacb" and "acb".'),
        Example(["abc"]),
    ],
    edge_cases=[["aaa"], ["cba"], ["aabbcc"], ["cccab"]],
    generator=lambda rng: [word(rng, pick_n(rng, 3, 40, big=15000), "abc")],
    random_count=8,
)


# ---------------------------------------------------------------- Find the Index of the First Occurrence in a String


def _str_str(haystack: str, needle: str) -> int:
    failure = [0] * len(needle)
    k = 0
    for i in range(1, len(needle)):
        while k and needle[i] != needle[k]:
            k = failure[k - 1]
        if needle[i] == needle[k]:
            k += 1
        failure[i] = k
    k = 0
    for i, c in enumerate(haystack):
        while k and c != needle[k]:
            k = failure[k - 1]
        if c == needle[k]:
            k += 1
        if k == len(needle):
            return i - k + 1
    return -1


FIRST_OCCURRENCE = ProblemSource(
    title="Find the Index of the First Occurrence in a String",
    statement="""
Given two strings `haystack` and `needle`, return the index of the first place where `needle` occurs as a
substring of `haystack`, or `-1` if it never does.
""",
    constraints="""
- `1 <= haystack.length, needle.length <= 10^4`
- both strings consist of lowercase English letters
""",
    signature=function("strStr", [("haystack", "string"), ("needle", "string")], "int"),
    reference=_str_str,
    brute=lambda haystack, needle: haystack.find(needle),
    examples=[
        Example(["sadbutsad", "sad"], '"sad" first occurs at index 0.'),
        Example(["leetcode", "leeto"], '"leeto" does not occur.'),
    ],
    edge_cases=[
        ["a", "a"],
        ["a", "b"],
        ["abc", "c"],
        ["aaa", "aaaa"],
        ["aabaaabaaac", "aabaaac"],
        ["mississippi", "issip"],
    ],
    generator=lambda rng: [
        (h := word(rng, pick_n(rng, 1, 40, big=5000), "ab")),
        h[(i := rng.randrange(len(h))) : i + rng.randint(1, 8)]
        if rng.random() < 0.6
        else word(rng, rng.randint(1, 8), "ab"),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Max Consecutive Ones III


def _longest_ones(nums: list[int], k: int) -> int:
    lo = zeros = best = 0
    for hi, x in enumerate(nums):
        zeros += x == 0
        while zeros > k:
            zeros -= nums[lo] == 0
            lo += 1
        best = max(best, hi - lo + 1)
    return best


MAX_ONES_III = ProblemSource(
    title="Max Consecutive Ones III",
    statement="""
Given a binary array `nums` and an integer `k`, you may flip at most `k` zeros into ones. Return the
length of the longest run of consecutive ones you can obtain.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `nums[i]` is `0` or `1`
- `0 <= k <= nums.length`
""",
    signature=function("longestOnes", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_longest_ones,
    brute=lambda nums, k: max(
        (j - i for i in range(len(nums)) for j in range(i, len(nums) + 1) if nums[i:j].count(0) <= k), default=0
    ),
    brute_input_limit=200,
    examples=[
        Example([[1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2], "Flip two zeros to get six ones in a row."),
        Example([[0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3], "The best run has length 10."),
    ],
    edge_cases=[[[0], 0], [[0], 1], [[1], 0], [[0, 0, 0], 3], [[1, 0, 1], 0]],
    generator=lambda rng: [
        (n := [int(rng.random() < 0.6) for _ in range(pick_n(rng, 1, 40, big=5000))]),
        rng.randint(0, min(len(n), 6)),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Subarray With Diff At Most Limit


def _longest_diff_limit(nums: list[int], limit: int) -> int:
    highs: deque[int] = deque()
    lows: deque[int] = deque()
    lo = best = 0
    for hi, x in enumerate(nums):
        while highs and highs[-1] < x:
            highs.pop()
        while lows and lows[-1] > x:
            lows.pop()
        highs.append(x)
        lows.append(x)
        while highs[0] - lows[0] > limit:
            if highs[0] == nums[lo]:
                highs.popleft()
            if lows[0] == nums[lo]:
                lows.popleft()
            lo += 1
        best = max(best, hi - lo + 1)
    return best


LONGEST_DIFF_LIMIT = ProblemSource(
    title="Longest Subarray With Diff At Most Limit",
    statement="""
Given an integer array `nums` and an integer `limit`, return the length of the longest non-empty
contiguous subarray in which the difference between **any two** elements is at most `limit` (that is,
its maximum minus its minimum is at most `limit`).
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^9`
- `0 <= limit <= 10^9`
""",
    signature=function("longestSubarray", [("nums", "int[]"), ("limit", "int")], "int"),
    reference=_longest_diff_limit,
    brute=lambda nums, limit: max(
        j - i for i in range(len(nums)) for j in range(i + 1, len(nums) + 1) if max(nums[i:j]) - min(nums[i:j]) <= limit
    ),
    brute_input_limit=200,
    examples=[
        Example([[8, 2, 4, 7], 4], "[2, 4] and [4, 7] have difference at most 4; length 2."),
        Example([[10, 1, 2, 4, 7, 2], 5], "[2, 4, 7, 2] has max 7 and min 2."),
        Example([[4, 2, 2, 2, 4, 4, 2, 2], 0], "Three equal 2s in a row."),
    ],
    edge_cases=[[[1], 0], [[1, 1000000000], 999999999], [[1, 1000000000], 1000000000], [[5, 5, 5], 0]],
    generator=lambda rng: [
        ints(rng, pick_n(rng, 1, 40, big=4500), 1, rng.choice([10, 10**9])),
        rng.randint(0, rng.choice([5, 10**9])),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Subarray Product Less Than K


def _product_less_than_k(nums: list[int], k: int) -> int:
    if k <= 1:
        return 0
    product, lo, count = 1, 0, 0
    for hi, x in enumerate(nums):
        product *= x
        while product >= k:
            product //= nums[lo]
            lo += 1
        count += hi - lo + 1
    return count


def _product_brute(nums: list[int], k: int) -> int:
    count = 0
    for i in range(len(nums)):
        product = 1
        for j in range(i, len(nums)):
            product *= nums[j]
            count += product < k
    return count


PRODUCT_LESS_THAN_K = ProblemSource(
    title="Subarray Product Less Than K",
    statement="""
Given an array of positive integers `nums` and an integer `k`, return the number of contiguous subarrays
whose product is **strictly less** than `k`.
""",
    constraints="""
- `1 <= nums.length <= 3 * 10^4`
- `1 <= nums[i] <= 1000`
- `0 <= k <= 10^6`
""",
    signature=function("numSubarrayProductLessThanK", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_product_less_than_k,
    brute=_product_brute,
    brute_input_limit=200,
    examples=[
        Example([[10, 5, 2, 6], 100], "Eight subarrays: [10], [5], [2], [6], [10,5], [5,2], [2,6], [5,2,6]."),
        Example([[1, 2, 3], 0], "Nothing is below 0."),
    ],
    edge_cases=[[[1], 1], [[1], 2], [[1, 1, 1], 2], [[1000, 1000], 1000000]],
    generator=lambda rng: [
        ints(rng, pick_n(rng, 1, 40, big=5000), 1, rng.choice([3, 1000])),
        rng.randint(0, rng.choice([100, 10**6])),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Count Number of Nice Subarrays


def _nice_subarrays(nums: list[int], k: int) -> int:
    prefix: defaultdict[int, int] = defaultdict(int)
    prefix[0] = 1
    odd = count = 0
    for x in nums:
        odd += x % 2
        count += prefix[odd - k]
        prefix[odd] += 1
    return count


NICE_SUBARRAYS = ProblemSource(
    title="Count Number of Nice Subarrays",
    statement="""
A contiguous subarray is *nice* if it contains exactly `k` odd numbers. Given an integer array `nums`
and `k`, return the number of nice subarrays.
""",
    constraints="""
- `1 <= nums.length <= 5 * 10^4`
- `1 <= nums[i] <= 10^5`
- `1 <= k <= nums.length`
""",
    signature=function("numberOfSubarrays", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_nice_subarrays,
    brute=lambda nums, k: sum(
        sum(x % 2 for x in nums[i:j]) == k for i in range(len(nums)) for j in range(i + 1, len(nums) + 1)
    ),
    brute_input_limit=200,
    examples=[
        Example([[1, 1, 2, 1, 1], 3], "[1,1,2,1] and [1,2,1,1]."),
        Example([[2, 4, 6], 1], "There are no odd numbers."),
        Example([[2, 2, 2, 1, 2, 2, 1, 2, 2, 2], 2], "16 subarrays contain exactly two odd numbers."),
    ],
    edge_cases=[[[1], 1], [[2], 1], [[1, 1, 1], 3], [[1, 2, 1], 1]],
    generator=lambda rng: [(n := ints(rng, pick_n(rng, 1, 40, big=5000), 1, 20)), rng.randint(1, min(len(n), 5))],
    random_count=8,
)


PROBLEMS = [
    CHARACTER_REPLACEMENT,
    MIN_WINDOW,
    LONGEST_SUBSTRING,
    BEST_TIME,
    REPEATED_DNA,
    SLIDING_WINDOW_MAX,
    MIN_WINDOW_SUBSEQUENCE,
    MIN_SUBARRAY_SUM,
    FRUIT_BASKETS,
    MAX_FREQUENCY,
    MAX_AVERAGE,
    DIET_PLAN,
    K_DIFFERENT,
    SCORE_LESS_THAN_K,
    K_FREQUENCY_SUBSTRINGS,
    CONCATENATION,
    BINARY_SUBARRAYS,
    PERMUTATION_IN_STRING,
    ALL_THREE,
    FIRST_OCCURRENCE,
    MAX_ONES_III,
    LONGEST_DIFF_LIMIT,
    PRODUCT_LESS_THAN_K,
    NICE_SUBARRAYS,
]
