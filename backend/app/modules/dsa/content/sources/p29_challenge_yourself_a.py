"""Pattern 29: Challenge Yourself (part 1 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import bisect
import itertools
import math
import random
from collections import deque
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, random_tree, sample, word
from app.modules.dsa.content.sources.p20_tree_dfs_a import _all_nodes
from app.modules.dsa.judge.codec import ListNode, TreeNode, tree_from_json, tree_to_json

PATTERN_NUMBER = 29


def _grid_neighbours(m: int, n: int, i: int, j: int):
    for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
        if 0 <= a < m and 0 <= b < n:
            yield a, b


# ---------------------------------------------------------------- Number of Connected Components in an Undirected Graph


def _count_components(n: int, edges: list[list[int]]) -> int:
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    components = n
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            components -= 1
    return components


def _components_brute(n: int, edges: list[list[int]]) -> int:
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    seen, count = set(), 0
    for s in range(n):
        if s not in seen:
            count += 1
            stack = [s]
            seen.add(s)
            while stack:
                for w in adjacent[stack.pop()]:
                    if w not in seen:
                        seen.add(w)
                        stack.append(w)
    return count


CONNECTED_COMPONENTS = ProblemSource(
    title="Number of Connected Components in an Undirected Graph",
    statement="""
An undirected graph has `n` nodes labelled `0` to `n - 1` and the edges in `edges`. Return the number of connected components.
""",
    constraints="""
- `1 <= n <= 2000`, `0 <= edges.length <= 5000`
- no self-loops or repeated edges
""",
    signature=function("countComponents", [("n", "int"), ("edges", "int[][]")], "int"),
    reference=_count_components,
    brute=_components_brute,
    examples=[Example([5, [[0, 1], [1, 2], [3, 4]]]), Example([5, [[0, 1], [1, 2], [2, 3], [3, 4]]])],
    edge_cases=[[1, []], [3, []], [2, [[0, 1]]]],
    generator=lambda rng: [(n := pick_n(rng, 1, 12, big=2000)), [sorted(e) for e in {tuple(sorted(sample(rng, range(n), 2))) for _ in range(rng.randint(0, n))}] if n >= 2 else []],
    random_count=8,
)


# ---------------------------------------------------------------- Pacific Atlantic Water Flow


def _pacific_atlantic(heights: list[list[int]]) -> list[list[int]]:
    m, n = len(heights), len(heights[0])

    def reachable(starts: list[tuple[int, int]]) -> set[tuple[int, int]]:
        seen, queue = set(starts), deque(starts)
        while queue:  # walk uphill from the ocean
            i, j = queue.popleft()
            for a, b in _grid_neighbours(m, n, i, j):
                if (a, b) not in seen and heights[a][b] >= heights[i][j]:
                    seen.add((a, b))
                    queue.append((a, b))
        return seen

    pacific = reachable([(0, j) for j in range(n)] + [(i, 0) for i in range(m)])
    atlantic = reachable([(m - 1, j) for j in range(n)] + [(i, n - 1) for i in range(m)])
    return [list(c) for c in sorted(pacific & atlantic)]


def _pacific_brute(heights: list[list[int]]) -> list[list[int]]:
    m, n = len(heights), len(heights[0])
    out = []
    for i in range(m):
        for j in range(n):
            seen, stack = {(i, j)}, [(i, j)]
            pac = atl = False
            while stack:  # flow downhill from the cell
                a, b = stack.pop()
                pac |= a == 0 or b == 0
                atl |= a == m - 1 or b == n - 1
                for c in _grid_neighbours(m, n, a, b):
                    if c not in seen and heights[c[0]][c[1]] <= heights[a][b]:
                        seen.add(c)
                        stack.append(c)
            if pac and atl:
                out.append([i, j])
    return out


PACIFIC_ATLANTIC = ProblemSource(
    title="Pacific Atlantic Water Flow",
    statement="""
`heights` is an island map; the Pacific Ocean touches its top and left edges and the Atlantic its bottom and right edges. Rain water flows from a
cell to a side-adjacent cell whose height is less than or equal, and from edge cells into the adjacent ocean. Return the coordinates
`[r, c]` of every cell from which water can reach **both** oceans, in any order.
""",
    constraints="""
- `1 <= m, n <= 200`
- `0 <= heights[r][c] <= 10^5`
""",
    signature=function("pacificAtlantic", [("heights", "int[][]")], "int[][]"),
    reference=_pacific_atlantic,
    brute=_pacific_brute,
    brute_input_limit=1500,
    compare="unordered",
    examples=[Example([[[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]]]), Example([[[1]]], "A single cell touches both oceans.")],
    edge_cases=[[[[1, 2], [4, 3]]], [[[5, 5, 5]]]],
    generator=lambda rng: [[[rng.randint(0, hi) for _ in range(n)] for _ in range(m)] for m, n, hi in [(pick_n(rng, 1, 7, big=60), pick_n(rng, 1, 7, big=60), rng.choice([3, 10, 10**5]))]],
    random_count=8,
)


# ---------------------------------------------------------------- Contains Duplicate


def _contains_duplicate(nums: list[int]) -> bool:
    return len(set(nums)) < len(nums)


CONTAINS_DUPLICATE = ProblemSource(
    title="Contains Duplicate",
    statement="""
