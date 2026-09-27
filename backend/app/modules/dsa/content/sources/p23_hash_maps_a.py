"""Pattern 23: Hash Maps (part 1 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import random
import re
from collections import Counter, defaultdict
from fractions import Fraction

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ints, ops, pick_n, sample, word

PATTERN_NUMBER = 23


# ---------------------------------------------------------------- Design HashMap


class _MyHashMap:
    """Separate chaining over a fixed number of buckets."""

    def __init__(self) -> None:
        self.buckets: list[list[list[int]]] = [[] for _ in range(1009)]

    def _bucket(self, key: int) -> list[list[int]]:
        return self.buckets[key % len(self.buckets)]

    def put(self, key: int, value: int) -> None:
        bucket = self._bucket(key)
        for pair in bucket:
            if pair[0] == key:
                pair[1] = value
                return
        bucket.append([key, value])

    def get(self, key: int) -> int:
        return next((v for k, v in self._bucket(key) if k == key), -1)

    def remove(self, key: int) -> None:
        bucket = self._bucket(key)
        bucket[:] = [pair for pair in bucket if pair[0] != key]


class _MyHashMapBrute:
    def __init__(self) -> None:
        self.data: dict[int, int] = {}

    def put(self, key: int, value: int) -> None:
        self.data[key] = value

    def get(self, key: int) -> int:
        return self.data.get(key, -1)

    def remove(self, key: int) -> None:
        self.data.pop(key, None)


def _hashmap_gen(rng: random.Random) -> dict:
    keys = sample(rng, range(10**6 + 1), rng.randint(1, 8)) + [0, 1009, 2018]
    calls: list[tuple[str, list]] = [("MyHashMap", [])]
    for _ in range(pick_n(rng, 1, 25, big=500)):
        op = rng.choice(["put", "put", "get", "get", "remove"])
        key = rng.choice(keys)
        calls.append((op, [key, rng.randint(0, 10**6)] if op == "put" else [key]))
    return ops(*calls)


DESIGN_HASHMAP = ProblemSource(
    title="Design HashMap",
    statement="""
Design a hash map without using any built-in hash table library:
- `put(key, value)` inserts the pair, or updates the value if `key` is already present.
- `get(key)` returns the value mapped to `key`, or `-1` if there is none.
- `remove(key)` removes `key` and its value if present.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor,
`put` and `remove`).
""",
    constraints="""
- `0 <= key, value <= 10^6`
- at most `10^4` calls
""",
    signature=design("MyHashMap", [], [("put", [("key", "int"), ("value", "int")], "void"), ("get", [("key", "int")], "int"), ("remove", [("key", "int")], "void")]),
    reference=_MyHashMap,
    brute=_MyHashMapBrute,
    examples=[
        Example(ops(("MyHashMap", []), ("put", [1, 1]), ("put", [2, 2]), ("get", [1]), ("get", [3]), ("put", [2, 1]), ("get", [2]), ("remove", [2]), ("get", [2]))),
        Example(ops(("MyHashMap", []), ("put", [0, 7]), ("put", [1009, 8]), ("get", [0]), ("get", [1009])), "Keys that collide must still be kept apart."),
    ],
    edge_cases=[ops(("MyHashMap", []), ("remove", [5]), ("get", [5]), ("put", [5, 0]), ("get", [5]))],
    generator=_hashmap_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Fraction to Recurring Decimal


def _fraction_to_decimal(numerator: int, denominator: int) -> str:
    if numerator == 0:
        return "0"
    sign = "-" if (numerator < 0) != (denominator < 0) else ""
    n, d = abs(numerator), abs(denominator)
    whole, remainder = divmod(n, d)
    if remainder == 0:
        return f"{sign}{whole}"
    digits: list[str] = []
    seen: dict[int, int] = {}
    while remainder and remainder not in seen:
        seen[remainder] = len(digits)
        digit, remainder = divmod(remainder * 10, d)
        digits.append(str(digit))
    if remainder:
        start = seen[remainder]
        return f"{sign}{whole}.{''.join(digits[:start])}({''.join(digits[start:])})"
    return f"{sign}{whole}.{''.join(digits)}"


def _fraction_brute(numerator: int, denominator: int) -> str:
    """Split the denominator into its 2/5 part (the terminating prefix) and the rest (the repeating period)."""
    value = Fraction(numerator, denominator)
    if value.denominator == 1:
        return str(value.numerator)
    sign = "-" if value < 0 else ""
    n, d = abs(value.numerator), value.denominator
    rest = d
    twos = fives = 0
    while rest % 2 == 0:
        rest, twos = rest // 2, twos + 1
    while rest % 5 == 0:
        rest, fives = rest // 5, fives + 1
    prefix_len = max(twos, fives)
    period = 0
    if rest > 1:
        period, power = 1, 10 % rest
        while power != 1:
            power, period = power * 10 % rest, period + 1
    scaled = n * 10 ** (prefix_len + period) // d
    digits = str(scaled)[-(prefix_len + period) :].rjust(prefix_len + period, "0") if prefix_len + period else ""
    whole = n // d
    head, tail = digits[:prefix_len], digits[prefix_len:]
    return f"{sign}{whole}.{head}({tail})" if period else f"{sign}{whole}.{head}"


FRACTION_TO_DECIMAL = ProblemSource(
    title="Fraction to Recurring Decimal",
    statement="""
