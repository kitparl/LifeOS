"""Pattern 28: Math and Geometry (part 2 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import math
import random
from collections import deque
from fractions import Fraction

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, sample
from app.modules.dsa.judge.codec import ListNode

PATTERN_NUMBER = 28


def _digit_list(rng: random.Random, n: int) -> list[int]:
    """Digits of a non-negative number, most significant first, without leading zeros."""
    if n == 1:
        return [rng.randint(0, 9)]
    return [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(n - 1)]


# ---------------------------------------------------------------- Add Two Numbers


def _add_two_numbers(l1: ListNode | None, l2: ListNode | None) -> ListNode | None:
    dummy = tail = ListNode()
    carry = 0
    while l1 or l2 or carry:
        total = carry + (l1.val if l1 else 0) + (l2.val if l2 else 0)
        carry, digit = divmod(total, 10)
        tail.next = ListNode(digit)
        tail = tail.next
        l1, l2 = l1.next if l1 else None, l2.next if l2 else None
    return dummy.next


def _add_two_brute(l1: ListNode | None, l2: ListNode | None) -> ListNode | None:
    def number(node: ListNode | None) -> int:
        digits = []
        while node:
            digits.append(str(node.val))
            node = node.next
        return int("".join(reversed(digits)))

    head = None
    for d in str(number(l1) + number(l2)):  # most significant digit ends up last
        head = ListNode(int(d), head)
    return head


ADD_TWO_NUMBERS = ProblemSource(
    title="Add Two Numbers",
    statement="""
Two non-negative integers are stored in linked lists with their digits in **reverse** order (the head is the ones digit), one digit per node and
no leading zeros except for the number `0` itself. Return their sum as a linked list in the same format.
""",
    constraints="""
- `1 <= number of nodes in each list <= 100`
- `0 <= Node.val <= 9`
""",
    signature=function("addTwoNumbers", [("l1", "ListNode"), ("l2", "ListNode")], "ListNode"),
    reference=_add_two_numbers,
    brute=_add_two_brute,
    examples=[Example([[2, 4, 3], [5, 6, 4]], "342 + 465 = 807."), Example([[0], [0]]), Example([[9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9]])],
    edge_cases=[[[5], [5]], [[1], [9, 9, 9]]],
    generator=lambda rng: [_digit_list(rng, rng.randint(1, rng.choice([5, 100])))[::-1], _digit_list(rng, rng.randint(1, rng.choice([5, 100])))[::-1]],
    random_count=8,
)


# ---------------------------------------------------------------- Plus One


def _plus_one(digits: list[int]) -> list[int]:
    out = digits[:]
    for i in range(len(out) - 1, -1, -1):
        if out[i] < 9:
            out[i] += 1
            return out
        out[i] = 0
    return [1, *out]


PLUS_ONE = ProblemSource(
    title="Plus One",
    statement="""
`digits` is a non-negative integer written as its decimal digits, most significant first, without leading zeros. Add one to it and return the
resulting digits.
""",
    constraints="""
- `1 <= digits.length <= 100`
- `0 <= digits[i] <= 9`
""",
    signature=function("plusOne", [("digits", "int[]")], "int[]"),
    reference=_plus_one,
    brute=lambda digits: [int(c) for c in str(int("".join(map(str, digits))) + 1)],
    examples=[Example([[1, 2, 3]]), Example([[4, 3, 2, 1]]), Example([[9]], "Carrying adds a digit.")],
    edge_cases=[[[0]], [[9, 9, 9]], [[1, 9, 9]]],
    generator=lambda rng: [_digit_list(rng, rng.randint(1, rng.choice([5, 100]))) if rng.random() < 0.7 else [rng.randint(1, 8)] + [9] * rng.randint(0, 10)],
    random_count=8,
)


# ---------------------------------------------------------------- Confusing Number


_ROTATE = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}


def _confusing_number(n: int) -> bool:
    text = str(n)
    if any(c not in _ROTATE for c in text):
        return False
    return "".join(_ROTATE[c] for c in reversed(text)) != text


def _confusing_brute(n: int) -> bool:
    rotated, x = 0, n
    while x:
        x, d = divmod(x, 10)
        if d in (2, 3, 4, 5, 7):
            return False
        rotated = rotated * 10 + {0: 0, 1: 1, 6: 9, 8: 8, 9: 6}[d]
    return rotated != n


CONFUSING_NUMBER = ProblemSource(
    title="Confusing Number",
    statement="""
Rotating a digit by 180 degrees turns `0, 1, 6, 8, 9` into `0, 1, 9, 8, 6`; the digits `2, 3, 4, 5, 7` become invalid. A *confusing number*
becomes a **different** valid number when rotated as a whole (leading zeros of the result are ignored). Return `true` if `n` is confusing.
""",
    constraints="""
