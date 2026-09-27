"""Pattern 23: Hash Maps (part 2 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import random
from collections import Counter

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, sample, word

PATTERN_NUMBER = 23


# ---------------------------------------------------------------- Intersection of Two Arrays


def _intersection(nums1: list[int], nums2: list[int]) -> list[int]:
    return sorted(set(nums1) & set(nums2))


INTERSECTION = ProblemSource(
    title="Intersection of Two Arrays",
    statement="""
Return the values that appear in both `nums1` and `nums2`, each value once, in any order.
""",
    constraints="""
- `1 <= nums1.length, nums2.length <= 1000`
- `0 <= nums1[i], nums2[i] <= 1000`
""",
    signature=function("intersection", [("nums1", "int[]"), ("nums2", "int[]")], "int[]"),
    reference=_intersection,
    brute=lambda nums1, nums2: [x for i, x in enumerate(nums1) if x in nums2 and x not in nums1[:i]],
    compare="unordered",
    examples=[Example([[1, 2, 2, 1], [2, 2]]), Example([[4, 9, 5], [9, 4, 9, 8, 4]])],
    edge_cases=[[[1], [2]], [[0], [0]], [[1, 1, 1], [1, 1]]],
    generator=lambda rng: [ints(rng, rng.randint(1, 20), 0, (hi := rng.choice([10, 1000]))), ints(rng, rng.randint(1, 20), 0, hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Word Pattern


def _word_pattern(pattern: str, s: str) -> bool:
    words = s.split(" ")
    if len(words) != len(pattern):
        return False
    return len(set(pattern)) == len(set(words)) == len(set(zip(pattern, words, strict=True)))


def _word_pattern_brute(pattern: str, s: str) -> bool:
    words = s.split(" ")
    return len(words) == len(pattern) and [pattern.index(c) for c in pattern] == [words.index(w) for w in words]


def _word_pattern_gen(rng: random.Random) -> list:
    pattern = word(rng, rng.randint(1, 8), "abc")
    vocab = {c: word(rng, rng.randint(1, 3), "xyz") for c in "abc"}
    words = [vocab[c] for c in pattern]
    if rng.random() < 0.4:
        words[rng.randrange(len(words))] = word(rng, rng.randint(1, 3), "xyz")
    if rng.random() < 0.1:
        words.append("q")
    return [pattern, " ".join(words)]


WORD_PATTERN = ProblemSource(
    title="Word Pattern",
    statement="""
Return `true` if the words of `s` (separated by single spaces) follow `pattern`: there must be a one-to-one correspondence between the letters of
`pattern` and the words, applied position by position.
""",
    constraints="""
- `1 <= pattern.length <= 300`, lowercase letters
- `1 <= s.length <= 3000`, lowercase words separated by single spaces
""",
    signature=function("wordPattern", [("pattern", "string"), ("s", "string")], "bool"),
    reference=_word_pattern,
    brute=_word_pattern_brute,
    examples=[Example(["abba", "dog cat cat dog"]), Example(["abba", "dog cat cat fish"]), Example(["aaaa", "dog cat cat dog"])],
    edge_cases=[["a", "x"], ["ab", "x x"], ["aa", "x y"], ["a", "x y"]],
    generator=_word_pattern_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Valid Sudoku


def _is_valid_sudoku(board: list[list[str]]) -> bool:
    seen: set[tuple] = set()
    for i, row in enumerate(board):
        for j, ch in enumerate(row):
            if ch == ".":
                continue
            keys = [("row", i, ch), ("col", j, ch), ("box", i // 3, j // 3, ch)]
            if any(k in seen for k in keys):
                return False
            seen.update(keys)
    return True


def _sudoku_brute(board: list[list[str]]) -> bool:
    groups = [row for row in board]
    groups += [[board[i][j] for i in range(9)] for j in range(9)]
    groups += [[board[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)] for br in (0, 3, 6) for bc in (0, 3, 6)]
    return all(len(digits) == len(set(digits)) for digits in ([c for c in g if c != "."] for g in groups))


_SOLVED = [
    "534678912", "672195348", "198342567", "859761423", "426853791", "713924856", "961537284", "287419635", "345286179",
]


def _sudoku_gen(rng: random.Random) -> list:
    digits = sample(rng, list("123456789"), 9)
    relabel = dict(zip("123456789", digits, strict=True))
    board = [[relabel[c] if rng.random() < 0.4 else "." for c in row] for row in _SOLVED]
    if rng.random() < 0.5:  # plant a guaranteed clash: repeat a digit elsewhere in its row
        i = rng.randrange(9)
        j, k = sample(rng, range(9), 2)
        board[i][k] = board[i][j] = relabel[_SOLVED[i][j]]
    return [board]


VALID_SUDOKU = ProblemSource(
    title="Valid Sudoku",
    statement="""
