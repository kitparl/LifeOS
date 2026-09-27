"""Pattern 10: Subsets. Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import itertools

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, sample, word

PATTERN_NUMBER = 10

_PHONE = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl", "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}


# ---------------------------------------------------------------- Find K-Sum Subsets


def _k_sum_subsets(nums: list[int], k: int) -> list[list[int]]:
    out: list[list[int]] = []

    def build(i: int, chosen: list[int], total: int) -> None:
        if total == k:
            out.append(chosen[:])
        if total >= k:
            return
        for j in range(i, len(nums)):
            chosen.append(nums[j])
            build(j + 1, chosen, total + nums[j])
            chosen.pop()

    build(0, [], 0)
    return out


def _k_sum_subsets_brute(nums: list[int], k: int) -> list[list[int]]:
    return [list(c) for r in range(1, len(nums) + 1) for c in itertools.combinations(nums, r) if sum(c) == k]


def _k_sum_gen(rng):
    nums = sample(rng, range(1, rng.choice([12, 40])), rng.randint(1, 14))
    return [nums, rng.randint(1, max(1, sum(nums) // 2))]


K_SUM_SUBSETS = ProblemSource(
    title="Find K-Sum Subsets",
    statement="""
`nums` is a set of **distinct positive** integers. Return every non-empty subset whose elements add up exactly to `k`.
Subsets may be returned in any order, and the values inside a subset may be in any order.
""",
    constraints="""
- `1 <= nums.length <= 14`
- `1 <= nums[i] <= 50`, all distinct
- `1 <= k <= 500`
""",
    signature=function("getKSumSubsets", [("nums", "int[]"), ("k", "int")], "int[][]"),
    reference=_k_sum_subsets,
    brute=_k_sum_subsets_brute,
    compare="unordered_nested",
    examples=[Example([[1, 3, 5, 21, 19, 7, 2], 10], "Three subsets sum to 10: [3, 7], [1, 2, 7] and [2, 3, 5]."), Example([[2, 4, 6], 6], "[2, 4] and [6].")],
    edge_cases=[[[1], 1], [[5], 1], [[1, 2, 3], 6], [[10, 20], 5]],
    generator=_k_sum_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Subsets


def _subsets(nums: list[int]) -> list[list[int]]:
    out = [[]]
    for x in nums:
        out += [s + [x] for s in out]
    return out


SUBSETS = ProblemSource(
    title="Subsets",
    statement="""
`nums` holds distinct integers. Return all of its subsets (the *power set*), including the empty set, without duplicates.
The subsets may be in any order, and so may the values inside each subset.
""",
    constraints="""
- `1 <= nums.length <= 10`
- `-10 <= nums[i] <= 10`, all distinct
""",
    signature=function("subsets", [("nums", "int[]")], "int[][]"),
    reference=_subsets,
    brute=lambda nums: [list(c) for r in range(len(nums) + 1) for c in itertools.combinations(nums, r)],
    compare="unordered_nested",
    examples=[Example([[1, 2, 3]], "All 8 subsets, from [] to [1, 2, 3]."), Example([[0]], "[] and [0].")],
    edge_cases=[[[-10, 10]], [[5, -3, 0, 2]]],
    generator=lambda rng: [sample(rng, range(-10, 11), rng.randint(1, 10))],
    random_count=7,
)


# ---------------------------------------------------------------- Permutations


def _permute(nums: list[int]) -> list[list[int]]:
    out: list[list[int]] = []

    def build(i: int) -> None:
        if i == len(nums):
            out.append(nums[:])
            return
        for j in range(i, len(nums)):
            nums[i], nums[j] = nums[j], nums[i]
            build(i + 1)
            nums[i], nums[j] = nums[j], nums[i]

    build(0)
    return out


PERMUTATIONS = ProblemSource(
    title="Permutations",
    statement="""
`nums` holds distinct integers. Return every possible ordering (permutation) of its values, in any order.
""",
    constraints="""