- `0 <= n <= 10^9`
""",
    signature=function("confusingNumber", [("n", "int")], "bool"),
    reference=_confusing_number,
    brute=_confusing_brute,
    examples=[Example([6], "6 becomes 9."), Example([89], "89 becomes 68."), Example([11], "11 stays 11.")],
    edge_cases=[[0], [10], [25], [916], [1000000000]],
    generator=lambda rng: [int("".join(rng.choice("01689") for _ in range(rng.randint(1, 9)))) if rng.random() < 0.7 else rng.randint(0, 10**9)],
    random_count=10,
)


# ---------------------------------------------------------------- Nim Game


def _can_win_nim(n: int) -> bool:
    return n % 4 != 0


def _nim_brute(n: int) -> bool:
    if n > 2000:
        return NotImplemented
    win = [False] * (n + 1)
    for k in range(1, n + 1):
        win[k] = any(not win[k - take] for take in (1, 2, 3) if take <= k)
    return win[n]


NIM_GAME = ProblemSource(
    title="Nim Game",
    statement="""
There is a heap of `n` stones. You and a friend alternate turns, you first; each turn removes 1, 2 or 3 stones, and whoever removes the last stone
wins. Both players play optimally. Return `true` if you can win.
""",
    constraints="""
- `1 <= n <= 2^31 - 1`
""",
    signature=function("canWinNim", [("n", "int")], "bool"),
    reference=_can_win_nim,
    brute=_nim_brute,
    examples=[Example([4], "Whatever you take, your friend takes the rest."), Example([1]), Example([2])],
    edge_cases=[[3], [8], [2147483647]],
    generator=lambda rng: [4 * rng.randint(1, 500) if rng.random() < 0.4 else rng.randint(1, rng.choice([2000, 2**31 - 1]))],
    random_count=8,
)


# ---------------------------------------------------------------- Bulb Switcher


def _bulb_switch(n: int) -> int:
    return math.isqrt(n)  # a bulb ends on iff it has an odd number of divisors, i.e. it is a perfect square


def _bulb_brute(n: int) -> int:
    if n > 3000:
        return NotImplemented
    on = [False] * (n + 1)
    for step in range(1, n + 1):
        for bulb in range(step, n + 1, step):
            on[bulb] = not on[bulb]
    return sum(on)


BULB_SWITCHER = ProblemSource(
    title="Bulb Switcher",
    statement="""
`n` bulbs start off. In round 1 you turn every bulb on; in round 2 you toggle every second bulb; in round `i` you toggle every `i`-th bulb; you
finish after round `n`. Return how many bulbs are on at the end.
""",
    constraints="""
- `0 <= n <= 10^9`
""",
    signature=function("bulbSwitch", [("n", "int")], "int"),
    reference=_bulb_switch,
    brute=_bulb_brute,
    examples=[Example([3], "Only bulb 1 stays on."), Example([0]), Example([1])],
    edge_cases=[[4], [1000000000], [99]],
    generator=lambda rng: [rng.randint(0, rng.choice([3000, 10**9]))],
    random_count=8,
)


# ---------------------------------------------------------------- Water and Jug Problem


def _can_measure_water(x: int, y: int, target: int) -> bool:
    return target <= x + y and target % math.gcd(x, y) == 0


def _jug_brute(x: int, y: int, target: int) -> bool:
    if x * y > 5000:
        return NotImplemented
    seen, queue = {(0, 0)}, deque([(0, 0)])
    while queue:
        a, b = queue.popleft()
        if a + b == target:
            return True
        pour_ab, pour_ba = min(a, y - b), min(b, x - a)
        for state in ((x, b), (a, y), (0, b), (a, 0), (a - pour_ab, b + pour_ab), (a + pour_ba, b - pour_ba)):
            if state not in seen:
                seen.add(state)
                queue.append(state)
    return False


WATER_AND_JUG = ProblemSource(
    title="Water and Jug Problem",
    statement="""
You have two jugs holding `x` and `y` litres and an unlimited water supply. You may fill a jug completely, empty a jug, or pour one jug into the
other until the receiving jug is full or the pouring jug is empty. Return `true` if you can end up with exactly `target` litres in total across
both jugs.
""",
    constraints="""