Return `true` if some value appears at least twice in `nums`, and `false` if every element is distinct.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `-10^9 <= nums[i] <= 10^9`
""",
    signature=function("containsDuplicate", [("nums", "int[]")], "bool"),
    reference=_contains_duplicate,
    brute=lambda nums: any(a == b for a, b in itertools.pairwise(sorted(nums))),
    examples=[Example([[1, 2, 3, 1]]), Example([[1, 2, 3, 4]]), Example([[1, 1, 1, 3, 3, 4, 3, 2, 4, 2]])],
    edge_cases=[[[1]], [[-1000000000, 1000000000]], [[0, 0]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 2, 15, big=5000), -(hi := rng.choice([5, 30])), hi) if rng.random() < 0.5 else sample(rng, range(-(10**9), 10**9), pick_n(rng, 1, 15, big=5000))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Subarray


def _max_sub_array(nums: list[int]) -> int:
    best = current = nums[0]
    for x in nums[1:]:
        current = max(x, current + x)
        best = max(best, current)
    return best


MAXIMUM_SUBARRAY = ProblemSource(
    title="Maximum Subarray",
    statement="""
Return the largest sum of a non-empty contiguous subarray of `nums`.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
""",
    signature=function("maxSubArray", [("nums", "int[]")], "int"),
    reference=_max_sub_array,
    brute=lambda nums: max(sum(nums[i:j]) for i in range(len(nums)) for j in range(i + 1, len(nums) + 1)) if len(nums) <= 150 else NotImplemented,
    examples=[Example([[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "[4,-1,2,1] sums to 6."), Example([[1]]), Example([[5, 4, -1, 7, 8]])],
    edge_cases=[[[-3]], [[-2, -1]], [[0, 0, 0]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=10**4), -(10**4), 10**4)],
    random_count=8,
)


# ---------------------------------------------------------------- Two Sum


def _two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    raise ValueError("no solution")


def _two_sum_gen(rng: random.Random) -> list:
    """A unique pair sums to target: all other values are spread so no second pair can match."""
    n = pick_n(rng, 2, 12, big=5000)
    values = sample(rng, range(1, 10**6), n)
    values = [4 * v for v in values]  # multiples of 4 ...
    i, j = sample(rng, range(n), 2)
    values[j] = values[j] + 1  # ... except one value that is 1 mod 4, so only pairs using it can hit an odd target
    values[i] = values[i] + 2  # and one 2 mod 4: the only pair summing to 3 mod 4
    return [values, values[i] + values[j]]


TWO_SUM = ProblemSource(
    title="Two Sum",
    statement="""
Return the indices of the two numbers in `nums` that add up to `target`. Exactly one valid pair exists, and you may not use the same element
twice. The two indices may be returned in any order.
""",
    constraints="""
- `2 <= nums.length <= 10^4`
- `-10^9 <= nums[i], target <= 10^9`; exactly one solution
""",
    signature=function("twoSum", [("nums", "int[]"), ("target", "int")], "int[]"),
    reference=_two_sum,
    brute=lambda nums, target: next([i, j] for i, j in itertools.combinations(range(len(nums)), 2) if nums[i] + nums[j] == target) if len(nums) <= 300 else NotImplemented,
    compare="unordered",
    examples=[Example([[2, 7, 11, 15], 9]), Example([[3, 2, 4], 6]), Example([[3, 3], 6])],
    edge_cases=[[[-1000000000, 1000000000], 0], [[0, 4, 3, 0], 0]],
    generator=_two_sum_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find Minimum in Rotated Sorted Array


def _find_min(nums: list[int]) -> int:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]


def _rotated_gen(rng: random.Random) -> list:
    values = sorted(sample(rng, range(-5000, 5001), pick_n(rng, 1, 15, big=5000)))
    k = rng.randrange(len(values))
    return [values[k:] + values[:k]]


FIND_MIN_ROTATED = ProblemSource(
    title="Find Minimum in Rotated Sorted Array",
    statement="""
An array of distinct integers sorted in ascending order was rotated between 1 and `n` times (rotating `[a0, ..., a(n-1)]` once gives
`[a(n-1), a0, ..., a(n-2)]`). Return its minimum element in `O(log n)` time.
""",
    constraints="""