- `1 <= nums.length <= 7`
- `-10 <= nums[i] <= 10`, all distinct
""",
    signature=function("permute", [("nums", "int[]")], "int[][]"),
    reference=_permute,
    brute=lambda nums: [list(p) for p in itertools.permutations(nums)],
    compare="unordered",
    examples=[Example([[1, 2, 3]], "Six orderings."), Example([[0, 1]]), Example([[1]])],
    edge_cases=[[[-10, 10, 0]], [[4, 3, 2, 1]]],
    generator=lambda rng: [sample(rng, range(-10, 11), rng.randint(1, 7))],
    random_count=6,
)


# ---------------------------------------------------------------- Letter Combinations of a Phone Number


def _letter_combinations(digits: str) -> list[str]:
    if not digits:
        return []
    out = [""]
    for d in digits:
        out = [prefix + ch for prefix in out for ch in _PHONE[d]]
    return out


PHONE_LETTERS = ProblemSource(
    title="Letter Combinations of a Phone Number",
    statement="""
On a phone keypad the digits map to letters: `2 -> abc`, `3 -> def`, `4 -> ghi`, `5 -> jkl`, `6 -> mno`,
`7 -> pqrs`, `8 -> tuv`, `9 -> wxyz`. Given a string of digits from `2` to `9`, return every letter string the digits
could spell, in any order. An empty input gives an empty list.
""",
    constraints="""
- `0 <= digits.length <= 4`
- each digit is between `2` and `9`
""",
    signature=function("letterCombinations", [("digits", "string")], "string[]"),
    reference=_letter_combinations,
    brute=lambda digits: ["".join(p) for p in itertools.product(*(_PHONE[d] for d in digits))] if digits else [],
    compare="unordered",
    examples=[Example(["23"], "ad, ae, af, bd, be, bf, cd, ce, cf."), Example([""]), Example(["2"])],
    edge_cases=[["79"], ["9999"], ["2345"]],
    generator=lambda rng: [word(rng, rng.randint(0, 4), "23456789")],
    random_count=6,
)


# ---------------------------------------------------------------- Generate Parentheses


def _generate_parentheses(n: int) -> list[str]:
    out: list[str] = []

    def build(prefix: str, opened: int, closed: int) -> None:
        if len(prefix) == 2 * n:
            out.append(prefix)
            return
        if opened < n:
            build(prefix + "(", opened + 1, closed)
        if closed < opened:
            build(prefix + ")", opened, closed + 1)

    build("", 0, 0)
    return out


def _parentheses_brute(n: int) -> list[str]:
    def valid(s: str) -> bool:
        depth = 0
        for ch in s:
            depth += 1 if ch == "(" else -1
            if depth < 0:
                return False
        return depth == 0

    return ["".join(p) for p in itertools.product("()", repeat=2 * n) if valid(p)]


GENERATE_PARENTHESES = ProblemSource(
    title="Generate Parentheses",
    statement="""
Return every string of `n` pairs of parentheses that is *well formed* (every `(` is closed by a later `)`, and no
prefix has more `)` than `(`), in any order.
""",
    constraints="""
- `1 <= n <= 8`
""",
    signature=function("generateParenthesis", [("n", "int")], "string[]"),
    reference=_generate_parentheses,
    brute=lambda n: _parentheses_brute(n) if n <= 6 else NotImplemented,
    compare="unordered",
    examples=[Example([3], "((())), (()()), (())(), ()(()), ()()()."), Example([1])],
    edge_cases=[[2], [4], [8]],
    generator=lambda rng: [rng.randint(1, 7)],
    random_count=4,
)


# ---------------------------------------------------------------- Letter Case Permutation


def _letter_case_permutation(s: str) -> list[str]:
    out = [""]
    for ch in s:
        out = [p + c for p in out for c in ({ch.lower(), ch.upper()} if ch.isalpha() else {ch})]
    return out


LETTER_CASE = ProblemSource(
    title="Letter Case Permutation",
    statement="""