Return the fraction `numerator / denominator` as a decimal string. If the fractional part repeats, enclose the repeating block in parentheses
(for example `1/3` is `"0.(3)"` and `1/6` is `"0.1(6)"`). Use the shortest repeating block, starting as early as possible.
""",
    constraints="""
- `-2^31 <= numerator, denominator <= 2^31 - 1`, `denominator != 0`
- the answer is shorter than `10^4` characters
""",
    signature=function("fractionToDecimal", [("numerator", "int"), ("denominator", "int")], "string"),
    reference=_fraction_to_decimal,
    brute=_fraction_brute,
    examples=[Example([1, 2]), Example([2, 1]), Example([4, 333], "\"0.(012)\".")],
    edge_cases=[[0, -5], [-1, 6], [1, -7], [-2147483648, -1], [-2147483648, 1], [22, 7]],
    generator=lambda rng: [rng.randint(-rng.choice([50, 2**31]), rng.choice([50, 2**31 - 1])), rng.choice([-1, 1]) * rng.randint(1, rng.choice([30, 997]))],
    random_count=10,
)


# ---------------------------------------------------------------- Logger Rate Limiter


class _Logger:
    def __init__(self) -> None:
        self.next_allowed: dict[str, int] = {}

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:  # noqa: N802 - judge method name
        if timestamp < self.next_allowed.get(message, 0):
            return False
        self.next_allowed[message] = timestamp + 10
        return True


class _LoggerBrute:
    def __init__(self) -> None:
        self.printed: list[tuple[int, str]] = []

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:  # noqa: N802
        if any(m == message and timestamp - t < 10 for t, m in self.printed):
            return False
        self.printed.append((timestamp, message))
        return True


def _logger_gen(rng: random.Random) -> dict:
    messages = [word(rng, rng.randint(1, 3), "ab") for _ in range(rng.randint(1, 4))]
    calls: list[tuple[str, list]] = [("Logger", [])]
    t = 0
    for _ in range(pick_n(rng, 1, 20, big=300)):
        t += rng.choice([0, 1, 2, 5, 9, 10, 11])
        calls.append(("shouldPrintMessage", [t, rng.choice(messages)]))
    return ops(*calls)


LOGGER = ProblemSource(
    title="Logger Rate Limiter",
    statement="""
Design a logger that receives messages with timestamps (in seconds, non-decreasing). Each unique message may be printed at most once every 10
seconds: if a message is printed at time `t`, the same message is suppressed until time `t + 10`.

- `shouldPrintMessage(timestamp, message)` returns `true` if the message should be printed at `timestamp` (and records that it was printed),
  otherwise `false`.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor).
""",
    constraints="""
- `0 <= timestamp <= 10^9`, non-decreasing across calls
- `1 <= message.length <= 30`; at most `10^4` calls
""",
    signature=design("Logger", [], [("shouldPrintMessage", [("timestamp", "int"), ("message", "string")], "bool")]),
    reference=_Logger,
    brute=_LoggerBrute,
    examples=[
        Example(ops(("Logger", []), ("shouldPrintMessage", [1, "foo"]), ("shouldPrintMessage", [2, "bar"]), ("shouldPrintMessage", [3, "foo"]), ("shouldPrintMessage", [8, "bar"]), ("shouldPrintMessage", [10, "foo"]), ("shouldPrintMessage", [11, "foo"])), "\"foo\" is allowed again from time 11."),
        Example(ops(("Logger", []), ("shouldPrintMessage", [0, "a"]), ("shouldPrintMessage", [0, "a"]))),
    ],
    edge_cases=[ops(("Logger", []), ("shouldPrintMessage", [5, "x"]), ("shouldPrintMessage", [15, "x"]), ("shouldPrintMessage", [24, "x"]))],
    generator=_logger_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Next Greater Element I


def _next_greater_element(nums1: list[int], nums2: list[int]) -> list[int]:
    greater: dict[int, int] = {}
    stack: list[int] = []
    for x in nums2:
        while stack and stack[-1] < x:
            greater[stack.pop()] = x
        stack.append(x)
    return [greater.get(x, -1) for x in nums1]


def _next_greater_brute(nums1: list[int], nums2: list[int]) -> list[int]:
    return [next((y for y in nums2[nums2.index(x) + 1 :] if y > x), -1) for x in nums1]


def _next_greater_gen(rng: random.Random) -> list:
    nums2 = sample(rng, range(rng.choice([30, 10**4]) + 1), pick_n(rng, 1, 15, big=1000))
    return [sample(rng, nums2, rng.randint(1, len(nums2))), nums2]


NEXT_GREATER_I = ProblemSource(
    title="Next Greater Element I",
    statement="""