- `1 <= n <= 5000`
- `-5000 <= nums[i] <= 5000`, all distinct
""",
    signature=function("findMin", [("nums", "int[]")], "int"),
    reference=_find_min,
    brute=lambda nums: min(nums),
    examples=[Example([[3, 4, 5, 1, 2]]), Example([[4, 5, 6, 7, 0, 1, 2]]), Example([[11, 13, 15, 17]], "Rotated n times: back to sorted order.")],
    edge_cases=[[[1]], [[2, 1]], [[1, 2]]],
    generator=_rotated_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Non-overlapping Intervals


def _erase_overlap_intervals(intervals: list[list[int]]) -> int:
    kept_end, kept = -math.inf, 0
    for start, end in sorted(intervals, key=lambda iv: iv[1]):
        if start >= kept_end:
            kept += 1
            kept_end = end
    return len(intervals) - kept


def _overlap_brute(intervals: list[list[int]]) -> int:
    n = len(intervals)
    if n > 14:
        return NotImplemented
    for keep in range(n, -1, -1):
        for combo in itertools.combinations(sorted(intervals), keep):
            if all(a[1] <= b[0] for a, b in itertools.pairwise(combo)):
                return n - keep
    return n


NON_OVERLAPPING = ProblemSource(
    title="Non-overlapping Intervals",
    statement="""
Return the minimum number of intervals to remove from `intervals` so that the rest don't overlap. Intervals that only touch at a point (like
`[1, 2]` and `[2, 3]`) do not overlap.
""",
    constraints="""
- `1 <= intervals.length <= 10^5`
- `-5 * 10^4 <= start < end <= 5 * 10^4`
""",
    signature=function("eraseOverlapIntervals", [("intervals", "int[][]")], "int"),
    reference=_erase_overlap_intervals,
    brute=_overlap_brute,
    examples=[Example([[[1, 2], [2, 3], [3, 4], [1, 3]]], "Remove [1,3]."), Example([[[1, 2], [1, 2], [1, 2]]]), Example([[[1, 2], [2, 3]]])],
    edge_cases=[[[[0, 1]]], [[[1, 100], [11, 22], [1, 11], [2, 12]]]],
    generator=lambda rng: [[[s, s + rng.randint(1, rng.choice([3, 10]))] for s in (rng.randint(0, rng.choice([10, 40])) for _ in range(pick_n(rng, 1, 12, big=3000)))]],
    random_count=8,
)


# ---------------------------------------------------------------- Meeting Rooms


def _can_attend_meetings(intervals: list[list[int]]) -> bool:
    ordered = sorted(intervals)
    return all(a[1] <= b[0] for a, b in itertools.pairwise(ordered))


MEETING_ROOMS = ProblemSource(
    title="Meeting Rooms",
    statement="""
`intervals[i] = [start, end]` is a meeting. Return `true` if one person can attend all meetings (no two overlap; a meeting may start exactly when
another ends).
""",
    constraints="""
- `0 <= intervals.length <= 10^4`
- `0 <= start < end <= 10^6`
""",
    signature=function("canAttendMeetings", [("intervals", "int[][]")], "bool"),
    reference=_can_attend_meetings,
    brute=lambda intervals: all(a[1] <= b[0] or b[1] <= a[0] for a, b in itertools.combinations(intervals, 2)) if len(intervals) <= 300 else NotImplemented,
    examples=[Example([[[0, 30], [5, 10], [15, 20]]]), Example([[[7, 10], [2, 4]]]), Example([[]])],
    edge_cases=[[[[1, 2], [2, 3]]], [[[1, 5], [4, 6]]]],
    generator=lambda rng: [[[s, s + rng.randint(1, 5)] for s in sample(rng, range(0, rng.choice([30, 200])), rng.randint(0, 8))]],
    random_count=8,
)


# ---------------------------------------------------------------- Subtree of Another Tree


def _is_subtree(root: TreeNode | None, subRoot: TreeNode | None) -> bool:
    def same(a: TreeNode | None, b: TreeNode | None) -> bool:
        if a is None or b is None:
            return a is b
        return a.val == b.val and same(a.left, b.left) and same(a.right, b.right)

    return any(same(node, subRoot) for node in _all_nodes(root))


def _subtree_brute(root: TreeNode | None, subRoot: TreeNode | None) -> bool:
    def serial(node: TreeNode | None) -> str:
        return "#" if node is None else f"({node.val},{serial(node.left)},{serial(node.right)})"

    return serial(subRoot) in serial(root)


def _subtree_gen(rng: random.Random) -> list:
    tree = random_tree(rng, pick_n(rng, 1, 15, big=2000), 0, rng.choice([2, 10**4]))
    root = tree_from_json(tree)
    sub = tree_to_json(rng.choice(_all_nodes(root)))
    if rng.random() < 0.4 and len(sub) > 0:
        sub = random_tree(rng, rng.randint(1, 4), 0, 2)
    return [tree, sub]


SUBTREE = ProblemSource(
    title="Subtree of Another Tree",
    statement="""
Return `true` if `root` contains a subtree identical to `subRoot` in structure and node values. A subtree consists of some node and **all** of its
descendants.
""",
    constraints="""