Every letter of `s` may be written in lowercase or uppercase (digits stay as they are). Return every distinct string you
can make this way, in any order.
""",
    constraints="""
- `1 <= s.length <= 12`
- `s` consists of English letters and digits
""",
    signature=function("letterCasePermutation", [("s", "string")], "string[]"),
    reference=_letter_case_permutation,
    brute=lambda s: list({"".join(p) for p in itertools.product(*({c.lower(), c.upper()} for c in s))}),
    compare="unordered",
    examples=[Example(["a1b2"], "a1b2, a1B2, A1b2, A1B2."), Example(["3z4"], "3z4, 3Z4.")],
    edge_cases=[["1"], ["C"], ["12345"], ["aBc"]],
    generator=lambda rng: [word(rng, rng.randint(1, 9), "aZb3x9")],
    random_count=6,
)


# ---------------------------------------------------------------- Letter Tile Possibilities


def _num_tile_possibilities(tiles: str) -> int:
    counts: dict[str, int] = {}
    for t in tiles:
        counts[t] = counts.get(t, 0) + 1

    def count() -> int:
        total = 0
        for ch in counts:
            if counts[ch]:
                counts[ch] -= 1
                total += 1 + count()
                counts[ch] += 1
        return total

    return count()


LETTER_TILES = ProblemSource(
    title="Letter Tile Possibilities",
    statement="""
You have letter tiles; each tile shows the letter `tiles[i]`. Return the number of different **non-empty** letter sequences
you can spell by lining up some of the tiles (each tile used at most once).
""",
    constraints="""
- `1 <= tiles.length <= 7`
- `tiles` consists of uppercase English letters
""",
    signature=function("numTilePossibilities", [("tiles", "string")], "int"),
    reference=_num_tile_possibilities,
    brute=lambda tiles: len({"".join(p) for r in range(1, len(tiles) + 1) for p in itertools.permutations(tiles, r)}),
    examples=[Example(["AAB"], "A, B, AA, AB, BA, AAB, ABA, BAA: 8."), Example(["AAABBC"]), Example(["V"])],
    edge_cases=[["AB"], ["AAAA"], ["ABCDEFG"]],
    generator=lambda rng: [word(rng, rng.randint(1, 7), "AABBCD")],
    random_count=6,
)


# ---------------------------------------------------------------- Subsets II


def _subsets_with_dup(nums: list[int]) -> list[list[int]]:
    nums = sorted(nums)
    out: list[list[int]] = []

    def build(i: int, chosen: list[int]) -> None:
        out.append(chosen[:])
        for j in range(i, len(nums)):
            if j > i and nums[j] == nums[j - 1]:
                continue
            chosen.append(nums[j])
            build(j + 1, chosen)
            chosen.pop()

    build(0, [])
    return out


SUBSETS_II = ProblemSource(
    title="Subsets II",
    statement="""
`nums` may contain duplicate values. Return all of its **distinct** subsets, including the empty set. Two subsets are the same
if they hold the same values with the same multiplicities. Return them in any order.
""",
    constraints="""
- `1 <= nums.length <= 10`
- `-10 <= nums[i] <= 10`
""",
    signature=function("subsetsWithDup", [("nums", "int[]")], "int[][]"),
    reference=_subsets_with_dup,
    brute=lambda nums: [list(t) for t in {tuple(sorted(c)) for r in range(len(nums) + 1) for c in itertools.combinations(nums, r)}],
    compare="unordered_nested",
    examples=[Example([[1, 2, 2]], "[], [1], [1,2], [1,2,2], [2], [2,2]."), Example([[0]])],
    edge_cases=[[[5, 5, 5]], [[4, 4, 4, 1, 4]], [[-1, 1]]],
    generator=lambda rng: [ints(rng, rng.randint(1, 10), -3, 3)],
    random_count=6,
)


PROBLEMS = [K_SUM_SUBSETS, SUBSETS, PERMUTATIONS, PHONE_LETTERS, GENERATE_PARENTHESES, LETTER_CASE, LETTER_TILES, SUBSETS_II]
