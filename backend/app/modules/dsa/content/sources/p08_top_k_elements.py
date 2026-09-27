"""Pattern 8: Top K Elements. Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import heapq
import itertools
import math
from collections import Counter

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ints, ops, pick_n, word

PATTERN_NUMBER = 8
_MOD = 10**9 + 7


# ---------------------------------------------------------------- Top K Frequent Elements


def _top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    return [v for _, v in heapq.nlargest(k, ((n, v) for v, n in counts.items()))]


def _top_k_gen(rng):
    nums = ints(rng, pick_n(rng, 1, 40, big=6000), -rng.choice([5, 10**4]), rng.choice([5, 10**4]))
    return [nums, rng.randint(1, len(set(nums)))]


TOP_K_FREQUENT = ProblemSource(
    title="Top K Frequent Elements",
    statement="""
Given an integer array `nums` and an integer `k`, return the `k` values that occur most often, in any order.
When values tie in frequency at the cut-off, any of the tied values may be chosen.

Aim for better than `O(n log n)` time.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
- `1 <= k <=` the number of distinct values
""",
    signature=function("topKFrequent", [("nums", "int[]"), ("k", "int")], "int[]"),
    reference=_top_k_frequent,
    brute=lambda nums, k: [v for v, _ in sorted(Counter(nums).items(), key=lambda kv: (-kv[1], kv[0]))[:k]],
    compare="checker",
    checker="top_k_frequent",
    examples=[Example([[1, 1, 1, 2, 2, 3], 2], "1 appears three times and 2 twice."), Example([[1], 1])],
    edge_cases=[[[4, 4, 5, 5], 1], [[1, 2, 3], 3], [[-1, -1, 7], 1]],
    generator=_top_k_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Kth Largest Element in a Stream


class _KthLargest:
    def __init__(self, k: int, nums: list[int]) -> None:
        self.k = k
        self.heap = heapq.nlargest(k, nums)
        heapq.heapify(self.heap)

    def add(self, val: int) -> int:
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]


class _KthLargestBrute:
    def __init__(self, k: int, nums: list[int]) -> None:
        self.k, self.values = k, list(nums)

    def add(self, val: int) -> int:
        self.values.append(val)
        return sorted(self.values, reverse=True)[self.k - 1]


def _kth_stream_gen(rng):
    k = rng.randint(1, 8)
    nums = ints(rng, rng.randint(max(0, k - 1), k + 10), -10**4, 10**4)
    calls = [("KthLargest", [k, nums])] + [("add", [rng.randint(-10**4, 10**4)]) for _ in range(pick_n(rng, 1, 20, big=600))]
    return ops(*calls)


KTH_LARGEST_STREAM = ProblemSource(
    title="Kth Largest Element in a Stream",
    statement="""
Design `KthLargest`, which tracks the `k`-th largest value (in sorted order, counting duplicates) of a
growing stream of integers:
- `KthLargest(k, nums)` starts with `k` and the initial values `nums`.
- `add(val)` appends `val` to the stream and returns the current `k`-th largest value.

It is guaranteed that the stream holds at least `k` values whenever `add` returns.

**Test format:** a list of operations with their arguments; the expected output lists each operation's
return value (`null` for the constructor).
""",
    constraints="""
- `1 <= k <= 10^4`, `0 <= nums.length <= 10^4`
- `-10^4 <= nums[i], val <= 10^4`
- at most `10^4` calls to `add`
""",
    signature=design("KthLargest", [("k", "int"), ("nums", "int[]")], [("add", [("val", "int")], "int")]),
    reference=_KthLargest,
    brute=_KthLargestBrute,
    examples=[
        Example(
            ops(("KthLargest", [3, [4, 5, 8, 2]]), ("add", [3]), ("add", [5]), ("add", [10]), ("add", [9]), ("add", [4])),
            "The 3rd largest value becomes 4, 5, 5, 8, 8.",
        ),
        Example(ops(("KthLargest", [1, []]), ("add", [-3]), ("add", [-2]))),
    ],
    edge_cases=[ops(("KthLargest", [2, [0]]), ("add", [-1]), ("add", [1]), ("add", [-2]))],
    generator=_kth_stream_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Reorganize String


def _reorganize(s: str) -> str:
    heap = [(-n, ch) for ch, n in Counter(s).items()]
    heapq.heapify(heap)
    if -heap[0][0] > (len(s) + 1) // 2:
        return ""
    out: list[str] = []
    while len(heap) >= 2:
        n1, c1 = heapq.heappop(heap)
        n2, c2 = heapq.heappop(heap)
        out += [c1, c2]
        if n1 + 1:
            heapq.heappush(heap, (n1 + 1, c1))
        if n2 + 1:
            heapq.heappush(heap, (n2 + 1, c2))
    if heap:
        out.append(heap[0][1])
    return "".join(out)


def _reorganize_brute(s: str) -> str:
    for perm in itertools.permutations(s):
        if all(a != b for a, b in itertools.pairwise(perm)):
            return "".join(perm)
    return ""


REORGANIZE_STRING = ProblemSource(
    title="Reorganize String",
    statement="""
