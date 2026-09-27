"""Pattern 9: Modified Binary Search (part 1 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import bisect
import itertools
import math

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sample, sorted_ints

PATTERN_NUMBER = 9


def _rotate(values: list[int], k: int) -> list[int]:
    return values[k:] + values[:k] if values else values


# ---------------------------------------------------------------- Search in Rotated Sorted Array


def _search_rotated(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        elif nums[mid] < target <= nums[hi]:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def _rotated_distinct_gen(rng):
    n = pick_n(rng, 1, 20, big=4000)
    values = sorted(rng.sample(range(-10**4, 10**4), n))
    nums = _rotate(values, rng.randrange(n))
    target = rng.choice(nums) if rng.random() < 0.6 else rng.randint(-10**4, 10**4)
    return [nums, target]


SEARCH_ROTATED = ProblemSource(
    title="Search in Rotated Sorted Array",
    statement="""
An array of **distinct** integers, originally sorted in ascending order, has been rotated at an unknown
pivot (for example `[0,1,2,4,5,6,7]` might become `[4,5,6,7,0,1,2]`). Given the rotated array `nums` and a
`target`, return the index of `target`, or `-1` if it is not present.

Your algorithm must run in `O(log n)` time.
""",
    constraints="""
- `1 <= nums.length <= 5000`
- `-10^4 <= nums[i], target <= 10^4`
- values are distinct; `nums` is an ascending array rotated at some pivot
""",
    signature=function("search", [("nums", "int[]"), ("target", "int")], "int"),
    reference=_search_rotated,
    brute=lambda nums, target: nums.index(target) if target in nums else -1,
    examples=[Example([[4, 5, 6, 7, 0, 1, 2], 0], "0 is at index 4."), Example([[4, 5, 6, 7, 0, 1, 2], 3]), Example([[1], 0])],
    edge_cases=[[[1], 1], [[3, 1], 1], [[1, 3], 3], [[5, 1, 3], 5], [[2, 3, 4, 5, 1], 1]],
    generator=_rotated_distinct_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Binary Search


def _binary_search(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


BINARY_SEARCH = ProblemSource(
    title="Binary Search",
    statement="""
