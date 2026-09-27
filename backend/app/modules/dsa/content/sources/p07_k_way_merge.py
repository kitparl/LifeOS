"""Pattern 7: K-way Merge. Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import heapq
import itertools
from fractions import Fraction

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n
from app.modules.dsa.judge.codec import ListNode

PATTERN_NUMBER = 7

_PRIMES = [p for p in range(2, 3000) if all(p % d for d in range(2, int(p**0.5) + 1))]


# ---------------------------------------------------------------- Merge Sorted Array


def _merge_sorted(nums1: list[int], m: int, nums2: list[int], n: int) -> None:
    i, j, k = m - 1, n - 1, m + n - 1
    while j >= 0:
        if i >= 0 and nums1[i] > nums2[j]:
            nums1[k] = nums1[i]
            i -= 1
        else:
            nums1[k] = nums2[j]
            j -= 1
        k -= 1


def _merge_sorted_brute(nums1: list[int], m: int, nums2: list[int], n: int) -> None:
    nums1[:] = sorted(nums1[:m] + nums2[:n])


def _merge_sorted_gen(rng):
    m, n = pick_n(rng, 0, 12, big=200), pick_n(rng, 0, 12, big=200)
    if m + n == 0:
        m = 1
    a = sorted(ints(rng, m, -10**9, 10**9) if rng.random() < 0.3 else ints(rng, m, -9, 9))
    b = sorted(ints(rng, n, -10**9, 10**9) if rng.random() < 0.3 else ints(rng, n, -9, 9))
    return [a + [0] * n, m, b, n]


MERGE_SORTED_ARRAY = ProblemSource(
    title="Merge Sorted Array",
    statement="""
`nums1` and `nums2` are sorted in non-decreasing order and hold `m` and `n` meaningful values respectively.
`nums1` has length `m + n`: its first `m` positions hold its values and the last `n` positions are
placeholders (zeros).

Merge `nums2` into `nums1` **in place** so that `nums1` holds all `m + n` values in sorted order.
Can you do it in `O(m + n)` time without extra space?
""",
    constraints="""
- `nums1.length == m + n`, `nums2.length == n`
- `0 <= m, n <= 200`, `1 <= m + n <= 200`
- `-10^9 <= nums1[i], nums2[j] <= 10^9`
""",
    signature=function("merge", [("nums1", "int[]"), ("m", "int"), ("nums2", "int[]"), ("n", "int")], "void", mutates="nums1"),
    reference=_merge_sorted,
    brute=_merge_sorted_brute,
    examples=[
        Example([[1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3], "The merged array is 1, 2, 2, 3, 5, 6."),
        Example([[1], 1, [], 0]),
        Example([[0], 0, [1], 1], "nums1 has no values of its own; the result is [1]."),
    ],
    edge_cases=[[[4, 5, 6, 0, 0, 0], 3, [1, 2, 3], 3], [[2, 0], 1, [1], 1], [[-1, 0, 0], 1, [-1, 0], 2]],
    generator=_merge_sorted_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Merge K Sorted Lists


def _merge_k_lists(lists: list[ListNode | None]) -> ListNode | None:
    heap = [(node.val, i, node) for i, node in enumerate(lists) if node]
    heapq.heapify(heap)
    dummy = tail = ListNode()
    counter = itertools.count(len(lists))
    while heap:
        _, _, node = heapq.heappop(heap)
        tail.next = node
        tail = node
        if node.next:
            heapq.heappush(heap, (node.next.val, next(counter), node.next))
    return dummy.next


def _merge_k_brute(lists: list[ListNode | None]) -> ListNode | None:
    values = []
    for node in lists:
        while node:
            values.append(node.val)
            node = node.next
    dummy = tail = ListNode()
    for v in sorted(values):
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


MERGE_K_LISTS = ProblemSource(
    title="Merge K Sorted Lists",
    statement="""
You are given an array of `k` linked lists, each sorted in ascending order (some may be empty). Merge them
into one sorted linked list and return its head.

Lists are given, and the answer is shown, as values from head to tail.
""",
    constraints="""