Rearrange the characters of the lowercase string `s` so that no two adjacent characters are equal. Return
any such arrangement, or `""` if none exists.
""",
    constraints="""
- `1 <= s.length <= 500`
- `s` consists of lowercase English letters
""",
    signature=function("reorganizeString", [("s", "string")], "string"),
    reference=_reorganize,
    brute=_reorganize_brute,
    brute_input_limit=10,
    compare="checker",
    checker="reorganize_string",
    examples=[Example(["aab"], "\"aba\" is the only valid arrangement."), Example(["aaab"], "Three a's can't be separated by one b.")],
    edge_cases=[["a"], ["aa"], ["ab"], ["aabb"], ["vvvlo"], ["aaabbbccc"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 7, big=500), rng.choice(["ab", "abc", "aab", "abcdef"]))],
    random_count=9,
)


# ---------------------------------------------------------------- K Closest Points to Origin


def _k_closest(points: list[list[int]], k: int) -> list[list[int]]:
    return heapq.nsmallest(k, points, key=lambda p: p[0] * p[0] + p[1] * p[1])


def _points_gen(rng):
    hi = rng.choice([3, 10**4])
    points = [[rng.randint(-hi, hi), rng.randint(-hi, hi)] for _ in range(pick_n(rng, 1, 20, big=2000))]
    return [points, rng.randint(1, len(points))]


K_CLOSEST = ProblemSource(
    title="K Closest Points to Origin",
    statement="""
`points[i] = [x_i, y_i]` are points on a plane. Return the `k` points closest to the origin `(0, 0)` by
Euclidean distance, in any order. When several points tie for the last place, any of them may be chosen.
""",
    constraints="""
- `1 <= k <= points.length <= 10^4`
- `-10^4 <= x_i, y_i <= 10^4`
""",
    signature=function("kClosest", [("points", "int[][]"), ("k", "int")], "int[][]"),
    reference=_k_closest,
    brute=lambda points, k: sorted(points, key=lambda p: p[0] ** 2 + p[1] ** 2)[:k],
    compare="checker",
    checker="k_closest_points",
    examples=[
        Example([[[1, 3], [-2, 2]], 1], "(-2, 2) is at distance sqrt(8), closer than sqrt(10)."),
        Example([[[3, 3], [5, -1], [-2, 4]], 2], "[3,3] and [-2,4] in any order."),
    ],
    edge_cases=[[[[0, 0]], 1], [[[1, 0], [0, 1], [-1, 0]], 2], [[[2, 2], [2, 2]], 1]],
    generator=_points_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Kth Largest Element in an Array


def _find_kth_largest(nums: list[int], k: int) -> int:
    heap = nums[:k]
    heapq.heapify(heap)
    for x in nums[k:]:
        if x > heap[0]:
            heapq.heapreplace(heap, x)
    return heap[0]


KTH_LARGEST_ARRAY = ProblemSource(
    title="Kth Largest Element in an Array",
    statement="""
Return the `k`-th largest value of `nums` in sorted order (counting duplicates), without fully sorting the
array if you can.
""",
    constraints="""
