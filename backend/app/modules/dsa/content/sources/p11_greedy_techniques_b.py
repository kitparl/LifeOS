"""Pattern 11: Greedy Techniques (part 2 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import functools
import itertools
from collections import deque

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, word

PATTERN_NUMBER = 11


# ---------------------------------------------------------------- Sort an Array


def _sort_array(nums: list[int]) -> list[int]:
    if len(nums) <= 1:
        return nums
    mid = len(nums) // 2
    left, right = _sort_array(nums[:mid]), _sort_array(nums[mid:])
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    return out + left[i:] + right[j:]


SORT_ARRAY = ProblemSource(
    title="Sort an Array",
    statement="""
Sort `nums` in ascending order and return it, **without** using any built-in sort function, in `O(n log n)` time and with as little
extra space as you can.
""",
    constraints="""
- `1 <= nums.length <= 5 * 10^4`
- `-5 * 10^4 <= nums[i] <= 5 * 10^4`
""",
    signature=function("sortArray", [("nums", "int[]")], "int[]"),
    reference=_sort_array,
    brute=sorted,
    examples=[Example([[5, 2, 3, 1]]), Example([[5, 1, 1, 2, 0, 0]])],
    edge_cases=[[[1]], [[2, 2, 2]], [[-50000, 50000]], [[3, 2, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 40, big=4500), -5 * 10**4, 5 * 10**4)],
    random_count=8,
)


# ---------------------------------------------------------------- Text Justification


def _full_justify(words: list[str], maxWidth: int) -> list[str]:
    lines, i = [], 0
    while i < len(words):
        j, width = i, 0
        while j < len(words) and width + len(words[j]) + (j - i) <= maxWidth:
            width += len(words[j])
            j += 1
        line_words = words[i:j]
        if j == len(words) or len(line_words) == 1:
            line = " ".join(line_words)
            lines.append(line + " " * (maxWidth - len(line)))
        else:
            gaps = len(line_words) - 1
            spaces, extra = divmod(maxWidth - width, gaps)
            line = ""
            for k, w in enumerate(line_words[:-1]):
                line += w + " " * (spaces + (1 if k < extra else 0))
            lines.append(line + line_words[-1])
        i = j
    return lines


def _justify_brute(words: list[str], maxWidth: int) -> list[str]:
    groups: list[list[str]] = [[]]
    for w in words:
        if groups[-1] and len(" ".join(groups[-1] + [w])) > maxWidth:
            groups.append([])
        groups[-1].append(w)
    out = []
    for idx, group in enumerate(groups):
        if idx == len(groups) - 1 or len(group) == 1:
            out.append(" ".join(group).ljust(maxWidth))
            continue
        slots = [" "] * (len(group) - 1)
        free = maxWidth - len("".join(group)) - len(slots)
        k = 0
        while free:
            slots[k % len(slots)] += " "
            free -= 1
            k += 1
        out.append("".join(w + s for w, s in zip(group, slots + [""], strict=True)))
    return out


def _justify_gen(rng):
    width = rng.randint(5, 40)
    words = [word(rng, rng.randint(1, width), "abcdefg") for _ in range(pick_n(rng, 1, 15, big=300))]
    return [words, width]


TEXT_JUSTIFICATION = ProblemSource(
    title="Text Justification",
    statement="""
Format `words` into lines of exactly `maxWidth` characters, fully justified:

- Pack words greedily: put as many words on each line as fit, with at least one space between neighbouring words.
- Spread the extra spaces of a line as evenly as possible between its words; when they don't divide evenly, the gaps on the **left**
  get the extra spaces.
- The **last** line, and any line with a single word, is left-justified: single spaces between words, padded with spaces on the right.

Return the lines.
""",
    constraints="""