- `1 <= x, y, target <= 10^3`
""",
    signature=function("canMeasureWater", [("x", "int"), ("y", "int"), ("target", "int")], "bool"),
    reference=_can_measure_water,
    brute=_jug_brute,
    examples=[Example([3, 5, 4], "The classic puzzle."), Example([2, 6, 5]), Example([1, 2, 3])],
    edge_cases=[[1, 1, 2], [1, 1, 3], [6, 9, 3], [1000, 1000, 1000]],
    generator=lambda rng: [rng.randint(1, (hi := rng.choice([20, 1000]))), rng.randint(1, hi), rng.randint(1, hi)],
    random_count=10,
)


# ---------------------------------------------------------------- Poor Pigs


def _poor_pigs(buckets: int, minutesToDie: int, minutesToTest: int) -> int:
    states = minutesToTest // minutesToDie + 1  # each pig dies in one of the rounds or survives
    pigs = 0
    while states**pigs < buckets:
        pigs += 1
    return pigs


def _pigs_brute(buckets: int, minutesToDie: int, minutesToTest: int) -> int:
    states = minutesToTest // minutesToDie + 1
    return math.ceil(round(math.log(buckets, states), 9)) if buckets > 1 else 0


POOR_PIGS = ProblemSource(
    title="Poor Pigs",
    statement="""
Exactly one of `buckets` buckets holds poison. A pig that drinks poison dies after `minutesToDie` minutes. In each round you may make any pigs
drink from any buckets simultaneously and then wait `minutesToDie` minutes; you have `minutesToTest` minutes in total. Return the minimum number
of pigs that guarantees identifying the poisoned bucket.
""",
    constraints="""
- `1 <= buckets <= 1000`
- `1 <= minutesToDie <= minutesToTest <= 100`
""",
    signature=function("poorPigs", [("buckets", "int"), ("minutesToDie", "int"), ("minutesToTest", "int")], "int"),
    reference=_poor_pigs,
    brute=_pigs_brute,
    examples=[Example([4, 15, 15], "Two pigs, one round: 2^2 = 4 outcomes."), Example([4, 15, 30]), Example([1000, 15, 60])],
    edge_cases=[[1, 1, 1], [2, 10, 10], [1000, 1, 100]],
    generator=lambda rng: [rng.randint(1, 1000), (d := rng.randint(1, 100)), rng.randint(d, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Add to Array-Form of Integer


def _add_to_array_form(num: list[int], k: int) -> list[int]:
    out = []
    i = len(num) - 1
    while i >= 0 or k:
        if i >= 0:
            k += num[i]
            i -= 1
        k, digit = divmod(k, 10)
        out.append(digit)
    return out[::-1] or [0]


ARRAY_FORM = ProblemSource(
    title="Add to Array-Form of Integer",
    statement="""
`num` is the array form of a non-negative integer (its digits from left to right, no leading zeros). Return the array form of `num + k`.
""",
    constraints="""
- `1 <= num.length <= 10^4`, `0 <= num[i] <= 9`
- `1 <= k <= 10^4`
""",
    signature=function("addToArrayForm", [("num", "int[]"), ("k", "int")], "int[]"),
    reference=_add_to_array_form,
    brute=lambda num, k: [int(c) for c in str(int("".join(map(str, num))) + k)],
    examples=[Example([[1, 2, 0, 0], 34]), Example([[2, 7, 4], 181]), Example([[2, 1, 5], 806], "215 + 806 = 1021.")],
    edge_cases=[[[0], 1], [[9, 9], 1], [[0], 10000]],
    generator=lambda rng: [_digit_list(rng, rng.randint(1, rng.choice([5, 3000]))), rng.randint(1, 10**4)],
    random_count=8,
)


# ---------------------------------------------------------------- Greatest Common Divisor of Strings


def _gcd_of_strings(str1: str, str2: str) -> str:
    if str1 + str2 != str2 + str1:
        return ""
    return str1[: math.gcd(len(str1), len(str2))]


def _gcd_strings_brute(str1: str, str2: str) -> str:
    for length in range(min(len(str1), len(str2)), 0, -1):
        base = str1[:length]
        if len(str1) % length == 0 and len(str2) % length == 0 and base * (len(str1) // length) == str1 and base * (len(str2) // length) == str2:
            return base
    return ""


def _gcd_strings_gen(rng: random.Random) -> list:
    base = "".join(rng.choice("AB") for _ in range(rng.randint(1, 3)))
    a, b = base * rng.randint(1, 6), base * rng.randint(1, 6)
    if rng.random() < 0.3:
        b = b[:-1] + ("A" if b[-1] == "B" else "B")
    return [a, b]


GCD_OF_STRINGS = ProblemSource(
    title="Greatest Common Divisor of Strings",
    statement="""
String `t` *divides* string `s` if `s` is `t` repeated one or more times. Return the longest string that divides both `str1` and `str2`, or `""`
if there is none.
""",
    constraints="""