- `1 <= k <= nums.length <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
""",
    signature=function("findKthLargest", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_find_kth_largest,
    brute=lambda nums, k: sorted(nums, reverse=True)[k - 1],
    examples=[Example([[3, 2, 1, 5, 6, 4], 2], "Sorted descending: 6, 5, ...; the 2nd is 5."), Example([[3, 2, 3, 1, 2, 4, 5, 5, 6], 4])],
    edge_cases=[[[1], 1], [[2, 1], 2], [[7, 7, 7], 2], [[-1, -2], 1]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 40, big=5000), -10**4, 10**4)), rng.randint(1, len(v))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximal Score After Applying K Operations


def _max_kelements(nums: list[int], k: int) -> int:
    heap = [-x for x in nums]
    heapq.heapify(heap)
    score = 0
    for _ in range(k):
        x = -heapq.heappop(heap)
        score += x
        heapq.heappush(heap, -math.ceil(x / 3))
    return score


def _max_kelements_brute(nums: list[int], k: int) -> int:
    nums, score = list(nums), 0
    for _ in range(k):
        i = max(range(len(nums)), key=lambda j: nums[j])
        score += nums[i]
        nums[i] = (nums[i] + 2) // 3
    return score


MAXIMAL_SCORE = ProblemSource(
    title="Maximal Score After Applying K Operations",
    statement="""
You start with a score of `0`. In one operation you pick an index `i`, add `nums[i]` to your score, and
replace `nums[i]` with `ceil(nums[i] / 3)`. Perform exactly `k` operations (the same index may be picked
again) and return the maximum possible score.
""",
    constraints="""
- `1 <= nums.length, k <= 10^5`
- `1 <= nums[i] <= 10^9`
""",
    signature=function("maxKelements", [("nums", "int[]"), ("k", "int")], "long"),
    reference=_max_kelements,
    brute=_max_kelements_brute,
    brute_input_limit=300,
    examples=[Example([[10, 10, 10, 10, 10], 5], "Take each 10 once: 50."), Example([[1, 10, 3, 3, 3], 3], "10, then 4 (ceil(10/3)), then 3: 17.")],
    edge_cases=[[[1], 5], [[1000000000], 3], [[2, 2], 4]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=4000), 1, rng.choice([20, 10**9])), rng.randint(1, rng.choice([10, 4000]))],
    random_count=8,
)


# ---------------------------------------------------------------- Find the Kth Largest Integer in the Array


def _kth_largest_number(nums: list[str], k: int) -> str:
    heap: list[tuple[int, str]] = []
    for s in nums:
        heapq.heappush(heap, (len(s), s))
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0][1]


def _big_number_gen(rng):
    nums = []
    for _ in range(pick_n(rng, 1, 20, big=400)):
        n = rng.randint(1, rng.choice([3, 40]))
        s = word(rng, n, "0123456789")
        nums.append(s.lstrip("0") or "0")
    return [nums, rng.randint(1, len(nums))]


KTH_LARGEST_STRING = ProblemSource(
    title="Find the Kth Largest Integer in the Array",
    statement="""
`nums` contains non-negative integers written as strings without leading zeros; they may be far too big
for any integer type. Return (as a string) the `k`-th largest value in sorted order, counting duplicates.
""",
    constraints="""
- `1 <= k <= nums.length <= 10^4`
- `1 <= nums[i].length <= 100`
- `nums[i]` has only digits and no leading zeros (except `"0"` itself)
""",
    signature=function("kthLargestNumber", [("nums", "string[]"), ("k", "int")], "string"),
    reference=_kth_largest_number,
    brute=lambda nums, k: sorted(nums, key=int, reverse=True)[k - 1],
    examples=[Example([["3", "6", "7", "10"], 4], "Sorted: 10, 7, 6, 3; the 4th is \"3\"."), Example([["2", "21", "12", "1"], 3]), Example([["0", "0"], 2])],
    edge_cases=[[["9"], 1], [["100", "99"], 1], [["123456789012345678901234567890", "5"], 1]],
    generator=_big_number_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Third Maximum Number


def _third_max(nums: list[int]) -> int:
    top: list[int] = []
    for x in nums:
        if x in top:
            continue
        top.append(x)
        top.sort(reverse=True)
        del top[3:]
    return top[2] if len(top) == 3 else top[0]


THIRD_MAX = ProblemSource(
    title="Third Maximum Number",
    statement="""
Return the third largest **distinct** value in `nums`. If there are fewer than three distinct values,
return the largest value instead. Can you do it in `O(n)` time?
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-2^31 <= nums[i] <= 2^31 - 1`
""",
    signature=function("thirdMax", [("nums", "int[]")], "int"),
    reference=_third_max,
    brute=lambda nums: sorted(set(nums), reverse=True)[2] if len(set(nums)) >= 3 else max(nums),
    examples=[Example([[3, 2, 1]], "The third distinct maximum is 1."), Example([[1, 2]], "Only two distinct values; return the maximum, 2."), Example([[2, 2, 3, 1]], "Distinct values 3, 2, 1: the answer is 1.")],
    edge_cases=[[[5]], [[1, 1, 1]], [[-2147483648, 1, 2]], [[2147483647, 2147483647, -2147483648, 0]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 30, big=5000), rng.choice([-3, -(2**31)]), rng.choice([3, 2**31 - 1]))],
    random_count=8,
)


# ---------------------------------------------------------------- Find Subsequence of Length K with the Largest Sum


def _max_subsequence(nums: list[int], k: int) -> list[int]:
    chosen = sorted(heapq.nlargest(k, range(len(nums)), key=lambda i: nums[i]))
    return [nums[i] for i in chosen]


def _max_subsequence_brute(nums: list[int], k: int) -> list[int]:
    best = max(itertools.combinations(range(len(nums)), k), key=lambda idx: sum(nums[i] for i in idx))
    return [nums[i] for i in best]


MAX_SUBSEQUENCE = ProblemSource(
    title="Find Subsequence of Length K with the Largest Sum",
    statement="""