- `1 <= nodes in root <= 2000`, `1 <= nodes in subRoot <= 1000`
- `-10^4 <= Node.val <= 10^4`
""",
    signature=function("isSubtree", [("root", "TreeNode"), ("subRoot", "TreeNode")], "bool"),
    reference=_is_subtree,
    brute=_subtree_brute,
    examples=[Example([[3, 4, 5, 1, 2], [4, 1, 2]]), Example([[3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]], "4's subtree also contains 0.")],
    edge_cases=[[[1], [1]], [[1, 1], [1]], [[12], [2]]],
    generator=_subtree_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Number of 1 Bits


def _hamming_weight(n: int) -> int:
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


ONE_BITS = ProblemSource(
    title="Number of 1 Bits",
    statement="""
Return the number of `1` bits in the binary representation of the positive integer `n`.
""",
    constraints="""
- `1 <= n <= 2^31 - 1`
""",
    signature=function("hammingWeight", [("n", "int")], "int"),
    reference=_hamming_weight,
    brute=lambda n: bin(n).count("1"),
    examples=[Example([11], "1011."), Example([128]), Example([2147483645])],
    edge_cases=[[1], [2147483647]],
    generator=lambda rng: [rng.randint(1, 2**31 - 1)],
    random_count=8,
)


# ---------------------------------------------------------------- Container with Most Water


def _max_area(height: list[int]) -> int:
    i, j, best = 0, len(height) - 1, 0
    while i < j:
        best = max(best, (j - i) * min(height[i], height[j]))
        if height[i] < height[j]:
            i += 1
        else:
            j -= 1
    return best


CONTAINER_WATER = ProblemSource(
    title="Container with Most Water",
    statement="""
`height[i]` is the height of a vertical line at `x = i`. Choose two lines that, together with the x-axis, hold the most water, and return that
amount (width times the shorter height).
""",
    constraints="""
- `2 <= height.length <= 10^5`
- `0 <= height[i] <= 10^4`
""",
    signature=function("maxArea", [("height", "int[]")], "int"),
    reference=_max_area,
    brute=lambda height: max((j - i) * min(height[i], height[j]) for i, j in itertools.combinations(range(len(height)), 2)) if len(height) <= 300 else NotImplemented,
    examples=[Example([[1, 8, 6, 2, 5, 4, 8, 3, 7]], "Lines at 1 and 8: 7 * 7 = 49."), Example([[1, 1]])],
    edge_cases=[[[0, 0]], [[10000, 10000]], [[1, 2, 4, 3]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 2, 25, big=10**4), 0, rng.choice([10, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Product of Array Except Self


def _product_except_self(nums: list[int]) -> list[int]:
    out = [1] * len(nums)
    left = 1
    for i, x in enumerate(nums):
        out[i] = left
        left *= x
    right = 1
    for i in range(len(nums) - 1, -1, -1):
        out[i] *= right
        right *= nums[i]
    return out


PRODUCT_EXCEPT_SELF = ProblemSource(
    title="Product of Array Except Self",
    statement="""
Return `answer` where `answer[i]` is the product of every element of `nums` except `nums[i]`. Don't use division, and run in `O(n)` time. The
products fit in a signed 32-bit integer.
""",
    constraints="""
- `2 <= nums.length <= 10^5`
- `-30 <= nums[i] <= 30`
""",
    signature=function("productExceptSelf", [("nums", "int[]")], "int[]"),
    reference=_product_except_self,
    brute=lambda nums: [math.prod(nums[:i] + nums[i + 1 :]) for i in range(len(nums))] if len(nums) <= 300 else NotImplemented,
    examples=[Example([[1, 2, 3, 4]]), Example([[-1, 1, 0, -3, 3]], "Only the 0's position gets a non-zero product.")],
    edge_cases=[[[0, 0]], [[5, -2]], [[0, 4, 0]]],
    generator=lambda rng: [[rng.choice([-2, -1, 0, 1, 1, 2, 3]) for _ in range(pick_n(rng, 2, 15, big=5000))] if rng.random() < 0.7 else ints(rng, rng.randint(2, 5), -30, 30)],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Increasing Subsequence


def _length_of_lis(nums: list[int]) -> int:
    tails: list[int] = []
    for x in nums:
        i = bisect.bisect_left(tails, x)
        tails[i : i + 1] = [x]
    return len(tails)


def _lis_brute(nums: list[int]) -> int:
    best = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                best[i] = max(best[i], best[j] + 1)
    return max(best)


LIS = ProblemSource(
    title="Longest Increasing Subsequence",
    statement="""
Return the length of the longest **strictly** increasing subsequence of `nums`. Aim for `O(n log n)`.
""",
    constraints="""
- `1 <= nums.length <= 2500`
- `-10^4 <= nums[i] <= 10^4`
""",
    signature=function("lengthOfLIS", [("nums", "int[]")], "int"),
    reference=_length_of_lis,
    brute=_lis_brute,
    brute_input_limit=6000,
    examples=[Example([[10, 9, 2, 5, 3, 7, 101, 18]], "[2,3,7,101]."), Example([[0, 1, 0, 3, 2, 3]]), Example([[7, 7, 7, 7]])],
    edge_cases=[[[1]], [[3, 2, 1]], [[1, 2, 3, 4, 5]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=2500), -(hi := rng.choice([5, 10**4])), hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Sum of Two Integers


def _get_sum(a: int, b: int) -> int:
    mask = 0xFFFFFFFF
    while b & mask:  # carry propagation in 32-bit two's complement
        a, b = a ^ b, (a & b) << 1
    a &= mask
    return a if a <= 0x7FFFFFFF else ~(a ^ mask)


SUM_TWO_INTEGERS = ProblemSource(
    title="Sum of Two Integers",
    statement="""