Check whether a partially filled `9 x 9` Sudoku board is valid: every row, every column, and every `3 x 3` box must contain each digit `1`-`9` at
most once. Empty cells are `"."`. The board does not need to be solvable.
""",
    constraints="""
- `board` is `9 x 9`; each cell is a digit `1`-`9` or `"."`
""",
    signature=function("isValidSudoku", [("board", "char[][]")], "bool"),
    reference=_is_valid_sudoku,
    brute=_sudoku_brute,
    examples=[
        Example([[list(r) for r in ["53..7....", "6..195...", ".98....6.", "8...6...3", "4..8.3..1", "7...2...6", ".6....28.", "...419..5", "....8..79"]]]),
        Example([[list(r) for r in ["83..7....", "6..195...", ".98....6.", "8...6...3", "4..8.3..1", "7...2...6", ".6....28.", "...419..5", "....8..79"]]], "Two 8s in the first column and top-left box."),
    ],
    edge_cases=[[[["."] * 9 for _ in range(9)]], [[list("11......."), *[["."] * 9 for _ in range(8)]]]],
    generator=_sudoku_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Roman to Integer


_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _roman_to_int(s: str) -> int:
    total = 0
    for a, b in itertools.pairwise(s + " "):
        value = _ROMAN[a]
        total += -value if b != " " and _ROMAN[b] > value else value
    return total


def _to_roman(n: int) -> str:
    out = ""
    for value, text in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        count, n = divmod(n, value)
        out += text * count
    return out


ROMAN_TO_INTEGER = ProblemSource(
    title="Roman to Integer",
    statement="""
Convert the Roman numeral `s` to an integer. The symbols are `I=1, V=5, X=10, L=50, C=100, D=500, M=1000`; a smaller symbol placed before a
larger one is subtracted (only `IV, IX, XL, XC, CD, CM` occur), otherwise values add up.
""",
    constraints="""
- `1 <= s.length <= 15`
- `s` is a valid Roman numeral for a value in `[1, 3999]`
""",
    signature=function("romanToInt", [("s", "string")], "int"),
    reference=_roman_to_int,
    brute=lambda s: next(n for n in range(1, 4000) if _to_roman(n) == s),
    examples=[Example(["III"]), Example(["LVIII"], "50 + 5 + 3."), Example(["MCMXCIV"], "1000 + 900 + 90 + 4.")],
    edge_cases=[["I"], ["IV"], ["MMMCMXCIX"]],
    generator=lambda rng: [_to_roman(rng.randint(1, 3999))],
    random_count=8,
)


# ---------------------------------------------------------------- Contiguous Array


def _find_max_length(nums: list[int]) -> int:
    first_at = {0: -1}
    balance = best = 0
    for i, x in enumerate(nums):
        balance += 1 if x else -1
        if balance in first_at:
            best = max(best, i - first_at[balance])
        else:
            first_at[balance] = i
    return best


def _contiguous_brute(nums: list[int]) -> int:
    n = len(nums)
    if n > 300:
        return NotImplemented
    return max((j - i for i in range(n) for j in range(i + 2, n + 1, 2) if 2 * sum(nums[i:j]) == j - i), default=0)


CONTIGUOUS_ARRAY = ProblemSource(
    title="Contiguous Array",
    statement="""
`nums` is a binary array. Return the length of the longest contiguous subarray with an equal number of `0`s and `1`s.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `nums[i]` is `0` or `1`
""",
    signature=function("findMaxLength", [("nums", "int[]")], "int"),
    reference=_find_max_length,
    brute=_contiguous_brute,
    examples=[Example([[0, 1]]), Example([[0, 1, 0]]), Example([[0, 1, 1, 1, 1, 1, 0, 0, 0]])],
    edge_cases=[[[0]], [[1, 1]], [[1, 0, 1, 0]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 30, big=10**4), 0, 1)],
    random_count=8,
)


# ---------------------------------------------------------------- Jewels and Stones


def _num_jewels(jewels: str, stones: str) -> int:
    kinds = set(jewels)
    return sum(ch in kinds for ch in stones)


JEWELS_AND_STONES = ProblemSource(
    title="Jewels and Stones",
    statement="""