`nums2` holds distinct integers and `nums1` is a subset of them. For each `x` in `nums1`, find `x` in `nums2` and return the first element to its
right that is greater than `x`, or `-1` if there is none.
""",
    constraints="""
- `1 <= nums1.length <= nums2.length <= 1000`
- `0 <= values <= 10^4`, all distinct within each array; every `nums1[i]` is in `nums2`
""",
    signature=function("nextGreaterElement", [("nums1", "int[]"), ("nums2", "int[]")], "int[]"),
    reference=_next_greater_element,
    brute=_next_greater_brute,
    examples=[Example([[4, 1, 2], [1, 3, 4, 2]], "[-1,3,-1]."), Example([[2, 4], [1, 2, 3, 4]])],
    edge_cases=[[[5], [5]], [[1, 2], [2, 1]], [[3], [3, 2, 1, 4]]],
    generator=_next_greater_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Isomorphic Strings


def _is_isomorphic(s: str, t: str) -> bool:
    forward: dict[str, str] = {}
    backward: dict[str, str] = {}
    for a, b in zip(s, t, strict=True):
        if forward.setdefault(a, b) != b:
            return False
        if backward.setdefault(b, a) != a:
            return False
    return True


def _isomorphic_brute(s: str, t: str) -> bool:
    return [s.index(c) for c in s] == [t.index(c) for c in t]


def _isomorphic_gen(rng: random.Random) -> list:
    s = word(rng, rng.randint(1, rng.choice([8, 200])), "abcd")
    letters = sample(rng, list("wxyzab"), 4)
    t = "".join(letters["abcd".index(c)] for c in s)
    if rng.random() < 0.5:
        i = rng.randrange(len(t))
        t = t[:i] + rng.choice("wxyzab") + t[i + 1 :]
    return [s, t]


ISOMORPHIC_STRINGS = ProblemSource(
    title="Isomorphic Strings",
    statement="""
Two strings are *isomorphic* if the characters of `s` can be replaced to get `t`: every occurrence of a character is replaced by the same
character, and no two different characters map to the same character (a character may map to itself). Return `true` if `s` and `t` are
isomorphic.
""",
    constraints="""
- `1 <= s.length == t.length <= 5 * 10^4`
- `s` and `t` consist of printable ASCII characters
""",
    signature=function("isIsomorphic", [("s", "string"), ("t", "string")], "bool"),
    reference=_is_isomorphic,
    brute=_isomorphic_brute,
    brute_input_limit=3000,
    examples=[Example(["egg", "add"]), Example(["foo", "bar"], "'o' would have to map to both 'a' and 'r'."), Example(["paper", "title"])],
    edge_cases=[["a", "a"], ["ab", "aa"], ["badc", "baba"]],
    generator=_isomorphic_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find Duplicate File in System


def _find_duplicate(paths: list[str]) -> list[list[str]]:
    by_content: dict[str, list[str]] = defaultdict(list)
    for entry in paths:
        directory, *files = entry.split(" ")
        for f in files:
            name, content = f[:-1].split("(")
            by_content[content].append(f"{directory}/{name}")
    return [group for group in by_content.values() if len(group) > 1]


def _duplicate_brute(paths: list[str]) -> list[list[str]]:
    files = [(f"{d}/{name}", content) for entry in paths for d in [entry.split(" ")[0]] for name, content in re.findall(r"(\S+?)\((\S*?)\)", entry)]
    contents = sorted({c for _, c in files})
    groups = [[path for path, c in files if c == content] for content in contents]
    return [g for g in groups if len(g) > 1]


def _duplicate_files_gen(rng: random.Random) -> list:
    contents = [word(rng, rng.randint(1, 4), "abcd") for _ in range(rng.randint(1, 5))]
    paths = []
    for d in range(rng.randint(1, 6)):
        directory = "root" + "".join(f"/{word(rng, 1, 'xyz')}{d}" for _ in range(rng.randint(0, 2)))
        files = [f"f{d}_{i}.txt({rng.choice(contents)})" for i in range(rng.randint(1, 4))]
        paths.append(" ".join([directory, *files]))
    return [paths]


DUPLICATE_FILES = ProblemSource(
    title="Find Duplicate File in System",
    statement="""