- `1 <= words.length <= 300`
- `1 <= words[i].length <= maxWidth <= 100`
- words consist of letters and symbols, no spaces
""",
    signature=function("fullJustify", [("words", "string[]"), ("maxWidth", "int")], "string[]"),
    reference=_full_justify,
    brute=_justify_brute,
    examples=[
        Example([["This", "is", "an", "example", "of", "text", "justification."], 16], "\"This    is    an\", \"example  of text\", \"justification.  \"."),
        Example([["What", "must", "be", "acknowledgment", "shall", "be"], 16]),
    ],
    edge_cases=[[["a"], 1], [["a", "b"], 3], [["ab", "cd", "e"], 5], [["x"], 10]],
    generator=_justify_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Best Time to Buy and Sell Stock II


def _max_profit_ii(prices: list[int]) -> int:
    return sum(max(0, b - a) for a, b in itertools.pairwise(prices))


def _profit_ii_brute(prices: list[int]) -> int:
    @functools.cache
    def best(i: int, holding: bool) -> int:
        if i == len(prices):
            return 0
        skip = best(i + 1, holding)
        act = best(i + 1, not holding) + (prices[i] if holding else -prices[i])
        return max(skip, act)

    return best(0, False)


BEST_TIME_II = ProblemSource(
    title="Best Time to Buy and Sell Stock II",
    statement="""
`prices[i]` is a stock's price on day `i`. You may hold at most one share at a time, and you may buy and sell as many times as you like
(even buying and selling on the same day). Return the maximum total profit.
""",
    constraints="""
- `1 <= prices.length <= 3 * 10^4`
- `0 <= prices[i] <= 10^4`
""",
    signature=function("maxProfit", [("prices", "int[]")], "int"),
    reference=_max_profit_ii,
    brute=_profit_ii_brute,
    brute_input_limit=500,
    examples=[Example([[7, 1, 5, 3, 6, 4]], "Buy at 1 sell at 5, buy at 3 sell at 6: 7."), Example([[1, 2, 3, 4, 5]]), Example([[7, 6, 4, 3, 1]])],
    edge_cases=[[[5]], [[1, 5]], [[5, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 30, big=5000), 0, rng.choice([10, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Wildcard Matching


def _is_match(s: str, p: str) -> bool:
    dp = [False] * (len(p) + 1)
    dp[0] = True
    for j in range(1, len(p) + 1):
        dp[j] = dp[j - 1] and p[j - 1] == "*"
    for ch in s:
        new = [False] * (len(p) + 1)
        for j in range(1, len(p) + 1):
            if p[j - 1] == "*":
                new[j] = new[j - 1] or dp[j]
            else:
                new[j] = dp[j - 1] and p[j - 1] in (ch, "?")
        dp = new
    return dp[-1]


def _is_match_brute(s: str, p: str) -> bool:
    @functools.cache
    def match(i: int, j: int) -> bool:
        if j == len(p):
            return i == len(s)
        if p[j] == "*":
            return any(match(k, j + 1) for k in range(i, len(s) + 1))
        return i < len(s) and p[j] in (s[i], "?") and match(i + 1, j + 1)

    return match(0, 0)


def _wild_gen(rng):
    s = word(rng, pick_n(rng, 0, 12, big=1500), "ab")
    p = word(rng, pick_n(rng, 0, 8, big=1500), "ab?**")
    if rng.random() < 0.4 and s:
        p = "".join(c if rng.random() < 0.6 else rng.choice("?*") for c in s)
    return [s, p]


WILDCARD = ProblemSource(
    title="Wildcard Matching",
    statement="""
Match the whole string `s` against the pattern `p`, where `?` matches any single character and `*` matches any sequence of characters
(including the empty one). Return `true` if `p` matches all of `s`.
""",
    constraints="""
- `0 <= s.length, p.length <= 2000`
- `s` has lowercase letters; `p` has lowercase letters, `?` and `*`
""",
    signature=function("isMatch", [("s", "string"), ("p", "string")], "bool"),
    reference=_is_match,
    brute=_is_match_brute,
    brute_input_limit=60,
    examples=[Example(["aa", "a"], "\"a\" doesn't cover the whole string."), Example(["aa", "*"]), Example(["cb", "?a"], "'?' matches c but 'a' doesn't match b.")],
    edge_cases=[["", ""], ["", "*"], ["a", ""], ["adceb", "*a*b"], ["acdcb", "a*c?b"], ["abc", "***"]],
    generator=_wild_gen,
    random_count=9,
    time_limit_ms=1500,
)


# ---------------------------------------------------------------- Remove K Digits


def _remove_k_digits(num: str, k: int) -> str:
    stack: list[str] = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    result = "".join(stack[: len(stack) - k]).lstrip("0")
    return result or "0"


def _remove_k_brute(num: str, k: int) -> str:
    best = None
    for keep in itertools.combinations(range(len(num)), len(num) - k):
        value = int("".join(num[i] for i in keep) or "0")
        best = value if best is None else min(best, value)
    return str(best)


REMOVE_K_DIGITS = ProblemSource(
    title="Remove K Digits",
    statement="""