- `1 <= str1.length, str2.length <= 1000`
- uppercase English letters
""",
    signature=function("gcdOfStrings", [("str1", "string"), ("str2", "string")], "string"),
    reference=_gcd_of_strings,
    brute=_gcd_strings_brute,
    examples=[Example(["ABCABC", "ABC"]), Example(["ABABAB", "ABAB"], "\"AB\"."), Example(["LEET", "CODE"])],
    edge_cases=[["A", "A"], ["AA", "A"], ["AB", "BA"]],
    generator=_gcd_strings_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Count Substrings with Only One Distinct Letter


def _count_letters(s: str) -> int:
    total = run = 0
    for i, ch in enumerate(s):
        run = run + 1 if i and ch == s[i - 1] else 1
        total += run
    return total


ONE_DISTINCT_LETTER = ProblemSource(
    title="Count Substrings with Only One Distinct Letter",
    statement="""
Return the number of non-empty substrings of `s` that contain a single distinct letter (substrings at different positions count separately).
""",
    constraints="""
- `1 <= s.length <= 1000`
- lowercase English letters
""",
    signature=function("countLetters", [("s", "string")], "int"),
    reference=_count_letters,
    brute=lambda s: sum(len(set(s[i:j])) == 1 for i in range(len(s)) for j in range(i + 1, len(s) + 1)) if len(s) <= 150 else NotImplemented,
    examples=[Example(["aaaba"], "aaa: 1, aa: 2, a: 4, b: 1 — 8 in all."), Example(["aaaaaaaaaa"])],
    edge_cases=[["a"], ["ab"], ["zzz"]],
    generator=lambda rng: ["".join(rng.choice("abc") * rng.randint(1, 5) for _ in range(rng.randint(1, rng.choice([10, 150]))))[:1000]],
    random_count=8,
)


# ---------------------------------------------------------------- Equal Rational Numbers


def _to_fraction(s: str) -> Fraction:
    if "(" not in s:
        return Fraction(s)
    head, repeat = s.rstrip(")").split("(")
    decimals = len(head.split(".")[1]) if "." in head else 0
    base = Fraction(head) if head.strip(".") else Fraction(0)
    return base + Fraction(int(repeat), (10 ** len(repeat) - 1) * 10**decimals)


def _is_rational_equal(s: str, t: str) -> bool:
    return _to_fraction(s) == _to_fraction(t)


def _rational_brute(s: str, t: str) -> bool:
    def expand(x: str) -> float:
        if "(" in x:
            head, repeat = x.rstrip(")").split("(")
            x = head + repeat * 20
        return float(x)

    return abs(expand(s) - expand(t)) < 1e-9


def _rational_text(rng: random.Random) -> str:
    whole = str(rng.randint(0, 20))
    kind = rng.random()
    if kind < 0.2:
        return whole
    decimals = "".join(str(rng.randint(0, 9)) for _ in range(rng.randint(0, 3)))
    if kind < 0.4:
        return f"{whole}.{decimals}"
    repeat = rng.choice(["9", "0", "3", "6", "12", "142857", str(rng.randint(1, 99))])
    return f"{whole}.{decimals}({repeat})"


def _rational_gen(rng: random.Random) -> list:
    s = _rational_text(rng)
    if rng.random() < 0.5:  # an equivalent rewrite of s
        if "(" in s:
            head, repeat = s.rstrip(")").split("(")
            return [s, f"{head}{repeat[0]}({repeat[1:]}{repeat[0]})"]  # 0.(52) == 0.5(25)
        if "." not in s and int(s) >= 1:
            return [s, f"{int(s) - 1}.(9)"]  # 3 == 2.(9)
    return [s, _rational_text(rng)]


EQUAL_RATIONALS = ProblemSource(
    title="Equal Rational Numbers",
    statement="""
`s` and `t` are non-negative rational numbers written with an optional repeating part in parentheses: `"12"`, `"0.5"`, `"1."`, `"2.12"` and
`"0.1(6)"` are all valid (`"0.1(6)"` means `0.1666...`). The integer part has at most 4 digits, the non-repeating decimals at most 4, and the
repeating part at most 4. Return `true` if `s` and `t` denote the same number.
""",
    constraints="""