Return `a + b` without using the `+` or `-` operators.
""",
    constraints="""
- `-1000 <= a, b <= 1000`
""",
    signature=function("getSum", [("a", "int"), ("b", "int")], "int"),
    reference=_get_sum,
    brute=lambda a, b: a + b,
    examples=[Example([1, 2]), Example([2, 3]), Example([-7, 3])],
    edge_cases=[[0, 0], [-1000, -1000], [1000, -1000], [-1, 1]],
    generator=lambda rng: [rng.randint(-1000, 1000), rng.randint(-1000, 1000)],
    random_count=8,
)


# ---------------------------------------------------------------- Unique Paths


def _unique_paths(m: int, n: int) -> int:
    return math.comb(m + n - 2, m - 1)


def _unique_paths_brute(m: int, n: int) -> int:
    row = [1] * n
    for _ in range(m - 1):
        for j in range(1, n):
            row[j] += row[j - 1]
    return row[-1]


UNIQUE_PATHS = ProblemSource(
    title="Unique Paths",
    statement="""
A robot at the top-left of an `m x n` grid moves only right or down. Return the number of distinct paths to the bottom-right corner. The answer
is at most `2 * 10^9`.
""",
    constraints="""
- `1 <= m, n <= 100`; the answer fits in a signed 32-bit integer
""",
    signature=function("uniquePaths", [("m", "int"), ("n", "int")], "int"),
    reference=_unique_paths,
    brute=_unique_paths_brute,
    examples=[Example([3, 7]), Example([3, 2], "Right-down-down, down-right-down, down-down-right.")],
    edge_cases=[[1, 1], [1, 100], [100, 1], [17, 17]],
    generator=lambda rng: [(m := rng.randint(1, 17)), rng.randint(1, 34 - m)],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Palindromic Substring


def _longest_palindrome(s: str) -> str:
    best = s[0]
    for center in range(2 * len(s) - 1):  # expand around each centre
        lo, hi = center // 2, (center + 1) // 2
        while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
            lo, hi = lo - 1, hi + 1
        if hi - lo - 1 > len(best):
            best = s[lo + 1 : hi]
    return best


def _palindrome_brute(s: str) -> str:
    if len(s) > 150:
        return NotImplemented
    return max((s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1) if s[i:j] == s[i:j][::-1]), key=len)


LONGEST_PALINDROMIC_SUBSTRING = ProblemSource(
    title="Longest Palindromic Substring",
    statement="""
Return the longest substring of `s` that is a palindrome. If several have the maximum length, any of them is accepted.
""",
    constraints="""
- `1 <= s.length <= 1000`
- digits and English letters
""",
    signature=function("longestPalindrome", [("s", "string")], "string"),
    reference=_longest_palindrome,
    brute=_palindrome_brute,
    compare="checker",
    checker="palindrome_substring",
    examples=[Example(["babad"], "\"bab\" or \"aba\"."), Example(["cbbd"])],
    edge_cases=[["a"], ["ac"], ["aaaa"], ["abacdfgdcaba"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([20, 1000])), rng.choice(["ab", "abc", "aB1"]))],
    random_count=8,
)


# ---------------------------------------------------------------- House Robber


def _rob(nums: list[int]) -> int:
    take = skip = 0
    for x in nums:
        take, skip = skip + x, max(take, skip)
    return max(take, skip)


def _rob_brute(nums: list[int]) -> int:
    @cache
    def best(i: int) -> int:
        return 0 if i >= len(nums) else max(best(i + 1), nums[i] + best(i + 2))

    return best(0)


HOUSE_ROBBER = ProblemSource(
    title="House Robber",
    statement="""
`nums[i]` is the money in house `i` along a street. Robbing two adjacent houses triggers an alarm. Return the most money you can rob without
robbing adjacent houses.
""",
    constraints="""
- `1 <= nums.length <= 100`
- `0 <= nums[i] <= 400`
""",
    signature=function("rob", [("nums", "int[]")], "int"),
    reference=_rob,
    brute=_rob_brute,
    examples=[Example([[1, 2, 3, 1]], "Houses 0 and 2."), Example([[2, 7, 9, 3, 1]])],
    edge_cases=[[[0]], [[5]], [[2, 1, 1, 2]]],
    generator=lambda rng: [ints(rng, rng.randint(1, 100), 0, rng.choice([10, 400]))],
    random_count=8,
)


# ---------------------------------------------------------------- Same Tree


def _is_same_tree(p: TreeNode | None, q: TreeNode | None) -> bool:
    stack = [(p, q)]
    while stack:
        a, b = stack.pop()
        if a is None and b is None:
            continue
        if a is None or b is None or a.val != b.val:
            return False
        stack += [(a.left, b.left), (a.right, b.right)]
    return True


def _same_gen(rng: random.Random) -> list:
    tree = random_tree(rng, pick_n(rng, 0, 12, big=100), 0, rng.choice([2, 10**4]))
    other = list(tree)
    roll = rng.random()
    if roll < 0.3 and other:
        k = rng.choice([i for i, v in enumerate(other) if v is not None])
        other[k] = other[k] + 1
    elif roll < 0.5:
        other = random_tree(rng, len([v for v in tree if v is not None]), 0, 2)
    return [tree, other]


SAME_TREE = ProblemSource(
    title="Same Tree",
    statement="""
