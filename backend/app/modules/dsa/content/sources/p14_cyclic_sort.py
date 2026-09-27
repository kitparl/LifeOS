"""Pattern 14: Cyclic Sort. Original statements; outputs come from `reference`."""

from __future__ import annotations

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sample

PATTERN_NUMBER = 14


def _cyclic_place(nums: list[int], lo: int, hi: int) -> None:
    """Swap every value in [lo, hi] into index value - lo; other values stay where they land."""
    i = 0
    while i < len(nums):
        target = nums[i] - lo
        if lo <= nums[i] <= hi and target < len(nums) and nums[target] != nums[i]:
            nums[i], nums[target] = nums[target], nums[i]
        else:
            i += 1


# ---------------------------------------------------------------- Missing Number


def _drop_one(rng, n: int) -> list[int]:
    values = list(range(n + 1))
    values.remove(rng.randint(0, n))
    rng.shuffle(values)
    return values


def _missing_number(nums: list[int]) -> int:
    nums = nums[:]
    _cyclic_place(nums, 0, len(nums) - 1)
    return next((i for i, v in enumerate(nums) if v != i), len(nums))


MISSING_NUMBER = ProblemSource(
    title="Missing Number",
    statement="""
`nums` holds `n` distinct numbers taken from the range `[0, n]`, so exactly one number of that range is absent. Return it.

Aim for `O(n)` time and `O(1)` extra space.
""",
    constraints="""
- `1 <= n <= 10^4`
- `0 <= nums[i] <= n`, all distinct
""",
    signature=function("missingNumber", [("nums", "int[]")], "int"),
    reference=_missing_number,
    brute=lambda nums: (set(range(len(nums) + 1)) - set(nums)).pop(),
    examples=[Example([[3, 0, 1]], "Range 0..3; 2 is absent."), Example([[0, 1]], "Range 0..2; 2 is absent."), Example([[9, 6, 4, 2, 3, 5, 7, 0, 1]])],
    edge_cases=[[[0]], [[1]], [list(range(1, 50))]],
    generator=lambda rng: [_drop_one(rng, pick_n(rng, 1, 20, big=10**4))],
    random_count=8,
)


# ---------------------------------------------------------------- First Missing Positive

def _first_missing_positive(nums: list[int]) -> int:
    nums = nums[:]
    _cyclic_place(nums, 1, len(nums))
    return next((i + 1 for i, v in enumerate(nums) if v != i + 1), len(nums) + 1)


def _first_missing_brute(nums: list[int]) -> int:
    present = set(nums)
    k = 1
    while k in present:
        k += 1
    return k


def _first_missing_gen(rng):
    n = pick_n(rng, 1, 15, big=10**4)
    if rng.random() < 0.3:
        return [ints(rng, n, -(2**31), 2**31 - 1)]
    nums = [x if rng.random() < 0.85 else rng.choice([-x, x + n, 0]) for x in range(1, n + 1)]  # mostly 1..n, a few holes
    rng.shuffle(nums)
    return [nums]