Each entry of `paths` describes one directory: `"dir f1.txt(content1) f2.txt(content2) ..."` (names and contents contain no spaces or
parentheses, and every file path in the system is unique). Return every group of two or more files that have identical content, each file
written as its full path `"dir/name"`. Groups, and the files within a group, may be in any order.
""",
    constraints="""
- `1 <= paths.length <= 2 * 10^4`, total length `<= 5 * 10^5`
- every directory holds at least one file
""",
    signature=function("findDuplicate", [("paths", "string[]")], "string[][]"),
    reference=_find_duplicate,
    brute=_duplicate_brute,
    compare="unordered_nested",
    examples=[
        Example([["root/a 1.txt(abcd) 2.txt(efgh)", "root/c 3.txt(abcd)", "root/c/d 4.txt(efgh)", "root 4.txt(efgh)"]], "Contents abcd and efgh are each shared."),
        Example([["root/a 1.txt(abcd)", "root/b 2.txt(xyz)"]], "No duplicates."),
    ],
    edge_cases=[[["root x.txt(a) y.txt(a)"]], [["r 1.txt(q)"]]],
    generator=_duplicate_files_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Longest Palindrome


def _longest_palindrome(s: str) -> int:
    odd = sum(count % 2 for count in Counter(s).values())
    return len(s) - odd + (1 if odd else 0)


def _longest_palindrome_brute(s: str) -> int:
    pairs = sum(c // 2 for c in Counter(s).values())
    return 2 * pairs + (1 if 2 * pairs < len(s) else 0)


LONGEST_PALINDROME = ProblemSource(
    title="Longest Palindrome",
    statement="""
Return the length of the longest palindrome that can be built from the letters of `s`, using each letter at most as many times as it occurs.
Letters are case-sensitive (`"Aa"` is not a palindrome).
""",
    constraints="""
- `1 <= s.length <= 2000`
- lowercase and uppercase English letters
""",
    signature=function("longestPalindrome", [("s", "string")], "int"),
    reference=_longest_palindrome,
    brute=_longest_palindrome_brute,
    examples=[Example(["abccccdd"], "\"dccaccd\"."), Example(["a"])],
    edge_cases=[["Aa"], ["aaa"], ["abcdef"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([12, 2000])), rng.choice(["ab", "abcAB", "abcdefghijklmnopqrstuvwxyzABC"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Continuous Subarray Sum


def _check_subarray_sum(nums: list[int], k: int) -> bool:
    first_at = {0: -1}
    total = 0
    for i, x in enumerate(nums):
        total = (total + x) % k
        if total in first_at:
            if i - first_at[total] >= 2:
                return True
        else:
            first_at[total] = i
    return False


def _subarray_sum_brute(nums: list[int], k: int) -> bool:
    n = len(nums)
    if n > 200:
        return NotImplemented
    return any(sum(nums[i:j]) % k == 0 for i in range(n) for j in range(i + 2, n + 1))


CONTINUOUS_SUBARRAY_SUM = ProblemSource(
    title="Continuous Subarray Sum",
    statement="""
Return `true` if `nums` has a contiguous subarray of **length at least 2** whose sum is a multiple of `k` (`0` counts as a multiple of `k`).
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `0 <= nums[i] <= 10^9`, `sum(nums) <= 2^31 - 1`
- `1 <= k <= 2^31 - 1`
""",
    signature=function("checkSubarraySum", [("nums", "int[]"), ("k", "int")], "bool"),
    reference=_check_subarray_sum,
    brute=_subarray_sum_brute,
    examples=[Example([[23, 2, 4, 6, 7], 6], "[2, 4] sums to 6."), Example([[23, 2, 6, 4, 7], 6]), Example([[23, 2, 6, 4, 7], 13])],
    edge_cases=[[[0], 1], [[0, 0], 1], [[5, 0, 0, 0], 3], [[1, 2, 12], 6]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 12, big=3000), 0, rng.choice([10, 1000])), rng.randint(1, rng.choice([7, 40, 5000]))],
    random_count=10,
)


# ---------------------------------------------------------------- Unique Number of Occurrences


def _unique_occurrences(arr: list[int]) -> bool:
    counts = Counter(arr).values()
    return len(counts) == len(set(counts))


def _occurrences_gen(rng: random.Random) -> list:
    values = sample(rng, range(-1000, 1001), rng.randint(1, 6))
    arr = [v for i, v in enumerate(values) for _ in range(i + 1 + rng.choice([0, 0, 1]))]  # counts are often distinct
    rng.shuffle(arr)
    return [arr]


UNIQUE_OCCURRENCES = ProblemSource(
    title="Unique Number of Occurrences",
    statement="""