Return `true` if the binary trees `p` and `q` are identical: same structure and same values in the same places.
""",
    constraints="""
- `0 <= number of nodes <= 100`
- `-10^4 <= Node.val <= 10^4`
""",
    signature=function("isSameTree", [("p", "TreeNode"), ("q", "TreeNode")], "bool"),
    reference=_is_same_tree,
    brute=lambda p, q: tree_to_json(p) == tree_to_json(q),
    examples=[Example([[1, 2, 3], [1, 2, 3]]), Example([[1, 2], [1, None, 2]], "Same values, different shape."), Example([[1, 2, 1], [1, 1, 2]])],
    edge_cases=[[[], []], [[1], []], [[0], [0]]],
    generator=_same_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Shortest Bridge


def _shortest_bridge(grid: list[list[int]]) -> int:
    n = len(grid)
    start = next((i, j) for i in range(n) for j in range(n) if grid[i][j])
    island, stack = {start}, [start]
    while stack:  # collect the first island
        for c in _grid_neighbours(n, n, *stack.pop()):
            if grid[c[0]][c[1]] and c not in island:
                island.add(c)
                stack.append(c)
    dist = {c: 0 for c in island}
    queue = deque(island)
    while queue:  # expand outward until touching the other island
        v = queue.popleft()
        for c in _grid_neighbours(n, n, *v):
            if c in dist:
                continue
            if grid[c[0]][c[1]]:
                return dist[v]
            dist[c] = dist[v] + 1
            queue.append(c)
    raise AssertionError("two islands exist")


def _bridge_brute(grid: list[list[int]]) -> int:
    n = len(grid)
    cells = [(i, j) for i in range(n) for j in range(n) if grid[i][j]]
    label: dict[tuple[int, int], int] = {}
    for c in cells:
        if c not in label:
            label[c] = len(set(label.values()))
            stack = [c]
            while stack:
                for d in _grid_neighbours(n, n, *stack.pop()):
                    if grid[d[0]][d[1]] and d not in label:
                        label[d] = label[c]
                        stack.append(d)
    a = [c for c in cells if label[c] == 0]
    b = [c for c in cells if label[c] == 1]
    return min(abs(x[0] - y[0]) + abs(x[1] - y[1]) for x in a for y in b) - 1


def _two_islands_gen(rng: random.Random) -> list:
    while True:  # retry the rare layouts where the first island leaves no room for a separate second one
        grid = _try_two_islands(rng, rng.randint(3, rng.choice([6, 30])))
        if grid is not None:
            return [grid]


def _try_two_islands(rng: random.Random, n: int) -> list[list[int]] | None:
    grid = [[0] * n for _ in range(n)]
    for _island in range(2):
        free = [(i, j) for i in range(n) for j in range(n) if grid[i][j] == 0 and all(grid[a][b] == 0 for a, b in _grid_neighbours(n, n, i, j))]
        if not free:
            return None
        i, j = rng.choice(free)
        grid[i][j] = 2 + _island
        cells = [(i, j)]
        for _ in range(rng.randint(0, n)):
            ci, cj = rng.choice(cells)
            options = [(a, b) for a, b in _grid_neighbours(n, n, ci, cj) if grid[a][b] == 0 and all(grid[x][y] in (0, 2 + _island) for x, y in _grid_neighbours(n, n, a, b))]
            if options:
                a, b = rng.choice(options)
                grid[a][b] = 2 + _island
                cells.append((a, b))
    return [[1 if v else 0 for v in row] for row in grid]


SHORTEST_BRIDGE = ProblemSource(
    title="Shortest Bridge",
    statement="""
The `n x n` binary grid contains exactly **two** islands (groups of `1`s connected horizontally or vertically). You may turn `0`s into `1`s to
connect them. Return the smallest number of `0`s you must flip.
""",
    constraints="""