`num` is a non-negative integer written as a string. Remove exactly `k` of its digits so that the remaining digits (in their original
order) form the smallest possible number. Return it as a string without leading zeros; an empty result is `"0"`.
""",
    constraints="""
- `1 <= k <= num.length <= 10^5`
- `num` has only digits and no leading zeros except for `"0"` itself
""",
    signature=function("removeKdigits", [("num", "string"), ("k", "int")], "string"),
    reference=_remove_k_digits,
    brute=_remove_k_brute,
    brute_input_limit=18,
    examples=[Example(["1432219", 3], "Remove 4, 3 and 2: \"1219\"."), Example(["10200", 1], "Remove the 1; leading zeros drop: \"200\"."), Example(["10", 2])],
    edge_cases=[["9", 1], ["112", 1], ["100", 1], ["123456", 3]],
    generator=lambda rng: [(s := (lambda t: ("1" + t[1:]) if t.startswith("0") and len(t) > 1 else t)(word(rng, pick_n(rng, 1, 9, big=15000), "0123456789"))), rng.randint(1, len(s))],
    random_count=8,
)


# ---------------------------------------------------------------- Largest Number


def _largest_number(nums: list[int]) -> str:
    strs = sorted(map(str, nums), key=functools.cmp_to_key(lambda a, b: (b + a > a + b) - (b + a < a + b)))
    result = "".join(strs)
    return "0" if result[0] == "0" else result


LARGEST_NUMBER = ProblemSource(
    title="Largest Number",
    statement="""
Arrange the non-negative integers in `nums` in some order and concatenate them to form the largest possible number. Return it as a string
(it can be huge). Don't return leading zeros: an all-zero input gives `"0"`.
""",
    constraints="""
- `1 <= nums.length <= 100`
- `0 <= nums[i] <= 10^9`
""",
    signature=function("largestNumber", [("nums", "int[]")], "string"),
    reference=_largest_number,
    brute=lambda nums: str(max(int("".join(map(str, p))) for p in itertools.permutations(nums))),
    brute_input_limit=24,
    examples=[Example([[10, 2]], "\"210\"."), Example([[3, 30, 34, 5, 9]], "\"9534330\".")],
    edge_cases=[[[0]], [[0, 0]], [[1000000000, 9]], [[121, 12]], [[432, 43243]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 6, big=100), 0, rng.choice([99, 10**9]))],
    random_count=8,
)


# ---------------------------------------------------------------- Strong Password Checker


def _strong_password(password: str) -> int:
    n = len(password)
    missing = 3 - (any(c.islower() for c in password) + any(c.isupper() for c in password) + any(c.isdigit() for c in password))
    replace = one = two = 0
    i = 2
    while i < n:
        if password[i] == password[i - 1] == password[i - 2]:
            length = 2
            while i < n and password[i] == password[i - 1]:
                length += 1
                i += 1
            replace += length // 3
            if length % 3 == 0:
                one += 1
            elif length % 3 == 1:
                two += 1
        else:
            i += 1
    if n < 6:
        return max(missing, 6 - n)
    if n <= 20:
        return max(missing, replace)
    delete = n - 20
    replace -= min(delete, one)
    replace -= min(max(delete - one, 0), two * 2) // 2
    replace -= max(delete - one - 2 * two, 0) // 3
    return delete + max(missing, replace)


# Published answers, checked when this module is imported by the build.
for _pw, _answer in (("a", 5), ("aA1", 3), ("1337C0d3", 0), ("aaa111", 2), ("a" * 21, 7), ("ABABABABABABABABABAB1", 2), ("bbaaaaaaaaaaaaaaacccccc", 8), ("FFFFFFFFFFFFFFF11111111111111111111AAA", 23)):
    assert _strong_password(_pw) == _answer, _pw


def _password_gen(rng):
    runs = []
    for _ in range(rng.randint(1, 10)):
        runs.append(rng.choice("aA1.b") * rng.choice([1, 1, 2, 3, 4, 5, 7]))
    return ["".join(runs)[:50]]


STRONG_PASSWORD = ProblemSource(
    title="Strong Password Checker",
    statement="""