- each string is a valid representation as described above
""",
    signature=function("isRationalEqual", [("s", "string"), ("t", "string")], "bool"),
    reference=_is_rational_equal,
    brute=_rational_brute,
    examples=[Example(["0.(52)", "0.5(25)"]), Example(["0.1666(6)", "0.166(66)"]), Example(["0.9(9)", "1."], "0.999... equals 1.")],
    edge_cases=[["1", "1.0"], ["0.(0)", "0"], ["0.1", "0.(1)"], ["3.(3)", "3.3(33)"]],
    generator=_rational_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Adding Two Negabinary Numbers


def _add_negabinary(arr1: list[int], arr2: list[int]) -> list[int]:
    out, carry = [], 0
    i, j = len(arr1) - 1, len(arr2) - 1
    while i >= 0 or j >= 0 or carry:
        total = carry + (arr1[i] if i >= 0 else 0) + (arr2[j] if j >= 0 else 0)
        out.append(total & 1)
        carry = -(total >> 1)  # base -2: a carry into the next place is negative
        i, j = i - 1, j - 1
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out[::-1]


def _from_negabinary(bits: list[int]) -> int:
    return sum(b * (-2) ** k for k, b in enumerate(reversed(bits)))


def _to_negabinary(n: int) -> list[int]:
    if n == 0:
        return [0]
    out = []
    while n:
        n, r = divmod(n, -2)
        if r < 0:
            n, r = n + 1, r + 2
        out.append(r)
    return out[::-1]


NEGABINARY_ADD = ProblemSource(
    title="Adding Two Negabinary Numbers",
    statement="""
A number in base `-2` is given as its bits from most to least significant: `[1, 1, 0, 1]` means `(-2)^3 + (-2)^2 + (-2)^0 = -3`. Both inputs have
no leading zeros (except for `[0]`). Return their sum in the same format, without leading zeros.
""",
    constraints="""
- `1 <= arr1.length, arr2.length <= 1000`
- bits are `0` or `1`
""",
    signature=function("addNegabinary", [("arr1", "int[]"), ("arr2", "int[]")], "int[]"),
    reference=_add_negabinary,
    brute=lambda arr1, arr2: _to_negabinary(_from_negabinary(arr1) + _from_negabinary(arr2)),
    examples=[Example([[1, 1, 1, 1, 1], [1, 0, 1]], "11 + 5 = 16 = [1,0,0,0,0]."), Example([[0], [0]]), Example([[0], [1]])],
    edge_cases=[[[1], [1]], [[1, 1], [1]], [[1, 1, 0], [1, 1, 0]]],
    generator=lambda rng: [_to_negabinary(rng.randint(-(hi := rng.choice([30, 10**12])), hi)), _to_negabinary(rng.randint(-hi, hi))],
    random_count=10,
)


# ---------------------------------------------------------------- Power of Three


def _is_power_of_three(n: int) -> bool:
    return n > 0 and 1162261467 % n == 0  # 3^19 is the largest power of three in int32


POWER_OF_THREE = ProblemSource(
    title="Power of Three",
    statement="""
Return `true` if `n` equals `3^x` for some integer `x >= 0`. Try to solve it without loops or recursion.
""",
    constraints="""
- `-2^31 <= n <= 2^31 - 1`
""",
    signature=function("isPowerOfThree", [("n", "int")], "bool"),
    reference=_is_power_of_three,
    brute=lambda n: n in {3**k for k in range(20)},
    examples=[Example([27]), Example([0]), Example([-1])],
    edge_cases=[[1], [1162261467], [45], [2147483647]],
    generator=lambda rng: [rng.choice([3 ** rng.randint(0, 19), rng.randint(-(2**31), 2**31 - 1), 3 ** rng.randint(1, 19) + rng.choice([-1, 1, 3])])],
    random_count=8,
)


# ---------------------------------------------------------------- Base 7


def _convert_to_base7(num: int) -> str:
    if num == 0:
        return "0"
    digits, n = [], abs(num)
    while n:
        n, d = divmod(n, 7)
        digits.append(str(d))
    return ("-" if num < 0 else "") + "".join(reversed(digits))


def _base7_brute(num: int) -> str:
    n = abs(num)
    power = 1
    while power * 7 <= n:
        power *= 7
    out = ""
    while power:
        out += str(n // power)
        n %= power
        power //= 7
    return ("-" if num < 0 else "") + out


BASE_7 = ProblemSource(
    title="Base 7",
    statement="""
Return the base-7 representation of the integer `num` as a string (with a leading `-` for negative numbers).
""",
    constraints="""