- `0 <= k <= 10^4`
- each list has between `0` and `500` nodes, and there are at most `10^4` nodes in total
- `-10^4 <= Node.val <= 10^4`
""",
    signature=function("mergeKLists", [("lists", "ListNode[]")], "ListNode"),
    reference=_merge_k_lists,
    brute=_merge_k_brute,
    examples=[
        Example([[[1, 4, 5], [1, 3, 4], [2, 6]]], "All eight values in order: 1, 1, 2, 3, 4, 4, 5, 6."),
        Example([[]], "No lists at all."),
        Example([[[]]], "One empty list."),
    ],
    edge_cases=[[[[1], [0]]], [[[], [1], []]], [[[5, 5], [5]]]],
    generator=lambda rng: [[sorted(ints(rng, pick_n(rng, 0, 8, big=150), -10**4, 10**4)) for _ in range(pick_n(rng, 0, 6, big=40))]],
    random_count=8,
)


# ---------------------------------------------------------------- Kth Smallest Number in M Sorted Lists


def _kth_smallest_lists(lists: list[list[int]], k: int) -> int:
    heap = [(row[0], r, 0) for r, row in enumerate(lists) if row]
    heapq.heapify(heap)
    for _ in range(k - 1):
        _, r, c = heapq.heappop(heap)
        if c + 1 < len(lists[r]):
            heapq.heappush(heap, (lists[r][c + 1], r, c + 1))
    return heap[0][0]


def _kth_lists_gen(rng):
    lists = [sorted(ints(rng, pick_n(rng, 0, 8, big=200), -10**5, 10**5)) for _ in range(pick_n(rng, 1, 5, big=30))]
    if not any(lists):
        lists[0] = [rng.randint(-5, 5)]
    total = sum(map(len, lists))
    return [lists, rng.randint(1, total)]


KTH_SMALLEST_LISTS = ProblemSource(
    title="Kth Smallest Number in M Sorted Lists",
    statement="""
You are given `m` integer arrays, each sorted in non-decreasing order (some may be empty), and an integer
`k`. Considering all values from all arrays together, with duplicates counted separately, return the
`k`-th smallest one.

Try not to merge everything: a min-heap holding one candidate per array needs only `O(k log m)` time.
""",
    constraints="""
- `1 <= m <= 100`
- each array has between `0` and `1000` values, `-10^5 <= value <= 10^5`
- `1 <= k <=` total number of values
""",
    signature=function("kthSmallest", [("lists", "int[][]"), ("k", "int")], "int"),
    reference=_kth_smallest_lists,
    brute=lambda lists, k: sorted(v for row in lists for v in row)[k - 1],
    examples=[
        Example([[[2, 6, 8], [3, 6, 7], [1, 3, 4]], 5], "Merged: 1, 2, 3, 3, 4, 6, 6, 7, 8; the 5th is 4."),
        Example([[[5, 8, 9], [1, 7]], 3], "Merged: 1, 5, 7, 8, 9."),
    ],
    edge_cases=[[[[1]], 1], [[[], [4]], 1], [[[1, 1, 1], [1]], 4], [[[-3, 0], [], [2]], 3]],
    generator=_kth_lists_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find K Pairs with Smallest Sums


def _k_smallest_pairs(nums1: list[int], nums2: list[int], k: int) -> list[list[int]]:
    heap = [(nums1[i] + nums2[0], i, 0) for i in range(min(k, len(nums1)))]
    heapq.heapify(heap)
    out = []
    while heap and len(out) < k:
        _, i, j = heapq.heappop(heap)
        out.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return out


def _k_pairs_brute(nums1: list[int], nums2: list[int], k: int) -> list[list[int]]:
    pairs = sorted(([u, v] for u in nums1 for v in nums2), key=lambda p: p[0] + p[1])
    return pairs[:k]


def _k_pairs_gen(rng):
    a = sorted(ints(rng, pick_n(rng, 1, 8, big=500), -10**4 if rng.random() < 0.3 else -5, 10**4 if rng.random() < 0.3 else 5))
    b = sorted(ints(rng, pick_n(rng, 1, 8, big=500), -10**4 if rng.random() < 0.3 else -5, 10**4 if rng.random() < 0.3 else 5))
    return [a, b, rng.randint(1, min(len(a) * len(b), 1000))]


K_PAIRS = ProblemSource(
    title="Find K Pairs with Smallest Sums",
    statement="""