Return `true` if the number of occurrences of each distinct value in `arr` is different from that of every other value.
""",
    constraints="""
- `1 <= arr.length <= 1000`
- `-1000 <= arr[i] <= 1000`
""",
    signature=function("uniqueOccurrences", [("arr", "int[]")], "bool"),
    reference=_unique_occurrences,
    brute=lambda arr: all(arr.count(a) != arr.count(b) for a, b in itertools.combinations(set(arr), 2)),
    examples=[Example([[1, 2, 2, 1, 1, 3]], "Counts 3, 2 and 1 are all different."), Example([[1, 2]]), Example([[-3, 0, 1, -3, 1, 1, 1, -3, 10, 0]])],
    edge_cases=[[[7]], [[1, 1, 2, 2]]],
    generator=_occurrences_gen,
    random_count=8,
)


# ---------------------------------------------------------------- High Five


def _high_five(items: list[list[int]]) -> list[list[int]]:
    scores: dict[int, list[int]] = defaultdict(list)
    for student, score in items:
        scores[student].append(score)
    return [[student, sum(sorted(scores[student])[-5:]) // 5] for student in sorted(scores)]


def _high_five_gen(rng: random.Random) -> list:
    items = []
    for student in sample(rng, range(1, 1001), rng.randint(1, 6)):
        items += [[student, rng.randint(0, 100)] for _ in range(rng.randint(5, 9))]
    rng.shuffle(items)
    return [items]


HIGH_FIVE = ProblemSource(
    title="High Five",
    statement="""
`items[i] = [id, score]` is one test score of the student `id`; every student has at least five scores. For each student, compute the integer
average (sum divided by 5, rounded down) of their **top five** scores. Return `[id, average]` pairs sorted by `id`.
""",
    constraints="""
- `1 <= items.length <= 1000`
- `1 <= id <= 1000`, `0 <= score <= 100`
""",
    signature=function("highFive", [("items", "int[][]")], "int[][]"),
    reference=_high_five,
    brute=lambda items: [[i, sum(sorted((s for j, s in items if j == i), reverse=True)[:5]) // 5] for i in sorted({j for j, _ in items})],
    examples=[
        Example([[[1, 91], [1, 92], [2, 93], [2, 97], [1, 60], [2, 77], [1, 65], [1, 87], [1, 100], [2, 100], [2, 76]]], "Student 1: (100+92+91+87+65)/5 = 87."),
        Example([[[1, 100], [7, 100], [1, 100], [7, 100], [1, 100], [7, 100], [1, 100], [7, 100], [1, 100], [7, 100]]]),
    ],
    edge_cases=[[[[7, 100], [7, 100], [7, 100], [7, 100], [7, 99]]]],
    generator=_high_five_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Bulls and Cows


def _get_hint(secret: str, guess: str) -> str:
    bulls = sum(a == b for a, b in zip(secret, guess, strict=True))
    common = sum((Counter(secret) & Counter(guess)).values())
    return f"{bulls}A{common - bulls}B"


def _hint_brute(secret: str, guess: str) -> str:
    bulls = [i for i in range(len(secret)) if secret[i] == guess[i]]
    left = [secret[i] for i in range(len(secret)) if i not in bulls]
    cows = 0
    for i, ch in enumerate(guess):
        if i not in bulls and ch in left:
            left.remove(ch)
            cows += 1
    return f"{len(bulls)}A{cows}B"


BULLS_AND_COWS = ProblemSource(
    title="Bulls and Cows",
    statement="""
In Bulls and Cows, `secret` and `guess` are digit strings of equal length. *Bulls* are digits of `guess` in the right position. *Cows* are
digits of `guess` that appear in `secret` but in the wrong position, counting each secret digit at most once (bulls are matched first). Return
the hint `"xAyB"`, where `x` is the number of bulls and `y` the number of cows.
""",
    constraints="""