- `-10^7 <= num <= 10^7`
""",
    signature=function("convertToBase7", [("num", "int")], "string"),
    reference=_convert_to_base7,
    brute=_base7_brute,
    examples=[Example([100]), Example([-7])],
    edge_cases=[[0], [6], [10000000], [-10000000]],
    generator=lambda rng: [rng.randint(-(hi := rng.choice([100, 10**7])), hi)],
    random_count=8,
)


# ---------------------------------------------------------------- Sum of k-Mirror Numbers


def _k_mirror(k: int, n: int) -> int:
    def base_k_palindrome(x: int) -> bool:
        digits = []
        while x:
            x, d = divmod(x, k)
            digits.append(d)
        return digits == digits[::-1]

    found = []
    length = 1
    while len(found) < n:  # decimal palindromes in increasing order: build from the left half
        half_len = (length + 1) // 2
        for half in range(10 ** (half_len - 1), 10**half_len):
            text = str(half)
            value = int(text + text[::-1][length % 2 :])
            if base_k_palindrome(value):
                found.append(value)
                if len(found) == n:
                    break
        length += 1
    return sum(found)


def _k_mirror_brute(k: int, n: int) -> int:
    if n > 12:
        return NotImplemented
    found, x = [], 0
    while len(found) < n:
        x += 1
        s = str(x)
        if s == s[::-1]:
            digits = []
            y = x
            while y:
                y, d = divmod(y, k)
                digits.append(d)
            if digits == digits[::-1]:
                found.append(x)
    return sum(found)


K_MIRROR = ProblemSource(
    title="Sum of k-Mirror Numbers",
    statement="""
A *k-mirror number* is a positive integer with no leading zeros that reads the same forwards and backwards in **both** base 10 and base `k` (for
example `9` is 2-mirror: `9` in base 10 and `1001` in base 2). Return the sum of the `n` smallest k-mirror numbers.
""",
    constraints="""
- `2 <= k <= 9`
- `1 <= n <= 30`
""",
    signature=function("kMirror", [("k", "int"), ("n", "int")], "long"),
    reference=_k_mirror,
    brute=_k_mirror_brute,
    examples=[Example([2, 5], "1, 3, 5, 7 and 9: sum 25."), Example([3, 7]), Example([7, 17])],
    edge_cases=[[2, 1], [9, 1], [2, 20]],
    generator=lambda rng: [rng.randint(2, 9), rng.randint(1, rng.choice([10, 20]))],
    random_count=6,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Sum of Squares of Special Elements


def _sum_of_squares(nums: list[int]) -> int:
    n = len(nums)
    return sum(x * x for i, x in enumerate(nums, start=1) if n % i == 0)


SPECIAL_SQUARES = ProblemSource(
    title="Sum of Squares of Special Elements",
    statement="""
`nums` is 1-indexed and has length `n`. Element `nums[i]` is *special* if `i` divides `n`. Return the sum of the squares of all special
elements.
""",
    constraints="""
- `1 <= n <= 50`
- `1 <= nums[i] <= 50`
""",
    signature=function("sumOfSquares", [("nums", "int[]")], "int"),
    reference=_sum_of_squares,
    brute=lambda nums: sum(nums[d - 1] ** 2 for d in range(1, len(nums) + 1) if len(nums) % d == 0),
    examples=[Example([[1, 2, 3, 4]], "Indices 1, 2 and 4: 1 + 4 + 16 = 21."), Example([[2, 7, 1, 19, 18, 3]])],
    edge_cases=[[[5]], [[50] * 50]],
    generator=lambda rng: [ints(rng, rng.randint(1, 50), 1, 50)],
    random_count=8,
)


# ---------------------------------------------------------------- Add Digits


def _add_digits(num: int) -> int:
    return 0 if num == 0 else 1 + (num - 1) % 9


def _add_digits_brute(num: int) -> int:
    while num >= 10:
        num = sum(int(d) for d in str(num))
    return num


ADD_DIGITS = ProblemSource(
    title="Add Digits",
    statement="""
Repeatedly replace `num` with the sum of its decimal digits until it has a single digit, and return that digit. Try an `O(1)` solution without
loops.
""",
    constraints="""
- `0 <= num <= 2^31 - 1`
""",
    signature=function("addDigits", [("num", "int")], "int"),
    reference=_add_digits,
    brute=_add_digits_brute,
    examples=[Example([38], "3 + 8 = 11, 1 + 1 = 2."), Example([0])],
    edge_cases=[[9], [10], [2147483647]],
    generator=lambda rng: [rng.randint(0, rng.choice([1000, 2**31 - 1]))],
    random_count=8,
)


# ---------------------------------------------------------------- Count Primes


def _count_primes(n: int) -> int:
    if n < 3:
        return 0
    sieve = bytearray([1]) * n
    sieve[0] = sieve[1] = 0
    for p in range(2, math.isqrt(n - 1) + 1):
        if sieve[p]:
            sieve[p * p :: p] = bytearray(len(range(p * p, n, p)))
    return sum(sieve)


def _primes_brute(n: int) -> int:
    if n > 5000:
        return NotImplemented
    return sum(all(x % d for d in range(2, math.isqrt(x) + 1)) for x in range(2, n))


COUNT_PRIMES = ProblemSource(
    title="Count Primes",
    statement="""