Each character of `jewels` is a distinct type of stone that is a jewel; each character of `stones` is one stone you have. Return how many of your
stones are jewels. Letters are case-sensitive.
""",
    constraints="""
- `1 <= jewels.length, stones.length <= 50`
- English letters; the characters of `jewels` are distinct
""",
    signature=function("numJewelsInStones", [("jewels", "string"), ("stones", "string")], "int"),
    reference=_num_jewels,
    brute=lambda jewels, stones: sum(stones.count(j) for j in jewels),
    examples=[Example(["aA", "aAAbbbb"]), Example(["z", "ZZ"], "Case matters.")],
    edge_cases=[["a", "a"], ["abc", "d"]],
    generator=lambda rng: ["".join(sample(rng, list("abcABC"), rng.randint(1, 6))), word(rng, rng.randint(1, 50), "abcdABCD")],
    random_count=8,
)


# ---------------------------------------------------------------- Vowel Spellchecker


def _devowel(w: str) -> str:
    return "".join("*" if c in "aeiou" else c for c in w.lower())


def _spellchecker(wordlist: list[str], queries: list[str]) -> list[str]:
    exact = set(wordlist)
    by_case: dict[str, str] = {}
    by_vowel: dict[str, str] = {}
    for w in wordlist:
        by_case.setdefault(w.lower(), w)
        by_vowel.setdefault(_devowel(w), w)
    out = []
    for q in queries:
        if q in exact:
            out.append(q)
        else:
            out.append(by_case.get(q.lower()) or by_vowel.get(_devowel(q), ""))
    return out


def _spell_brute(wordlist: list[str], queries: list[str]) -> list[str]:
    out = []
    for q in queries:
        match = next((w for w in wordlist if w == q), None)
        match = match or next((w for w in wordlist if w.lower() == q.lower()), None)
        match = match or next((w for w in wordlist if _devowel(w) == _devowel(q)), None)
        out.append(match or "")
    return out


def _spell_gen(rng: random.Random) -> list:
    wordlist = [word(rng, rng.randint(1, 4), "kaEtoI") for _ in range(rng.randint(1, 10))]
    queries = []
    for _ in range(rng.randint(1, 12)):
        base = rng.choice(wordlist)
        roll = rng.random()
        if roll < 0.25:
            queries.append(base)
        elif roll < 0.5:
            queries.append("".join(c.swapcase() if rng.random() < 0.5 else c for c in base))
        elif roll < 0.75:
            queries.append("".join(rng.choice("aeiouAE") if c.lower() in "aeiou" else c for c in base))
        else:
            queries.append(word(rng, rng.randint(1, 4), "kaEtoI"))
    return [wordlist, queries]


VOWEL_SPELLCHECKER = ProblemSource(
    title="Vowel Spellchecker",
    statement="""
For each query, return the correction from `wordlist` using these rules, in priority order:

1. an exact (case-sensitive) match returns the query itself;
2. otherwise, the **first** word in `wordlist` equal to the query ignoring case;
3. otherwise, the **first** word equal to the query ignoring case after replacing every vowel (`a, e, i, o, u`) with any vowel;
4. otherwise `""`.
""",
    constraints="""
- `1 <= wordlist.length, queries.length <= 5000`
- `1 <= word length <= 7`, English letters only
""",
    signature=function("spellchecker", [("wordlist", "string[]"), ("queries", "string[]")], "string[]"),
    reference=_spellchecker,
    brute=_spell_brute,
    examples=[
        Example([["KiTe", "kite", "hare", "Hare"], ["kite", "Kite", "KiTe", "Hare", "HARE", "Hear", "hear", "keti", "keet", "keto"]]),
        Example([["yellow"], ["YellOw"]]),
    ],
    edge_cases=[[["a"], ["A", "e", "b"]], [["ae", "AE"], ["ea", "AE"]]],
    generator=_spell_gen,
    random_count=8,
)


# ---------------------------------------------------------------- N-Repeated Element in Size 2N Array


def _repeated_n_times(nums: list[int]) -> int:
    seen: set[int] = set()
    for x in nums:
        if x in seen:
            return x
        seen.add(x)
    raise ValueError("no repeated element")


def _n_repeated_gen(rng: random.Random) -> list:
    n = pick_n(rng, 2, 10, big=5000)
    values = sample(rng, range(10**4 + 1), n)
    nums = [values[0]] * n + values[1:]
    rng.shuffle(nums)
    return [nums]


N_REPEATED = ProblemSource(
    title="N-Repeated Element in Size 2N Array",
    statement="""