Return a subsequence of `nums` with exactly `k` elements whose sum is as large as possible. A subsequence
keeps the elements' original order. If several subsequences have the largest sum, any of them is accepted.
""",
    constraints="""
- `1 <= nums.length <= 1000`
- `-10^5 <= nums[i] <= 10^5`
- `1 <= k <= nums.length`
""",
    signature=function("maxSubsequence", [("nums", "int[]"), ("k", "int")], "int[]"),
    reference=_max_subsequence,
    brute=_max_subsequence_brute,
    brute_input_limit=40,
    compare="checker",
    checker="k_subsequence_max_sum",
    examples=[
        Example([[2, 1, 3, 3], 2], "[3, 3] has the largest sum, 6."),
        Example([[-1, -2, 3, 4], 3], "[-1, 3, 4] sums to 6."),
        Example([[3, 4, 3, 3], 2], "[3, 4] and [4, 3] both sum to 7."),
    ],
    edge_cases=[[[5], 1], [[-5, -1], 1], [[1, 1, 1], 3]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 10, big=1000), -5 if rng.random() < 0.5 else -10**5, 5 if rng.random() < 0.5 else 10**5)), rng.randint(1, len(v))],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Cost to Hire K Workers


def _min_cost_hire(quality: list[int], wage: list[int], k: int) -> float:
    workers = sorted((w / q, q) for q, w in zip(quality, wage, strict=True))
    heap: list[int] = []
    total = 0
    best = float("inf")
    for ratio, q in workers:
        heapq.heappush(heap, -q)
        total += q
        if len(heap) > k:
            total += heapq.heappop(heap)
        if len(heap) == k:
            best = min(best, ratio * total)
    return best


def _hire_brute(quality: list[int], wage: list[int], k: int) -> float:
    best = float("inf")
    for group in itertools.combinations(range(len(quality)), k):
        ratio = max(wage[i] / quality[i] for i in group)
        best = min(best, ratio * sum(quality[i] for i in group))
    return best


def _hire_gen(rng):
    n = pick_n(rng, 1, 8, big=2000)
    return [ints(rng, n, 1, rng.choice([10, 10**4])), ints(rng, n, 1, rng.choice([10, 10**4])), rng.randint(1, n)]


HIRE_K_WORKERS = ProblemSource(
    title="Minimum Cost to Hire K Workers",
    statement="""
Worker `i` has quality `quality[i]` and a minimum wage expectation `wage[i]`. You must hire exactly `k`
workers and pay them so that:
1. every worker in the group is paid in proportion to their quality relative to the others, and
2. every worker receives at least their minimum wage expectation.

Return the minimum total amount of money needed. Answers within `10^-5` are accepted.
""",
    constraints="""