Return the number of prime numbers strictly less than `n`.
""",
    constraints="""
- `0 <= n <= 5 * 10^6`
""",
    signature=function("countPrimes", [("n", "int")], "int"),
    reference=_count_primes,
    brute=_primes_brute,
    examples=[Example([10], "2, 3, 5, 7."), Example([0]), Example([1])],
    edge_cases=[[2], [3], [5000000]],
    generator=lambda rng: [rng.randint(0, rng.choice([5000, 5 * 10**6]))],
    random_count=8,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Pow(x, n)


def _my_pow(x: float, n: int) -> float:
    if n < 0:
        x, n = 1 / x, -n
    result = 1.0
    while n:  # fast exponentiation by squaring
        if n & 1:
            result *= x
        x *= x
        n >>= 1
    return result


def _pow_gen(rng: random.Random) -> list:
    x = round(rng.uniform(-3, 3), 3) or 1.5
    limit = int(math.log(10**4) / math.log(max(abs(x), 1.0001)))  # keep |x^n| <= 10^4
    return [x, rng.randint(-min(limit, 2**31 - 1), min(limit, 2**31 - 1))] if abs(x) > 1 else [x, rng.randint(0, rng.choice([10, 1000]))]


POW = ProblemSource(
    title="Pow(x, n)",
    statement="""
Compute `x` raised to the power `n` (`x^n`) without a built-in power function. Answers within `10^-5` are accepted.
""",
    constraints="""
- `-100.0 < x < 100.0`, `-2^31 <= n <= 2^31 - 1`
- `x != 0` or `n > 0`; `-10^4 <= x^n <= 10^4`
""",
    signature=function("myPow", [("x", "double"), ("n", "int")], "double"),
    reference=_my_pow,
    brute=lambda x, n: math.pow(x, n),
    compare="float_tolerance",
    examples=[Example([2.0, 10]), Example([2.1, 3]), Example([2.0, -2], "1 / 4.")],
    edge_cases=[[1.0, 2147483647], [1.0, -2147483648], [-1.0, 2147483647], [0.5, 10]],
    generator=_pow_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Find the Winner of the Circular Game


def _find_the_winner(n: int, k: int) -> int:
    winner = 0  # Josephus recurrence, 0-indexed
    for size in range(2, n + 1):
        winner = (winner + k) % size
    return winner + 1


def _circle_brute(n: int, k: int) -> int:
    friends = list(range(1, n + 1))
    i = 0
    while len(friends) > 1:
        i = (i + k - 1) % len(friends)
        friends.pop(i)
    return friends[0]


CIRCULAR_GAME = ProblemSource(
    title="Find the Winner of the Circular Game",
    statement="""
`n` friends numbered `1` to `n` sit in a circle. Starting from friend 1, count `k` friends clockwise (including the one you start from); the
friend counted last leaves the circle, and counting restarts from the next friend clockwise. The last friend remaining wins; return their number.
""",
    constraints="""
- `1 <= k <= n <= 500`
""",
    signature=function("findTheWinner", [("n", "int"), ("k", "int")], "int"),
    reference=_find_the_winner,
    brute=_circle_brute,
    examples=[Example([5, 2], "Friends 2, 4, 1 and 5 leave; 3 wins."), Example([6, 5])],
    edge_cases=[[1, 1], [2, 2], [500, 500]],
    generator=lambda rng: [(n := rng.randint(1, 500)), rng.randint(1, n)],
    random_count=8,
)


# ---------------------------------------------------------------- Build Array from Permutation


def _build_array(nums: list[int]) -> list[int]:
    return [nums[x] for x in nums]


BUILD_ARRAY_PERMUTATION = ProblemSource(
    title="Build Array from Permutation",
    statement="""
`nums` is a permutation of `0..n-1`. Return `ans` with `ans[i] = nums[nums[i]]`. As a follow-up, try doing it in place with `O(1)` extra space.
""",
    constraints="""