FIRST_MISSING_POSITIVE = ProblemSource(
    title="First Missing Positive",
    statement="""
Given an unsorted integer array `nums`, return the smallest positive integer that does not appear in it.

Your solution should run in `O(n)` time using `O(1)` extra space (modifying `nums` is allowed).
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `-2^31 <= nums[i] <= 2^31 - 1`
""",
    signature=function("firstMissingPositive", [("nums", "int[]")], "int"),
    reference=_first_missing_positive,
    brute=_first_missing_brute,
    examples=[Example([[1, 2, 0]]), Example([[3, 4, -1, 1]], "1 is present, 2 is not."), Example([[7, 8, 9, 11, 12]])],
    edge_cases=[[[1]], [[2]], [[-2147483648]], [[1, 1]], [list(range(1, 101))]],
    generator=_first_missing_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find the Corrupt Pair

def _find_corrupt_pair(nums: list[int]) -> list[int]:
    nums = nums[:]
    _cyclic_place(nums, 1, len(nums))
    for i, v in enumerate(nums):
        if v != i + 1:
            return [v, i + 1]
    raise ValueError("no corrupt pair")


def _corrupt_brute(nums: list[int]) -> list[int]:
    seen = set()
    duplicate = next(x for x in nums if x in seen or seen.add(x))
    missing = (set(range(1, len(nums) + 1)) - set(nums)).pop()
    return [duplicate, missing]


def _corrupt_gen(rng):
    n = pick_n(rng, 2, 15, big=10**4)
    values = list(range(1, n + 1))
    missing, duplicate = sample(rng, values, 2)
    values[values.index(missing)] = duplicate
    rng.shuffle(values)
    return [values]


CORRUPT_PAIR = ProblemSource(
    title="Find the Corrupt Pair",
    statement="""
`nums` should contain every number from `1` to `n` exactly once, but it got corrupted: one number was overwritten with a copy of another, so one
value appears twice and one value is missing. Return `[duplicate, missing]`.

Aim for `O(n)` time and `O(1)` extra space.
""",
    constraints="""
- `2 <= n <= 10^4`
- exactly one value of `1..n` is duplicated and exactly one is missing
""",
    signature=function("findCorruptPair", [("nums", "int[]")], "int[]"),
    reference=_find_corrupt_pair,
    brute=_corrupt_brute,
    examples=[Example([[3, 1, 2, 5, 2]], "2 appears twice; 4 is missing."), Example([[3, 1, 2, 3, 6, 4]], "3 appears twice; 5 is missing.")],
    edge_cases=[[[1, 1]], [[2, 2]], [[1, 2, 3, 3]]],
    generator=_corrupt_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find the First K Missing Positive Numbers

def _find_k_missing(nums: list[int], k: int) -> list[int]:
    nums = nums[:]
    _cyclic_place(nums, 1, len(nums))
    missing, extras = [], set()
    for i, v in enumerate(nums):
        if len(missing) == k:
            break
        if v != i + 1:
            missing.append(i + 1)
            extras.add(v)
    candidate = len(nums) + 1
    while len(missing) < k:
        if candidate not in extras:
            missing.append(candidate)
        candidate += 1
    return missing


def _k_missing_brute(nums: list[int], k: int) -> list[int]:
    present, out, x = set(nums), [], 1
    while len(out) < k:
        if x not in present:
            out.append(x)
        x += 1
    return out


FIRST_K_MISSING = ProblemSource(
    title="Find the First K Missing Positive Numbers",
    statement="""
Given an unsorted array `nums` and an integer `k`, return the `k` smallest positive integers that do not appear in `nums`, in increasing order.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-10^4 <= nums[i] <= 10^4`
- `1 <= k <= 10^4`
""",
    signature=function("findFirstKMissing", [("nums", "int[]"), ("k", "int")], "int[]"),
    reference=_find_k_missing,
    brute=_k_missing_brute,
    examples=[Example([[3, -1, 4, 5, 5], 3], "1, 2 and 6 are the first three absent positives."), Example([[2, 3, 4], 3]), Example([[-2, -3, 4], 2])],
    edge_cases=[[[1], 1], [[1, 2, 3], 2], [[-5], 4], [[10000], 10000]],
    generator=lambda rng: [ints(rng, (n := pick_n(rng, 1, 15, big=3000)), -rng.choice([3, 10**4]), rng.choice([n + 3, 10**4])), rng.randint(1, rng.choice([5, 3000]))],
    random_count=8,
)


# ---------------------------------------------------------------- Sort Array By Parity II

def _sort_by_parity_ii(nums: list[int]) -> list[int]:
    nums = nums[:]
    odd = 1
    for even in range(0, len(nums), 2):
        if nums[even] % 2:
            while nums[odd] % 2:
                odd += 2
            nums[even], nums[odd] = nums[odd], nums[even]
    return nums


def _parity_gen(rng):
    half = pick_n(rng, 1, 10, big=10**4)
    nums = [2 * rng.randint(0, 500) for _ in range(half)] + [2 * rng.randint(0, 499) + 1 for _ in range(half)]
    rng.shuffle(nums)
    return [nums]


SORT_BY_PARITY_II = ProblemSource(
    title="Sort Array By Parity II",
    statement="""
`nums` has even length, and exactly half of its values are even. Rearrange it so that every even index holds an even value and every odd index
holds an odd value, and return the rearranged array. Any valid arrangement is accepted.
""",
    constraints="""
- `2 <= nums.length <= 2 * 10^4`, even
- half of the values are even
- `0 <= nums[i] <= 1000`
""",
    signature=function("sortArrayByParityII", [("nums", "int[]")], "int[]"),
    reference=_sort_by_parity_ii,
    compare="checker",
    checker="parity_ii",
    examples=[Example([[4, 2, 5, 7]], "[4,5,2,7], [2,7,4,5] and others are all valid."), Example([[2, 3]])],
    edge_cases=[[[1, 0]], [[1, 3, 0, 2]], [[0, 0, 1, 1]]],
    generator=_parity_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Cyclic Sort

def _cyclic_sort(nums: list[int]) -> None:
    _cyclic_place(nums, 1, len(nums))


CYCLIC_SORT = ProblemSource(
    title="Cyclic Sort",
    statement="""
`nums` is a permutation of the numbers `1` to `n`. Sort it **in place** in ascending order without using a general-purpose sort: place each
number directly at the index it belongs to. Nothing is returned; the judge inspects `nums` afterwards.

Aim for `O(n)` time and `O(1)` extra space.
""",
    constraints="""
- `1 <= n <= 10^4`
- `nums` is a permutation of `1..n`
""",
    signature=function("cyclicSort", [("nums", "int[]")], "void", mutates="nums"),
    reference=_cyclic_sort,
    brute=lambda nums: nums.sort(),
    examples=[Example([[3, 1, 5, 4, 2]], "Becomes [1,2,3,4,5]."), Example([[2, 6, 4, 3, 1, 5]])],
    edge_cases=[[[1]], [[2, 1]], [list(range(30, 0, -1))]],
    generator=lambda rng: [sample(rng, range(1, (n := pick_n(rng, 1, 20, big=10**4)) + 1), n)],
    random_count=8,
)


PROBLEMS = [MISSING_NUMBER, FIRST_MISSING_POSITIVE, CORRUPT_PAIR, FIRST_K_MISSING, SORT_BY_PARITY_II, CYCLIC_SORT]
