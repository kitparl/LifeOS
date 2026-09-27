"""Pattern 16: Sort and Search. Original statements; outputs come from `reference`."""

from __future__ import annotations

import bisect
import itertools
import random

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sample

PATTERN_NUMBER = 16
_MOD = 10**9 + 7


# ---------------------------------------------------------------- Sum of Mutated Array Closest to Target


def _find_best_value(arr: list[int], target: int) -> int:
    values = sorted(arr)
    prefix = [0, *itertools.accumulate(values)]

    def mutated_sum(v: int) -> int:
        i = bisect.bisect_right(values, v)
        return prefix[i] + v * (len(values) - i)

    lo, hi = 0, values[-1]
    while lo < hi:  # smallest v with mutated_sum(v) >= target
        mid = (lo + hi) // 2
        if mutated_sum(mid) >= target:
            hi = mid
        else:
            lo = mid + 1
    if lo > 0 and abs(mutated_sum(lo - 1) - target) <= abs(mutated_sum(lo) - target):
        return lo - 1
    return lo


def _best_value_brute(arr: list[int], target: int) -> int:
    if max(arr) > 5000:
        return NotImplemented
    return min(range(max(arr) + 1), key=lambda v: (abs(sum(min(x, v) for x in arr) - target), v))


MUTATED_ARRAY = ProblemSource(
    title="Sum of Mutated Array Closest to Target",
    statement="""
Choose a non-negative integer `value` and replace every element of `arr` larger than `value` with `value`. Return the `value` for which the sum of the
modified array is as close as possible (in absolute difference) to `target`. If several values tie, return the smallest one.

Note that the answer is not necessarily an element of `arr`.
""",
    constraints="""
- `1 <= arr.length <= 10^4`
- `1 <= arr[i], target <= 10^5`
""",
    signature=function("findBestValue", [("arr", "int[]"), ("target", "int")], "int"),
    reference=_find_best_value,
    brute=_best_value_brute,
    examples=[Example([[4, 9, 3], 10], "value 3 makes [3,3,3], summing to 9."), Example([[2, 3, 5], 10], "value 5 changes nothing; sum is 10."), Example([[60864, 25176, 27249, 21296, 20204], 56803])],
    edge_cases=[[[1], 1], [[1], 100000], [[5, 5, 5], 1], [[1, 1, 1], 2]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 12, big=10**4), 1, rng.choice([50, 5000, 10**5])), rng.randint(1, rng.choice([200, 10**5]))],
    random_count=8,
)


# ---------------------------------------------------------------- Contains Duplicate II


def _contains_nearby_duplicate(nums: list[int], k: int) -> bool:
    last: dict[int, int] = {}
    for i, x in enumerate(nums):
        if x in last and i - last[x] <= k:
            return True
        last[x] = i
    return False


def _nearby_brute(nums: list[int], k: int) -> bool:
    return any(nums[i] == nums[j] for i in range(len(nums)) for j in range(i + 1, min(len(nums), i + k + 1)))


CONTAINS_DUPLICATE_II = ProblemSource(
    title="Contains Duplicate II",
    statement="""
Return `true` if there are two different indices `i` and `j` with `nums[i] == nums[j]` and `|i - j| <= k`, otherwise `false`.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `-10^9 <= nums[i] <= 10^9`
- `0 <= k <= 10^5`
""",
    signature=function("containsNearbyDuplicate", [("nums", "int[]"), ("k", "int")], "bool"),
    reference=_contains_nearby_duplicate,
    brute=_nearby_brute,
    brute_input_limit=3000,
    examples=[Example([[1, 2, 3, 1], 3]), Example([[1, 0, 1, 1], 1]), Example([[1, 2, 3, 1, 2, 3], 2], "Equal values are always 3 apart.")],
    edge_cases=[[[1], 0], [[1, 1], 0], [[1, 1], 1], [[5, 6, 5], 1]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 30, big=10**4), 0, rng.choice([10, 60, 10**9])), rng.randint(0, rng.choice([3, 30]))],
    random_count=8,
)


# ---------------------------------------------------------------- Find K-th Smallest Pair Distance