- `1 <= k <= n <= 10^4`, `n == quality.length == wage.length`
- `1 <= quality[i], wage[i] <= 10^4`
""",
    signature=function("mincostToHireWorkers", [("quality", "int[]"), ("wage", "int[]"), ("k", "int")], "double"),
    reference=_min_cost_hire,
    brute=_hire_brute,
    brute_input_limit=70,
    compare="float_tolerance",
    examples=[
        Example([[10, 20, 5], [70, 50, 30], 2], "Hire workers 0 and 2 and pay 70 and 35: 105."),
        Example([[3, 1, 10, 10, 1], [4, 8, 2, 2, 7], 3], "About 30.66667."),
    ],
    edge_cases=[[[1], [1], 1], [[5, 5], [10, 1], 2], [[1, 1, 1], [1, 2, 3], 1]],
    generator=_hire_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Smallest Range Covering Elements from K Lists


def _smallest_range(nums: list[list[int]]) -> list[int]:
    heap = [(row[0], r, 0) for r, row in enumerate(nums)]
    heapq.heapify(heap)
    high = max(row[0] for row in nums)
    best = [heap[0][0], high]
    while True:
        low, r, c = heapq.heappop(heap)
        if high - low < best[1] - best[0] or (high - low == best[1] - best[0] and low < best[0]):
            best = [low, high]
        if c + 1 == len(nums[r]):
            return best
        nxt = nums[r][c + 1]
        high = max(high, nxt)
        heapq.heappush(heap, (nxt, r, c + 1))


def _smallest_range_brute(nums: list[list[int]]) -> list[int]:
    values = sorted({v for row in nums for v in row})
    best = None
    for a in values:
        for b in values:
            covers = b >= a and all(any(a <= v <= b for v in row) for row in nums)
            if covers and (best is None or (b - a, a) < (best[1] - best[0], best[0])):
                best = [a, b]
    return best


def _range_gen(rng):
    hi = rng.choice([20, 10**5])
    return [[sorted(ints(rng, pick_n(rng, 1, 6, big=150), -hi, hi)) for _ in range(pick_n(rng, 1, 5, big=40))]]


SMALLEST_RANGE = ProblemSource(
    title="Smallest Range Covering Elements from K Lists",
    statement="""
You have `k` lists of integers, each sorted in non-decreasing order. Find the smallest range `[a, b]` that
includes **at least one number from each list**.

Range `[a, b]` is smaller than `[c, d]` if `b - a < d - c`, or if `b - a == d - c` and `a < c`.
""",
    constraints="""
- `1 <= k <= 3500`
- `1 <= nums[i].length <= 50`
- `-10^5 <= nums[i][j] <= 10^5`, each list sorted in non-decreasing order
""",
    signature=function("smallestRange", [("nums", "int[][]")], "int[]"),
    reference=_smallest_range,
    brute=_smallest_range_brute,
    brute_input_limit=250,
    examples=[
        Example([[[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]], "[20, 24] contains 24, 20 and 22."),
        Example([[[1, 2, 3], [1, 2, 3], [1, 2, 3]]], "[1, 1] already covers every list."),
    ],
    edge_cases=[[[[5]]], [[[1], [9]]], [[[1, 9], [5]]], [[[-100000], [100000]]]],
    generator=_range_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Performance of a Team


def _max_performance(n: int, speed: list[int], efficiency: list[int], k: int) -> int:
    engineers = sorted(zip(efficiency, speed, strict=True), reverse=True)
    heap: list[int] = []
    total = best = 0
    for eff, spd in engineers:
        heapq.heappush(heap, spd)
        total += spd
        if len(heap) > k:
            total -= heapq.heappop(heap)
        best = max(best, total * eff)
    return best % _MOD


def _performance_brute(n: int, speed: list[int], efficiency: list[int], k: int) -> int:
    best = 0
    for size in range(1, k + 1):
        for team in itertools.combinations(range(n), size):
            best = max(best, sum(speed[i] for i in team) * min(efficiency[i] for i in team))
    return best % _MOD


def _performance_gen(rng):
    n = pick_n(rng, 1, 8, big=3000)
    return [n, ints(rng, n, 1, rng.choice([10, 10**5])), ints(rng, n, 1, rng.choice([10, 10**8])), rng.randint(1, n)]


MAX_PERFORMANCE = ProblemSource(
    title="Maximum Performance of a Team",
    statement="""
There are `n` engineers; engineer `i` has speed `speed[i]` and efficiency `efficiency[i]`. Choose a team of
**at most** `k` engineers. A team's performance is the sum of its members' speeds multiplied by the
minimum efficiency among them.

Return the maximum performance, modulo `10^9 + 7` (maximise the true value first, then take the modulo).
""",
    constraints="""