`nums` has length `2n` and contains `n + 1` distinct values, one of which appears exactly `n` times. Return that value.
""",
    constraints="""
- `2 <= n <= 5000`
- `0 <= nums[i] <= 10^4`
""",
    signature=function("repeatedNTimes", [("nums", "int[]")], "int"),
    reference=_repeated_n_times,
    brute=lambda nums: Counter(nums).most_common(1)[0][0],
    examples=[Example([[1, 2, 3, 3]]), Example([[2, 1, 2, 5, 3, 2]]), Example([[5, 1, 5, 2, 5, 3, 5, 4]])],
    edge_cases=[[[9, 5, 6, 9]], [[0, 0, 1, 2]]],
    generator=_n_repeated_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Powerful Integers


def _powerful_integers(x: int, y: int, bound: int) -> list[int]:
    def powers(base: int) -> list[int]:
        out, p = [], 1
        while p <= bound:
            out.append(p)
            if base == 1:
                break
            p *= base
        return out

    return sorted({a + b for a in powers(x) for b in powers(y) if a + b <= bound})


def _powerful_brute(x: int, y: int, bound: int) -> list[int]:
    if bound > 2000:
        return NotImplemented
    return [v for v in range(bound + 1) if any(v - x**i >= 1 and _is_power(v - x**i, y) for i in range(12) if x**i <= v)]


def _is_power(value: int, base: int) -> bool:
    if base == 1:
        return value == 1
    while value % base == 0:
        value //= base
    return value == 1


POWERFUL_INTEGERS = ProblemSource(
    title="Powerful Integers",
    statement="""
An integer is *powerful* if it equals `x^i + y^j` for some integers `i >= 0` and `j >= 0`. Return every powerful integer less than or equal to
`bound`, each once, in any order.
""",
    constraints="""
- `1 <= x, y <= 100`
- `0 <= bound <= 10^6`
""",
    signature=function("powerfulIntegers", [("x", "int"), ("y", "int"), ("bound", "int")], "int[]"),
    reference=_powerful_integers,
    brute=_powerful_brute,
    compare="unordered",
    examples=[Example([2, 3, 10], "2, 3, 4, 5, 7, 9, 10."), Example([3, 5, 15])],
    edge_cases=[[1, 1, 0], [1, 1, 2], [1, 2, 100], [100, 100, 1000000]],
    generator=lambda rng: [rng.randint(1, rng.choice([5, 100])), rng.randint(1, rng.choice([5, 100])), rng.randint(0, rng.choice([2000, 10**6]))],
    random_count=8,
)


# ---------------------------------------------------------------- Before and After Puzzle


def _before_and_after_puzzles(phrases: list[str]) -> list[str]:
    by_first: dict[str, list[int]] = {}
    for i, p in enumerate(phrases):
        by_first.setdefault(p.split(" ")[0], []).append(i)
    out = set()
    for i, p in enumerate(phrases):
        last = p.split(" ")[-1]
        for j in by_first.get(last, []):
            if j != i:
                out.add(p + phrases[j][len(last) :])
    return sorted(out)


def _puzzles_brute(phrases: list[str]) -> list[str]:
    out = set()
    for i, j in itertools.permutations(range(len(phrases)), 2):
        a, b = phrases[i].split(" "), phrases[j].split(" ")
        if a[-1] == b[0]:
            out.add(" ".join(a + b[1:]))
    return sorted(out)


def _phrases_gen(rng: random.Random) -> list:
    vocab = [word(rng, rng.randint(1, 3), "ab") for _ in range(rng.randint(2, 5))]
    return [[" ".join(rng.choice(vocab) for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(1, 10))]]


BEFORE_AFTER = ProblemSource(
    title="Before and After Puzzle",
    statement="""
Each phrase is lowercase words separated by single spaces. A *before and after puzzle* joins two phrases `phrases[i]` and `phrases[j]` (with
`i != j`) whose last word of the first equals the first word of the second, writing the shared word once. Return all distinct puzzles in
lexicographical order.
""",
    constraints="""
