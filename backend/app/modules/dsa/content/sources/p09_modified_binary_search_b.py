"""Pattern 9: Modified Binary Search (part 2 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import bisect
import itertools
import math

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sorted_ints

PATTERN_NUMBER = 9


# ---------------------------------------------------------------- Split Array Into Two Arrays to Minimize Sum Difference


def _minimum_difference(nums: list[int]) -> int:
    n = len(nums) // 2
    total = sum(nums)
    left, right = nums[:n], nums[n:]

    def sums_by_size(half: list[int]) -> list[list[int]]:
        out = [[] for _ in range(n + 1)]
        for mask in range(1 << n):
            size = bin(mask).count("1")
            out[size].append(sum(half[i] for i in range(n) if mask >> i & 1))
        return out

    left_sums, right_sums = sums_by_size(left), [sorted(s) for s in sums_by_size(right)]
    best = math.inf
    for size, options in enumerate(left_sums):
        pool = right_sums[n - size]
        for a in options:
            # choose b so that 2 * (a + b) is as close as possible to total
            want = total / 2 - a
            i = bisect.bisect_left(pool, want)
            for j in (i - 1, i):
                if 0 <= j < len(pool):
                    best = min(best, abs(total - 2 * (a + pool[j])))
    return int(best)


def _minimum_difference_brute(nums: list[int]) -> int:
    n, total = len(nums) // 2, sum(nums)
    return min(abs(total - 2 * sum(c)) for c in itertools.combinations(nums, n))


def _partition_gen(rng):
    n = rng.randint(1, rng.choice([4, 4, 12]))
    return [ints(rng, 2 * n, -rng.choice([10, 10**7]), rng.choice([10, 10**7]))]


MIN_SUM_DIFFERENCE = ProblemSource(
    title="Split Array Into Two Arrays to Minimize Sum Difference",
    statement="""
`nums` has `2n` integers. Split it into two arrays of exactly `n` elements each (every element goes into one
of them) so that the absolute difference between the two arrays' sums is as small as possible. Return that
minimum difference.

Hint: `n` is small, but `C(30, 15)` is too many to try; think "meet in the middle".
""",
    constraints="""
- `1 <= n <= 15`
- `nums.length == 2 * n`
- `-10^7 <= nums[i] <= 10^7`
""",
    signature=function("minimumDifference", [("nums", "int[]")], "int"),
    reference=_minimum_difference,
    brute=_minimum_difference_brute,
    brute_input_limit=60,
    examples=[Example([[3, 9, 7, 3]], "[3, 9] and [7, 3] differ by 2."), Example([[-36, 36]], "The only split differs by 72."), Example([[2, -1, 0, 4, -2, -9]], "[2, 4, -9] and [-1, 0, -2] both sum to -3.")],
    edge_cases=[[[5, 5]], [[1, 2, 3, 4]], [[-10000000, 10000000, 0, 0]]],
    generator=_partition_gen,
    random_count=8,
    time_limit_ms=2500,
)


# ---------------------------------------------------------------- Number of Flowers in Full Bloom


def _full_bloom(flowers: list[list[int]], people: list[int]) -> list[int]:
    starts = sorted(s for s, _ in flowers)
    ends = sorted(e for _, e in flowers)
    return [bisect.bisect_right(starts, t) - bisect.bisect_left(ends, t) for t in people]


def _bloom_gen(rng):
    hi = rng.choice([30, 10**9])
    flowers = [[s, min(hi, s + rng.randint(0, max(1, hi // 5)))] for s in (rng.randint(1, hi) for _ in range(pick_n(rng, 1, 15, big=1500)))]
    return [flowers, [rng.randint(1, hi) for _ in range(pick_n(rng, 1, 15, big=1500))]]


FULL_BLOOM = ProblemSource(
    title="Number of Flowers in Full Bloom",
    statement="""
`flowers[i] = [start_i, end_i]` means flower `i` is in full bloom from day `start_i` to day `end_i`, inclusive.
`people[j]` is the day person `j` visits.

Return an array whose `j`-th value is the number of flowers in full bloom when person `j` arrives.
""",
    constraints="""