- `1 <= n <= 1000`
- `nums` is a permutation of `0..n-1`
""",
    signature=function("buildArray", [("nums", "int[]")], "int[]"),
    reference=_build_array,
    brute=lambda nums: [nums[nums[i]] for i in range(len(nums))],
    examples=[Example([[0, 2, 1, 5, 3, 4]]), Example([[5, 0, 1, 2, 3, 4]])],
    edge_cases=[[[0]], [[1, 0]]],
    generator=lambda rng: [sample(rng, range(n), n) for n in [rng.randint(1, rng.choice([10, 1000]))]],
    random_count=6,
)


# ---------------------------------------------------------------- Excel Sheet Column Number


def _title_to_number(columnTitle: str) -> int:
    number = 0
    for ch in columnTitle:
        number = number * 26 + ord(ch) - 64
    return number


def _column_title(n: int) -> str:
    out = ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


EXCEL_COLUMN = ProblemSource(
    title="Excel Sheet Column Number",
    statement="""
Spreadsheet columns are titled `A, B, ..., Z, AA, AB, ..., AZ, BA, ...`. Given a column title, return its column number (`A` is 1).
""",
    constraints="""
- `1 <= columnTitle.length <= 7`, uppercase letters
- the answer is at most `2^31 - 1` (the largest title is `"FXSHRXW"`)
""",
    signature=function("titleToNumber", [("columnTitle", "string")], "int"),
    reference=_title_to_number,
    brute=lambda columnTitle: next(n for n in range(1, 20000) if _column_title(n) == columnTitle) if len(columnTitle) <= 3 else NotImplemented,
    examples=[Example(["A"]), Example(["AB"]), Example(["ZY"])],
    edge_cases=[["Z"], ["AA"], ["FXSHRXW"]],
    generator=lambda rng: [_column_title(rng.randint(1, rng.choice([18000, 2**31 - 1])))],
    random_count=8,
)


# ---------------------------------------------------------------- The kth Factor of n


def _kth_factor(n: int, k: int) -> int:
    small, large = [], []
    for d in range(1, math.isqrt(n) + 1):
        if n % d == 0:
            small.append(d)
            if d != n // d:
                large.append(n // d)
    factors = small + large[::-1]
    return factors[k - 1] if k <= len(factors) else -1


KTH_FACTOR = ProblemSource(
    title="The kth Factor of n",
    statement="""
List the positive factors of `n` in ascending order and return the `k`-th one, or `-1` if `n` has fewer than `k` factors.
""",
    constraints="""
- `1 <= k <= n <= 1000`
""",
    signature=function("kthFactor", [("n", "int"), ("k", "int")], "int"),
    reference=_kth_factor,
    brute=lambda n, k: ([d for d in range(1, n + 1) if n % d == 0] + [-1] * k)[k - 1],
    examples=[Example([12, 3], "Factors 1, 2, 3, 4, 6, 12."), Example([7, 2]), Example([4, 4])],
    edge_cases=[[1, 1], [1000, 16], [1000, 17]],
    generator=lambda rng: [(n := rng.randint(1, 1000)), rng.randint(1, min(n, 20))],
    random_count=8,
)


# ---------------------------------------------------------------- Perfect Number


def _check_perfect_number(num: int) -> bool:
    if num < 2:
        return False
    total = 1
    for d in range(2, math.isqrt(num) + 1):
        if num % d == 0:
            total += d + (num // d if d != num // d else 0)
    return total == num


PERFECT_NUMBER = ProblemSource(
    title="Perfect Number",
    statement="""
A *perfect number* equals the sum of its positive divisors excluding itself (for example `28 = 1 + 2 + 4 + 7 + 14`). Return `true` if `num` is
perfect.
""",
    constraints="""
- `1 <= num <= 10^8`
""",
    signature=function("checkPerfectNumber", [("num", "int")], "bool"),
    reference=_check_perfect_number,
    brute=lambda num: num in {6, 28, 496, 8128, 33550336},
    examples=[Example([28]), Example([7])],
    edge_cases=[[1], [6], [33550336], [100000000]],
    generator=lambda rng: [rng.choice([6, 28, 496, 8128, rng.randint(1, 10**8), rng.randint(1, 10**4)])],
    random_count=8,
)


PROBLEMS = [
    ADD_TWO_NUMBERS,
    PLUS_ONE,
    CONFUSING_NUMBER,
    NIM_GAME,
    BULB_SWITCHER,
    WATER_AND_JUG,
    POOR_PIGS,
    ARRAY_FORM,
    GCD_OF_STRINGS,
    ONE_DISTINCT_LETTER,
    EQUAL_RATIONALS,
    NEGABINARY_ADD,
    POWER_OF_THREE,
    BASE_7,
    K_MIRROR,
    SPECIAL_SQUARES,
    ADD_DIGITS,
    COUNT_PRIMES,
    POW,
    CIRCULAR_GAME,
    BUILD_ARRAY_PERMUTATION,
    EXCEL_COLUMN,
    KTH_FACTOR,
    PERFECT_NUMBER,
]