- `1 <= k <= n <= 10^5`
- `speed.length == efficiency.length == n`
- `1 <= speed[i] <= 10^5`, `1 <= efficiency[i] <= 10^8`
""",
    signature=function("maxPerformance", [("n", "int"), ("speed", "int[]"), ("efficiency", "int[]"), ("k", "int")], "int"),
    reference=_max_performance,
    brute=_performance_brute,
    brute_input_limit=90,
    examples=[
        Example([6, [2, 10, 3, 1, 5, 8], [5, 4, 3, 9, 7, 2], 2], "Engineers 2 and 5: (10 + 5) * min(4, 7) = 60."),
        Example([6, [2, 10, 3, 1, 5, 8], [5, 4, 3, 9, 7, 2], 3], "(2 + 10 + 5) * 4 = 68."),
    ],
    edge_cases=[[1, [5], [5], 1], [2, [100000, 100000], [100000000, 100000000], 2], [3, [1, 1, 1], [3, 2, 1], 3]],
    generator=_performance_gen,
    random_count=8,
)


# ---------------------------------------------------------------- K Maximum Sum Combinations From Two Arrays


def _max_combinations(A: list[int], B: list[int], k: int) -> list[int]:
    a, b = sorted(A, reverse=True), sorted(B, reverse=True)
    heap = [(-(a[0] + b[0]), 0, 0)]
    seen = {(0, 0)}
    out = []
    while len(out) < k:
        total, i, j = heapq.heappop(heap)
        out.append(-total)
        for x, y in ((i + 1, j), (i, j + 1)):
            if x < len(a) and y < len(b) and (x, y) not in seen:
                seen.add((x, y))
                heapq.heappush(heap, (-(a[x] + b[y]), x, y))
    return out


def _combinations_gen(rng):
    n = pick_n(rng, 1, 8, big=1000)
    A, B = ints(rng, n, 1, rng.choice([10, 10**4])), ints(rng, n, 1, rng.choice([10, 10**4]))
    return [A, B, rng.randint(1, min(n * n, 500))]


MAX_SUM_COMBINATIONS = ProblemSource(
    title="K Maximum Sum Combinations From Two Arrays",
    statement="""
`A` and `B` are integer arrays of the same length `n`. A *combination* adds one element of `A` to one element
of `B`, so there are `n * n` combinations (elements at different positions count as different even when
equal).

Return the `k` largest combination sums, in **non-increasing** order.
""",
    constraints="""
- `1 <= n <= 10^5`
- `1 <= A[i], B[i] <= 10^4`
- `1 <= k <= min(n * n, 10^4)`
""",
    signature=function("maxCombinations", [("A", "int[]"), ("B", "int[]"), ("k", "int")], "int[]"),
    reference=_max_combinations,
    brute=lambda A, B, k: sorted((a + b for a in A for b in B), reverse=True)[:k],
    brute_input_limit=600,
    examples=[
        Example([[3, 2], [1, 4], 2], "The sums are 7, 6, 4, 3; the two largest are 7 and 6."),
        Example([[4, 2, 5, 1], [8, 0, 3, 5], 3], "13, 12, 10."),
    ],
    edge_cases=[[[1], [1], 1], [[5, 5], [5, 5], 4], [[1, 2, 3], [1, 2, 3], 9]],
    generator=_combinations_gen,
    random_count=8,
)


# ---------------------------------------------------------------- K Empty Slots


def _k_empty_slots(bulbs: list[int], k: int) -> int:
    n = len(bulbs)
    day_on = [0] * n
    for day, pos in enumerate(bulbs, start=1):
        day_on[pos - 1] = day
    best = math.inf
    left, right = 0, k + 1
    i = 1
    while right < n:
        if i == right:
            best = min(best, max(day_on[left], day_on[right]))
            left, right = right, right + k + 1
            i = left + 1
        elif day_on[i] < day_on[left] or day_on[i] < day_on[right]:
            left, right = i, i + k + 1
            i = left + 1
        else:
            i += 1
    return -1 if best == math.inf else int(best)


def _k_empty_brute(bulbs: list[int], k: int) -> int:
    on = set()
    for day, pos in enumerate(bulbs, start=1):
        on.add(pos)
        for other in (pos - k - 1, pos + k + 1):
            lo, hi = min(pos, other), max(pos, other)
            if other in on and not any(p in on for p in range(lo + 1, hi)):
                return day
    return -1


def _slots_gen(rng):
    n = pick_n(rng, 1, 12, big=3000)
    bulbs = list(range(1, n + 1))
    rng.shuffle(bulbs)
    return [bulbs, rng.randint(0, min(n, rng.choice([2, 20, n])))]


K_EMPTY_SLOTS = ProblemSource(
    title="K Empty Slots",
    statement="""
`n` bulbs stand in a row at positions `1..n`, all off. On day `i` (1-based) you turn on the bulb at
position `bulbs[i - 1]`; `bulbs` is a permutation of `1..n`, so each bulb is turned on exactly once.

Return the earliest day on which there are two turned-on bulbs with **exactly `k`** bulbs between them and
all of those `k` bulbs are off. Return `-1` if that never happens.
""",
    constraints="""