- `1 <= flowers.length, people.length <= 5 * 10^4`
- `1 <= start_i <= end_i <= 10^9`
- `1 <= people[j] <= 10^9`
""",
    signature=function("fullBloomFlowers", [("flowers", "int[][]"), ("people", "int[]")], "int[]"),
    reference=_full_bloom,
    brute=lambda flowers, people: [sum(s <= t <= e for s, e in flowers) for t in people],
    examples=[Example([[[1, 6], [3, 7], [9, 12], [4, 13]], [2, 3, 7, 11]], "Answers: 1, 2, 2, 2."), Example([[[1, 10], [3, 3]], [3, 3, 2]])],
    edge_cases=[[[[1, 1]], [1, 2]], [[[5, 5], [5, 5]], [4, 5, 6]]],
    generator=_bloom_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Koko Eating Bananas


def _min_eating_speed(piles: list[int], h: int) -> int:
    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum((p + mid - 1) // mid for p in piles) <= h:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _koko_brute(piles: list[int], h: int) -> int:
    k = 1
    while sum(math.ceil(p / k) for p in piles) > h:
        k += 1
    return k


def _koko_gen(rng):
    piles = ints(rng, pick_n(rng, 1, 10, big=3000), 1, rng.choice([30, 10**9]))
    return [piles, rng.randint(len(piles), len(piles) * rng.choice([1, 3, 1000]))]


KOKO = ProblemSource(
    title="Koko Eating Bananas",
    statement="""
There are piles of bananas, `piles[i]` in pile `i`, and `h` hours. Each hour Koko picks one pile and eats `k`
bananas from it; if the pile has fewer than `k`, she eats them all and does nothing else that hour.

Return the smallest integer speed `k` that lets her finish every pile within `h` hours.
""",
    constraints="""
- `1 <= piles.length <= 10^4`
- `piles.length <= h <= 10^9`
- `1 <= piles[i] <= 10^9`
""",
    signature=function("minEatingSpeed", [("piles", "int[]"), ("h", "int")], "int"),
    reference=_min_eating_speed,
    brute=lambda piles, h: _koko_brute(piles, h) if max(piles) <= 200 else NotImplemented,
    examples=[Example([[3, 6, 7, 11], 8], "At speed 4 the piles take 1 + 2 + 2 + 3 = 8 hours."), Example([[30, 11, 23, 4, 20], 5]), Example([[30, 11, 23, 4, 20], 6])],
    edge_cases=[[[1], 1], [[1000000000], 2], [[5, 5], 10], [[312884470], 312884469]],
    generator=_koko_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Search Insert Position


def _search_insert(nums: list[int], target: int) -> int:
    return bisect.bisect_left(nums, target)


SEARCH_INSERT = ProblemSource(
    title="Search Insert Position",
    statement="""