- `1 <= phrases.length <= 100`, `1 <= phrases[i].length <= 100`
- no leading, trailing or consecutive spaces
""",
    signature=function("beforeAndAfterPuzzles", [("phrases", "string[]")], "string[]"),
    reference=_before_and_after_puzzles,
    brute=_puzzles_brute,
    examples=[
        Example([["writing code", "code rocks"]], "\"writing code rocks\"."),
        Example([["a", "b", "a"]], "The two \"a\" phrases join into \"a\"."),
    ],
    edge_cases=[[["x"]], [["x y", "y x"]]],
    generator=_phrases_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Intersection of Two Arrays II


def _intersect(nums1: list[int], nums2: list[int]) -> list[int]:
    return sorted((Counter(nums1) & Counter(nums2)).elements())


def _intersect_brute(nums1: list[int], nums2: list[int]) -> list[int]:
    remaining = list(nums2)
    out = []
    for x in nums1:
        if x in remaining:
            remaining.remove(x)
            out.append(x)
    return out


INTERSECTION_II = ProblemSource(
    title="Intersection of Two Arrays II",
    statement="""
Return the intersection of `nums1` and `nums2` counting multiplicity: each value appears as many times as it appears in **both** arrays (the
smaller count). The result may be in any order.
""",
    constraints="""
- `1 <= nums1.length, nums2.length <= 1000`
- `0 <= nums1[i], nums2[i] <= 1000`
""",
    signature=function("intersect", [("nums1", "int[]"), ("nums2", "int[]")], "int[]"),
    reference=_intersect,
    brute=_intersect_brute,
    compare="unordered",
    examples=[Example([[1, 2, 2, 1], [2, 2]]), Example([[4, 9, 5], [9, 4, 9, 8, 4]])],
    edge_cases=[[[1], [2]], [[3, 3, 3], [3, 3]]],
    generator=lambda rng: [ints(rng, rng.randint(1, 20), 0, (hi := rng.choice([6, 1000]))), ints(rng, rng.randint(1, 20), 0, hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Subarray Sum Equals K


def _subarray_sum(nums: list[int], k: int) -> int:
    seen = Counter({0: 1})
    total = count = 0
    for x in nums:
        total += x
        count += seen[total - k]
        seen[total] += 1
    return count


def _subarray_sum_brute(nums: list[int], k: int) -> int:
    n = len(nums)
    if n > 300:
        return NotImplemented
    return sum(1 for i in range(n) for j in range(i + 1, n + 1) if sum(nums[i:j]) == k)


SUBARRAY_SUM_K = ProblemSource(
    title="Subarray Sum Equals K",
    statement="""
Return the number of non-empty contiguous subarrays of `nums` whose sum equals `k`.
""",
    constraints="""
- `1 <= nums.length <= 2 * 10^4`
- `-1000 <= nums[i] <= 1000`, `-10^7 <= k <= 10^7`
""",
    signature=function("subarraySum", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_subarray_sum,
    brute=_subarray_sum_brute,
    examples=[Example([[1, 1, 1], 2]), Example([[1, 2, 3], 3], "[1,2] and [3].")],
    edge_cases=[[[0], 0], [[0, 0, 0], 0], [[-1, 1], 0], [[5], 3]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=5000), -rng.choice([3, 1000]), rng.choice([3, 1000])), rng.randint(-5, 5)],
    random_count=8,
)


# ---------------------------------------------------------------- Identify the Largest Outlier in an Array


def _get_largest_outlier(nums: list[int]) -> int:
    total = sum(nums)
    counts = Counter(nums)
    best = None
    for x in counts:  # x is the outlier candidate: the rest sums to 2 * (special sum)
        rest = total - x
        if rest % 2:
            continue
        special_sum = rest // 2
        needed = counts[special_sum] - (1 if special_sum == x else 0)
        if needed >= 1 and (best is None or x > best):
            best = x
    return best  # type: ignore[return-value]


def _outlier_brute(nums: list[int]) -> int:
    n = len(nums)
    if n > 150:
        return NotImplemented
    total = sum(nums)
    return max(nums[o] for s in range(n) for o in range(n) if s != o and total - nums[s] - nums[o] == nums[s])


def _outlier_gen(rng: random.Random) -> list:
    special = ints(rng, rng.randint(1, rng.choice([6, 300])), -(hi := rng.choice([5, 1000])), hi)
    nums = special + [sum(special), rng.randint(-hi, hi)]
    rng.shuffle(nums)
    return [nums]


LARGEST_OUTLIER = ProblemSource(
    title="Identify the Largest Outlier in an Array",
    statement="""