A password is **strong** when all of these hold:
- it has at least 6 and at most 20 characters,
- it contains at least one lowercase letter, one uppercase letter and one digit,
- it does not contain the same character three times in a row (`"...aaa..."` is weak; `"...aa...a..."` is fine).

In one step you may insert one character, delete one character or replace one character. Return the minimum number of steps to make
`password` strong (0 if it already is).
""",
    constraints="""
- `1 <= password.length <= 50`
- `password` consists of letters, digits, dot `.` and exclamation mark `!`
""",
    signature=function("strongPasswordChecker", [("password", "string")], "int"),
    reference=_strong_password,
    examples=[Example(["a"], "Five insertions are needed (length and two missing kinds)."), Example(["aA1"]), Example(["1337C0d3"], "Already strong.")],
    edge_cases=[["aaa111"], ["a" * 21], ["ABABABABABABABABABAB1"], ["bbaaaaaaaaaaaaaaacccccc"], ["FFFFFFFFFFFFFFF11111111111111111111AAA"], ["......"]],
    generator=_password_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Points After Enemy Battles


def _maximum_points(enemyEnergies: list[int], currentEnergy: int) -> int:
    smallest = min(enemyEnergies)
    if currentEnergy < smallest:
        return 0
    return (currentEnergy + sum(enemyEnergies) - smallest) // smallest


def _points_brute(enemyEnergies: list[int], currentEnergy: int) -> int:
    n = len(enemyEnergies)

    @functools.cache
    def best(energy: int, marked: frozenset[int], has_point: bool) -> int:
        result = 0
        for i in range(n):
            if i in marked:
                continue
            if energy >= enemyEnergies[i]:
                result = max(result, 1 + best(energy - enemyEnergies[i], marked, True))
            if has_point:
                result = max(result, best(energy + enemyEnergies[i], marked | {i}, True))
        return result

    return best(currentEnergy, frozenset(), False)


ENEMY_BATTLES = ProblemSource(
    title="Maximum Points After Enemy Battles",
    statement="""
You start with `0` points and `currentEnergy` energy; all enemies start **unmarked**. Enemy `i` has energy `enemyEnergies[i]`. You may
repeat either operation any number of times:

1. Pick an unmarked enemy `i` with `currentEnergy >= enemyEnergies[i]`: gain 1 point and lose `enemyEnergies[i]` energy.
2. If you have at least 1 point, pick an unmarked enemy `i`: gain `enemyEnergies[i]` energy and **mark** enemy `i`.

Return the maximum number of points you can end up with.
""",
    constraints="""
- `1 <= enemyEnergies.length <= 10^5`
- `1 <= enemyEnergies[i] <= 10^9`
- `0 <= currentEnergy <= 10^9`
""",
    signature=function("maximumPoints", [("enemyEnergies", "int[]"), ("currentEnergy", "int")], "long"),
    reference=_maximum_points,
    brute=lambda enemyEnergies, currentEnergy: _points_brute(enemyEnergies, currentEnergy) if len(enemyEnergies) <= 4 and currentEnergy + sum(enemyEnergies) <= 40 else NotImplemented,
    examples=[Example([[3, 2, 2], 2], "3 points are reachable."), Example([[2], 10], "Fight the same enemy 5 times.")],
    edge_cases=[[[5], 4], [[1], 0], [[1, 1], 1], [[1000000000], 1000000000]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 4, big=4000), 1, rng.choice([5, 10**9])), rng.randint(0, rng.choice([8, 10**9]))],
    random_count=8,
)


# ---------------------------------------------------------------- Integer to Roman

_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _int_to_roman(num: int) -> str:
    out = []
    for value, symbol in _ROMAN:
        count, num = divmod(num, value)
        out.append(symbol * count)
    return "".join(out)


def _int_to_roman_brute(num: int) -> str:
    def digit(d: int, one: str, five: str, ten: str) -> str:
        return ["", one, one * 2, one * 3, one + five, five, five + one, five + one * 2, five + one * 3, one + ten][d]

    return "M" * (num // 1000) + digit(num // 100 % 10, "C", "D", "M") + digit(num // 10 % 10, "X", "L", "C") + digit(num % 10, "I", "V", "X")


INTEGER_TO_ROMAN = ProblemSource(
    title="Integer to Roman",
    statement="""