- `2 <= n <= 100`
- exactly two islands
""",
    signature=function("shortestBridge", [("grid", "int[][]")], "int"),
    reference=_shortest_bridge,
    brute=_bridge_brute,
    brute_input_limit=2500,
    examples=[Example([[[0, 1], [1, 0]]]), Example([[[0, 1, 0], [0, 0, 0], [0, 0, 1]]]), Example([[[1, 1, 1, 1, 1], [1, 0, 0, 0, 1], [1, 0, 1, 0, 1], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1]]], "The inner island is one flip away.")],
    edge_cases=[[[[1, 0, 1], [0, 0, 0], [0, 0, 0]]]],
    generator=_two_islands_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Median of Two Sorted Arrays


def _find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float:
    a, b = (nums1, nums2) if len(nums1) <= len(nums2) else (nums2, nums1)
    m, n = len(a), len(b)
    half = (m + n + 1) // 2
    lo, hi = 0, m
    while True:  # binary search the cut in the shorter array
        i = (lo + hi) // 2
        j = half - i
        a_left = a[i - 1] if i else -math.inf
        a_right = a[i] if i < m else math.inf
        b_left = b[j - 1] if j else -math.inf
        b_right = b[j] if j < n else math.inf
        if a_left <= b_right and b_left <= a_right:
            left_max = max(a_left, b_left)
            if (m + n) % 2:
                return float(left_max)
            return (left_max + min(a_right, b_right)) / 2
        if a_left > b_right:
            hi = i - 1
        else:
            lo = i + 1


def _median_brute(nums1: list[int], nums2: list[int]) -> float:
    merged = sorted(nums1 + nums2)
    k = len(merged)
    return float(merged[k // 2]) if k % 2 else (merged[k // 2 - 1] + merged[k // 2]) / 2


MEDIAN_TWO_ARRAYS = ProblemSource(
    title="Median of Two Sorted Arrays",
    statement="""
`nums1` and `nums2` are sorted in non-decreasing order. Return the median of all their elements combined. The overall run time should be
`O(log(m + n))`. Answers within `10^-5` are accepted.
""",
    constraints="""
- `0 <= m, n <= 1000`, `1 <= m + n <= 2000`
- `-10^6 <= values <= 10^6`
""",
    signature=function("findMedianSortedArrays", [("nums1", "int[]"), ("nums2", "int[]")], "double"),
    reference=_find_median_sorted_arrays,
    brute=_median_brute,
    compare="float_tolerance",
    examples=[Example([[1, 3], [2]]), Example([[1, 2], [3, 4]], "(2 + 3) / 2."), Example([[], [1]])],
    edge_cases=[[[1], []], [[1, 1], [1, 1]], [[-1000000], [1000000]]],
    generator=lambda rng: [sorted(ints(rng, rng.randint(0, rng.choice([5, 1000])), -(hi := rng.choice([10, 10**6])), hi)), sorted(ints(rng, rng.randint(1, rng.choice([5, 1000])), -hi, hi))],
    random_count=10,
)


# ---------------------------------------------------------------- Largest Rectangle in Histogram


def _largest_rectangle_area(heights: list[int]) -> int:
    stack: list[int] = []  # indices with increasing heights
    best = 0
    for i, h in enumerate([*heights, 0]):
        while stack and heights[stack[-1]] >= h:
            top = heights[stack.pop()]
            left = stack[-1] if stack else -1
            best = max(best, top * (i - left - 1))
        stack.append(i)
    return best


def _histogram_brute(heights: list[int]) -> int:
    n = len(heights)
    if n > 300:
        return NotImplemented
    best = 0
    for i in range(n):
        low = heights[i]
        for j in range(i, n):
            low = min(low, heights[j])
            best = max(best, low * (j - i + 1))
    return best


LARGEST_RECTANGLE = ProblemSource(
    title="Largest Rectangle in Histogram",
    statement="""
`heights[i]` is the height of the `i`-th bar of a histogram; every bar is 1 unit wide. Return the area of the largest rectangle that fits inside
the histogram.
""",
    constraints="""
- `1 <= heights.length <= 10^5`
- `0 <= heights[i] <= 10^4`
""",
    signature=function("largestRectangleArea", [("heights", "int[]")], "int"),
    reference=_largest_rectangle_area,
    brute=_histogram_brute,
    examples=[Example([[2, 1, 5, 6, 2, 3]], "Bars 5 and 6: 2 * 5 = 10."), Example([[2, 4]])],
    edge_cases=[[[0]], [[5]], [[1, 1, 1, 1]], [[4, 2, 0, 3, 2, 5]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=10**4), 0, rng.choice([6, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Sort List


def _sort_list(head: ListNode | None) -> ListNode | None:
    """Bottom-up merge sort: O(n log n) time, O(1) extra space."""
    length, node = 0, head
    while node:
        length, node = length + 1, node.next
    dummy = ListNode(0, head)
    size = 1
    while size < length:
        tail, current = dummy, dummy.next
        while current:
            left = current
            right = _split(left, size)
            current = _split(right, size)
            tail = _merge(left, right, tail)
        size *= 2
    return dummy.next


def _split(head: ListNode | None, size: int) -> ListNode | None:
    """Cut the list after `size` nodes and return the rest."""
    for _ in range(size - 1):
        if head is None:
            break
        head = head.next
    if head is None:
        return None
    rest, head.next = head.next, None
    return rest


def _merge(a: ListNode | None, b: ListNode | None, tail: ListNode) -> ListNode:
    """Append the merge of a and b after `tail`; return the new tail."""
    while a and b:
        if a.val <= b.val:
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a or b
    while tail.next:
        tail = tail.next
    return tail


def _sort_list_brute(head: ListNode | None) -> ListNode | None:
    values = []
    while head:
        values.append(head.val)
        head = head.next
    out = None
    for v in sorted(values, reverse=True):
        out = ListNode(v, out)
    return out


SORT_LIST = ProblemSource(
    title="Sort List",
    statement="""