- `1 <= secret.length == guess.length <= 1000`
- only digits
""",
    signature=function("getHint", [("secret", "string"), ("guess", "string")], "string"),
    reference=_get_hint,
    brute=_hint_brute,
    brute_input_limit=1000,
    examples=[Example(["1807", "7810"], "One bull (8), three cows."), Example(["1123", "0111"], "\"1A1B\".")],
    edge_cases=[["1", "1"], ["1", "2"], ["11", "11"], ["1122", "2211"]],
    generator=lambda rng: [word(rng, (n := rng.randint(1, rng.choice([6, 300]))), (d := rng.choice(["0123", "0123456789"]))), word(rng, n, d)],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Wonderful Substrings


def _wonderful_substrings(word_: str) -> int:
    seen = Counter({0: 1})
    mask = count = 0
    for ch in word_:
        mask ^= 1 << (ord(ch) - ord("a"))
        count += seen[mask] + sum(seen[mask ^ (1 << b)] for b in range(10))
        seen[mask] += 1
    return count


def _wonderful_brute(word_: str) -> int:
    n = len(word_)
    if n > 200:
        return NotImplemented
    return sum(1 for i in range(n) for j in range(i + 1, n + 1) if sum(c % 2 for c in Counter(word_[i:j]).values()) <= 1)


WONDERFUL_SUBSTRINGS = ProblemSource(
    title="Number of Wonderful Substrings",
    statement="""
A string is *wonderful* if at most one letter appears in it an odd number of times. `word` uses only the letters `a` to `j`. Return how many
non-empty substrings of `word` are wonderful (equal substrings at different positions count separately).
""",
    constraints="""
- `1 <= word.length <= 10^5`
- letters `a` to `j`
""",
    signature=function("wonderfulSubstrings", [("word", "string")], "long"),
    reference=_wonderful_substrings,
    brute=_wonderful_brute,
    examples=[Example(["aba"], "a, b, a, aba."), Example(["aabb"]), Example(["he"])],
    edge_cases=[["a"], ["j"], ["aaaa"], ["abcdefghij"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 30, big=10**4), rng.choice(["ab", "abc", "abcdefghij"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Distinct Islands


def _num_distinct_islands(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    shapes: set[tuple[tuple[int, int], ...]] = set()
    for i in range(m):
        for j in range(n):
            if grid[i][j] and (i, j) not in seen:
                seen.add((i, j))
                stack, cells = [(i, j)], []
                while stack:
                    a, b = stack.pop()
                    cells.append((a - i, b - j))  # relative to the island's first cell in scan order
                    for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= c < m and 0 <= d < n and grid[c][d] and (c, d) not in seen:
                            seen.add((c, d))
                            stack.append((c, d))
                shapes.add(tuple(sorted(cells)))
    return len(shapes)


def _distinct_islands_brute(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    label: dict[tuple[int, int], int] = {}
    for i in range(m):
        for j in range(n):
            if grid[i][j] and (i, j) not in label:
                label[(i, j)] = len(set(label.values()))  # a fresh island id
                frontier = [(i, j)]
                while frontier:
                    a, b = frontier.pop()
                    for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= c < m and 0 <= d < n and grid[c][d] and (c, d) not in label:
                            label[(c, d)] = label[(i, j)]
                            frontier.append((c, d))
    islands: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for cell, k in label.items():
        islands[k].append(cell)
    shapes = set()
    for cells in islands.values():
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        shapes.add(frozenset((r - top, c - left) for r, c in cells))
    return len(shapes)


DISTINCT_ISLANDS = ProblemSource(
    title="Number of Distinct Islands",
    statement="""
In the binary grid, an *island* is a group of `1`s connected horizontally or vertically. Two islands are the same if one can be **translated**
(not rotated or reflected) to exactly cover the other. Return the number of distinct islands.
""",
    constraints="""
- `1 <= m, n <= 50`
- `grid[i][j]` is `0` or `1`
""",
    signature=function("numDistinctIslands", [("grid", "int[][]")], "int"),
    reference=_num_distinct_islands,
    brute=_distinct_islands_brute,
    examples=[Example([[[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 0, 1, 1], [0, 0, 0, 1, 1]]], "Two identical 2x2 squares."), Example([[[1, 1, 0, 1, 1], [1, 0, 0, 0, 0], [0, 0, 0, 0, 1], [1, 1, 0, 1, 1]]])],
    edge_cases=[[[[0]]], [[[1]]], [[[1, 0, 1]]], [[[1, 1], [0, 0], [0, 1], [0, 1]]]],
    generator=lambda rng: [[[int(rng.random() < 0.4) for _ in range(n)] for _ in range(m)] for m, n in [(pick_n(rng, 1, 8, big=50), pick_n(rng, 1, 8, big=50))]],
    random_count=8,
)


# ---------------------------------------------------------------- Custom Sort String


def _custom_sort_string(order: str, s: str) -> str:
    counts = Counter(s)
    head = "".join(ch * counts.pop(ch, 0) for ch in order)
    return head + "".join(ch * n for ch, n in counts.items())


def _custom_sort_brute(order: str, s: str) -> str:
    return "".join(sorted(s, key=lambda ch: order.find(ch) if ch in order else len(order)))


CUSTOM_SORT_STRING = ProblemSource(
    title="Custom Sort String",
    statement="""