`nums1` and `nums2` are sorted in non-decreasing order. A pair `[u, v]` takes `u` from `nums1` and `v` from
`nums2` (equal values at different positions form different pairs).

Return the `k` pairs with the smallest sums `u + v`. When several pairs tie for the last places, any of
them may be chosen; the pairs may be listed in any order.
""",
    constraints="""
- `1 <= nums1.length, nums2.length <= 10^5`
- `-10^9 <= nums1[i], nums2[i] <= 10^9`
- both arrays are sorted in non-decreasing order
- `1 <= k <= min(10^4, nums1.length * nums2.length)`
""",
    signature=function("kSmallestPairs", [("nums1", "int[]"), ("nums2", "int[]"), ("k", "int")], "int[][]"),
    reference=_k_smallest_pairs,
    brute=_k_pairs_brute,
    brute_input_limit=500,
    compare="checker",
    checker="k_smallest_pairs",
    examples=[
        Example([[1, 7, 11], [2, 4, 6], 3], "[1,2], [1,4] and [1,6] have sums 3, 5 and 7."),
        Example([[1, 1, 2], [1, 2, 3], 2], "The two smallest sums are both 2: [1,1] twice (different 1s from nums1)."),
    ],
    edge_cases=[[[1], [1], 1], [[1, 2], [3], 2], [[-5, 5], [-5, 5], 4], [[0, 0, 0], [0, 0], 5]],
    generator=_k_pairs_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Kth Smallest Element in a Sorted Matrix


def _kth_smallest_matrix(matrix: list[list[int]], k: int) -> int:
    n = len(matrix)
    lo, hi = matrix[0][0], matrix[-1][-1]
    while lo < hi:
        mid = (lo + hi) // 2
        count, col = 0, n - 1
        for row in range(n):
            while col >= 0 and matrix[row][col] > mid:
                col -= 1
            count += col + 1
        if count < k:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _sorted_matrix_gen(rng):
    n = pick_n(rng, 1, 6, big=60)
    step = rng.choice([2, 50])
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            base = max(matrix[i - 1][j] if i else -10**4, matrix[i][j - 1] if j else -10**4)
            matrix[i][j] = min(10**9, base + rng.randint(0, step))
    return [matrix, rng.randint(1, n * n)]


KTH_SORTED_MATRIX = ProblemSource(
    title="Kth Smallest Element in a Sorted Matrix",
    statement="""
Every row and every column of the `n x n` matrix is sorted in non-decreasing order. Return the `k`-th
smallest value in the matrix, counting duplicates separately (the `k`-th value in the fully sorted list
of all `n^2` values).

Can you beat `O(n^2)` memory?
""",
    constraints="""
- `1 <= n <= 300`
- `-10^9 <= matrix[i][j] <= 10^9`
- rows and columns are sorted in non-decreasing order
- `1 <= k <= n^2`
""",
    signature=function("kthSmallest", [("matrix", "int[][]"), ("k", "int")], "int"),
    reference=_kth_smallest_matrix,
    brute=lambda matrix, k: sorted(v for row in matrix for v in row)[k - 1],
    examples=[
        Example([[[1, 5, 9], [10, 11, 13], [12, 13, 15]], 8], "Sorted values: 1, 5, 9, 10, 11, 12, 13, 13, 15; the 8th is 13."),
        Example([[[-5]], 1]),
    ],
    edge_cases=[[[[1, 2], [1, 3]], 2], [[[1, 1], [1, 1]], 4], [[[-3, -2], [-1, 0]], 1]],
    generator=_sorted_matrix_gen,
    random_count=8,
)


# ---------------------------------------------------------------- K-th Smallest Prime Fraction


def _kth_prime_fraction(arr: list[int], k: int) -> list[int]:
    n = len(arr)
    heap = [(arr[0] / arr[j], 0, j) for j in range(1, n)]
    heapq.heapify(heap)
    for _ in range(k - 1):
        _, i, j = heapq.heappop(heap)
        if i + 1 < j:
            heapq.heappush(heap, (arr[i + 1] / arr[j], i + 1, j))
    _, i, j = heap[0]
    return [arr[i], arr[j]]


def _kth_fraction_brute(arr: list[int], k: int) -> list[int]:
    fractions = sorted((Fraction(arr[i], arr[j]), arr[i], arr[j]) for i in range(len(arr)) for j in range(i + 1, len(arr)))
    _, a, b = fractions[k - 1]
    return [a, b]


def _fraction_gen(rng):
    pool = _PRIMES[: rng.choice([10, 60, 400])]
    arr = [1] + sorted(rng.sample(pool, min(len(pool), pick_n(rng, 1, 8, big=250))))
    n = len(arr)
    return [arr, rng.randint(1, n * (n - 1) // 2)]


KTH_PRIME_FRACTION = ProblemSource(
    title="K-th Smallest Prime Fraction",
    statement="""