Sort the linked list in ascending order and return its head. Aim for `O(n log n)` time and `O(1)` extra space.
""",
    constraints="""
- `0 <= number of nodes <= 5 * 10^4`
- `-10^5 <= Node.val <= 10^5`
""",
    signature=function("sortList", [("head", "ListNode")], "ListNode"),
    reference=_sort_list,
    brute=_sort_list_brute,
    examples=[Example([[4, 2, 1, 3]]), Example([[-1, 5, 3, 4, 0]]), Example([[]])],
    edge_cases=[[[1]], [[2, 1]], [[3, 3, 1, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=5000), -(10**5), 10**5)],
    random_count=8,
)


# ---------------------------------------------------------------- Evaluate Reverse Polish Notation


def _eval_rpn(tokens: list[str]) -> int:
    stack: list[int] = []
    for t in tokens:
        if t in {"+", "-", "*", "/"}:
            b, a = stack.pop(), stack.pop()
            if t == "+":
                stack.append(a + b)
            elif t == "-":
                stack.append(a - b)
            elif t == "*":
                stack.append(a * b)
            else:
                stack.append(abs(a) // abs(b) * (1 if (a >= 0) == (b > 0) else -1))  # truncate toward zero
        else:
            stack.append(int(t))
    return stack[0]


def _rpn_brute(tokens: list[str]) -> int:
    def build(i: int) -> tuple[str, int]:
        """Rebuild the expression recursively from the end, returning (python expr, next index)."""
        t = tokens[i]
        if t not in {"+", "-", "*", "/"}:
            return t, i - 1
        right, i = build(i - 1)
        left, i = build(i)
        if t == "/":
            return f"_div({left}, {right})", i
        return f"({left} {t} {right})", i

    def _div(a: int, b: int) -> int:
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b > 0) else -q

    expr, _ = build(len(tokens) - 1)
    return eval(expr, {"__builtins__": {}, "_div": _div})  # noqa: S307 - oracle over our own generated input


def _rpn_gen(rng: random.Random) -> list:
    def expr(depth: int) -> tuple[list[str], int]:
        if depth == 0 or rng.random() < 0.3:
            v = rng.randint(-20, 20)
            return [str(v)], v
        (left, a), (right, b) = expr(depth - 1), expr(depth - 1)
        op = rng.choice("+-*/" if b != 0 else "+-*")
        if op == "*" and abs(a * b) > 10**6:
            op = "+"
        value = {"+": a + b, "-": a - b, "*": a * b}.get(op, abs(a) // abs(b) * (1 if (a >= 0) == (b > 0) else -1) if b else 0)
        return left + right + [op], value

    return [expr(rng.randint(1, 5))[0]]


EVAL_RPN = ProblemSource(
    title="Evaluate Reverse Polish Notation",
    statement="""
`tokens` is an arithmetic expression in Reverse Polish Notation, with the operators `+ - * /` and integer operands. Evaluate it and return the
result. Division truncates toward zero, there is never division by zero, and every intermediate value fits in a signed 32-bit integer.
""",
    constraints="""
- `1 <= tokens.length <= 10^4`
- each token is an operator or an integer in `[-200, 200]`
""",
    signature=function("evalRPN", [("tokens", "string[]")], "int"),
    reference=_eval_rpn,
    brute=_rpn_brute,
    examples=[Example([["2", "1", "+", "3", "*"]], "(2 + 1) * 3."), Example([["4", "13", "5", "/", "+"]]), Example([["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]])],
    edge_cases=[[["7"]], [["-7", "2", "/"]], [["0", "3", "/"]]],
    generator=_rpn_gen,
    random_count=10,
)


PROBLEMS = [
    CONNECTED_COMPONENTS,
    PACIFIC_ATLANTIC,
    CONTAINS_DUPLICATE,
    MAXIMUM_SUBARRAY,
    TWO_SUM,
    FIND_MIN_ROTATED,
    NON_OVERLAPPING,
    MEETING_ROOMS,
    SUBTREE,
    ONE_BITS,
    CONTAINER_WATER,
    PRODUCT_EXCEPT_SELF,
    LIS,
    SUM_TWO_INTEGERS,
    UNIQUE_PATHS,
    LONGEST_PALINDROMIC_SUBSTRING,
    HOUSE_ROBBER,
    SAME_TREE,
    SHORTEST_BRIDGE,
    MEDIAN_TWO_ARRAYS,
    LARGEST_RECTANGLE,
    SORT_LIST,
    EVAL_RPN,
]