`order` lists distinct letters in a custom order. Rearrange `s` so that, for any two letters that both appear in `order`, the one earlier in
`order` comes first. Letters not in `order` may go anywhere. Return any valid arrangement.
""",
    constraints="""
- `1 <= order.length <= 26`, distinct letters
- `1 <= s.length <= 200`, lowercase letters
""",
    signature=function("customSortString", [("order", "string"), ("s", "string")], "string"),
    reference=_custom_sort_string,
    brute=_custom_sort_brute,
    compare="checker",
    checker="custom_sort",
    examples=[Example(["cba", "abcd"], "\"cbad\"; \"dcba\" or \"cdba\" are also accepted."), Example(["bcafg", "abcd"])],
    edge_cases=[["a", "a"], ["a", "b"], ["zyx", "xxyyzz"]],
    generator=lambda rng: ["".join(sample(rng, list("abcdefgh"), rng.randint(1, 8))), word(rng, rng.randint(1, rng.choice([10, 200])), "abcdefghij")],
    random_count=8,
)


# ---------------------------------------------------------------- Total Appeal of a String


def _appeal_sum(s: str) -> int:
    last: dict[str, int] = {}
    total = 0
    for i, ch in enumerate(s):
        # ch contributes to every substring starting after its previous occurrence and ending at or after i
        total += (i - last.get(ch, -1)) * (len(s) - i)
        last[ch] = i
    return total


def _appeal_brute(s: str) -> int:
    n = len(s)
    if n > 200:
        return NotImplemented
    return sum(len(set(s[i:j])) for i in range(n) for j in range(i + 1, n + 1))


TOTAL_APPEAL = ProblemSource(
    title="Total Appeal of a String",
    statement="""
The *appeal* of a string is its number of distinct characters. Return the sum of the appeals of all non-empty substrings of `s` (substrings at
different positions count separately).
""",
    constraints="""
- `1 <= s.length <= 10^5`
- lowercase English letters
""",
    signature=function("appealSum", [("s", "string")], "long"),
    reference=_appeal_sum,
    brute=_appeal_brute,
    examples=[Example(["abbca"]), Example(["code"])],
    edge_cases=[["a"], ["aaaa"], ["ab"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 30, big=10**4), rng.choice(["ab", "abcde", "abcdefghijklmnopqrstuvwxyz"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Dot Product of Two Sparse Vectors


def _dot_product(vec1: list[list[int]], vec2: list[list[int]]) -> int:
    lookup = dict(map(tuple, vec1)) if len(vec1) <= len(vec2) else dict(map(tuple, vec2))
    other = vec2 if len(vec1) <= len(vec2) else vec1
    return sum(value * lookup.get(index, 0) for index, value in other)


def _dot_brute(vec1: list[list[int]], vec2: list[list[int]]) -> int:
    size = 1 + max([i for i, _ in vec1 + vec2], default=0)
    dense1, dense2 = [0] * size, [0] * size
    for i, v in vec1:
        dense1[i] = v
    for i, v in vec2:
        dense2[i] = v
    return sum(a * b for a, b in zip(dense1, dense2, strict=True))


def _sparse_gen(rng: random.Random) -> list:
    size = rng.randint(1, rng.choice([20, 10**5]))

    def vector() -> list[list[int]]:
        indices = sorted(sample(rng, range(size), rng.randint(0, min(size, rng.choice([5, 200])))))
        return [[i, rng.randint(1, 100)] for i in indices]

    return [vector(), vector()]


SPARSE_DOT_PRODUCT = ProblemSource(
    title="Dot Product of Two Sparse Vectors",
    statement="""
*Adapted I/O:* two sparse vectors of the same length are given in compressed form — a list of `[index, value]` pairs for their non-zero entries,
sorted by index. Return their dot product (the sum over all indices of `vec1[i] * vec2[i]`).

Work with the compressed form directly; the dense vectors can be up to `10^5` long even when they have only a few non-zero entries.
""",
    constraints="""