In `nums`, exactly `n - 2` elements are *special numbers*; of the remaining two, one is the **sum** of all special numbers and the other is an
*outlier* (neither special nor the sum). Elements are identified by index, but values may repeat. Return the largest value that could be the
outlier under some valid choice. A valid choice is guaranteed to exist.
""",
    constraints="""
- `3 <= nums.length <= 10^5`
- `-1000 <= nums[i] <= 1000`
""",
    signature=function("getLargestOutlier", [("nums", "int[]")], "int"),
    reference=_get_largest_outlier,
    brute=_outlier_brute,
    examples=[Example([[2, 3, 5, 10]], "2 + 3 = 5, so 10 is the outlier."), Example([[-2, -1, -3, -6, 4]]), Example([[1, 1, 1, 1, 1, 5, 5]])],
    edge_cases=[[[0, 0, 7]], [[1, 1, 1]], [[6, -2, -2, 4]]],
    generator=_outlier_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find the Length of the Longest Common Prefix


def _longest_common_prefix(arr1: list[int], arr2: list[int]) -> int:
    prefixes = {str(x)[:k] for x in arr1 for k in range(1, len(str(x)) + 1)}
    best = 0
    for y in arr2:
        text = str(y)
        for k in range(len(text), best, -1):
            if text[:k] in prefixes:
                best = k
                break
    return best


def _common_prefix_brute(arr1: list[int], arr2: list[int]) -> int:
    def common(a: str, b: str) -> int:
        k = 0
        while k < min(len(a), len(b)) and a[k] == b[k]:
            k += 1
        return k

    return max(common(str(x), str(y)) for x in arr1 for y in arr2)


INTEGER_PREFIX = ProblemSource(
    title="Find the Length of the Longest Common Prefix",
    statement="""
A *prefix* of a positive integer is formed by one or more of its leading digits. Over all pairs `x` from `arr1` and `y` from `arr2`, return the
length of the longest common prefix of `x` and `y`, or `0` if no pair shares a first digit.
""",
    constraints="""
- `1 <= arr1.length, arr2.length <= 5 * 10^4`
- `1 <= arr1[i], arr2[i] <= 10^8`
""",
    signature=function("longestCommonPrefix", [("arr1", "int[]"), ("arr2", "int[]")], "int"),
    reference=_longest_common_prefix,
    brute=lambda arr1, arr2: _common_prefix_brute(arr1, arr2) if len(arr1) * len(arr2) <= 20000 else NotImplemented,
    examples=[Example([[1, 10, 100], [1000]], "100 and 1000 share \"100\"."), Example([[1, 2, 3], [4, 4, 4]])],
    edge_cases=[[[5], [5]], [[100000000], [100000000]], [[12], [21]]],
    generator=lambda rng: [ints(rng, rng.randint(1, 30), 1, (hi := rng.choice([300, 10**8]))), ints(rng, rng.randint(1, 30), 1, hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Subarray Sums Divisible by K


def _subarrays_div_by_k(nums: list[int], k: int) -> int:
    seen = Counter({0: 1})
    total = count = 0
    for x in nums:
        total = (total + x) % k
        count += seen[total]
        seen[total] += 1
    return count


SUMS_DIVISIBLE_K = ProblemSource(
    title="Subarray Sums Divisible by K",
    statement="""
Return the number of non-empty contiguous subarrays of `nums` whose sum is divisible by `k`.
""",
    constraints="""