def _smallest_distance_pair(nums: list[int], k: int) -> int:
    values = sorted(nums)

    def pairs_within(d: int) -> int:
        count = left = 0
        for right, v in enumerate(values):
            while v - values[left] > d:
                left += 1
            count += right - left
        return count

    lo, hi = 0, values[-1] - values[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if pairs_within(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _pair_distance_brute(nums: list[int], k: int) -> int:
    if len(nums) > 300:
        return NotImplemented
    return sorted(abs(a - b) for a, b in itertools.combinations(nums, 2))[k - 1]


def _pair_distance_gen(rng: random.Random) -> list:
    nums = ints(rng, pick_n(rng, 2, 15, big=10**4), 0, rng.choice([20, 10**6]))
    return [nums, rng.randint(1, len(nums) * (len(nums) - 1) // 2)]


KTH_PAIR_DISTANCE = ProblemSource(
    title="Find K-th Smallest Pair Distance",
    statement="""
The *distance* of a pair of integers `a` and `b` is `|a - b|`. Considering all pairs `nums[i], nums[j]` with `i < j`, return the `k`-th smallest
distance (counting repeats).
""",
    constraints="""
- `2 <= nums.length <= 10^4`
- `0 <= nums[i] <= 10^6`
- `1 <= k <= n * (n - 1) / 2`
""",
    signature=function("smallestDistancePair", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_smallest_distance_pair,
    brute=_pair_distance_brute,
    examples=[Example([[1, 3, 1], 1], "Distances are 2, 0, 2; the smallest is 0."), Example([[1, 1, 1], 2]), Example([[1, 6, 1], 3])],
    edge_cases=[[[0, 1000000], 1], [[5, 5], 1], [[1, 2, 3, 4], 6]],
    generator=_pair_distance_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Number of Integers to Choose from a Range I


def _max_count(banned: list[int], n: int, maxSum: int) -> int:
    blocked = set(banned)
    total = count = 0
    for x in range(1, n + 1):
        if x in blocked:
            continue
        if total + x > maxSum:
            break
        total += x
        count += 1
    return count


def _max_count_brute(banned: list[int], n: int, maxSum: int) -> int:
    allowed = [x for x in range(1, n + 1) if x not in banned]
    if len(allowed) > 14:
        return NotImplemented
    return max(r for r in range(len(allowed) + 1) for c in itertools.combinations(allowed, r) if sum(c) <= maxSum)


CHOOSE_FROM_RANGE = ProblemSource(
    title="Maximum Number of Integers to Choose from a Range I",
    statement="""
Choose some distinct integers from `1` to `n` such that none of them appears in `banned` and their sum is at most `maxSum`. Return the maximum
number of integers you can choose.
""",
    constraints="""
- `1 <= banned.length <= 10^4`, `1 <= banned[i], n <= 10^4`
- `1 <= maxSum <= 10^9`
""",
    signature=function("maxCount", [("banned", "int[]"), ("n", "int"), ("maxSum", "int")], "int"),
    reference=_max_count,
    brute=_max_count_brute,
    examples=[Example([[1, 6, 5], 5, 6], "Choose 2 and 4."), Example([[1, 2, 3, 4, 5, 6, 7], 8, 1]), Example([[11], 7, 50], "All of 1..7 fit.")],
    edge_cases=[[[1], 1, 1], [[2], 3, 1000000000], [[10000], 10000, 1000000000]],
    generator=lambda rng: [ints(rng, rng.randint(1, 10), 1, (n := pick_n(rng, 1, 16, big=10**4))), n, rng.randint(1, rng.choice([30, 10**9]))],
    random_count=8,
)


# ---------------------------------------------------------------- Find the Distance Value Between Two Arrays


def _distance_value(arr1: list[int], arr2: list[int], d: int) -> int:
    other = sorted(arr2)
    count = 0
    for x in arr1:
        i = bisect.bisect_left(other, x - d)
        count += i == len(other) or other[i] > x + d
    return count


DISTANCE_VALUE = ProblemSource(
    title="Find the Distance Value Between Two Arrays",
    statement="""
Return how many elements `arr1[i]` have no element `arr2[j]` with `|arr1[i] - arr2[j]| <= d`.
""",
    constraints="""
- `1 <= arr1.length, arr2.length <= 500`
- `-1000 <= arr1[i], arr2[j] <= 1000`
- `0 <= d <= 100`
""",
    signature=function("findTheDistanceValue", [("arr1", "int[]"), ("arr2", "int[]"), ("d", "int")], "int"),
    reference=_distance_value,
    brute=lambda arr1, arr2, d: sum(all(abs(a - b) > d for b in arr2) for a in arr1),
    examples=[Example([[4, 5, 8], [10, 9, 1, 8], 2], "Only 4 and 5 are far from every arr2 value."), Example([[1, 4, 2, 3], [-4, -3, 6, 10, 20, 30], 3]), Example([[2, 1, 100, 3], [-5, -2, 10, -3, 7], 6])],
    edge_cases=[[[0], [0], 0], [[0], [1], 0], [[-1000], [1000], 100]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 15, big=500), -1000, 1000), ints(rng, pick_n(rng, 1, 15, big=500), -1000, 1000), rng.randint(0, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Find Target Indices After Sorting Array


def _target_indices(nums: list[int], target: int) -> list[int]:
    smaller = sum(x < target for x in nums)
    equal = nums.count(target)
    return list(range(smaller, smaller + equal))


TARGET_INDICES = ProblemSource(
    title="Find Target Indices After Sorting Array",
    statement="""
Sort `nums` in non-decreasing order and return, in increasing order, every index where the sorted array holds `target`. Return an empty list if
`target` doesn't occur.
""",
    constraints="""
- `1 <= nums.length <= 100`
- `1 <= nums[i], target <= 100`
""",
    signature=function("targetIndices", [("nums", "int[]"), ("target", "int")], "int[]"),
    reference=_target_indices,
    brute=lambda nums, target: [i for i, x in enumerate(sorted(nums)) if x == target],
    examples=[Example([[1, 2, 5, 2, 3], 2], "Sorted: [1,2,2,3,5]."), Example([[1, 2, 5, 2, 3], 3]), Example([[1, 2, 5, 2, 3], 4])],
    edge_cases=[[[7], 7], [[7], 1], [[3, 3, 3], 3]],
    generator=lambda rng: [(v := ints(rng, rng.randint(1, 100), 1, rng.choice([5, 100]))), rng.choice([rng.choice(v), rng.randint(1, 100)])],
    random_count=8,
)


# ---------------------------------------------------------------- Russian Doll Envelopes


def _max_envelopes(envelopes: list[list[int]]) -> int:
    tails: list[int] = []
    for _, h in sorted(envelopes, key=lambda e: (e[0], -e[1])):
        i = bisect.bisect_left(tails, h)
        tails[i : i + 1] = [h]
    return len(tails)


def _envelopes_brute(envelopes: list[list[int]]) -> int:
    ordered = sorted(envelopes)
    best = [1] * len(ordered)
    for i, (w, h) in enumerate(ordered):
        for j in range(i):
            if ordered[j][0] < w and ordered[j][1] < h:
                best[i] = max(best[i], best[j] + 1)
    return max(best)


RUSSIAN_DOLL = ProblemSource(
    title="Russian Doll Envelopes",
    statement="""
`envelopes[i] = [w, h]` gives an envelope's width and height. One envelope fits inside another only if **both** its width and height are strictly
smaller. Envelopes can't be rotated. Return the maximum number of envelopes you can nest one inside another.
""",
    constraints="""
- `1 <= envelopes.length <= 10^5`
- `1 <= w, h <= 10^5`
""",
    signature=function("maxEnvelopes", [("envelopes", "int[][]")], "int"),
    reference=_max_envelopes,
    brute=_envelopes_brute,
    brute_input_limit=6000,
    examples=[Example([[[5, 4], [6, 4], [6, 7], [2, 3]]], "[2,3] -> [5,4] -> [6,7]."), Example([[[1, 1], [1, 1], [1, 1]]])],
    edge_cases=[[[[1, 1]]], [[[1, 2], [1, 3], [1, 4]]], [[[3, 3], [2, 2], [1, 1]]]],
    generator=lambda rng: [[[rng.randint(1, (hi := rng.choice([6, 100, 10**5]))), rng.randint(1, hi)] for _ in range(pick_n(rng, 1, 20, big=3000))]],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Operations to Make All Array Elements Equal


def _min_operations(nums: list[int], queries: list[int]) -> list[int]:
    values = sorted(nums)
    prefix = [0, *itertools.accumulate(values)]
    total, n = prefix[-1], len(values)
    out = []
    for q in queries:
        i = bisect.bisect_left(values, q)
        out.append(q * i - prefix[i] + (total - prefix[i]) - q * (n - i))
    return out


MIN_OPS_EQUAL = ProblemSource(
    title="Minimum Operations to Make All Array Elements Equal",
    statement="""
For each `queries[i]`, find the minimum number of operations to make every element of `nums` equal to `queries[i]`, where one operation increases
or decreases a single element by `1`. Each query starts from the original `nums`. Return the answers as a list.
""",
    constraints="""
- `1 <= nums.length, queries.length <= 10^5`
- `1 <= nums[i], queries[i] <= 10^9`
- answers can exceed 32 bits
""",
    signature=function("minOperations", [("nums", "int[]"), ("queries", "int[]")], "long[]"),
    reference=_min_operations,
    brute=lambda nums, queries: [sum(abs(x - q) for x in nums) for q in queries],
    brute_input_limit=8000,
    examples=[Example([[3, 1, 6, 8], [1, 5]], "To 1: 0+2+5+7 = 14. To 5: 2+4+1+3 = 10."), Example([[2, 9, 6, 3], [10]])],
    edge_cases=[[[1], [1]], [[1000000000] * 3, [1]], [[5, 5], [5, 4, 6]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 15, big=2000), 1, (hi := rng.choice([20, 10**9]))), ints(rng, pick_n(rng, 1, 10, big=1000), 1, hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Subsequence With Limited Sum


def _answer_queries(nums: list[int], queries: list[int]) -> list[int]:
    prefix = list(itertools.accumulate(sorted(nums)))
    return [bisect.bisect_right(prefix, q) for q in queries]


def _limited_sum_brute(nums: list[int], queries: list[int]) -> list[int]:
    out = []
    for q in queries:
        total = count = 0
        for x in sorted(nums):
            if total + x > q:
                break
            total += x
            count += 1
        out.append(count)
    return out


LIMITED_SUM = ProblemSource(
    title="Longest Subsequence With Limited Sum",
    statement="""
For each `queries[i]`, return the maximum size of a subsequence of `nums` whose sum is at most `queries[i]`. Return the answers as a list.
""",
    constraints="""
- `1 <= nums.length, queries.length <= 1000`
- `1 <= nums[i], queries[i] <= 10^6`
""",
    signature=function("answerQueries", [("nums", "int[]"), ("queries", "int[]")], "int[]"),
    reference=_answer_queries,
    brute=_limited_sum_brute,
    examples=[Example([[4, 5, 2, 1], [3, 10, 21]], "[2,1], [4,5,1], and all four."), Example([[2, 3, 4, 5], [1]])],
    edge_cases=[[[1], [1]], [[1000000], [999999]], [[1, 1, 1], [1000000]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 15, big=1000), 1, (hi := rng.choice([20, 10**6]))), ints(rng, pick_n(rng, 1, 10, big=1000), 1, hi * 5)],
    random_count=8,
)


# ---------------------------------------------------------------- Range Sum of Sorted Subarray Sums


def _range_sum(nums: list[int], n: int, left: int, right: int) -> int:
    def count_and_sum(limit: int) -> tuple[int, int]:
        """Number and total of subarray sums <= limit (two pointers over prefix sums)."""
        count = total = window = acc = 0
        i = 0
        for j, x in enumerate(nums):
            window += x
            acc += x * (j - i + 1)
            while window > limit:
                acc -= window
                window -= nums[i]
                i += 1
            count += j - i + 1
            total += acc
        return count, total

    def first_k_sum(k: int) -> int:
        lo, hi = min(nums), sum(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if count_and_sum(mid)[0] >= k:
                hi = mid
            else:
                lo = mid + 1
        count, total = count_and_sum(lo)
        return total - lo * (count - k)

    return (first_k_sum(right) - first_k_sum(left - 1)) % _MOD


def _range_sum_brute(nums: list[int], n: int, left: int, right: int) -> int:
    sums = sorted(sum(nums[i:j]) for i in range(n) for j in range(i + 1, n + 1))
    return sum(sums[left - 1 : right]) % _MOD


def _range_sum_gen(rng: random.Random) -> list:
    nums = ints(rng, pick_n(rng, 1, 12, big=1000), 1, 100)
    total = len(nums) * (len(nums) + 1) // 2
    left = rng.randint(1, total)
    return [nums, len(nums), left, rng.randint(left, total)]


RANGE_SUM_SORTED = ProblemSource(
    title="Range Sum of Sorted Subarray Sums",
    statement="""
`nums` has `n` positive integers. Compute the sums of all `n * (n + 1) / 2` non-empty contiguous subarrays and sort them in non-decreasing order.
Return the sum of the elements from position `left` to position `right` (1-indexed, inclusive) of that sorted list, modulo `10^9 + 7`.
""",
    constraints="""
- `n == nums.length`, `1 <= n <= 1000`
- `1 <= nums[i] <= 100`
- `1 <= left <= right <= n * (n + 1) / 2`
""",
    signature=function("rangeSum", [("nums", "int[]"), ("n", "int"), ("left", "int"), ("right", "int")], "int"),
    reference=_range_sum,
    brute=lambda nums, n, left, right: _range_sum_brute(nums, n, left, right) if n <= 150 else NotImplemented,
    examples=[Example([[1, 2, 3, 4], 4, 1, 5], "Sorted sums: 1,2,3,3,4,5,6,7,9,10; the first five add to 13."), Example([[1, 2, 3, 4], 4, 3, 4]), Example([[1, 2, 3, 4], 4, 1, 10])],
    edge_cases=[[[100], 1, 1, 1], [[1, 1], 2, 1, 3], [[100] * 1000, 1000, 1, 500500]],
    generator=_range_sum_gen,
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Magnetic Force Between Two Balls


def _max_distance(position: list[int], m: int) -> int:
    spots = sorted(position)

    def fits(gap: int) -> bool:
        placed, last = 1, spots[0]
        for p in spots[1:]:
            if p - last >= gap:
                placed, last = placed + 1, p
        return placed >= m

    lo, hi = 1, spots[-1] - spots[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fits(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def _magnetic_brute(position: list[int], m: int) -> int:
    if len(position) > 12:
        return NotImplemented
    return max(min(b - a for a, b in itertools.pairwise(c)) for c in itertools.combinations(sorted(position), m))


MAGNETIC_FORCE = ProblemSource(
    title="Magnetic Force Between Two Balls",
    statement="""
There are baskets at the distinct positions in `position`. Place `m` balls into `m` different baskets so that the *minimum* distance between any
two balls is as large as possible. Return that largest possible minimum distance.
""",
    constraints="""
- `2 <= position.length <= 10^5`, distinct values
- `1 <= position[i] <= 10^9`
- `2 <= m <= position.length`
""",
    signature=function("maxDistance", [("position", "int[]"), ("m", "int")], "int"),
    reference=_max_distance,
    brute=_magnetic_brute,
    examples=[Example([[1, 2, 3, 4, 7], 3], "Balls at 1, 4 and 7."), Example([[5, 4, 3, 2, 1, 1000000000], 2])],
    edge_cases=[[[1, 2], 2], [[1, 1000000000], 2], [[1, 3, 6, 10], 4]],
    generator=lambda rng: [(p := sample(rng, range(1, rng.choice([30, 10**9])), pick_n(rng, 2, 12, big=5000))), rng.randint(2, len(p))],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Space Wasted from Packaging


def _min_wasted_space(packages: list[int], boxes: list[list[int]]) -> int:
    packages = sorted(packages)
    prefix = [0, *itertools.accumulate(packages)]
    best = None
    for supplier in boxes:
        sizes = sorted(supplier)
        if sizes[-1] < packages[-1]:
            continue
        total, start = 0, 0
        for size in sizes:
            end = bisect.bisect_right(packages, size)
            total += size * (end - start)
            start = end
        best = total if best is None else min(best, total)
    return -1 if best is None else (best - prefix[-1]) % _MOD


def _wasted_brute(packages: list[int], boxes: list[list[int]]) -> int:
    best = None
    for supplier in boxes:
        if max(supplier) < max(packages):
            continue
        waste = sum(min(b for b in supplier if b >= p) - p for p in packages)
        best = waste if best is None else min(best, waste)
    return -1 if best is None else best % _MOD


def _packaging_gen(rng: random.Random) -> list:
    hi = rng.choice([20, 10**5])
    packages = ints(rng, pick_n(rng, 1, 10, big=2000), 1, hi)
    boxes = [sample(rng, range(1, hi + 1), rng.randint(1, rng.choice([4, 50]))) for _ in range(rng.randint(1, rng.choice([4, 40])))]
    return [packages, boxes]


PACKAGING = ProblemSource(
    title="Minimum Space Wasted from Packaging",
    statement="""
Each package `packages[i]` must go into its own box, and a package fits in a box if its size is at most the box's size. You must buy **all** boxes
from a single supplier; supplier `j` sells boxes in the sizes listed in `boxes[j]`, with unlimited stock of each size. The *wasted space* of a
packed box is `box size - package size`.

Choose the supplier that minimises the total wasted space and return that minimum modulo `10^9 + 7`, or `-1` if no supplier can fit every
package.
""",
    constraints="""
- `1 <= packages.length <= 10^5`, `1 <= boxes.length <= 10^5`
- `1 <= boxes[j].length`, total box sizes `<= 10^5`, sizes within a supplier are distinct
- `1 <= packages[i], boxes[j][k] <= 10^5`
""",
    signature=function("minWastedSpace", [("packages", "int[]"), ("boxes", "int[][]")], "int"),
    reference=_min_wasted_space,
    brute=_wasted_brute,
    brute_input_limit=5000,
    examples=[Example([[2, 3, 5], [[4, 8], [2, 8]]], "Supplier 0: boxes 4, 4, 8 waste 6."), Example([[2, 3, 5], [[1, 4], [2, 3], [3, 4]]], "Nobody sells a box of size >= 5."), Example([[3, 5, 8, 10, 11, 12], [[12], [11, 9], [10, 5, 14]]])],
    edge_cases=[[[1], [[1]]], [[100000], [[99999]]], [[1, 1, 1], [[100000]]]],
    generator=_packaging_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Two Sum Less Than K


def _two_sum_less_than_k(nums: list[int], k: int) -> int:
    values = sorted(nums)
    best, i, j = -1, 0, len(values) - 1
    while i < j:
        s = values[i] + values[j]
        if s < k:
            best = max(best, s)
            i += 1
        else:
            j -= 1
    return best


TWO_SUM_LESS = ProblemSource(
    title="Two Sum Less Than K",
    statement="""
Return the largest `nums[i] + nums[j]` with `i < j` that is strictly less than `k`, or `-1` if no pair qualifies.
""",
    constraints="""
- `1 <= nums.length <= 100`
- `1 <= nums[i] <= 1000`
- `1 <= k <= 2000`
""",
    signature=function("twoSumLessThanK", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_two_sum_less_than_k,
    brute=lambda nums, k: max((a + b for a, b in itertools.combinations(nums, 2) if a + b < k), default=-1),
    examples=[Example([[34, 23, 1, 24, 75, 33, 54, 8], 60], "34 + 24 = 58."), Example([[10, 20, 30], 15])],
    edge_cases=[[[1], 5], [[1, 1], 2], [[1, 1], 3], [[1000, 1000], 2000]],
    generator=lambda rng: [ints(rng, rng.randint(1, 100), 1, rng.choice([50, 1000])), rng.randint(1, 2000)],
    random_count=8,
)


# ---------------------------------------------------------------- Valid Triangle Number


def _triangle_number(nums: list[int]) -> int:
    values = sorted(nums)
    count = 0
    for k in range(len(values) - 1, 1, -1):
        i, j = 0, k - 1
        while i < j:
            if values[i] + values[j] > values[k]:
                count += j - i
                j -= 1
            else:
                i += 1
    return count


def _triangle_brute(nums: list[int]) -> int:
    if len(nums) > 80:
        return NotImplemented
    return sum(1 for a, b, c in itertools.combinations(sorted(nums), 3) if a + b > c)


TRIANGLE_NUMBER = ProblemSource(
    title="Valid Triangle Number",
    statement="""
Return how many triples of indices `i < j < k` pick side lengths `nums[i], nums[j], nums[k]` that form a triangle with positive area (each side
strictly shorter than the sum of the other two).
""",
    constraints="""
- `1 <= nums.length <= 1000`
- `0 <= nums[i] <= 1000`
""",
    signature=function("triangleNumber", [("nums", "int[]")], "int"),
    reference=_triangle_number,
    brute=_triangle_brute,
    examples=[Example([[2, 2, 3, 4]], "(2,3,4) twice and (2,2,3)."), Example([[4, 2, 3, 4]])],
    edge_cases=[[[1]], [[0, 0, 0]], [[1, 1, 1]], [[1, 2, 3]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=1000), 0, rng.choice([10, 1000]))],
    random_count=8,
)


# ---------------------------------------------------------------- Count Pairs in Two Arrays


def _count_pairs(nums1: list[int], nums2: list[int]) -> int:
    diffs = sorted(a - b for a, b in zip(nums1, nums2, strict=True))
    count, i, j = 0, 0, len(diffs) - 1
    while i < j:
        if diffs[i] + diffs[j] > 0:
            count += j - i
            j -= 1
        else:
            i += 1
    return count


def _count_pairs_brute(nums1: list[int], nums2: list[int]) -> int:
    n = len(nums1)
    if n > 400:
        return NotImplemented
    return sum(1 for i in range(n) for j in range(i + 1, n) if nums1[i] + nums1[j] > nums2[i] + nums2[j])


COUNT_PAIRS_TWO = ProblemSource(
    title="Count Pairs in Two Arrays",
    statement="""
`nums1` and `nums2` have the same length `n`. Count the index pairs `i < j` with `nums1[i] + nums1[j] > nums2[i] + nums2[j]`. The count can exceed
32 bits.
""",
    constraints="""
- `1 <= n <= 10^5`
- `1 <= nums1[i], nums2[i] <= 10^5`
""",
    signature=function("countPairs", [("nums1", "int[]"), ("nums2", "int[]")], "long"),
    reference=_count_pairs,
    brute=_count_pairs_brute,
    examples=[Example([[2, 1, 2, 1], [1, 2, 1, 2]], "Only (0, 2): 4 > 2."), Example([[1, 10, 6, 2], [1, 4, 1, 5]])],
    edge_cases=[[[1], [1]], [[5, 5], [1, 1]], [[1, 1, 1], [2, 2, 2]]],
    generator=lambda rng: [ints(rng, (n := pick_n(rng, 1, 20, big=3000)), 1, (hi := rng.choice([5, 10**5]))), ints(rng, n, 1, hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Put Marbles in Bags


def _put_marbles(weights: list[int], k: int) -> int:
    cuts = sorted(a + b for a, b in itertools.pairwise(weights))
    return sum(cuts[len(cuts) - k + 1 :]) - sum(cuts[: k - 1]) if k > 1 else 0


def _marbles_brute(weights: list[int], k: int) -> int:
    n = len(weights)
    if n > 14:
        return NotImplemented
    scores = []
    for cuts in itertools.combinations(range(1, n), k - 1):
        bounds = [0, *cuts, n]
        scores.append(sum(weights[bounds[i]] + weights[bounds[i + 1] - 1] for i in range(k)))
    return max(scores) - min(scores)


MARBLES = ProblemSource(
    title="Put Marbles in Bags",
    statement="""
Split the marbles `weights` (in order) into exactly `k` non-empty contiguous bags. A bag holding marbles `i..j` costs `weights[i] + weights[j]`,
and a distribution's score is the sum of its bag costs. Return the difference between the maximum and minimum possible scores.
""",
    constraints="""
- `1 <= k <= weights.length <= 10^5`
- `1 <= weights[i] <= 10^9`
- the answer can exceed 32 bits
""",
    signature=function("putMarbles", [("weights", "int[]"), ("k", "int")], "long"),
    reference=_put_marbles,
    brute=_marbles_brute,
    examples=[Example([[1, 3, 5, 1], 2], "The three splits score 6, 10 and 8, so the answer is 10 - 6 = 4."), Example([[1, 3], 2], "Only one split exists.")],
    edge_cases=[[[7], 1], [[1, 2, 3], 3], [[1000000000] * 5, 2]],
    generator=lambda rng: [(w := ints(rng, pick_n(rng, 1, 12, big=5000), 1, rng.choice([20, 10**9]))), rng.randint(1, len(w))],
    random_count=8,
)


# ---------------------------------------------------------------- H-Index


def _h_index(citations: list[int]) -> int:
    counts = [0] * (len(citations) + 1)
    for c in citations:
        counts[min(c, len(citations))] += 1
    papers = 0
    for h in range(len(citations), -1, -1):
        papers += counts[h]
        if papers >= h:
            return h
    return 0


H_INDEX = ProblemSource(
    title="H-Index",
    statement="""
`citations[i]` is the number of citations of a researcher's `i`-th paper. Their *h-index* is the largest `h` such that at least `h` papers have
at least `h` citations each. Return it.
""",
    constraints="""
- `1 <= citations.length <= 5000`
- `0 <= citations[i] <= 1000`
""",
    signature=function("hIndex", [("citations", "int[]")], "int"),
    reference=_h_index,
    brute=lambda citations: max(h for h in range(len(citations) + 1) if sum(c >= h for c in citations) >= h),
    brute_input_limit=6000,
    examples=[Example([[3, 0, 6, 1, 5]], "Three papers have at least 3 citations."), Example([[1, 3, 1]])],
    edge_cases=[[[0]], [[100]], [[0, 0, 0]], [[1000] * 10]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=5000), 0, rng.choice([10, 1000]))],
    random_count=8,
)


# ---------------------------------------------------------------- Reverse Pairs


def _reverse_pairs(nums: list[int]) -> int:
    def sort_count(lo: int, hi: int) -> int:
        if hi - lo <= 1:
            return 0
        mid = (lo + hi) // 2
        count = sort_count(lo, mid) + sort_count(mid, hi)
        j = mid
        for i in range(lo, mid):
            while j < hi and nums[i] > 2 * nums[j]:
                j += 1
            count += j - mid
        nums[lo:hi] = sorted(nums[lo:hi])
        return count

    nums = nums[:]
    return sort_count(0, len(nums))


def _reverse_pairs_brute(nums: list[int]) -> int:
    n = len(nums)
    if n > 500:
        return NotImplemented
    return sum(1 for i in range(n) for j in range(i + 1, n) if nums[i] > 2 * nums[j])


REVERSE_PAIRS = ProblemSource(
    title="Reverse Pairs",
    statement="""
A *reverse pair* is a pair of indices `i < j` with `nums[i] > 2 * nums[j]`. Return the number of reverse pairs in `nums`.
""",
    constraints="""
- `1 <= nums.length <= 5 * 10^4`
- `-2^31 <= nums[i] <= 2^31 - 1`
""",
    signature=function("reversePairs", [("nums", "int[]")], "int"),
    reference=_reverse_pairs,
    brute=_reverse_pairs_brute,
    examples=[Example([[1, 3, 2, 3, 1]], "(1,4) and (3,4)."), Example([[2, 4, 3, 5, 1]])],
    edge_cases=[[[1]], [[2147483647, 2147483647, 2147483647]], [[-5, -5]], [[-2147483648, -1073741825]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=5000), -(hi := rng.choice([10, 2**31 - 1])), hi)],
    random_count=8,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Minimum Time Difference


def _find_min_difference(timePoints: list[str]) -> int:
    minutes = sorted(int(t[:2]) * 60 + int(t[3:]) for t in timePoints)
    gaps = [b - a for a, b in itertools.pairwise(minutes)]
    return min([*gaps, minutes[0] + 1440 - minutes[-1]])


def _time_diff_brute(timePoints: list[str]) -> int:
    minutes = [int(t[:2]) * 60 + int(t[3:]) for t in timePoints]
    return min(min(abs(a - b), 1440 - abs(a - b)) for a, b in itertools.combinations(minutes, 2))


def _time_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 10, big=1440)
    return [[f"{rng.randint(0, rng.choice([1, 23])):02d}:{rng.randint(0, 59):02d}" for _ in range(n)]]


MIN_TIME_DIFFERENCE = ProblemSource(
    title="Minimum Time Difference",
    statement="""
`timePoints` holds 24-hour clock times in `"HH:MM"` format. Return the minimum difference, in minutes, between any two of them. The clock wraps
around: `"23:59"` and `"00:00"` are one minute apart.
""",
    constraints="""
- `2 <= timePoints.length <= 2 * 10^4`
- every entry is a valid `"HH:MM"` time
""",
    signature=function("findMinDifference", [("timePoints", "string[]")], "int"),
    reference=_find_min_difference,
    brute=_time_diff_brute,
    brute_input_limit=4000,
    examples=[Example([["23:59", "00:00"]]), Example([["00:00", "23:59", "00:00"]], "Two identical times are 0 apart.")],
    edge_cases=[[["12:00", "00:00"]], [["01:00", "02:30", "23:00"]], [["05:31", "22:08", "00:35"]]],
    generator=_time_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Absolute Difference


def _minimum_abs_difference(arr: list[int]) -> list[list[int]]:
    values = sorted(arr)
    best = min(b - a for a, b in itertools.pairwise(values))
    return [[a, b] for a, b in itertools.pairwise(values) if b - a == best]


def _min_abs_brute(arr: list[int]) -> list[list[int]]:
    best = min(abs(a - b) for a, b in itertools.combinations(arr, 2))
    return sorted(sorted(p) for p in itertools.combinations(arr, 2) if abs(p[0] - p[1]) == best)


MIN_ABS_DIFFERENCE = ProblemSource(
    title="Minimum Absolute Difference",
    statement="""
`arr` holds distinct integers. Find the minimum absolute difference between any two of them and return every pair `[a, b]` with `a < b` that
has that difference, sorted in ascending order of `a`.
""",
    constraints="""
- `2 <= arr.length <= 10^5`, distinct values
- `-10^6 <= arr[i] <= 10^6`
""",
    signature=function("minimumAbsDifference", [("arr", "int[]")], "int[][]"),
    reference=_minimum_abs_difference,
    brute=lambda arr: _min_abs_brute(arr) if len(arr) <= 200 else NotImplemented,
    examples=[Example([[4, 2, 1, 3]], "Every consecutive pair differs by 1."), Example([[1, 3, 6, 10, 15]]), Example([[3, 8, -10, 23, 19, -4, -14, 27]])],
    edge_cases=[[[1, 2]], [[-1000000, 1000000]], [[0, 5, 10, 15]]],
    generator=lambda rng: [sample(rng, range(-(hi := rng.choice([20, 10**6])), hi + 1), pick_n(rng, 2, 15, big=5000))],
    random_count=8,
)


PROBLEMS = [
    MUTATED_ARRAY,
    CONTAINS_DUPLICATE_II,
    KTH_PAIR_DISTANCE,
    CHOOSE_FROM_RANGE,
    DISTANCE_VALUE,
    TARGET_INDICES,
    RUSSIAN_DOLL,
    MIN_OPS_EQUAL,
    LIMITED_SUM,
    RANGE_SUM_SORTED,
    MAGNETIC_FORCE,
    PACKAGING,
    TWO_SUM_LESS,
    TRIANGLE_NUMBER,
    COUNT_PAIRS_TWO,
    MARBLES,
    H_INDEX,
    REVERSE_PAIRS,
    MIN_TIME_DIFFERENCE,
    MIN_ABS_DIFFERENCE,
]