- `1 <= n <= 2 * 10^4`
- `bulbs` is a permutation of `1..n`
- `0 <= k <= 2 * 10^4`
""",
    signature=function("kEmptySlots", [("bulbs", "int[]"), ("k", "int")], "int"),
    reference=_k_empty_slots,
    brute=_k_empty_brute,
    brute_input_limit=300,
    examples=[
        Example([[1, 3, 2], 1], "On day 2 bulbs 1 and 3 are on and bulb 2 between them is off."),
        Example([[1, 2, 3], 1], "Bulbs turn on next to each other; it never happens."),
    ],
    edge_cases=[[[1], 0], [[2, 1], 0], [[1, 2], 1], [[3, 1, 2], 1], [[6, 5, 8, 9, 7, 1, 10, 2, 3, 4], 2]],
    generator=_slots_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find the K-Sum of an Array


def _k_sum(nums: list[int], k: int) -> int:
    top = sum(x for x in nums if x > 0)
    costs = sorted(abs(x) for x in nums)
    heap = [(0, 0)]  # (amount removed from the best sum, next index)
    removed = 0
    for _ in range(k):
        removed, i = heapq.heappop(heap)
        if i < len(costs):
            heapq.heappush(heap, (removed + costs[i], i + 1))
            if i:
                heapq.heappush(heap, (removed + costs[i] - costs[i - 1], i + 1))
    return top - removed


def _k_sum_brute(nums: list[int], k: int) -> int:
    sums = sorted((sum(c) for r in range(len(nums) + 1) for c in itertools.combinations(nums, r)), reverse=True)
    return sums[k - 1]


def _k_sum_gen(rng):
    nums = ints(rng, pick_n(rng, 1, 10, big=2000), -rng.choice([5, 10**9]), rng.choice([5, 10**9]))
    return [nums, rng.randint(1, min(2 ** len(nums), 2000))]


K_SUM = ProblemSource(
    title="Find the K-Sum of an Array",
    statement="""
A *subsequence* of `nums` is any selection of its elements (possibly none, possibly all); there are
`2^n` of them, and the empty subsequence sums to `0`.

The *K-Sum* of the array is the `k`-th largest subsequence sum, counting equal sums from different
subsequences separately. Return it.
""",
    constraints="""
- `1 <= n <= 10^5`
- `-10^9 <= nums[i] <= 10^9`
- `1 <= k <= min(2000, 2^n)`
""",
    signature=function("kSum", [("nums", "int[]"), ("k", "int")], "long"),
    reference=_k_sum,
    brute=_k_sum_brute,
    brute_input_limit=45,
    examples=[
        Example([[2, 4, -2], 5], "Subsequence sums in decreasing order: 6, 4, 4, 2, 2, 0, 0, -2; the 5th is 2."),
        Example([[1, -2, 3, 4, -10, 12], 16]),
    ],
    edge_cases=[[[5], 1], [[5], 2], [[-5], 1], [[0, 0], 4]],
    generator=_k_sum_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Product After K Increments


def _maximum_product(nums: list[int], k: int) -> int:
    heap = list(nums)
    heapq.heapify(heap)
    for _ in range(k):
        heapq.heapreplace(heap, heap[0] + 1)
    product = 1
    for x in heap:
        product = product * x % _MOD
    return product


def _maximum_product_brute(nums: list[int], k: int) -> int:
    if (k + 1) ** len(nums) > 10**6:
        return NotImplemented
    best = 0
    for split in itertools.product(range(k + 1), repeat=len(nums)):
        if sum(split) == k:
            best = max(best, math.prod(x + s for x, s in zip(nums, split, strict=True)))
    return best % _MOD


MAX_PRODUCT_INCREMENTS = ProblemSource(
    title="Maximum Product After K Increments",
    statement="""
You may perform at most `k` operations; each one increases any element of the non-negative array `nums`
by `1`. Return the maximum possible product of the elements, modulo `10^9 + 7` (maximise the true product
first, then take the modulo).
""",
    constraints="""