- `1 <= nums.length <= 3 * 10^4`
- `-10^4 <= nums[i] <= 10^4`, `2 <= k <= 10^4`
""",
    signature=function("subarraysDivByK", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_subarrays_div_by_k,
    brute=lambda nums, k: sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums) + 1) if sum(nums[i:j]) % k == 0) if len(nums) <= 200 else NotImplemented,
    examples=[Example([[4, 5, 0, -2, -3, 1], 5]), Example([[5], 9])],
    edge_cases=[[[0], 2], [[-1, 1], 2], [[-5], 5]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=5000), -rng.choice([10, 10**4]), rng.choice([10, 10**4])), rng.randint(2, rng.choice([6, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Black Blocks


def _count_black_blocks(m: int, n: int, coordinates: list[list[int]]) -> list[int]:
    blocks: Counter[tuple[int, int]] = Counter()
    for x, y in coordinates:
        for i in (x - 1, x):  # the up to four 2x2 blocks (by top-left corner) containing the cell
            for j in (y - 1, y):
                if 0 <= i < m - 1 and 0 <= j < n - 1:
                    blocks[(i, j)] += 1
    out = [0] * 5
    for count in blocks.values():
        out[count] += 1
    out[0] = (m - 1) * (n - 1) - len(blocks)
    return out


def _black_blocks_brute(m: int, n: int, coordinates: list[list[int]]) -> list[int]:
    if m * n > 5000:
        return NotImplemented
    black = {tuple(c) for c in coordinates}
    out = [0] * 5
    for i in range(m - 1):
        for j in range(n - 1):
            out[sum((a, b) in black for a in (i, i + 1) for b in (j, j + 1))] += 1
    return out


def _black_gen(rng: random.Random) -> list:
    m, n = rng.randint(2, rng.choice([8, 10**5])), rng.randint(2, rng.choice([8, 10**5]))
    count = min(m * n, rng.randint(0, rng.choice([10, 300])))
    cells = {(rng.randrange(m), rng.randrange(n)) for _ in range(count)}
    if m <= 8 and n <= 8:
        cells |= {(x + 1, y) for x, y in list(cells) if x + 1 < m and rng.random() < 0.5}
    return [m, n, [list(c) for c in sorted(cells)]]


BLACK_BLOCKS = ProblemSource(
    title="Number of Black Blocks",
    statement="""
An `m x n` grid is white except for the cells listed in `coordinates` (distinct `[x, y]` pairs), which are black. A *block* is any `2 x 2`
square of cells inside the grid. Return an array `arr` of length 5 where `arr[i]` is the number of blocks containing exactly `i` black cells.
Counts can exceed 32 bits.
""",
    constraints="""
- `2 <= m, n <= 10^5`
- `0 <= coordinates.length <= 10^4`, coordinates distinct and inside the grid
""",
    signature=function("countBlackBlocks", [("m", "int"), ("n", "int"), ("coordinates", "int[][]")], "long[]"),
    reference=_count_black_blocks,
    brute=_black_blocks_brute,
    examples=[Example([3, 3, [[0, 0]]], "Only the top-left block touches the black cell."), Example([3, 3, [[0, 0], [1, 1], [0, 2]]])],
    edge_cases=[[2, 2, []], [2, 2, [[0, 0], [0, 1], [1, 0], [1, 1]]], [100000, 100000, []]],
    generator=_black_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Reordered Power of 2


def _reordered_power_of_2(n: int) -> bool:
    key = sorted(str(n))
    return any(sorted(str(1 << k)) == key for k in range(31))


def _power_brute(n: int) -> bool:
    digits = str(n)
    if len(digits) > 7:
        return NotImplemented
    return any(p[0] != "0" and (v := int("".join(p))) & (v - 1) == 0 for p in itertools.permutations(digits))


REORDERED_POWER_2 = ProblemSource(
    title="Reordered Power of 2",
    statement="""
You may reorder the digits of `n` in any order, as long as the leading digit is not zero. Return `true` if some reordering is a power of two.
""",
    constraints="""
- `1 <= n <= 10^9`
""",
    signature=function("reorderedPowerOf2", [("n", "int")], "bool"),
    reference=_reordered_power_of_2,
    brute=_power_brute,
    examples=[Example([1]), Example([10], "\"01\" isn't allowed."), Example([46], "64 = 2^6.")],
    edge_cases=[[821], [1000000000], [536870912], [2048]],
    generator=lambda rng: [int("".join(sample(rng, list(str(1 << rng.randint(0, 29))), 30)).lstrip("0") or "1") if rng.random() < 0.5 else rng.randint(1, rng.choice([10**4, 10**9]))],
    random_count=10,
)


PROBLEMS = [
    INTERSECTION,
    WORD_PATTERN,
    VALID_SUDOKU,
    ROMAN_TO_INTEGER,
    CONTIGUOUS_ARRAY,
    JEWELS_AND_STONES,
    VOWEL_SPELLCHECKER,
    N_REPEATED,
    POWERFUL_INTEGERS,
    BEFORE_AFTER,
    INTERSECTION_II,
    SUBARRAY_SUM_K,
    LARGEST_OUTLIER,
    INTEGER_PREFIX,
    SUMS_DIVISIBLE_K,
    BLACK_BLOCKS,
    REORDERED_POWER_2,
]