Convert an integer to a Roman numeral. The symbols are `I = 1`, `V = 5`, `X = 10`, `L = 50`, `C = 100`, `D = 500`, `M = 1000`, written
from largest to smallest value. Subtractive forms are used for 4 and 9 in each place: `IV = 4`, `IX = 9`, `XL = 40`, `XC = 90`,
`CD = 400`, `CM = 900`; a symbol is never repeated more than three times in a row.
""",
    constraints="""
- `1 <= num <= 3999`
""",
    signature=function("intToRoman", [("num", "int")], "string"),
    reference=_int_to_roman,
    brute=_int_to_roman_brute,
    examples=[Example([3749], "MMM + DCC + XL + IX."), Example([58], "L + V + III."), Example([1994], "M + CM + XC + IV.")],
    edge_cases=[[1], [4], [9], [40], [3999], [444]],
    generator=lambda rng: [rng.randint(1, 3999)],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Adjacent Swaps to Make a Valid Array


def _minimum_swaps(nums: list[int]) -> int:
    lo = nums.index(min(nums))
    hi = len(nums) - 1 - nums[::-1].index(max(nums))
    return lo + (len(nums) - 1 - hi) - (1 if lo > hi else 0)


def _valid_array_brute(nums: list[int]) -> int:
    def ok(state: tuple[int, ...]) -> bool:
        return state[0] == min(state) and state[-1] == max(state)

    start = tuple(nums)
    seen, frontier = {start}, deque([(start, 0)])
    while frontier:
        state, d = frontier.popleft()
        if ok(state):
            return d
        for i in range(len(state) - 1):
            nxt = list(state)
            nxt[i], nxt[i + 1] = nxt[i + 1], nxt[i]
            t = tuple(nxt)
            if t not in seen:
                seen.add(t)
                frontier.append((t, d + 1))
    raise AssertionError


VALID_ARRAY_SWAPS = ProblemSource(
    title="Minimum Adjacent Swaps to Make a Valid Array",
    statement="""