`nums` is sorted in ascending order and its values are distinct. Return the index of `target` in `nums`, or
`-1` if it is absent. Your solution must run in `O(log n)` time.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-10^4 < nums[i], target < 10^4`
- values are distinct and sorted ascending
""",
    signature=function("search", [("nums", "int[]"), ("target", "int")], "int"),
    reference=_binary_search,
    brute=lambda nums, target: nums.index(target) if target in nums else -1,
    examples=[Example([[-1, 0, 3, 5, 9, 12], 9], "9 is at index 4."), Example([[-1, 0, 3, 5, 9, 12], 2])],
    edge_cases=[[[5], 5], [[5], -5], [[1, 2], 2], [[1, 2], 0]],
    generator=lambda rng: [(v := sorted(rng.sample(range(-9999, 10**4), pick_n(rng, 1, 20, big=4000)))), rng.choice(v) if rng.random() < 0.6 else rng.randint(-9999, 9999)],
    random_count=8,
)


# ---------------------------------------------------------------- First Bad Version (adapted)


def _first_bad(versions: list[bool]) -> int:
    lo, hi = 1, len(versions)
    while lo < hi:
        mid = (lo + hi) // 2
        if versions[mid - 1]:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _versions_gen(rng):
    n = pick_n(rng, 1, 20, big=5000)
    bad = rng.randint(1, n)
    return [[i + 1 >= bad for i in range(n)]]


FIRST_BAD_VERSION = ProblemSource(
    title="First Bad Version",
    statement="""
*Adapted I/O:* the original version of this problem hides the data behind an `isBadVersion(v)` API. Here you
receive the answers of that API directly.

Versions `1..n` of a product were released in order. Once a version is bad, every later version is bad too.
`versions[i]` is `true` when version `i + 1` is bad; at least one version is bad.

Return the number (1-based) of the **first** bad version. Look at as few entries as possible: binary search
needs only `O(log n)` of them.
""",
    constraints="""
- `1 <= n <= 5000`, `versions.length == n`
- `versions` is `false, ..., false, true, ..., true` with at least one `true`
""",
    signature=function("firstBadVersion", [("versions", "bool[]")], "int"),
    reference=_first_bad,
    brute=lambda versions: versions.index(True) + 1,
    is_variant=True,
    examples=[Example([[False, False, False, True, True]], "Version 4 is the first bad one."), Example([[True]])],
    edge_cases=[[[False, True]], [[True, True, True]], [[False] * 9 + [True]]],
    generator=_versions_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find K Closest Elements


def _find_closest(arr: list[int], k: int, x: int) -> list[int]:
    lo, hi = 0, len(arr) - k
    while lo < hi:
        mid = (lo + hi) // 2
        if x - arr[mid] > arr[mid + k] - x:
            lo = mid + 1
        else:
            hi = mid
    return arr[lo : lo + k]


def _closest_gen(rng):
    arr = sorted_ints(rng, pick_n(rng, 1, 20, big=4000), -rng.choice([10, 10**4]), rng.choice([10, 10**4]))
    return [arr, rng.randint(1, len(arr)), rng.randint(-10**4, 10**4) if rng.random() < 0.4 else rng.choice(arr)]


K_CLOSEST_ELEMENTS = ProblemSource(
    title="Find K Closest Elements",
    statement="""
`arr` is sorted in ascending order. Return the `k` values of `arr` closest to `x`, sorted in ascending order.

A value `a` is closer to `x` than `b` if `|a - x| < |b - x|`, or if `|a - x| == |b - x|` and `a < b`.
""",
    constraints="""
- `1 <= k <= arr.length <= 10^4`
- `arr` is sorted ascending
- `-10^4 <= arr[i], x <= 10^4`
""",
    signature=function("findClosestElements", [("arr", "int[]"), ("k", "int"), ("x", "int")], "int[]"),
    reference=_find_closest,
    brute=lambda arr, k, x: sorted(sorted(arr, key=lambda a: (abs(a - x), a))[:k]),
    examples=[Example([[1, 2, 3, 4, 5], 4, 3]), Example([[1, 1, 2, 3, 4, 5], 4, -1], "x is below every value, so take the four smallest.")],
    edge_cases=[[[1], 1, 5], [[1, 3], 1, 2], [[1, 1, 1, 10, 10, 10], 1, 9], [[0, 0, 1, 2, 3, 3, 4, 7, 7, 8], 3, 5]],
    generator=_closest_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Single Element in a Sorted Array


def _single_non_duplicate(nums: list[int]) -> int:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if mid % 2:
            mid -= 1
        if nums[mid] == nums[mid + 1]:
            lo = mid + 2
        else:
            hi = mid
    return nums[lo]


def _single_gen(rng):
    values = sorted(rng.sample(range(0, 10**5), pick_n(rng, 0, 15, big=2000) + 1))
    lone = rng.choice(values)
    return [sorted([v for v in values for _ in range(1 if v == lone else 2)])]


SINGLE_ELEMENT = ProblemSource(
    title="Single Element in a Sorted Array",
    statement="""
In the sorted array `nums`, every value appears exactly twice except one value, which appears once. Return
that value in `O(log n)` time and `O(1)` space.
""",
    constraints="""
- `1 <= nums.length <= 10^5` (always odd)
- `0 <= nums[i] <= 10^5`
""",
    signature=function("singleNonDuplicate", [("nums", "int[]")], "int"),
    reference=_single_non_duplicate,
    brute=lambda nums: next(v for v in set(nums) if nums.count(v) == 1),
    brute_input_limit=400,
    examples=[Example([[1, 1, 2, 3, 3, 4, 4, 8, 8]], "2 appears once."), Example([[3, 3, 7, 7, 10, 11, 11]])],
    edge_cases=[[[1]], [[1, 2, 2]], [[1, 1, 2]], [[0, 0, 1, 1, 2]]],
    generator=_single_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Split Array Largest Sum


def _split_array(nums: list[int], k: int) -> int:
    def pieces(limit: int) -> int:
        count, total = 1, 0
        for x in nums:
            if total + x > limit:
                count, total = count + 1, 0
            total += x
        return count

    lo, hi = max(nums), sum(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if pieces(mid) <= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _split_array_brute(nums: list[int], k: int) -> int:
    best = math.inf
    for cuts in itertools.combinations(range(1, len(nums)), k - 1):
        bounds = (0, *cuts, len(nums))
        best = min(best, max(sum(nums[a:b]) for a, b in itertools.pairwise(bounds)))
    return int(best)


SPLIT_ARRAY_LARGEST = ProblemSource(
    title="Split Array Largest Sum",
    statement="""
Split `nums` into exactly `k` non-empty contiguous parts so that the **largest** sum among the parts is as
small as possible. Return that minimised largest sum.
""",
    constraints="""
- `1 <= nums.length <= 1000`
- `0 <= nums[i] <= 10^6`
- `1 <= k <= min(50, nums.length)`
""",
    signature=function("splitArray", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_split_array,
    brute=_split_array_brute,
    brute_input_limit=45,
    examples=[Example([[7, 2, 5, 10, 8], 2], "[7,2,5] and [10,8] give a largest sum of 18."), Example([[1, 2, 3, 4, 5], 2], "[1,2,3] and [4,5]: 9.")],
    edge_cases=[[[5], 1], [[0, 0], 2], [[1, 4, 4], 3], [[1000000, 1000000], 1]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 9, big=1000), 0, rng.choice([10, 10**6]))), rng.randint(1, min(len(v), 50))],
    random_count=8,
)


# ---------------------------------------------------------------- The K Weakest Rows in a Matrix


def _k_weakest(mat: list[list[int]], k: int) -> list[int]:
    strength = [(bisect.bisect_left([-x for x in row], 0), i) for i, row in enumerate(mat)]
    return [i for _, i in sorted(strength)[:k]]


def _weak_gen(rng):
    m, n = pick_n(rng, 2, 12, big=100), pick_n(rng, 2, 12, big=100)
    mat = [[1] * (s := rng.randint(0, n)) + [0] * (n - s) for _ in range(m)]
    return [mat, rng.randint(1, m)]


K_WEAKEST_ROWS = ProblemSource(
    title="The K Weakest Rows in a Matrix",
    statement="""
Each row of the binary matrix `mat` has all its `1`s (soldiers) before all its `0`s (civilians). Row `i` is
weaker than row `j` if it has fewer soldiers, or the same number of soldiers and `i < j`.

Return the indices of the `k` weakest rows, from weakest to strongest.
""",
    constraints="""
- `2 <= m, n <= 100`
- `1 <= k <= m`
- each row is some 1s followed by some 0s
""",
    signature=function("kWeakestRows", [("mat", "int[][]"), ("k", "int")], "int[]"),
    reference=_k_weakest,
    brute=lambda mat, k: sorted(range(len(mat)), key=lambda i: (sum(mat[i]), i))[:k],
    examples=[
        Example([[[1, 1, 0, 0, 0], [1, 1, 1, 1, 0], [1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [1, 1, 1, 1, 1]], 3], "Soldier counts 2, 4, 1, 2, 5; weakest are rows 2, 0, 3."),
        Example([[[1, 0, 0, 0], [1, 1, 1, 1], [1, 0, 0, 0], [1, 0, 0, 0]], 2]),
    ],
    edge_cases=[[[[0, 0], [0, 0]], 2], [[[1, 1], [1, 0]], 1]],
    generator=_weak_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Value at a Given Index in a Bounded Array


def _max_value(n: int, index: int, maxSum: int) -> int:
    def needed(peak: int) -> int:
        def side(length: int) -> int:
            if peak - 1 >= length:
                return (peak - 1 + peak - length) * length // 2
            return (peak - 1) * peak // 2 + (length - (peak - 1))

        return peak + side(index) + side(n - index - 1)

    lo, hi = 1, maxSum
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if needed(mid) <= maxSum:
            lo = mid
        else:
            hi = mid - 1
    return lo


def _max_value_brute(n: int, index: int, maxSum: int) -> int:
    peak = 1
    while sum(max(peak + 1 - abs(i - index), 1) for i in range(n)) <= maxSum:
        peak += 1
    return peak


def _bounded_gen(rng):
    n = rng.randint(1, rng.choice([8, 10**9]))
    return [n, rng.randint(0, n - 1), rng.randint(n, n + rng.choice([20, 10**9]))]


BOUNDED_ARRAY = ProblemSource(
    title="Maximum Value at a Given Index in a Bounded Array",
    statement="""
Build an array `nums` of length `n` of **positive** integers where neighbouring values differ by at most 1
(`|nums[i] - nums[i+1]| <= 1`) and the total of all values is at most `maxSum`.

Return the largest possible value of `nums[index]`.
""",
    constraints="""
- `1 <= n <= maxSum <= 10^9`
- `0 <= index < n`
""",
    signature=function("maxValue", [("n", "int"), ("index", "int"), ("maxSum", "int")], "int"),
    reference=_max_value,
    brute=lambda n, index, maxSum: _max_value_brute(n, index, maxSum) if n <= 50 and maxSum <= 500 else NotImplemented,
    examples=[Example([4, 2, 6], "nums = [1, 2, 2, 1] gives nums[2] = 2."), Example([6, 1, 10], "nums = [2, 3, 2, 1, 1, 1].")],
    edge_cases=[[1, 0, 1], [1, 0, 1000000000], [3, 2, 18], [1000000000, 0, 1000000000], [5, 0, 28]],
    generator=_bounded_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Search in Rotated Sorted Array II


def _search_rotated_ii(nums: list[int], target: int) -> bool:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return True
        if nums[lo] == nums[mid] == nums[hi]:
            lo, hi = lo + 1, hi - 1
        elif nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        elif nums[mid] < target <= nums[hi]:
            lo = mid + 1
        else:
            hi = mid - 1
    return False


def _rotated_dup_gen(rng):
    values = sorted_ints(rng, pick_n(rng, 1, 20, big=4000), -10**4, rng.choice([-9990, 10**4]))
    nums = _rotate(values, rng.randrange(len(values)))
    return [nums, rng.choice(nums) if rng.random() < 0.5 else rng.randint(-10**4, 10**4)]


SEARCH_ROTATED_II = ProblemSource(
    title="Search in Rotated Sorted Array II",
    statement="""
An array sorted in non-decreasing order (duplicates allowed) has been rotated at an unknown pivot. Return
`true` if `target` occurs in the rotated array `nums`.

Try to keep the running time as low as possible. How do duplicates affect the worst case?
""",
    constraints="""
- `1 <= nums.length <= 5000`
- `-10^4 <= nums[i], target <= 10^4`
- `nums` is a non-decreasing array rotated at some pivot
""",
    signature=function("search", [("nums", "int[]"), ("target", "int")], "bool"),
    reference=_search_rotated_ii,
    brute=lambda nums, target: target in nums,
    examples=[Example([[2, 5, 6, 0, 0, 1, 2], 0]), Example([[2, 5, 6, 0, 0, 1, 2], 3])],
    edge_cases=[[[1], 1], [[1, 0, 1, 1, 1], 0], [[1, 1, 1, 1, 1, 1, 1, 1, 1, 13, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 13], [[3, 1], 1]],
    generator=_rotated_dup_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Count Pairs Whose Sum is Less than Target


def _count_pairs(nums: list[int], target: int) -> int:
    nums = sorted(nums)
    lo, hi, count = 0, len(nums) - 1, 0
    while lo < hi:
        if nums[lo] + nums[hi] < target:
            count += hi - lo
            lo += 1
        else:
            hi -= 1
    return count


COUNT_PAIRS_LESS = ProblemSource(
    title="Count Pairs Whose Sum is Less than Target",
    statement="""
Given an integer array `nums` and an integer `target`, return the number of index pairs `(i, j)` with
`0 <= i < j < n` and `nums[i] + nums[j] < target`.
""",
    constraints="""
- `1 <= nums.length <= 50`
- `-50 <= nums[i], target <= 50`
""",
    signature=function("countPairs", [("nums", "int[]"), ("target", "int")], "int"),
    reference=_count_pairs,
    brute=lambda nums, target: sum(a + b < target for a, b in itertools.combinations(nums, 2)),
    examples=[Example([[-1, 1, 2, 3, 1], 2], "The pairs (0,1), (0,2) and (0,4) sum to less than 2."), Example([[-6, 2, 5, -2, -7, -1, 3], -2])],
    edge_cases=[[[1], 5], [[1, 1], 2], [[1, 1], 3], [[-50, -50], -50]],
    generator=lambda rng: [ints(rng, rng.randint(1, 50), -50, 50), rng.randint(-50, 50)],
    random_count=8,
)


# ---------------------------------------------------------------- Find Minimum in Rotated Sorted Array II


def _find_min_ii(nums: list[int]) -> int:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        elif nums[mid] < nums[hi]:
            hi = mid
        else:
            hi -= 1
    return nums[lo]


FIND_MIN_ROTATED_II = ProblemSource(
    title="Find Minimum in Rotated Sorted Array II",
    statement="""
An array sorted in non-decreasing order (duplicates allowed) has been rotated between 1 and `n` times.
Return its minimum value, doing as little work as possible.
""",
    constraints="""
- `1 <= nums.length <= 5000`
- `-5000 <= nums[i] <= 5000`
- `nums` is a non-decreasing array rotated at some pivot
""",
    signature=function("findMin", [("nums", "int[]")], "int"),
    reference=_find_min_ii,
    brute=min,
    examples=[Example([[1, 3, 5]]), Example([[2, 2, 2, 0, 1]])],
    edge_cases=[[[1]], [[3, 1, 3]], [[10, 1, 10, 10, 10]], [[1, 1]]],
    generator=lambda rng: [_rotate(sorted_ints(rng, (n := pick_n(rng, 1, 20, big=4000)), -5000, rng.choice([-4995, 5000])), rng.randrange(n))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Running Time of N Computers


def _max_run_time(n: int, batteries: list[int]) -> int:
    lo, hi = 0, sum(batteries) // n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if sum(min(b, mid) for b in batteries) >= n * mid:
            lo = mid
        else:
            hi = mid - 1
    return lo


def _max_run_time_brute(n: int, batteries: list[int]) -> int:
    batteries = sorted(batteries)
    total = sum(batteries)
    while batteries[-1] > total // n:
        n -= 1
        total -= batteries.pop()
    return total // n


def _computers_gen(rng):
    batteries = ints(rng, pick_n(rng, 1, 15, big=4000), 1, rng.choice([10, 10**9]))
    return [rng.randint(1, len(batteries)), batteries]


MAX_RUNNING_TIME = ProblemSource(
    title="Maximum Running Time of N Computers",
    statement="""
You have `n` computers and batteries where battery `i` can power a computer for `batteries[i]` minutes. At
the start you put one battery in each of the `n` computers. At any whole minute you may swap batteries
between computers or swap in unused batteries; swapping takes no time. Batteries can't be recharged.

Return the maximum number of minutes all `n` computers can run **simultaneously**.
""",
    constraints="""
- `1 <= n <= batteries.length <= 10^5`
- `1 <= batteries[i] <= 10^9`
""",
    signature=function("maxRunTime", [("n", "int"), ("batteries", "int[]")], "long"),
    reference=_max_run_time,
    brute=_max_run_time_brute,
    examples=[Example([2, [3, 3, 3]], "Rotate the three batteries between two computers for 4 minutes."), Example([2, [1, 1, 1, 1]])],
    edge_cases=[[1, [5]], [1, [1, 2, 3]], [3, [10, 10, 3, 5]], [2, [1000000000, 1]]],
    generator=_computers_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimize Max Distance to Gas Station


def _minmax_gas(stations: list[int], k: int) -> float:
    gaps = [b - a for a, b in itertools.pairwise(stations)]
    lo, hi = 0.0, float(max(gaps))
    for _ in range(100):
        mid = (lo + hi) / 2
        if sum(math.ceil(g / mid) - 1 for g in gaps) <= k:
            hi = mid
        else:
            lo = mid
    return hi


def _minmax_gas_brute(stations: list[int], k: int) -> float:
    gaps = [b - a for a, b in itertools.pairwise(stations)]
    parts = [1] * len(gaps)
    for _ in range(k):
        i = max(range(len(gaps)), key=lambda j: gaps[j] / parts[j])
        parts[i] += 1
    return max(g / p for g, p in zip(gaps, parts, strict=True))


def _gas_gen(rng):
    stations = sorted(sample(rng, range(0, rng.choice([100, 10**8])), pick_n(rng, 2, 10, big=1500)))
    return [stations, rng.randint(1, rng.choice([20, 10**6]))]


MINMAX_GAS_STATION = ProblemSource(
    title="Minimize Max Distance to Gas Station",
    statement="""
Gas stations stand at the strictly increasing positions `stations` on a line. You must add exactly `k` new
stations, anywhere (not necessarily at integer positions).

Let `penalty` be the largest distance between two adjacent stations afterwards. Return the smallest
possible `penalty`. Answers within `10^-5` are accepted.
""",
    constraints="""
- `2 <= stations.length <= 2000`
- `0 <= stations[i] <= 10^8`, strictly increasing
- `1 <= k <= 10^6`
""",
    signature=function("minmaxGasDist", [("stations", "int[]"), ("k", "int")], "double"),
    reference=_minmax_gas,
    brute=lambda stations, k: _minmax_gas_brute(stations, k) if k <= 2000 else NotImplemented,
    compare="float_tolerance",
    examples=[Example([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 9], "Put one station in the middle of each gap: 0.5."), Example([[23, 24, 36, 39, 46, 56, 57, 65, 84, 98], 1], "Split the 84-98 gap: 14.")],
    edge_cases=[[[0, 100], 1], [[0, 1], 1000000], [[0, 3, 4], 2]],
    generator=_gas_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Divide Chocolate


def _max_sweetness(sweetness: list[int], k: int) -> int:
    def pieces(minimum: int) -> int:
        count = total = 0
        for s in sweetness:
            total += s
            if total >= minimum:
                count, total = count + 1, 0
        return count

    lo, hi = min(sweetness), sum(sweetness) // (k + 1)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if pieces(mid) >= k + 1:
            lo = mid
        else:
            hi = mid - 1
    return lo


def _sweetness_brute(sweetness: list[int], k: int) -> int:
    best = 0
    for cuts in itertools.combinations(range(1, len(sweetness)), k):
        bounds = (0, *cuts, len(sweetness))
        best = max(best, min(sum(sweetness[a:b]) for a, b in itertools.pairwise(bounds)))
    return best


DIVIDE_CHOCOLATE = ProblemSource(
    title="Divide Chocolate",
    statement="""
A chocolate bar is made of chunks with sweetness values `sweetness`. You will make `k` cuts to split it into
`k + 1` pieces of consecutive chunks, give the pieces to `k` friends and keep the **least sweet** piece for
yourself (a piece's sweetness is the sum of its chunks).

Cut optimally and return the maximum sweetness of the piece you keep.
""",
    constraints="""
- `0 <= k < sweetness.length <= 10^4`
- `1 <= sweetness[i] <= 10^5`
""",
    signature=function("maximizeSweetness", [("sweetness", "int[]"), ("k", "int")], "int"),
    reference=_max_sweetness,
    brute=_sweetness_brute,
    brute_input_limit=45,
    examples=[Example([[1, 2, 3, 4, 5, 6, 7, 8, 9], 5], "Pieces [1,2,3], [4,5], [6], [7], [8], [9]: you keep 6."), Example([[5, 6, 7, 8, 9, 1, 2, 3, 4], 8])],
    edge_cases=[[[5], 0], [[1, 2, 2, 1, 2, 2, 1, 2, 2], 2], [[3, 3], 1]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 9, big=4000), 1, rng.choice([9, 10**5]))), rng.randint(0, len(v) - 1)],
    random_count=8,
)


PROBLEMS = [
    SEARCH_ROTATED,
    BINARY_SEARCH,
    FIRST_BAD_VERSION,
    K_CLOSEST_ELEMENTS,
    SINGLE_ELEMENT,
    SPLIT_ARRAY_LARGEST,
    K_WEAKEST_ROWS,
    BOUNDED_ARRAY,
    SEARCH_ROTATED_II,
    COUNT_PAIRS_LESS,
    FIND_MIN_ROTATED_II,
    MAX_RUNNING_TIME,
    MINMAX_GAS_STATION,
    DIVIDE_CHOCOLATE,
]