`arr` is sorted in increasing order and contains `1` followed by distinct prime numbers. For every pair
of indices `i < j`, consider the fraction `arr[i] / arr[j]`.

Return the `k`-th smallest of these fractions as `[numerator, denominator]`. (All the fractions have
distinct values.)
""",
    constraints="""
- `2 <= arr.length <= 1000`
- `arr[0] == 1`, and every other value is a prime `<= 3 * 10^4`, strictly increasing
- `1 <= k <= arr.length * (arr.length - 1) / 2`
""",
    signature=function("kthSmallestPrimeFraction", [("arr", "int[]"), ("k", "int")], "int[]"),
    reference=_kth_prime_fraction,
    brute=_kth_fraction_brute,
    brute_input_limit=600,
    examples=[
        Example([[1, 2, 3, 5], 3], "Sorted: 1/5, 1/3, 2/5, 1/2, 3/5, 2/3; the 3rd is 2/5."),
        Example([[1, 7], 1]),
    ],
    edge_cases=[[[1, 2], 1], [[1, 2, 3], 3], [[1, 13, 17, 59], 6]],
    generator=_fraction_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Super Ugly Number


def _nth_super_ugly(n: int, primes: list[int]) -> int:
    ugly = [1]
    idx = [0] * len(primes)
    nxt = list(primes)
    while len(ugly) < n:
        value = min(nxt)
        ugly.append(value)
        for i, p in enumerate(primes):
            if nxt[i] == value:
                idx[i] += 1
                nxt[i] = ugly[idx[i]] * p
    return ugly[-1]


def _super_ugly_brute(n: int, primes: list[int]) -> int:
    seen, heap = {1}, [1]
    for _ in range(n - 1):
        value = heapq.heappop(heap)
        for p in primes:
            if value * p not in seen:
                seen.add(value * p)
                heapq.heappush(heap, value * p)
    return heap[0]


def _ugly_gen(rng):
    primes = sorted(rng.sample(_PRIMES[: rng.choice([4, 25])], rng.randint(1, 4)))
    n = rng.randint(1, rng.choice([30, 2000]))
    while _nth_super_ugly(n, primes) >= 2**31:  # keep the answer within a signed 32-bit int
        n //= 2
    return [max(n, 1), primes]


SUPER_UGLY = ProblemSource(
    title="Super Ugly Number",
    statement="""
A *super ugly number* is a positive integer whose prime factors all belong to the array `primes` (the
number `1`, with no prime factors, counts as super ugly).

Given `n` and `primes`, return the `n`-th super ugly number in increasing order. The answer is guaranteed
to fit in a signed 32-bit integer.
""",
    constraints="""
- `1 <= n <= 10^5`
- `1 <= primes.length <= 100`
- `primes` contains distinct primes `<= 1000` in increasing order
""",
    signature=function("nthSuperUglyNumber", [("n", "int"), ("primes", "int[]")], "int"),
    reference=_nth_super_ugly,
    brute=_super_ugly_brute,
    examples=[
        Example([12, [2, 7, 13, 19]], "The sequence starts 1, 2, 4, 7, 8, 13, 14, 16, 19, 26, 28, 32."),
        Example([1, [2, 3, 5]], "The first super ugly number is always 1."),
    ],
    edge_cases=[[5, [2]], [10, [3, 5]], [15, [2, 3, 5]]],
    generator=_ugly_gen,
    random_count=8,
)


PROBLEMS = [
    MERGE_SORTED_ARRAY,
    MERGE_K_LISTS,
    KTH_SMALLEST_LISTS,
    K_PAIRS,
    KTH_SORTED_MATRIX,
    KTH_PRIME_FRACTION,
    SUPER_UGLY,
]