- vector length `<= 10^5`; indices are distinct and sorted
- `1 <= value <= 100`
""",
    signature=function("dotProduct", [("vec1", "int[][]"), ("vec2", "int[][]")], "int"),
    reference=_dot_product,
    brute=_dot_brute,
    brute_input_limit=5000,
    is_variant=True,
    examples=[Example([[[0, 1], [3, 2], [4, 3]], [[3, 3], [4, 2]]], "Indices 3 and 4 overlap: 2*3 + 3*2 = 12."), Example([[[1, 1]], [[0, 1], [3, 2]]], "No overlap.")],
    edge_cases=[[[], []], [[[0, 100]], [[0, 100]]]],
    generator=_sparse_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Longest Happy Prefix


def _longest_prefix(s: str) -> str:
    failure = [0] * len(s)  # KMP prefix function
    k = 0
    for i in range(1, len(s)):
        while k and s[i] != s[k]:
            k = failure[k - 1]
        if s[i] == s[k]:
            k += 1
        failure[i] = k
    return s[: failure[-1]]


def _happy_prefix_brute(s: str) -> str:
    return next((s[:k] for k in range(len(s) - 1, 0, -1) if s[:k] == s[-k:]), "")


def _happy_gen(rng: random.Random) -> list:
    base = word(rng, rng.randint(1, 4), "ab")
    if rng.random() < 0.6:  # periodic strings have long happy prefixes
        return [base * rng.randint(1, 5) + base[: rng.randint(0, len(base))]]
    return [word(rng, rng.randint(1, 40), "ab")]


HAPPY_PREFIX = ProblemSource(
    title="Longest Happy Prefix",
    statement="""
A *happy prefix* is a non-empty prefix of `s` that is also a suffix of `s`, excluding `s` itself. Return the longest happy prefix, or `""` if
there is none.
""",
    constraints="""
- `1 <= s.length <= 10^5`
- lowercase English letters
""",
    signature=function("longestPrefix", [("s", "string")], "string"),
    reference=_longest_prefix,
    brute=_happy_prefix_brute,
    brute_input_limit=3000,
    examples=[Example(["level"], "\"l\"."), Example(["ababab"], "\"abab\" (prefixes may overlap the suffix).")],
    edge_cases=[["a"], ["aa"], ["abc"], ["aabaa"]],
    generator=_happy_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find Longest Self-Contained Substring


def _max_substring_length(s: str) -> int:
    first = {ch: s.index(ch) for ch in set(s)}
    last = {ch: s.rindex(ch) for ch in set(s)}
    best = -1
    for ch in first:  # a self-contained substring must start at the first occurrence of its first letter
        start, end = first[ch], last[ch]
        for i in range(start, len(s)):  # keep extending: a valid block may be followed by more valid blocks
            c = s[i]
            if first[c] < start:
                break
            end = max(end, last[c])
            if i == end and end - start + 1 < len(s):
                best = max(best, end - start + 1)
    return best


def _self_contained_brute(s: str) -> int:
    n = len(s)
    if n > 150:
        return NotImplemented
    best = -1
    for i in range(n):
        for j in range(i + 1, n + 1):
            inside = set(s[i:j])
            if j - i < n and not inside & set(s[:i] + s[j:]):
                best = max(best, j - i)
    return best


SELF_CONTAINED = ProblemSource(
    title="Find Longest Self-Contained Substring",
    statement="""
A substring `t` of `s` is *self-contained* if `t != s` and no letter of `t` appears anywhere in `s` outside `t`. Return the length of the longest
self-contained substring, or `-1` if there is none.
""",
    constraints="""
- `2 <= s.length <= 5 * 10^4`
- lowercase English letters
""",
    signature=function("maxSubstringLength", [("s", "string")], "int"),
    reference=_max_substring_length,
    brute=_self_contained_brute,
    examples=[Example(["abba"], "\"bb\"."), Example(["abab"]), Example(["abacd"], "\"abac\" holds every a, b and c.")],
    edge_cases=[["ab"], ["aa"], ["abcabc"]],
    generator=lambda rng: [word(rng, pick_n(rng, 2, 20, big=5000), rng.choice(["abc", "abcdef", "abcdefghij"]))],
    random_count=8,
)


PROBLEMS = [
    DESIGN_HASHMAP,
    FRACTION_TO_DECIMAL,
    LOGGER,
    NEXT_GREATER_I,
    ISOMORPHIC_STRINGS,
    DUPLICATE_FILES,
    LONGEST_PALINDROME,
    CONTINUOUS_SUBARRAY_SUM,
    UNIQUE_OCCURRENCES,
    HIGH_FIVE,
    BULLS_AND_COWS,
    WONDERFUL_SUBSTRINGS,
    DISTINCT_ISLANDS,
    CUSTOM_SORT_STRING,
    TOTAL_APPEAL,
    SPARSE_DOT_PRODUCT,
    HAPPY_PREFIX,
    SELF_CONTAINED,
]