An array is *valid* when its first element is a smallest value of the array and its last element is a largest value. In one operation you
may swap two adjacent elements. Return the minimum number of swaps needed to make `nums` valid.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^5`
""",
    signature=function("minimumSwaps", [("nums", "int[]")], "int"),
    reference=_minimum_swaps,
    brute=_valid_array_brute,
    brute_input_limit=24,
    examples=[Example([[3, 4, 5, 5, 3, 1]], "Move 1 to the front (5 swaps) and a 5 to the end (1 swap): 6."), Example([[9]])],
    edge_cases=[[[2, 1]], [[1, 2]], [[5, 1, 5]], [[3, 3, 3]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 6, big=5000), 1, rng.choice([4, 10**5]))],
    random_count=8,
)


# ---------------------------------------------------------------- Special Binary String


def _make_largest_special(s: str) -> str:
    parts, balance, start = [], 0, 0
    for i, ch in enumerate(s):
        balance += 1 if ch == "1" else -1
        if balance == 0:
            parts.append("1" + _make_largest_special(s[start + 1 : i]) + "0")
            start = i + 1
    return "".join(sorted(parts, reverse=True))


def _is_special(t: str) -> bool:
    balance = 0
    for ch in t:
        balance += 1 if ch == "1" else -1
        if balance < 0:
            return False
    return balance == 0 and bool(t)


def _special_brute(s: str) -> str:
    seen, frontier = {s}, [s]
    while frontier:
        cur = frontier.pop()
        n = len(cur)
        for i in range(n):
            for j in range(i + 1, n):
                if not _is_special(cur[i:j]):
                    continue
                for k in range(j + 1, n + 1):
                    if _is_special(cur[j:k]):
                        nxt = cur[:i] + cur[j:k] + cur[i:j] + cur[k:]
                        if nxt not in seen:
                            seen.add(nxt)
                            frontier.append(nxt)
    return max(seen)


def _special_gen(rng):
    def build(pairs: int) -> str:
        if pairs == 0:
            return ""
        inner = rng.randint(0, pairs - 1)
        return "1" + build(inner) + "0" + build(pairs - 1 - inner)

    return [build(rng.randint(1, rng.choice([5, 25])))]


SPECIAL_BINARY = ProblemSource(
    title="Special Binary String",
    statement="""
A binary string is *special* if it has as many `0`s as `1`s and every prefix has at least as many `1`s as `0`s.

Given a special string `s`, a move picks two **consecutive, non-empty** special substrings of `s` and swaps them. Return the
lexicographically largest string obtainable with any number of moves.
""",
    constraints="""
- `1 <= s.length <= 50`
- `s` is a special binary string
""",
    signature=function("makeLargestSpecial", [("s", "string")], "string"),
    reference=_make_largest_special,
    brute=_special_brute,
    brute_input_limit=14,
    examples=[Example(["11011000"], "Swap \"10\" and \"1100\": \"11100100\"."), Example(["10"])],
    edge_cases=[["1100"], ["1010"], ["101100"], ["110100"]],
    generator=_special_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximize Distance to Closest Person


def _max_dist_to_closest(seats: list[int]) -> int:
    people = [i for i, s in enumerate(seats) if s]
    best = max(people[0], len(seats) - 1 - people[-1])
    for a, b in itertools.pairwise(people):
        best = max(best, (b - a) // 2)
    return best


def _seats_gen(rng):
    seats = [int(rng.random() < 0.3) for _ in range(pick_n(rng, 2, 20, big=10000))]
    if not any(seats):
        seats[rng.randrange(len(seats))] = 1
    if all(seats):
        seats[rng.randrange(len(seats))] = 0
    return [seats]


MAXIMIZE_DISTANCE = ProblemSource(
    title="Maximize Distance to Closest Person",
    statement="""
`seats[i]` is `1` if seat `i` is taken and `0` if it's empty; there is at least one of each. Alex wants to sit in an empty seat whose
distance to the **closest** person is as large as possible. Return that maximum distance.
""",
    constraints="""
- `2 <= seats.length <= 2 * 10^4`
- `seats[i]` is `0` or `1`, with at least one of each
""",
    signature=function("maxDistToClosest", [("seats", "int[]")], "int"),
    reference=_max_dist_to_closest,
    brute=lambda seats: max(min(abs(i - j) for j, t in enumerate(seats) if t) for i, s in enumerate(seats) if not s),
    brute_input_limit=400,
    examples=[Example([[1, 0, 0, 0, 1, 0, 1]], "Seat 2 is 2 away from everyone."), Example([[1, 0, 0, 0]], "The last seat is 3 away."), Example([[0, 1]])],
    edge_cases=[[[1, 0]], [[0, 0, 1]], [[1, 0, 1]]],
    generator=_seats_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Number of Taps to Open to Water a Garden


def _min_taps(n: int, ranges: list[int]) -> int:
    furthest = [0] * (n + 1)
    for i, r in enumerate(ranges):
        left = max(0, i - r)
        furthest[left] = max(furthest[left], min(n, i + r))
    taps = end = reach = 0
    for i in range(n):
        reach = max(reach, furthest[i])
        if i == end:
            if reach <= i:
                return -1
            taps, end = taps + 1, reach
    return taps


def _min_taps_brute(n: int, ranges: list[int]) -> int:
    for count in range(n + 2):
        for taps in itertools.combinations(range(n + 1), count):
            covered = [False] * n
            for t in taps:
                for x in range(max(0, t - ranges[t]), min(n, t + ranges[t])):
                    covered[x] = True
            if all(covered):
                return count
    return -1


TAPS = ProblemSource(
    title="Minimum Number of Taps to Open to Water a Garden",
    statement="""
A garden covers the segment `[0, n]`. There are `n + 1` taps at positions `0..n`; tap `i`, if opened, waters `[i - ranges[i], i + ranges[i]]`.
Return the minimum number of taps to open so that the whole garden `[0, n]` is watered, or `-1` if that's impossible.
""",
    constraints="""
- `1 <= n <= 10^4`, `ranges.length == n + 1`
- `0 <= ranges[i] <= 100`
""",
    signature=function("minTaps", [("n", "int"), ("ranges", "int[]")], "int"),
    reference=_min_taps,
    brute=_min_taps_brute,
    brute_input_limit=30,
    examples=[Example([5, [3, 4, 1, 1, 0, 0]], "Tap 1 alone waters [-3, 5]."), Example([3, [0, 0, 0, 0]], "No tap waters anything.")],
    edge_cases=[[1, [1, 0]], [1, [0, 0]], [2, [0, 1, 0]], [7, [1, 2, 1, 0, 2, 1, 0, 1]]],
    generator=lambda rng: [(n := pick_n(rng, 1, 7, big=4000)), ints(rng, n + 1, 0, rng.choice([2, 100]))],
    random_count=8,
)


# ---------------------------------------------------------------- Valid Parenthesis String


def _check_valid_string(s: str) -> bool:
    low = high = 0
    for ch in s:
        low += 1 if ch == "(" else -1
        high += -1 if ch == ")" else 1
        if high < 0:
            return False
        low = max(low, 0)
    return low == 0


def _valid_string_brute(s: str) -> bool:
    stars = [i for i, c in enumerate(s) if c == "*"]
    for choice in itertools.product(["(", ")", ""], repeat=len(stars)):
        chars = list(s)
        for i, c in zip(stars, choice, strict=True):
            chars[i] = c
        depth = 0
        for c in "".join(chars):
            depth += 1 if c == "(" else -1
            if depth < 0:
                break
        else:
            if depth == 0:
                return True
    return False


VALID_PARENTHESIS_STRING = ProblemSource(
    title="Valid Parenthesis String",
    statement="""
`s` contains only `(`, `)` and `*`. Each `*` may stand for `(`, `)` or nothing. Return `true` if some choice for the stars makes `s` a
valid parenthesis string (every `(` closed by a later `)`, and no `)` without a matching earlier `(`).
""",
    constraints="""
- `1 <= s.length <= 100`
""",
    signature=function("checkValidString", [("s", "string")], "bool"),
    reference=_check_valid_string,
    brute=_valid_string_brute,
    brute_input_limit=12,
    examples=[Example(["()"]), Example(["(*)"]), Example(["(*))"], "The star becomes '('.")],
    edge_cases=[["*"], [")"], ["(("], ["**)("], ["(*()"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([8, 100])), "()*")],
    random_count=9,
)


# ---------------------------------------------------------------- Minimum Number of Swaps to Make the String Balanced


def _min_swaps_balanced(s: str) -> int:
    open_count = unmatched = 0
    for ch in s:
        if ch == "[":
            open_count += 1
        elif open_count:
            open_count -= 1
        else:
            unmatched += 1
    return (unmatched + 1) // 2


def _balanced_brute(s: str) -> int:
    def balanced(t: str) -> bool:
        depth = 0
        for ch in t:
            depth += 1 if ch == "[" else -1
            if depth < 0:
                return False
        return depth == 0

    seen, frontier = {s}, deque([(s, 0)])
    while frontier:
        cur, d = frontier.popleft()
        if balanced(cur):
            return d
        for i, j in itertools.combinations(range(len(cur)), 2):
            if cur[i] != cur[j]:
                nxt = list(cur)
                nxt[i], nxt[j] = nxt[j], nxt[i]
                t = "".join(nxt)
                if t not in seen:
                    seen.add(t)
                    frontier.append((t, d + 1))
    raise AssertionError


def _brackets_gen(rng):
    half = rng.randint(1, rng.choice([4, 5000]))
    chars = list("[" * half + "]" * half)
    rng.shuffle(chars)
    return ["".join(chars)]


SWAPS_BALANCED = ProblemSource(
    title="Minimum Number of Swaps to Make the String Balanced",
    statement="""
`s` has even length and contains exactly as many `[` as `]`. You may swap the characters at **any** two indices. Return the minimum number of
swaps needed to make `s` balanced (every `]` matches an earlier `[`).
""",
    constraints="""
- `2 <= s.length <= 10^6` (tests use up to `10^4`)
- `s` has equal numbers of `[` and `]`
""",
    signature=function("minSwaps", [("s", "string")], "int"),
    reference=_min_swaps_balanced,
    brute=_balanced_brute,
    brute_input_limit=12,
    examples=[Example(["][]["], "Swap the first and last characters."), Example(["]]][[["], "Two swaps are needed."), Example(["[]"])],
    edge_cases=[["]["], ["[[]]"], ["]]]][[[["]],
    generator=_brackets_gen,
    random_count=8,
)


PROBLEMS = [
    SORT_ARRAY,
    TEXT_JUSTIFICATION,
    BEST_TIME_II,
    WILDCARD,
    REMOVE_K_DIGITS,
    LARGEST_NUMBER,
    STRONG_PASSWORD,
    ENEMY_BATTLES,
    INTEGER_TO_ROMAN,
    VALID_ARRAY_SWAPS,
    SPECIAL_BINARY,
    MAXIMIZE_DISTANCE,
    TAPS,
    VALID_PARENTHESIS_STRING,
    SWAPS_BALANCED,
]
