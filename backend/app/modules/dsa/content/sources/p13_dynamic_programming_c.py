"""Pattern 13: Dynamic Programming (part 3 of 3). Original statements; outputs come from `reference`."""

from __future__ import annotations

import bisect
import heapq
import itertools
from collections import Counter
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sample, word

PATTERN_NUMBER = 13
_MOD = 10**9 + 7


# ---------------------------------------------------------------- Soup Servings


def _soup_servings(n: int) -> float:
    if n > 4800:
        return 1.0
    units = (n + 24) // 25

    @cache
    def prob(a: int, b: int) -> float:
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return 0.25 * (prob(a - 4, b) + prob(a - 3, b - 1) + prob(a - 2, b - 2) + prob(a - 1, b - 3))

    return prob(units, units)


def _soup_brute(n: int) -> float:
    if n > 4800:
        return NotImplemented
    dist = {(n, n): 1.0}
    result = 0.0
    while dist:
        nxt: dict[tuple[int, int], float] = {}
        for (a, b), p in dist.items():
            for da, db in ((100, 0), (75, 25), (50, 50), (25, 75)):
                na, nb = a - da, b - db
                if na <= 0 and nb <= 0:
                    result += p * 0.25 * 0.5
                elif na <= 0:
                    result += p * 0.25
                elif nb > 0:
                    nxt[(na, nb)] = nxt.get((na, nb), 0.0) + p * 0.25
        dist = nxt
    return result


SOUP_SERVINGS = ProblemSource(
    title="Soup Servings",
    statement="""
Two soups, A and B, start with `n` ml each. Each turn one of four operations is chosen with equal probability:

1. serve 100 ml of A and 0 ml of B,
2. serve 75 ml of A and 25 ml of B,
3. serve 50 ml of A and 50 ml of B,
4. serve 25 ml of A and 75 ml of B.

If a soup has less than the amount asked for, all of it is served. Serving stops as soon as at least one soup is empty. Return the probability
that A empties first, plus half the probability that both empty at the same time. Answers within `10^-5` are accepted.
""",
    constraints="""
- `0 <= n <= 10^9`
""",
    signature=function("soupServings", [("n", "int")], "double"),
    reference=_soup_servings,
    brute=_soup_brute,
    compare="float_tolerance",
    examples=[Example([50], "0.625."), Example([100], "0.71875.")],
    edge_cases=[[0], [1], [25], [4800], [1000000000]],
    generator=lambda rng: [rng.choice([rng.randint(0, 500), rng.randint(0, 5000), rng.randint(0, 10**9)])],
    random_count=6,
)


# ---------------------------------------------------------------- Number of People Aware of a Secret


def _people_aware(n: int, delay: int, forget: int) -> int:
    learned = [0] * (n + 1)
    learned[1] = 1
    sharing = 0
    for day in range(2, n + 1):
        sharing += learned[day - delay] if day - delay >= 1 else 0
        sharing -= learned[day - forget] if day - forget >= 1 else 0
        learned[day] = sharing % _MOD
    return sum(learned[max(1, n - forget + 1) :]) % _MOD


def _aware_brute(n: int, delay: int, forget: int) -> int:
    people = [1]  # day each person learned the secret
    for day in range(2, n + 1):
        people += [day for d in people if d + delay <= day < d + forget]
    return sum(1 for d in people if n < d + forget) % _MOD


AWARE_OF_SECRET = ProblemSource(
    title="Number of People Aware of a Secret",
    statement="""
On day 1 one person learns a secret. Each person, starting `delay` days after learning it, tells one new person every day. Each person forgets
the secret `forget` days after learning it and stops sharing that day (they can't share on the day they forget). Return how many people know
the secret at the end of day `n`, modulo `10^9 + 7`.
""",
    constraints="""
- `2 <= n <= 1000`
- `1 <= delay < forget <= n`
""",
    signature=function("peopleAwareOfSecret", [("n", "int"), ("delay", "int"), ("forget", "int")], "int"),
    reference=_people_aware,
    brute=lambda n, delay, forget: _aware_brute(n, delay, forget) if n <= 18 else NotImplemented,
    examples=[Example([6, 2, 4], "Five people know it at the end of day 6."), Example([4, 1, 3])],
    edge_cases=[[2, 1, 2], [10, 1, 10], [1000, 1, 1000]],
    generator=lambda rng: [(n := rng.randint(2, rng.choice([18, 1000]))), (d := rng.randint(1, n - 1)), rng.randint(d + 1, n)],
    random_count=8,
)