`nums` holds distinct integers in ascending order. Return the index of `target` if it is present, otherwise the
index where it would be inserted to keep the array sorted. Your solution must run in `O(log n)` time.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-10^4 <= nums[i], target <= 10^4`, values distinct and ascending
""",
    signature=function("searchInsert", [("nums", "int[]"), ("target", "int")], "int"),
    reference=_search_insert,
    brute=lambda nums, target: sum(x < target for x in nums),
    examples=[Example([[1, 3, 5, 6], 5]), Example([[1, 3, 5, 6], 2], "2 would go between 1 and 3."), Example([[1, 3, 5, 6], 7])],
    edge_cases=[[[1], 0], [[1], 1], [[1], 2]],
    generator=lambda rng: [sorted(rng.sample(range(-10**4, 10**4), pick_n(rng, 1, 20, big=4000))), rng.randint(-10**4, 10**4)],
    random_count=8,
)


# ---------------------------------------------------------------- Find Peak Element


def _find_peak(nums: list[int]) -> int:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[mid + 1]:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _peak_gen(rng):
    n = pick_n(rng, 1, 20, big=1000)
    nums = [rng.randint(-10**4, 10**4)]
    for _ in range(n - 1):
        nums.append(nums[-1] + rng.choice([-1, 1]) * rng.randint(1, 50))
    return [nums]


FIND_PEAK = ProblemSource(
    title="Find Peak Element",
    statement="""
A *peak* is an element strictly greater than its neighbours. Imagine `nums[-1] = nums[n] = -infinity`, so an
element on the border only has to beat its single neighbour. Adjacent values in `nums` are never equal.

Return the index of **any** peak, in `O(log n)` time.
""",
    constraints="""
- `1 <= nums.length <= 1000`
- `-2^31 <= nums[i] <= 2^31 - 1`
- `nums[i] != nums[i + 1]`
""",
    signature=function("findPeakElement", [("nums", "int[]")], "int"),
    reference=_find_peak,
    brute=lambda nums: max(range(len(nums)), key=lambda i: nums[i]),
    compare="checker",
    checker="peak_index",
    examples=[Example([[1, 2, 3, 1]], "3 at index 2 is a peak."), Example([[1, 2, 1, 3, 5, 6, 4]], "Index 1 or index 5 is accepted.")],
    edge_cases=[[[7]], [[1, 2]], [[2, 1]], [[-2147483648, 2147483647]]],
    generator=_peak_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find First and Last Position of Element in Sorted Array


def _search_range(nums: list[int], target: int) -> list[int]:
    lo = bisect.bisect_left(nums, target)
    if lo == len(nums) or nums[lo] != target:
        return [-1, -1]
    return [lo, bisect.bisect_right(nums, target) - 1]


def _search_range_brute(nums: list[int], target: int) -> list[int]:
    idx = [i for i, x in enumerate(nums) if x == target]
    return [idx[0], idx[-1]] if idx else [-1, -1]


SEARCH_RANGE = ProblemSource(
    title="Find First and Last Position of Element in Sorted Array",
    statement="""
`nums` is sorted in non-decreasing order. Return `[first, last]`, the first and last indices where `target`
occurs, or `[-1, -1]` if it doesn't occur. Your solution must run in `O(log n)` time.
""",
    constraints="""
- `0 <= nums.length <= 10^5`
- `-10^9 <= nums[i], target <= 10^9`
- `nums` is sorted in non-decreasing order
""",
    signature=function("searchRange", [("nums", "int[]"), ("target", "int")], "int[]"),
    reference=_search_range,
    brute=_search_range_brute,
    examples=[Example([[5, 7, 7, 8, 8, 10], 8]), Example([[5, 7, 7, 8, 8, 10], 6]), Example([[], 0])],
    edge_cases=[[[1], 1], [[2, 2], 2], [[1, 2, 3], 3]],
    generator=lambda rng: [(v := sorted_ints(rng, pick_n(rng, 0, 20, big=4000), -5, 5)), rng.choice(v) if v and rng.random() < 0.6 else rng.randint(-6, 6)],
    random_count=8,
)


# ---------------------------------------------------------------- Kth Smallest Product of Two Sorted Arrays


def _kth_smallest_product(nums1: list[int], nums2: list[int], k: int) -> int:
    def count_at_most(limit: int) -> int:
        count = 0
        for a in nums1:
            if a > 0:
                count += bisect.bisect_right(nums2, limit // a)
            elif a < 0:
                # a * b <= limit  <=>  b >= ceil(limit / a)  (exact integer ceiling)
                count += len(nums2) - bisect.bisect_left(nums2, -((-limit) // a))
            elif limit >= 0:
                count += len(nums2)
        return count

    lo, hi = -(10**10), 10**10
    while lo < hi:
        mid = (lo + hi) // 2
        if count_at_most(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _product_gen(rng):
    hi = rng.choice([5, 10**5])
    a = sorted_ints(rng, pick_n(rng, 1, 12, big=1500), -hi, hi)
    b = sorted_ints(rng, pick_n(rng, 1, 12, big=1500), -hi, hi)
    return [a, b, rng.randint(1, len(a) * len(b))]


KTH_PRODUCT = ProblemSource(
    title="Kth Smallest Product of Two Sorted Arrays",
    statement="""
`nums1` and `nums2` are sorted in non-decreasing order and may contain negative numbers and zeros. Consider all
`nums1.length * nums2.length` products `nums1[i] * nums2[j]`. Return the `k`-th smallest of them (1-based,
counting equal products separately).
""",
    constraints="""
- `1 <= nums1.length, nums2.length <= 5 * 10^4`
- `-10^5 <= nums1[i], nums2[j] <= 10^5`
- `1 <= k <= nums1.length * nums2.length`
""",
    signature=function("kthSmallestProduct", [("nums1", "int[]"), ("nums2", "int[]"), ("k", "long")], "long"),
    reference=_kth_smallest_product,
    brute=lambda nums1, nums2, k: sorted(a * b for a in nums1 for b in nums2)[k - 1],
    brute_input_limit=5000,
    examples=[Example([[2, 5], [3, 4], 2], "Products 6, 8, 15, 20; the 2nd smallest is 8."), Example([[-4, -2, 0, 3], [2, 4], 6]), Example([[-2, -1, 0, 1, 2], [-3, -1, 2, 4, 5], 3])],
    edge_cases=[[[0], [0], 1], [[-100000], [100000], 1], [[-1, 1], [-1, 1], 4]],
    generator=_product_gen,
    random_count=8,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Sqrt(x)


def _my_sqrt(x: int) -> int:
    lo, hi = 0, x
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= x:
            lo = mid
        else:
            hi = mid - 1
    return lo


SQRT = ProblemSource(
    title="Sqrt(x)",
    statement="""
Given a non-negative integer `x`, return the square root of `x` rounded **down** to an integer. Don't use a
built-in power or square-root function or operator.
""",
    constraints="""
- `0 <= x <= 2^31 - 1`
""",
    signature=function("mySqrt", [("x", "int")], "int"),
    reference=_my_sqrt,
    brute=math.isqrt,
    examples=[Example([4]), Example([8], "sqrt(8) = 2.828..., rounded down to 2.")],
    edge_cases=[[0], [1], [2], [2147395599], [2147483647]],
    generator=lambda rng: [rng.choice([rng.randint(0, 1000), rng.randint(0, 2**31 - 1), rng.randint(1, 46340) ** 2])],
    random_count=8,
)


# ---------------------------------------------------------------- Reaching Points


def _reaching_points(sx: int, sy: int, tx: int, ty: int) -> bool:
    while tx >= sx and ty >= sy:
        if tx == sx and ty == sy:
            return True
        if tx > ty:
            if ty == sy:
                return (tx - sx) % ty == 0
            tx %= ty
        else:
            if tx == sx:
                return (ty - sy) % tx == 0
            ty %= tx
    return False


def _reaching_brute(sx: int, sy: int, tx: int, ty: int) -> bool:
    frontier, seen = [(sx, sy)], set()
    while frontier:
        x, y = frontier.pop()
        if (x, y) == (tx, ty):
            return True
        if (x, y) in seen or x > tx or y > ty:
            continue
        seen.add((x, y))
        frontier += [(x + y, y), (x, x + y)]
    return False


def _points_gen(rng):
    sx, sy = rng.randint(1, 6), rng.randint(1, 6)
    x, y = sx, sy
    for _ in range(rng.randint(0, 12)):
        if rng.random() < 0.5:
            x += y
        else:
            y += x
    if rng.random() < 0.35:
        x += rng.randint(1, 3)
    return [sx, sy, min(x, 10**9), min(y, 10**9)]


REACHING_POINTS = ProblemSource(
    title="Reaching Points",
    statement="""
From a point `(x, y)` you may move to `(x, x + y)` or to `(x + y, y)`. Given a start `(sx, sy)` and a target
`(tx, ty)`, return `true` if the target can be reached from the start using any number of moves.
""",
    constraints="""
- `1 <= sx, sy, tx, ty <= 10^9`
""",
    signature=function("reachingPoints", [("sx", "int"), ("sy", "int"), ("tx", "int"), ("ty", "int")], "bool"),
    reference=_reaching_points,
    brute=lambda sx, sy, tx, ty: _reaching_brute(sx, sy, tx, ty) if tx * ty <= 10**5 else NotImplemented,
    examples=[Example([1, 1, 3, 5], "(1,1) -> (1,2) -> (3,2) -> (3,5)."), Example([1, 1, 2, 2]), Example([1, 1, 1, 1])],
    edge_cases=[[1, 1, 1000000000, 1], [3, 7, 3, 4], [9, 5, 12, 8], [1, 1, 2, 1], [35, 13, 455955547, 420098884]],
    generator=_points_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Kth Missing Positive Number


def _find_kth_positive(arr: list[int], k: int) -> int:
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] - mid - 1 < k:
            lo = mid + 1
        else:
            hi = mid
    return lo + k


def _kth_missing_brute(arr: list[int], k: int) -> int:
    present, x = set(arr), 0
    while k:
        x += 1
        if x not in present:
            k -= 1
    return x


KTH_MISSING = ProblemSource(
    title="Kth Missing Positive Number",
    statement="""
`arr` holds positive integers in strictly increasing order. Return the `k`-th positive integer that is
**missing** from `arr`. Can you do it in less than `O(n)` time?
""",
    constraints="""
- `1 <= arr.length <= 1000`
- `1 <= arr[i] <= 1000`, strictly increasing
- `1 <= k <= 1000`
""",
    signature=function("findKthPositive", [("arr", "int[]"), ("k", "int")], "int"),
    reference=_find_kth_positive,
    brute=_kth_missing_brute,
    examples=[Example([[2, 3, 4, 7, 11], 5], "Missing: 1, 5, 6, 8, 9, ...; the 5th is 9."), Example([[1, 2, 3, 4], 2], "Missing: 5, 6, ...")],
    edge_cases=[[[1], 1], [[2], 1], [[1000], 1000], [[1, 2, 3], 1000]],
    generator=lambda rng: [sorted(rng.sample(range(1, 1001), pick_n(rng, 1, 20, big=1000))), rng.randint(1, 1000)],
    random_count=8,
)


# ---------------------------------------------------------------- Find the Smallest Divisor Given a Threshold


def _smallest_divisor(nums: list[int], threshold: int) -> int:
    lo, hi = 1, max(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum((x + mid - 1) // mid for x in nums) <= threshold:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _divisor_gen(rng):
    nums = ints(rng, pick_n(rng, 1, 10, big=3000), 1, rng.choice([30, 10**6]))
    return [nums, rng.randint(len(nums), len(nums) * rng.choice([1, 4, 100]))]


SMALLEST_DIVISOR = ProblemSource(
    title="Find the Smallest Divisor Given a Threshold",
    statement="""
Choose a positive integer divisor `d`, divide every element of `nums` by it and round each result **up**; then
add up those rounded results. Return the smallest `d` for which this total is at most `threshold`.
""",
    constraints="""
- `1 <= nums.length <= 5 * 10^4`
- `1 <= nums[i] <= 10^6`
- `nums.length <= threshold <= 10^6`
""",
    signature=function("smallestDivisor", [("nums", "int[]"), ("threshold", "int")], "int"),
    reference=_smallest_divisor,
    brute=lambda nums, threshold: next(d for d in range(1, max(nums) + 1) if sum(math.ceil(x / d) for x in nums) <= threshold) if max(nums) <= 500 else NotImplemented,
    examples=[Example([[1, 2, 5, 9], 6], "With d = 5 the rounded results are 1, 1, 1, 2, totalling 5."), Example([[44, 22, 33, 11, 1], 5])],
    edge_cases=[[[1], 1], [[1000000], 1], [[2, 3, 5, 7, 11], 11], [[19], 5]],
    generator=_divisor_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Search a 2D Matrix


def _search_matrix(matrix: list[list[int]], target: int) -> bool:
    m, n = len(matrix), len(matrix[0])
    lo, hi = 0, m * n - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = matrix[mid // n][mid % n]
        if value == target:
            return True
        if value < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False


def _matrix_gen(rng):
    m, n = pick_n(rng, 1, 6, big=100), pick_n(rng, 1, 6, big=100)
    flat = sorted(ints(rng, m * n, -10**4, 10**4))
    matrix = [flat[i * n : (i + 1) * n] for i in range(m)]
    return [matrix, rng.choice(flat) if rng.random() < 0.5 else rng.randint(-10**4, 10**4)]


SEARCH_2D_MATRIX = ProblemSource(
    title="Search a 2D Matrix",
    statement="""
In the `m x n` matrix, each row is sorted in non-decreasing order and each row's first value is greater than the
previous row's last value. Return `true` if `target` is in the matrix, in `O(log(m * n))` time.
""",
    constraints="""
- `1 <= m, n <= 100`
- `-10^4 <= matrix[i][j], target <= 10^4`
""",
    signature=function("searchMatrix", [("matrix", "int[][]"), ("target", "int")], "bool"),
    reference=_search_matrix,
    brute=lambda matrix, target: any(target in row for row in matrix),
    examples=[Example([[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3]), Example([[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13])],
    edge_cases=[[[[1]], 1], [[[1]], 2], [[[1], [3]], 3]],
    generator=_matrix_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Zero Array Transformation II


def _min_zero_array(nums: list[int], queries: list[list[int]]) -> int:
    def works(k: int) -> bool:
        diff = [0] * (len(nums) + 1)
        for left, right, val in queries[:k]:
            diff[left] += val
            diff[right + 1] -= val
        running = 0
        for i, x in enumerate(nums):
            running += diff[i]
            if running < x:
                return False
        return True

    if not works(len(queries)):
        return -1
    lo, hi = 0, len(queries)
    while lo < hi:
        mid = (lo + hi) // 2
        if works(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def _zero_array_brute(nums: list[int], queries: list[list[int]]) -> int:
    for k in range(len(queries) + 1):
        room = [0] * len(nums)
        for left, right, val in queries[:k]:
            for i in range(left, right + 1):
                room[i] += val
        if all(r >= x for r, x in zip(room, nums, strict=True)):
            return k
    return -1


def _zero_gen(rng):
    n = pick_n(rng, 1, 10, big=2000)
    nums = ints(rng, n, 0, rng.choice([5, 500]))
    queries = []
    for _ in range(pick_n(rng, 1, 12, big=2000)):
        left = rng.randint(0, n - 1)
        queries.append([left, rng.randint(left, n - 1), rng.randint(1, 5)])
    return [nums, queries]


ZERO_ARRAY_II = ProblemSource(
    title="Zero Array Transformation II",
    statement="""
`queries[i] = [l_i, r_i, val_i]`. Processing query `i` lets you decrease each element of `nums` with index in
`[l_i, r_i]` by any amount between `0` and `val_i`, chosen independently per element.

Return the smallest `k` such that, after processing the first `k` queries in order, `nums` can have become all
zeros. Return `-1` if even all the queries are not enough. (`k = 0` means `nums` is already all zeros.)
""",
    constraints="""
- `1 <= nums.length <= 10^5`, `0 <= nums[i] <= 5 * 10^5`
- `1 <= queries.length <= 10^5`
- `0 <= l_i <= r_i < nums.length`, `1 <= val_i <= 5`
""",
    signature=function("minZeroArray", [("nums", "int[]"), ("queries", "int[][]")], "int"),
    reference=_min_zero_array,
    brute=_zero_array_brute,
    brute_input_limit=400,
    examples=[Example([[2, 0, 2], [[0, 2, 1], [0, 2, 1], [1, 1, 3]]], "After the first two queries each element can be reduced by 2."), Example([[4, 3, 2, 1], [[1, 3, 2], [0, 2, 1]]], "Index 0 can be reduced by at most 1.")],
    edge_cases=[[[0], [[0, 0, 1]]], [[5], [[0, 0, 5]]], [[1, 1], [[0, 0, 1]]]],
    generator=_zero_gen,
    random_count=8,
)


# ---------------------------------------------------------------- House Robber IV


def _min_capability(nums: list[int], k: int) -> int:
    def can_rob(cap: int) -> bool:
        count, i = 0, 0
        while i < len(nums):
            if nums[i] <= cap:
                count += 1
                i += 2
            else:
                i += 1
        return count >= k

    lo, hi = min(nums), max(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if can_rob(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def _robber_iv_brute(nums: list[int], k: int) -> int:
    best = math.inf
    for chosen in itertools.combinations(range(len(nums)), k):
        if all(b - a > 1 for a, b in itertools.pairwise(chosen)):
            best = min(best, max(nums[i] for i in chosen))
    return int(best)


HOUSE_ROBBER_IV = ProblemSource(
    title="House Robber IV",
    statement="""
Houses stand in a row with `nums[i]` dollars in house `i`. A robber refuses to rob two **adjacent** houses and must
rob at least `k` houses. The robber's *capability* is the most money taken from any single house robbed.

Return the minimum possible capability. It is guaranteed that robbing `k` non-adjacent houses is possible.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^9`
- `1 <= k <= (nums.length + 1) / 2`
""",
    signature=function("minCapability", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_min_capability,
    brute=_robber_iv_brute,
    brute_input_limit=40,
    examples=[Example([[2, 3, 5, 9], 2], "Rob houses 0 and 2: capability 5."), Example([[2, 7, 9, 3, 1], 2], "Rob houses 0 and 4: capability 2.")],
    edge_cases=[[[5], 1], [[1, 1000000000], 1], [[4, 1, 4], 2]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 9, big=4000), 1, rng.choice([20, 10**9]))), rng.randint(1, (len(v) + 1) // 2)],
    random_count=8,
)


PROBLEMS = [
    MIN_SUM_DIFFERENCE,
    FULL_BLOOM,
    KOKO,
    SEARCH_INSERT,
    FIND_PEAK,
    SEARCH_RANGE,
    KTH_PRODUCT,
    SQRT,
    REACHING_POINTS,
    KTH_MISSING,
    SMALLEST_DIVISOR,
    SEARCH_2D_MATRIX,
    ZERO_ARRAY_II,
    HOUSE_ROBBER_IV,
]