- `1 <= nums.length, k <= 10^5`
- `0 <= nums[i] <= 10^6`
""",
    signature=function("maximumProduct", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_maximum_product,
    brute=_maximum_product_brute,
    examples=[Example([[0, 4], 5], "Raise 0 to 5: 5 * 4 = 20."), Example([[6, 3, 3, 2], 2], "Raise 2 and one 3: 6 * 4 * 3 * 3 = 216.")],
    edge_cases=[[[0], 1], [[1000000], 1], [[0, 0, 0], 2], [[1, 1], 3]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 4, big=4000), 0, rng.choice([5, 10**6])), rng.randint(1, rng.choice([5, 10**5]))],
    random_count=8,
)


# ---------------------------------------------------------------- Least Number of Unique Integers after K Removals


def _least_unique(arr: list[int], k: int) -> int:
    counts = sorted(Counter(arr).values())
    remaining = len(counts)
    for c in counts:
        if k < c:
            break
        k -= c
        remaining -= 1
    return remaining


def _least_unique_brute(arr: list[int], k: int) -> int:
    counts = Counter(arr)
    values = list(counts)
    best = len(values)
    for r in range(len(values) + 1):
        for gone in itertools.combinations(values, r):
            if sum(counts[v] for v in gone) <= k:
                best = min(best, len(values) - r)
    return best


LEAST_UNIQUE = ProblemSource(
    title="Least Number of Unique Integers after K Removals",
    statement="""
Remove exactly `k` elements from `arr` (any elements you like). Return the smallest possible number of
distinct values left in the array.
""",
    constraints="""
- `1 <= arr.length <= 10^5`
- `1 <= arr[i] <= 10^9`
- `0 <= k <= arr.length`
""",
    signature=function("findLeastNumOfUniqueInts", [("arr", "int[]"), ("k", "int")], "int"),
    reference=_least_unique,
    brute=_least_unique_brute,
    brute_input_limit=60,
    examples=[Example([[5, 5, 4], 1], "Remove the 4; only 5 remains."), Example([[4, 3, 1, 1, 3, 3, 2], 3], "Remove 4, 2 and one 1: values 1 and 3 remain.")],
    edge_cases=[[[1], 0], [[1], 1], [[1, 2, 3], 3], [[7, 7, 7, 8], 2]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 12, big=5000), 1, rng.choice([6, 10**9]))), rng.randint(0, len(v))],
    random_count=8,
)


# ---------------------------------------------------------------- Final Array State After K Multiplication Operations I


def _final_state(nums: list[int], k: int, multiplier: int) -> list[int]:
    heap = [(x, i) for i, x in enumerate(nums)]
    heapq.heapify(heap)
    out = list(nums)
    for _ in range(k):
        x, i = heapq.heappop(heap)
        out[i] = x * multiplier
        heapq.heappush(heap, (out[i], i))
    return out


def _final_state_brute(nums: list[int], k: int, multiplier: int) -> list[int]:
    nums = list(nums)
    for _ in range(k):
        i = nums.index(min(nums))
        nums[i] *= multiplier
    return nums


FINAL_ARRAY_STATE = ProblemSource(
    title="Final Array State After K Multiplication Operations I",
    statement="""
Perform `k` operations on `nums`. In each operation, find the minimum value; if it occurs several times,
take its **first** occurrence. Replace that element with itself multiplied by `multiplier`.

Return the array after all `k` operations.
""",
    constraints="""
- `1 <= nums.length <= 100`
- `1 <= nums[i] <= 100`
- `1 <= k <= 10`
- `1 <= multiplier <= 5`
""",
    signature=function("getFinalState", [("nums", "int[]"), ("k", "int"), ("multiplier", "int")], "int[]"),
    reference=_final_state,
    brute=_final_state_brute,
    examples=[Example([[2, 1, 3, 5, 6], 5, 2], "Result: 8, 4, 6, 5, 6."), Example([[1, 2], 3, 4], "Result: 16, 8.")],
    edge_cases=[[[1], 10, 5], [[3, 3], 1, 2], [[5, 5, 5], 3, 1]],
    generator=lambda rng: [ints(rng, rng.randint(1, 100), 1, 100), rng.randint(1, 10), rng.randint(1, 5)],
    random_count=8,
)


PROBLEMS = [
    TOP_K_FREQUENT,
    KTH_LARGEST_STREAM,
    REORGANIZE_STRING,
    K_CLOSEST,
    KTH_LARGEST_ARRAY,
    MAXIMAL_SCORE,
    KTH_LARGEST_STRING,
    THIRD_MAX,
    MAX_SUBSEQUENCE,
    HIRE_K_WORKERS,
    SMALLEST_RANGE,
    MAX_PERFORMANCE,
    MAX_SUM_COMBINATIONS,
    K_EMPTY_SLOTS,
    K_SUM,
    MAX_PRODUCT_INCREMENTS,
    LEAST_UNIQUE,
    FINAL_ARRAY_STATE,
]