# ---------------------------------------------------------------- Edit Distance


def _min_distance(word1: str, word2: str) -> int:
    prev = list(range(len(word2) + 1))
    for i, a in enumerate(word1, start=1):
        cur = [i]
        for j, b in enumerate(word2, start=1):
            cur.append(prev[j - 1] if a == b else 1 + min(prev[j - 1], prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]


def _edit_brute(word1: str, word2: str) -> int:
    @cache
    def best(i: int, j: int) -> int:
        if i == len(word1):
            return len(word2) - j
        if j == len(word2):
            return len(word1) - i
        if word1[i] == word2[j]:
            return best(i + 1, j + 1)
        return 1 + min(best(i + 1, j), best(i, j + 1), best(i + 1, j + 1))

    return best(0, 0)


EDIT_DISTANCE = ProblemSource(
    title="Edit Distance",
    statement="""
Return the minimum number of single-character insertions, deletions and replacements needed to turn `word1` into `word2`.
""",
    constraints="""
- `0 <= word1.length, word2.length <= 500`
- lowercase English letters only
""",
    signature=function("minDistance", [("word1", "string"), ("word2", "string")], "int"),
    reference=_min_distance,
    brute=_edit_brute,
    brute_input_limit=300,
    examples=[Example(["horse", "ros"], "horse -> rorse -> rose -> ros."), Example(["intention", "execution"])],
    edge_cases=[["", ""], ["", "abc"], ["abc", ""], ["a", "a"], ["ab", "ba"]],
    generator=lambda rng: [word(rng, pick_n(rng, 0, 12, big=500), "abc"), word(rng, pick_n(rng, 0, 12, big=500), "abcd")],
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Unique Paths II


def _unique_paths_with_obstacles(obstacleGrid: list[list[int]]) -> int:
    n = len(obstacleGrid[0])
    ways = [1] + [0] * (n - 1)
    for row in obstacleGrid:
        for j in range(n):
            if row[j]:
                ways[j] = 0
            elif j:
                ways[j] += ways[j - 1]
    return ways[-1]


def _obstacle_brute(obstacleGrid: list[list[int]]) -> int:
    m, n = len(obstacleGrid), len(obstacleGrid[0])
    if m + n > 12:
        return NotImplemented
    count = 0
    for moves in set(itertools.permutations("R" * (n - 1) + "D" * (m - 1))):
        r = c = 0
        ok = obstacleGrid[0][0] == 0
        for step in moves:
            r, c = (r + 1, c) if step == "D" else (r, c + 1)
            ok = ok and obstacleGrid[r][c] == 0
        count += ok
    return count


def _obstacle_gen(rng):
    m, n = pick_n(rng, 1, 5, big=17), pick_n(rng, 1, 5, big=17)
    return [[[int(rng.random() < 0.15) for _ in range(n)] for _ in range(m)]]


UNIQUE_PATHS_II = ProblemSource(
    title="Unique Paths II",
    statement="""
A robot moves only right or down from the top-left to the bottom-right of the grid, where `1` marks an obstacle and `0` a free cell. Return the
number of distinct paths that avoid every obstacle.
""",
    constraints="""
- `1 <= m, n <= 100`, and the grid is sized so the answer fits a signed 32-bit integer
- `obstacleGrid[i][j]` is `0` or `1`
""",
    signature=function("uniquePathsWithObstacles", [("obstacleGrid", "int[][]")], "int"),
    reference=_unique_paths_with_obstacles,
    brute=_obstacle_brute,
    examples=[Example([[[0, 0, 0], [0, 1, 0], [0, 0, 0]]], "Two paths go around the centre."), Example([[[0, 1], [0, 0]]])],
    edge_cases=[[[[1]]], [[[0]]], [[[0, 0], [0, 1]]]],
    generator=lambda rng: _obstacle_gen(rng) if rng.random() < 0.8 else [[[0] * 16 for _ in range(16)]],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Cost For Tickets


def _mincost_tickets(days: list[int], costs: list[int]) -> int:
    travel = set(days)
    best = [0] * (days[-1] + 1)
    for d in range(1, days[-1] + 1):
        if d not in travel:
            best[d] = best[d - 1]
            continue
        best[d] = min(best[max(0, d - 1)] + costs[0], best[max(0, d - 7)] + costs[1], best[max(0, d - 30)] + costs[2])
    return best[-1]


def _tickets_brute(days: list[int], costs: list[int]) -> int:
    @cache
    def best(i: int) -> int:
        if i == len(days):
            return 0
        options = []
        for span, cost in zip((1, 7, 30), costs, strict=True):
            j = bisect.bisect_left(days, days[i] + span)
            options.append(cost + best(j))
        return min(options)

    return best(0)


TICKETS = ProblemSource(
    title="Minimum Cost For Tickets",
    statement="""
You will travel on the days listed in `days` (strictly increasing, within 1..365). Passes cost `costs[0]` for 1 day, `costs[1]` for 7 consecutive
days and `costs[2]` for 30 consecutive days. Return the minimum total cost to cover every travel day.
""",
    constraints="""
- `1 <= days.length <= 365`, `1 <= days[i] <= 365`, strictly increasing
- `costs.length == 3`, `1 <= costs[i] <= 1000`
""",
    signature=function("mincostTickets", [("days", "int[]"), ("costs", "int[]")], "int"),
    reference=_mincost_tickets,
    brute=_tickets_brute,
    examples=[Example([[1, 4, 6, 7, 8, 20], [2, 7, 15]], "A 1-day pass, a 7-day pass and another 1-day pass: 11."), Example([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30, 31], [2, 7, 15]])],
    edge_cases=[[[1], [5, 1, 1]], [[365], [1, 2, 3]], [list(range(1, 31)), [1, 100, 10]]],
    generator=lambda rng: [sorted(sample(rng, range(1, 366), pick_n(rng, 1, 30, big=365))), [rng.randint(1, 1000) for _ in range(3)]],
    random_count=8,
)


# ---------------------------------------------------------------- Count Palindromic Subsequences


def _count_palindromes(s: str) -> int:
    n = len(s)
    total = 0
    left = [[0] * 100 for _ in range(n + 1)]  # left[i][ab]: pairs "ab" in s[:i]
    counts = [0] * 10
    for i, ch in enumerate(s):
        left[i + 1] = left[i][:]
        d = int(ch)
        for a in range(10):
            left[i + 1][a * 10 + d] += counts[a]
        counts[d] += 1
    right = [0] * 100
    counts = [0] * 10
    for i in range(n - 1, -1, -1):
        d = int(s[i])
        for ab in range(100):
            a, b = divmod(ab, 10)
            total += left[i][ab] * right[b * 10 + a]
        for c in range(10):
            right[d * 10 + c] += counts[c]
        counts[d] += 1
    return total % _MOD


def _palindromes_brute(s: str) -> int:
    return sum(1 for c in itertools.combinations(s, 5) if c == c[::-1]) % _MOD


COUNT_PALINDROMIC = ProblemSource(
    title="Count Palindromic Subsequences",
    statement="""
`s` is a string of digits. Return the number of its subsequences of **length 5** that are palindromes, modulo `10^9 + 7`. Subsequences taken from
different positions count separately.
""",
    constraints="""
- `1 <= s.length <= 10^4`
- `s` consists of digits
""",
    signature=function("countPalindromes", [("s", "string")], "int"),
    reference=_count_palindromes,
    brute=lambda s: _palindromes_brute(s) if len(s) <= 18 else NotImplemented,
    examples=[Example(["103301"], "\"10301\" twice."), Example(["0000000"], "Every choice of 5 zeros: 21."), Example(["9999900000"])],
    edge_cases=[["1"], ["12321"], ["11111"], ["1234"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 16, big=1500), rng.choice(["01", "0123456789", "123"]))],
    random_count=8,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Delete and Earn


def _delete_and_earn(nums: list[int]) -> int:
    points = Counter()
    for x in nums:
        points[x] += x
    take = skip = 0
    prev = None
    for x in sorted(points):
        best_before = max(take, skip)
        if prev is not None and x == prev + 1:
            take, skip = skip + points[x], best_before
        else:
            take, skip = best_before + points[x], best_before
        prev = x
    return max(take, skip)


def _earn_brute(nums: list[int]) -> int:
    values = sorted(set(nums))
    best = 0
    for mask in range(1 << len(values)):
        chosen = [values[i] for i in range(len(values)) if mask >> i & 1]
        if all(b - a > 1 for a, b in itertools.pairwise(chosen)):
            best = max(best, sum(x for x in nums if x in chosen))
    return best


DELETE_AND_EARN = ProblemSource(
    title="Delete and Earn",
    statement="""
In one operation pick any `nums[i]`, earn `nums[i]` points and delete it, and also delete **every** element equal to `nums[i] - 1` or
`nums[i] + 1` (earning nothing for those). Repeat as long as you like and return the maximum total points.
""",
    constraints="""
- `1 <= nums.length <= 2 * 10^4`
- `1 <= nums[i] <= 10^4`
""",
    signature=function("deleteAndEarn", [("nums", "int[]")], "int"),
    reference=_delete_and_earn,
    brute=lambda nums: _earn_brute(nums) if len(set(nums)) <= 14 else NotImplemented,
    examples=[Example([[3, 4, 2]], "Take 4 (deleting 3), then 2: 6."), Example([[2, 2, 3, 3, 3, 4]], "Take all three 3s: 9.")],
    edge_cases=[[[1]], [[1, 1, 1, 2]], [[8, 10, 4, 9, 1, 3, 5, 9, 4, 10]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=5000), 1, rng.choice([12, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Longest String Chain


def _longest_str_chain(words: list[str]) -> int:
    best: dict[str, int] = {}
    for w in sorted(words, key=len):
        best[w] = 1 + max((best.get(w[:i] + w[i + 1 :], 0) for i in range(len(w))), default=0)
    return max(best.values())


def _chain_brute(words: list[str]) -> int:
    def predecessor(a: str, b: str) -> bool:
        return len(b) == len(a) + 1 and any(b[:i] + b[i + 1 :] == a for i in range(len(b)))

    @cache
    def longest_from(w: str) -> int:
        return 1 + max((longest_from(v) for v in words if predecessor(w, v)), default=0)

    return max(longest_from(w) for w in words)


def _chain_gen(rng):
    words = set()
    for _ in range(rng.randint(1, rng.choice([8, 60]))):
        base = word(rng, rng.randint(1, 3), "ab")
        words.add(base)
        for _ in range(rng.randint(0, 4)):
            i = rng.randint(0, len(base))
            base = base[:i] + rng.choice("abc") + base[i:]
            words.add(base)
    return [sorted(words)]


STRING_CHAIN = ProblemSource(
    title="Longest String Chain",
    statement="""
Word `a` is a *predecessor* of word `b` if inserting exactly one letter anywhere in `a` (without reordering) gives `b`. A *word chain* is a
sequence where each word is a predecessor of the next. Return the length of the longest word chain that uses words from `words` (each at most
once).
""",
    constraints="""
- `1 <= words.length <= 1000`
- `1 <= words[i].length <= 16`, lowercase letters, all distinct
""",
    signature=function("longestStrChain", [("words", "string[]")], "int"),
    reference=_longest_str_chain,
    brute=_chain_brute,
    brute_input_limit=400,
    examples=[Example([["a", "b", "ba", "bca", "bda", "bdca"]], "a -> ba -> bda -> bdca."), Example([["xbc", "pcxbcf", "xb", "cxbc", "pcxbc"]]), Example([["abcd", "dbqca"]])],
    edge_cases=[[["a"]], [["a", "ab", "abc", "abcd"]], [["ba", "ab"]]],
    generator=_chain_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Last Stone Weight II


def _last_stone_ii(stones: list[int]) -> int:
    total = sum(stones)
    reachable = 1
    for s in stones:
        reachable |= reachable << s
    half = total // 2
    while not reachable >> half & 1:
        half -= 1
    return total - 2 * half


def _stone_ii_brute(stones: list[int]) -> int:
    return min(abs(sum(s if mask >> i & 1 else -s for i, s in enumerate(stones))) for mask in range(1 << len(stones)))


LAST_STONE_II = ProblemSource(
    title="Last Stone Weight II",
    statement="""
Smash stones two at a time, in any order you choose: stones of weights `x <= y` become one stone of weight `y - x` (or both vanish if `x == y`).
Continue until at most one stone remains and return the smallest possible weight of that stone (`0` if none remains).
""",
    constraints="""
- `1 <= stones.length <= 30`
- `1 <= stones[i] <= 100`
""",
    signature=function("lastStoneWeightII", [("stones", "int[]")], "int"),
    reference=_last_stone_ii,
    brute=lambda stones: _stone_ii_brute(stones) if len(stones) <= 16 else NotImplemented,
    examples=[Example([[2, 7, 4, 1, 8, 1]], "The best order leaves a stone of weight 1."), Example([[31, 26, 33, 21, 40]])],
    edge_cases=[[[1]], [[3, 3]], [[1, 2]], [[100] * 30]],
    generator=lambda rng: [ints(rng, rng.randint(1, rng.choice([14, 30])), 1, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Stickers to Spell Word


def _min_stickers(stickers: list[str], target: str) -> int:
    sticker_counts = [Counter(s) for s in stickers]

    @cache
    def best(remaining: str) -> float:
        if not remaining:
            return 0
        need = Counter(remaining)
        answer = float("inf")
        for sc in sticker_counts:
            if remaining[0] not in sc:
                continue
            left = need - sc
            answer = min(answer, 1 + best("".join(sorted(left.elements()))))
        return answer

    result = best("".join(sorted(target)))
    return -1 if result == float("inf") else int(result)


def _stickers_brute(stickers: list[str], target: str) -> int:
    need = Counter(target)
    counts = [Counter(s) for s in stickers]
    for k in range(1, len(target) + 1):
        for combo in itertools.combinations_with_replacement(range(len(stickers)), k):
            have = Counter()
            for i in combo:
                have += counts[i]
            if all(have[c] >= n for c, n in need.items()):
                return k
    return -1


def _stickers_gen(rng):
    stickers = [word(rng, rng.randint(1, 6), "abcde") for _ in range(rng.randint(1, 5))]
    return [stickers, word(rng, rng.randint(1, rng.choice([5, 12])), "abcdef" if rng.random() < 0.2 else "abcde")]


STICKERS = ProblemSource(
    title="Stickers to Spell Word",
    statement="""
You have unlimited copies of each sticker in `stickers`; every sticker is a word. You may cut letters out of the stickers you use and rearrange
them. Return the minimum number of stickers needed to spell `target`, or `-1` if it's impossible.
""",
    constraints="""
- `1 <= stickers.length <= 50`, `1 <= stickers[i].length <= 10`
- `1 <= target.length <= 15`
- lowercase English letters only
""",
    signature=function("minStickers", [("stickers", "string[]"), ("target", "string")], "int"),
    reference=_min_stickers,
    brute=lambda stickers, target: _stickers_brute(stickers, target) if len(target) <= 6 and len(stickers) <= 5 else NotImplemented,
    examples=[Example([["with", "example", "science"], "thehat"], "Two \"with\" and one \"example\"."), Example([["notice", "possible"], "basicbasic"], "No 'a' anywhere.")],
    edge_cases=[[["a"], "a"], [["ab"], "aaaa"], [["abc"], "d"]],
    generator=_stickers_gen,
    random_count=8,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Target Sum


def _find_target_sum_ways(nums: list[int], target: int) -> int:
    ways = Counter({0: 1})
    for x in nums:
        nxt: Counter[int] = Counter()
        for total, count in ways.items():
            nxt[total + x] += count
            nxt[total - x] += count
        ways = nxt
    return ways[target]


def _target_sum_brute(nums: list[int], target: int) -> int:
    return sum(sum(s * x for s, x in zip(signs, nums, strict=True)) == target for signs in itertools.product((1, -1), repeat=len(nums)))


TARGET_SUM = ProblemSource(
    title="Target Sum",
    statement="""
Put a `+` or `-` sign in front of every number of `nums` and evaluate the expression. Return how many different sign choices make it equal
`target`.
""",
    constraints="""
- `1 <= nums.length <= 20`
- `0 <= nums[i] <= 1000`, `sum(nums) <= 1000`
- `-1000 <= target <= 1000`
""",
    signature=function("findTargetSumWays", [("nums", "int[]"), ("target", "int")], "int"),
    reference=_find_target_sum_ways,
    brute=lambda nums, target: _target_sum_brute(nums, target) if len(nums) <= 14 else NotImplemented,
    examples=[Example([[1, 1, 1, 1, 1], 3], "Five ways: one of the ones gets a minus."), Example([[1], 1])],
    edge_cases=[[[0], 0], [[0, 0, 1], 1], [[1000], -1000]],
    generator=lambda rng: [(v := ints(rng, rng.randint(1, 20), 0, rng.choice([3, 50]))), rng.randint(-sum(v), sum(v))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Sum Circular Subarray


def _max_subarray_circular(nums: list[int]) -> int:
    best_max = cur_max = best_min = cur_min = nums[0]
    for x in nums[1:]:
        cur_max = max(x, cur_max + x)
        best_max = max(best_max, cur_max)
        cur_min = min(x, cur_min + x)
        best_min = min(best_min, cur_min)
    total = sum(nums)
    return best_max if best_max < 0 else max(best_max, total - best_min)


def _circular_brute(nums: list[int]) -> int:
    n = len(nums)
    return max(sum(nums[(i + k) % n] for k in range(length)) for i in range(n) for length in range(1, n + 1))


MAX_CIRCULAR = ProblemSource(
    title="Maximum Sum Circular Subarray",
    statement="""
`nums` is a **circular** array (the end connects back to the start). Return the largest sum of a non-empty subarray; a subarray may wrap around
but may use each element at most once.
""",
    constraints="""
- `1 <= nums.length <= 3 * 10^4`
- `-3 * 10^4 <= nums[i] <= 3 * 10^4`
""",
    signature=function("maxSubarraySumCircular", [("nums", "int[]")], "int"),
    reference=_max_subarray_circular,
    brute=_circular_brute,
    brute_input_limit=150,
    examples=[Example([[1, -2, 3, -2]]), Example([[5, -3, 5]], "Wrapping: 5 + 5 = 10."), Example([[-3, -2, -3]], "All negative: take the largest single element.")],
    edge_cases=[[[7]], [[-1]], [[3, -1, 2, -1]], [[-2, 4, -5, 4, -5, 9, 4]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=4000), -rng.choice([10, 3 * 10**4]), rng.choice([10, 3 * 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Sum of 3 Non-Overlapping Subarrays


def _max_sum_of_three(nums: list[int], k: int) -> list[int]:
    sums = [sum(nums[:k])]
    for i in range(k, len(nums)):
        sums.append(sums[-1] + nums[i] - nums[i - k])
    n = len(sums)
    left, best = [0] * n, 0
    for i in range(n):
        if sums[i] > sums[best]:
            best = i
        left[i] = best
    right, best = [0] * n, n - 1
    for i in range(n - 1, -1, -1):
        if sums[i] >= sums[best]:
            best = i
        right[i] = best
    answer = None
    for mid in range(k, n - k):
        a, c = left[mid - k], right[mid + k]
        candidate = (sums[a] + sums[mid] + sums[c], [a, mid, c])
        if answer is None or candidate[0] > answer[0]:
            answer = candidate
    return answer[1]


def _three_brute(nums: list[int], k: int) -> list[int]:
    n = len(nums)
    best = None
    for a in range(n - 3 * k + 1):
        for b in range(a + k, n - 2 * k + 1):
            for c in range(b + k, n - k + 1):
                total = sum(nums[a : a + k]) + sum(nums[b : b + k]) + sum(nums[c : c + k])
                if best is None or total > best[0]:
                    best = (total, [a, b, c])
    return best[1]


def _three_gen(rng):
    k = rng.randint(1, rng.choice([3, 50]))
    nums = ints(rng, rng.randint(3 * k, 3 * k + rng.choice([6, 3000])), 1, rng.choice([5, 65535]))
    return [nums, k]


MAX_SUM_THREE = ProblemSource(
    title="Maximum Sum of 3 Non-Overlapping Subarrays",
    statement="""
Choose three non-overlapping subarrays of `nums`, each of length exactly `k`, with the largest total sum. Return their starting indices in
increasing order. If several choices tie, return the lexicographically smallest list of indices.
""",
    constraints="""
- `1 <= k <= nums.length / 3`
- `3 <= nums.length <= 2 * 10^4`
- `1 <= nums[i] < 2^16`
""",
    signature=function("maxSumOfThreeSubarrays", [("nums", "int[]"), ("k", "int")], "int[]"),
    reference=_max_sum_of_three,
    brute=lambda nums, k: _three_brute(nums, k) if len(nums) <= 30 else NotImplemented,
    examples=[Example([[1, 2, 1, 2, 6, 7, 5, 1], 2], "Subarrays [1,2], [2,6], [7,5] start at 0, 3, 5."), Example([[1, 2, 1, 2, 1, 2, 1, 2, 1], 2])],
    edge_cases=[[[1, 1, 1], 1], [[5, 5, 5, 5, 5, 5], 2], [[1, 1, 1, 9, 9, 9], 1]],
    generator=_three_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Coin Change II


def _change(amount: int, coins: list[int]) -> int:
    ways = [1] + [0] * amount
    for c in coins:
        for a in range(c, amount + 1):
            ways[a] += ways[a - c]
    return ways[amount]


def _change_brute(amount: int, coins: list[int]) -> int:
    @cache
    def count(i: int, left: int) -> int:
        if left == 0:
            return 1
        if i == len(coins):
            return 0
        return sum(count(i + 1, left - k * coins[i]) for k in range(left // coins[i] + 1))

    return count(0, amount)


COIN_CHANGE_II = ProblemSource(
    title="Coin Change II",
    statement="""
You have unlimited coins of each distinct denomination in `coins`. Return the number of combinations (ignoring order) that add up to exactly
`amount`. The answer fits in a signed 32-bit integer.
""",
    constraints="""
- `1 <= coins.length <= 300`
- `1 <= coins[i] <= 5000`, all distinct
- `0 <= amount <= 5000`
""",
    signature=function("change", [("amount", "int"), ("coins", "int[]")], "int"),
    reference=_change,
    brute=lambda amount, coins: _change_brute(amount, coins) if amount <= 200 else NotImplemented,
    examples=[Example([5, [1, 2, 5]], "5, 2+2+1, 2+1+1+1, 1+1+1+1+1."), Example([3, [2]]), Example([10, [10]])],
    edge_cases=[[0, [7]], [1, [2]], [100, [1, 5, 10, 25, 50]]],
    generator=lambda rng: [rng.randint(0, rng.choice([60, 500])), sorted(set(ints(rng, rng.randint(1, 6), 2, 40)))],
    random_count=8,
)


# ---------------------------------------------------------------- Ugly Number II


def _nth_ugly(n: int) -> int:
    ugly = [1]
    i2 = i3 = i5 = 0
    while len(ugly) < n:
        nxt = min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)
        ugly.append(nxt)
        if nxt == ugly[i2] * 2:
            i2 += 1
        if nxt == ugly[i3] * 3:
            i3 += 1
        if nxt == ugly[i5] * 5:
            i5 += 1
    return ugly[-1]


def _ugly_brute(n: int) -> int:
    heap, seen = [1], {1}
    for _ in range(n - 1):
        x = heapq.heappop(heap)
        for p in (2, 3, 5):
            if x * p not in seen:
                seen.add(x * p)
                heapq.heappush(heap, x * p)
    return heap[0]


UGLY_II = ProblemSource(
    title="Ugly Number II",
    statement="""
An *ugly number* is a positive integer whose only prime factors are 2, 3 and 5 (`1` counts as ugly). Return the `n`-th ugly number.
""",
    constraints="""
- `1 <= n <= 1690`
""",
    signature=function("nthUglyNumber", [("n", "int")], "int"),
    reference=_nth_ugly,
    brute=_ugly_brute,
    examples=[Example([10], "1, 2, 3, 4, 5, 6, 8, 9, 10, 12."), Example([1])],
    edge_cases=[[2], [7], [1690]],
    generator=lambda rng: [rng.randint(1, 1690)],
    random_count=6,
)


# ---------------------------------------------------------------- Different Ways to Add Parentheses


def _diff_ways(expression: str) -> list[int]:
    @cache
    def ways(expr: str) -> tuple[int, ...]:
        out = []
        for i, ch in enumerate(expr):
            if ch in "+-*":
                for a in ways(expr[:i]):
                    for b in ways(expr[i + 1 :]):
                        out.append(a + b if ch == "+" else a - b if ch == "-" else a * b)
        return tuple(out) if out else (int(expr),)

    return list(ways(expression))


def _diff_ways_brute(expression: str) -> list[int]:
    tokens = []
    num = ""
    for ch in expression:
        if ch.isdigit():
            num += ch
        else:
            tokens += [int(num), ch]
            num = ""
    tokens.append(int(num))

    def split(tok: list) -> list[int]:
        if len(tok) == 1:
            return [tok[0]]
        out = []
        for i in range(1, len(tok), 2):
            for a in split(tok[:i]):
                for b in split(tok[i + 1 :]):
                    out.append({"+": a + b, "-": a - b, "*": a * b}[tok[i]])
        return out

    return split(tokens)


def _expression_gen(rng):
    parts = [str(rng.randint(0, 99))]
    for _ in range(rng.randint(0, rng.choice([3, 8]))):
        parts += [rng.choice("+-*"), str(rng.randint(0, 99))]
    return ["".join(parts)]


DIFFERENT_WAYS = ProblemSource(
    title="Different Ways to Add Parentheses",
    statement="""
`expression` contains non-negative integers and the operators `+`, `-` and `*`. Return the results of **every** way to fully parenthesise it
(one result per distinct grouping, so equal values may repeat), in any order.
""",
    constraints="""
- `1 <= expression.length <= 20`
- numbers are between `0` and `99`; the expression is well formed
""",
    signature=function("diffWaysToCompute", [("expression", "string")], "int[]"),
    reference=_diff_ways,
    brute=_diff_ways_brute,
    compare="unordered",
    examples=[Example(["2-1-1"], "((2-1)-1) = 0 and (2-(1-1)) = 2."), Example(["2*3-4*5"], "-34, -14, -10, -10, 10.")],
    edge_cases=[["7"], ["1+1"], ["11*22"]],
    generator=_expression_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Longest Palindromic Subsequence


def _longest_palindrome_subseq(s: str) -> int:
    return _lcs_len(s, s[::-1])


def _lcs_len(a: str, b: str) -> int:
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def _lps_brute(s: str) -> int:
    @cache
    def best(i: int, j: int) -> int:
        if i > j:
            return 0
        if i == j:
            return 1
        if s[i] == s[j]:
            return 2 + best(i + 1, j - 1)
        return max(best(i + 1, j), best(i, j - 1))

    return best(0, len(s) - 1)


LONGEST_PALINDROMIC_SUBSEQ = ProblemSource(
    title="Longest Palindromic Subsequence",
    statement="""
Return the length of the longest subsequence of `s` that reads the same forwards and backwards.
""",
    constraints="""
- `1 <= s.length <= 1000`
- lowercase English letters only
""",
    signature=function("longestPalindromeSubseq", [("s", "string")], "int"),
    reference=_longest_palindrome_subseq,
    brute=_lps_brute,
    brute_input_limit=300,
    examples=[Example(["bbbab"], "\"bbbb\"."), Example(["cbbd"], "\"bb\".")],
    edge_cases=[["a"], ["ab"], ["aba"], ["abcde"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 20, big=1000), rng.choice(["ab", "abc"]))],
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Best Time to Buy and Sell Stock IV


def _max_profit_iv(k: int, prices: list[int]) -> int:
    buy = [float("-inf")] * (k + 1)
    sell = [0] * (k + 1)
    for p in prices:
        for t in range(1, k + 1):
            buy[t] = max(buy[t], sell[t - 1] - p)
            sell[t] = max(sell[t], buy[t] + p)
    return int(sell[k])


def _profit_iv_brute(k: int, prices: list[int]) -> int:
    @cache
    def best(i: int, left: int, holding: bool) -> int:
        if i == len(prices):
            return 0
        skip = best(i + 1, left, holding)
        if holding:
            return max(skip, prices[i] + best(i + 1, left, False))
        if left == 0:
            return skip
        return max(skip, -prices[i] + best(i + 1, left - 1, True))

    return best(0, k, False)


BEST_TIME_IV = ProblemSource(
    title="Best Time to Buy and Sell Stock IV",
    statement="""
`prices[i]` is a stock's price on day `i`. Make **at most `k`** transactions (each a buy followed by a later sell), holding at most one share at
a time. Return the maximum profit.
""",
    constraints="""
- `1 <= k <= 100`
- `1 <= prices.length <= 1000`
- `0 <= prices[i] <= 1000`
""",
    signature=function("maxProfit", [("k", "int"), ("prices", "int[]")], "int"),
    reference=_max_profit_iv,
    brute=_profit_iv_brute,
    brute_input_limit=400,
    examples=[Example([2, [2, 4, 1]], "Buy at 2, sell at 4."), Example([2, [3, 2, 6, 5, 0, 3]], "Two trades: 4 + 3 = 7.")],
    edge_cases=[[1, [5]], [3, [1, 2, 3, 4, 5]], [1, [7, 1, 5, 3, 6, 4]], [100, [1, 3, 1, 3, 1, 3]]],
    generator=lambda rng: [rng.randint(1, rng.choice([3, 100])), ints(rng, pick_n(rng, 1, 30, big=1000), 0, rng.choice([10, 1000]))],
    random_count=8,
    time_limit_ms=1500,
)


PROBLEMS = [
    SOUP_SERVINGS,
    AWARE_OF_SECRET,
    EDIT_DISTANCE,
    UNIQUE_PATHS_II,
    TICKETS,
    COUNT_PALINDROMIC,
    DELETE_AND_EARN,
    STRING_CHAIN,
    LAST_STONE_II,
    STICKERS,
    TARGET_SUM,
    MAX_CIRCULAR,
    MAX_SUM_THREE,
    COIN_CHANGE_II,
    UGLY_II,
    DIFFERENT_WAYS,
    LONGEST_PALINDROMIC_SUBSEQ,
    BEST_TIME_IV,
]
