"""Pattern 18: Stacks. Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import posixpath
import random
import re
from fractions import Fraction

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ints, ops, pick_n, sample, word

PATTERN_NUMBER = 18
_MOD = 10**9 + 7
_PAIRS = {")": "(", "]": "[", "}": "{"}


def _paren_string(rng: random.Random, n: int, alphabet: str) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


def _balanced(rng: random.Random, pairs: int, kinds: str = "()") -> str:
    out, stack = [], []
    opened = 0
    while opened < pairs or stack:
        if opened < pairs and (not stack or rng.random() < 0.5):
            ch = rng.choice(kinds[0::2])
            out.append(ch)
            stack.append(ch)
            opened += 1
        else:
            out.append(kinds[kinds.index(stack.pop()) + 1])
    return "".join(out)


# ---------------------------------------------------------------- Valid Parentheses


def _is_valid(s: str) -> bool:
    stack = []
    for ch in s:
        if ch in _PAIRS:
            if not stack or stack.pop() != _PAIRS[ch]:
                return False
        else:
            stack.append(ch)
    return not stack


def _valid_brute(s: str) -> bool:
    previous = None
    while previous != s:
        previous, s = s, s.replace("()", "").replace("[]", "").replace("{}", "")
    return s == ""


VALID_PARENTHESES = ProblemSource(
    title="Valid Parentheses",
    statement="""
`s` contains only the characters `()[]{}`. Return `true` if every bracket is closed by a bracket of the same type, in the correct order, and every
closing bracket has a matching opening bracket.
""",
    constraints="""
- `1 <= s.length <= 10^4`
- `s` consists only of `()[]{}`
""",
    signature=function("isValid", [("s", "string")], "bool"),
    reference=_is_valid,
    brute=_valid_brute,
    brute_input_limit=3000,
    examples=[Example(["()"]), Example(["()[]{}"]), Example(["(]"], "A round bracket closed by a square one.")],
    edge_cases=[["("], [")"], ["([)]"], ["{[]}"], ["(("]],
    generator=lambda rng: [_balanced(rng, pick_n(rng, 1, 10, big=3000), "()[]{}") if rng.random() < 0.6 else _paren_string(rng, pick_n(rng, 1, 12, big=5000), "()[]{}")],
    random_count=8,
)


# ---------------------------------------------------------------- Basic Calculator


def _calculate(s: str) -> int:
    total, sign, number = 0, 1, 0
    stack: list[tuple[int, int]] = []
    for ch in s:
        if ch.isdigit():
            number = number * 10 + int(ch)
        elif ch in "+-":
            total += sign * number
            number, sign = 0, 1 if ch == "+" else -1
        elif ch == "(":
            stack.append((total, sign))
            total, sign = 0, 1
        elif ch == ")":
            inner = total + sign * number
            total, outer_sign = stack.pop()
            total += outer_sign * inner
            number, sign = 0, 1
    return total + sign * number


def _expression(rng: random.Random, depth: int, first: bool = True) -> str:
    """Random +/- expression with parentheses; '-' may be unary, '+' never is."""
    parts = []
    for i in range(rng.randint(1, 4)):
        if i:
            parts.append(rng.choice([" + ", " - ", "-", "+"]))
        elif rng.random() < 0.2:
            parts.append("-")
        parts.append(f"({_expression(rng, depth - 1, False)})" if depth and rng.random() < 0.35 else str(rng.randint(0, rng.choice([9, 1000]))))
    return "".join(parts)


BASIC_CALCULATOR = ProblemSource(
    title="Basic Calculator",
    statement="""
Evaluate the expression `s`, which contains non-negative integers, `+`, `-`, parentheses and spaces, and return the result. `-` may be used as a
unary minus (for example `-1` or `-(2 + 3)`); `+` is never unary. No two operators appear in a row.

Don't use any built-in function that evaluates strings as expressions.
""",
    constraints="""
- `1 <= s.length <= 3 * 10^5`
- `s` is a valid expression; every intermediate result and the answer fit in a signed 32-bit integer
""",
    signature=function("calculate", [("s", "string")], "int"),
    reference=_calculate,
    brute=lambda s: eval(s.replace(" ", ""), {"__builtins__": {}}),  # noqa: S307 - oracle over our own generated input
    examples=[Example(["1 + 1"]), Example([" 2-1 + 2 "]), Example(["(1+(4+5+2)-3)+(6+8)"])],
    edge_cases=[["7"], ["-(2 + 3)"], ["- (3 + (4 + 5))"], ["2147483647"], ["1-(     -2)"]],
    generator=lambda rng: [_expression(rng, rng.randint(0, 3))],
    random_count=10,
)


# ---------------------------------------------------------------- Remove All Adjacent Duplicates In String


def _remove_duplicates(s: str) -> str:
    stack: list[str] = []
    for ch in s:
        if stack and stack[-1] == ch:
            stack.pop()
        else:
            stack.append(ch)
    return "".join(stack)


def _remove_duplicates_brute(s: str) -> str:
    pattern = re.compile(r"(.)\1")
    while pattern.search(s):
        s = pattern.sub("", s, count=1)
    return s


REMOVE_ADJACENT = ProblemSource(
    title="Remove All Adjacent Duplicates In String",
    statement="""
Repeatedly pick two adjacent equal letters in `s` and delete them, until no such pair remains. Return the final string (it is unique).
""",
    constraints="""
- `1 <= s.length <= 10^5`
- lowercase English letters only
""",
    signature=function("removeDuplicates", [("s", "string")], "string"),
    reference=_remove_duplicates,
    brute=_remove_duplicates_brute,
    brute_input_limit=1500,
    examples=[Example(["abbaca"], "Remove \"bb\" to get \"aaca\", then \"aa\": \"ca\"."), Example(["azxxzy"])],
    edge_cases=[["a"], ["aa"], ["abba"], ["abc"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 20, big=10**4), rng.choice(["ab", "abc"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Remove to Make Valid Parentheses


def _min_remove_to_make_valid(s: str) -> str:
    chars = list(s)
    stack = []
    for i, ch in enumerate(chars):
        if ch == "(":
            stack.append(i)
        elif ch == ")":
            if stack:
                stack.pop()
            else:
                chars[i] = ""
    for i in stack:
        chars[i] = ""
    return "".join(chars)


def _min_remove_brute(s: str) -> str:
    positions = [i for i, ch in enumerate(s) if ch in "()"]
    if len(positions) > 14:
        return NotImplemented
    for removed in range(len(positions) + 1):
        for drop in itertools.combinations(positions, removed):
            candidate = "".join(ch for i, ch in enumerate(s) if i not in drop)
            depth = 0
            for ch in candidate:
                depth += {"(": 1, ")": -1}.get(ch, 0)
                if depth < 0:
                    break
            if depth == 0:
                return candidate
    raise AssertionError("removing every parenthesis always works")


MIN_REMOVE_VALID = ProblemSource(
    title="Minimum Remove to Make Valid Parentheses",
    statement="""
`s` contains `(`, `)` and lowercase letters. Remove the minimum number of parentheses so that the parentheses in the result are balanced, and
return the result. Letters must stay in place. If several results are possible, any of them is accepted.
""",
    constraints="""
- `1 <= s.length <= 10^5`
- `s[i]` is `(`, `)` or a lowercase English letter
""",
    signature=function("minRemoveToMakeValid", [("s", "string")], "string"),
    reference=_min_remove_to_make_valid,
    brute=_min_remove_brute,
    compare="checker",
    checker="min_remove_parens",
    examples=[Example(["lee(t(c)o)de)"], "\"lee(t(co)de)\" and \"lee(t(c)ode)\" are also accepted."), Example(["a)b(c)d"]), Example(["))(("], "Everything must go.")],
    edge_cases=[["a"], ["("], ["()"], [")("], ["(a(b)"]],
    generator=lambda rng: [_paren_string(rng, pick_n(rng, 1, 16, big=10**4), rng.choice(["()ab", "((()a", "())b"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Exclusive Time of Functions


def _exclusive_time(n: int, logs: list[str]) -> list[int]:
    result = [0] * n
    stack: list[int] = []
    previous = 0
    for entry in logs:
        fid, kind, ts = entry.split(":")
        time = int(ts)
        if kind == "start":
            if stack:
                result[stack[-1]] += time - previous
            stack.append(int(fid))
            previous = time
        else:
            result[stack.pop()] += time - previous + 1
            previous = time + 1
    return result


def _exclusive_brute(n: int, logs: list[str]) -> list[int]:
    """Each time unit belongs to the most deeply nested call that covers it."""
    calls, stack = [], []
    for entry in logs:
        fid, kind, ts = entry.split(":")
        if kind == "start":
            stack.append((int(fid), int(ts)))
        else:
            fid_, begin = stack.pop()
            calls.append((fid_, begin, int(ts), len(stack)))
    result = [0] * n
    for t in range(max(c[2] for c in calls) + 1):
        covering = [c for c in calls if c[1] <= t <= c[2]]
        if covering:
            result[max(covering, key=lambda c: c[3])[0]] += 1
    return result


def _logs_gen(rng: random.Random) -> list:
    n = rng.randint(1, rng.choice([3, 20]))
    logs, stack, t = [], [], 0
    calls = pick_n(rng, 1, 8, big=200)
    started = 0
    while started < calls or stack:
        if started < calls and (not stack or rng.random() < 0.5):
            fid = rng.randrange(n)
            logs.append(f"{fid}:start:{t}")
            stack.append(fid)
            started += 1
        else:
            logs.append(f"{stack.pop()}:end:{t}")
            t += 1  # an end occupies its whole unit
        t += rng.choice([0, 0, 1, 3])
    return [n, logs]


EXCLUSIVE_TIME = ProblemSource(
    title="Exclusive Time of Functions",
    statement="""
A single-threaded CPU runs functions with ids `0` to `n - 1`, recorded in `logs` in timestamp order. Each entry is `"id:start:t"` (the function
starts at the **beginning** of time unit `t`) or `"id:end:t"` (it ends at the **end** of unit `t`). Functions can call each other, including
themselves; a caller is paused while its callee runs.

A function's *exclusive time* is the total number of units during which it was the one running. Return the exclusive time of every function,
indexed by id.
""",
    constraints="""
- `1 <= n <= 100`, `2 <= logs.length <= 500`
- the logs describe a valid, fully nested execution with non-decreasing timestamps
""",
    signature=function("exclusiveTime", [("n", "int"), ("logs", "string[]")], "int[]"),
    reference=_exclusive_time,
    brute=_exclusive_brute,
    brute_input_limit=3000,
    examples=[
        Example([2, ["0:start:0", "1:start:2", "1:end:5", "0:end:6"]], "Function 0 runs units 0-1 and 6; function 1 runs 2-5."),
        Example([1, ["0:start:0", "0:start:2", "0:end:5", "0:start:6", "0:end:6", "0:end:7"]], "Recursive calls all count for function 0."),
        Example([2, ["0:start:0", "0:start:2", "0:end:5", "1:start:6", "1:end:6", "0:end:7"]]),
    ],
    edge_cases=[[1, ["0:start:0", "0:end:0"]], [2, ["0:start:0", "1:start:0", "1:end:0", "0:end:0"]]],
    generator=_logs_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Flatten Nested List Iterator


class _NestedIterator:
    def __init__(self, tokens: list[str]) -> None:
        self.stack = [iter(tokens)]
        self.peeked: int | None = None

    def hasNext(self) -> bool:  # noqa: N802 - judge method name
        while self.peeked is None and self.stack:
            token = next(self.stack[-1], None)
            if token is None:
                self.stack.pop()
            elif token not in ("[", "]"):
                self.peeked = int(token)
        return self.peeked is not None

    def next(self) -> int:
        self.hasNext()
        value, self.peeked = self.peeked, None
        return value  # type: ignore[return-value]


class _NestedIteratorBrute:
    def __init__(self, tokens: list[str]) -> None:
        self.values = [int(t) for t in tokens if t not in ("[", "]")]
        self.index = 0

    def hasNext(self) -> bool:  # noqa: N802
        return self.index < len(self.values)

    def next(self) -> int:
        self.index += 1
        return self.values[self.index - 1]


def _nested_tokens(rng: random.Random, depth: int, budget: list[int]) -> list[str]:
    out = ["["]
    for _ in range(rng.randint(0, 4)):
        if budget[0] <= 0:
            break
        budget[0] -= 1
        if depth and rng.random() < 0.4:
            out += _nested_tokens(rng, depth - 1, budget)
        else:
            out.append(str(rng.randint(-(10**6), 10**6)))
    return out + ["]"]


def _nested_gen(rng: random.Random) -> dict:
    tokens = _nested_tokens(rng, rng.randint(0, 4), [pick_n(rng, 1, 15, big=500)])
    count = sum(t not in ("[", "]") for t in tokens)
    calls = [("NestedIterator", [tokens])]
    for _ in range(count):
        if rng.random() < 0.5:
            calls.append(("hasNext", []))
        calls.append(("next", []))
    calls.append(("hasNext", []))
    return ops(*calls)


FLATTEN_NESTED = ProblemSource(
    title="Flatten Nested List Iterator",
    statement="""
*Adapted I/O:* a nested list of integers (each element is an integer or another nested list, to any depth) is given as a **token stream**: `"["`
opens a list, `"]"` closes it, and any other token is an integer. For example `[[1,1],2,[1,1]]` arrives as
`["[", "[", "1", "1", "]", "2", "[", "1", "1", "]", "]"]`.

Design `NestedIterator`, which yields the integers in order, flattened:
- `NestedIterator(tokens)` initialises the iterator.
- `next()` returns the next integer.
- `hasNext()` returns `true` if integers remain.

Process the tokens lazily, the way you would walk real nested lists, rather than copying all integers up front.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor).
`next()` is only called when an integer remains.
""",
    constraints="""
- the outermost list is always present; lists may be empty
- `1 <= tokens.length <= 10^4`
- `-10^6 <= integer <= 10^6`
""",
    signature=design("NestedIterator", [("tokens", "string[]")], [("next", [], "int"), ("hasNext", [], "bool")]),
    reference=_NestedIterator,
    brute=_NestedIteratorBrute,
    is_variant=True,
    examples=[
        Example(ops(("NestedIterator", [["[", "[", "1", "1", "]", "2", "[", "1", "1", "]", "]"]]), ("next", []), ("next", []), ("next", []), ("next", []), ("next", []), ("hasNext", [])), "Flattened: 1, 1, 2, 1, 1."),
        Example(ops(("NestedIterator", [["[", "1", "[", "4", "[", "6", "]", "]", "]"]]), ("hasNext", []), ("next", []), ("next", []), ("next", []), ("hasNext", []))),
    ],
    edge_cases=[ops(("NestedIterator", [["[", "]"]]), ("hasNext", [])), ops(("NestedIterator", [["[", "[", "]", "[", "[", "]", "]", "3", "]"]]), ("hasNext", []), ("next", []), ("hasNext", []))],
    generator=_nested_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Implement Queue Using Stacks


class _MyQueue:
    def __init__(self) -> None:
        self.inbox: list[int] = []
        self.outbox: list[int] = []

    def push(self, x: int) -> None:
        self.inbox.append(x)

    def _shift(self) -> None:
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())

    def pop(self) -> int:
        self._shift()
        return self.outbox.pop()

    def peek(self) -> int:
        self._shift()
        return self.outbox[-1]

    def empty(self) -> bool:
        return not self.inbox and not self.outbox


class _MyQueueBrute:
    def __init__(self) -> None:
        self.items: list[int] = []

    def push(self, x: int) -> None:
        self.items.append(x)

    def pop(self) -> int:
        return self.items.pop(0)

    def peek(self) -> int:
        return self.items[0]

    def empty(self) -> bool:
        return not self.items


def _queue_gen(rng: random.Random) -> dict:
    calls: list[tuple[str, list]] = [("MyQueue", [])]
    size = 0
    for _ in range(pick_n(rng, 1, 20, big=100)):
        op = rng.choice(["push", "push", "pop", "peek", "empty"]) if size else rng.choice(["push", "push", "empty"])
        if op == "push":
            calls.append(("push", [rng.randint(1, 9)]))
            size += 1
        else:
            calls.append((op, []))
            size -= op == "pop"
    return ops(*calls)


QUEUE_USING_STACKS = ProblemSource(
    title="Implement Queue Using Stacks",
    statement="""
Implement a first-in-first-out queue using only two stacks (only push-to-top, peek/pop-from-top, size and is-empty operations):
- `push(x)` adds `x` to the back of the queue.
- `pop()` removes and returns the front element.
- `peek()` returns the front element.
- `empty()` returns `true` if the queue is empty.

Every operation should take amortised `O(1)` time.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor
and `push`). `pop` and `peek` are only called on a non-empty queue.
""",
    constraints="""
- `1 <= x <= 9`
- at most `100` calls
""",
    signature=design("MyQueue", [], [("push", [("x", "int")], "void"), ("pop", [], "int"), ("peek", [], "int"), ("empty", [], "bool")]),
    reference=_MyQueue,
    brute=_MyQueueBrute,
    examples=[Example(ops(("MyQueue", []), ("push", [1]), ("push", [2]), ("peek", []), ("pop", []), ("empty", [])), "The front is 1; after popping it, 2 remains."), Example(ops(("MyQueue", []), ("empty", [])))],
    edge_cases=[ops(("MyQueue", []), ("push", [5]), ("pop", []), ("empty", []), ("push", [6]), ("push", [7]), ("pop", []), ("push", [8]), ("pop", []), ("peek", []))],
    generator=_queue_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Decode String


def _decode_string(s: str) -> str:
    stack: list[tuple[str, int]] = []
    current, number = "", 0
    for ch in s:
        if ch.isdigit():
            number = number * 10 + int(ch)
        elif ch == "[":
            stack.append((current, number))
            current, number = "", 0
        elif ch == "]":
            prefix, times = stack.pop()
            current = prefix + current * times
        else:
            current += ch
    return current


def _decode_brute(s: str) -> str:
    innermost = re.compile(r"(\d+)\[([a-z]*)\]")
    while "[" in s:
        s = innermost.sub(lambda m: m.group(2) * int(m.group(1)), s)
    return s


def _encoded(rng: random.Random, depth: int) -> str:
    parts = []
    for _ in range(rng.randint(1, 3)):
        if depth and rng.random() < 0.5:
            parts.append(f"{rng.randint(1, 4 if depth > 1 else 12)}[{_encoded(rng, depth - 1)}]")
        else:
            parts.append(word(rng, rng.randint(1, 3), "abc"))
    return "".join(parts)


DECODE_STRING = ProblemSource(
    title="Decode String",
    statement="""
Decode `s`, where `k[text]` means `text` repeated exactly `k` times; encodings can be nested. Digits only ever appear as repeat counts, and the
input is always well formed. Return the decoded string.
""",
    constraints="""
- `1 <= s.length <= 100`
- `s` consists of lowercase letters, digits and square brackets; `1 <= k <= 300`
- the decoded string is at most `10^5` characters long
""",
    signature=function("decodeString", [("s", "string")], "string"),
    reference=_decode_string,
    brute=_decode_brute,
    examples=[Example(["3[a]2[bc]"], "\"aaabcbc\"."), Example(["3[a2[c]]"], "\"accaccacc\"."), Example(["2[abc]3[cd]ef"])],
    edge_cases=[["a"], ["1[z]"], ["10[a]"], ["2[a2[b]]c"]],
    generator=lambda rng: [_encoded(rng, rng.randint(1, 3))],
    random_count=8,
)


# ---------------------------------------------------------------- Daily Temperatures


def _daily_temperatures(temperatures: list[int]) -> list[int]:
    answer = [0] * len(temperatures)
    stack: list[int] = []
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            answer[j] = i - j
        stack.append(i)
    return answer


def _daily_brute(temperatures: list[int]) -> list[int]:
    n = len(temperatures)
    return [next((j - i for j in range(i + 1, n) if temperatures[j] > temperatures[i]), 0) for i in range(n)]


DAILY_TEMPERATURES = ProblemSource(
    title="Daily Temperatures",
    statement="""
`temperatures[i]` is the temperature on day `i`. For each day, return how many days you have to wait for a strictly warmer day, or `0` if there
is none.
""",
    constraints="""
- `1 <= temperatures.length <= 10^5`
- `30 <= temperatures[i] <= 100`
""",
    signature=function("dailyTemperatures", [("temperatures", "int[]")], "int[]"),
    reference=_daily_temperatures,
    brute=_daily_brute,
    brute_input_limit=3000,
    examples=[Example([[73, 74, 75, 71, 69, 72, 76, 73]]), Example([[30, 40, 50, 60]]), Example([[30, 60, 90]])],
    edge_cases=[[[50]], [[100, 90, 80]], [[70, 70, 70, 71]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=10**4), 30, rng.choice([35, 100]))],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum String Length After Removing Substrings


def _min_length(s: str) -> int:
    stack: list[str] = []
    for ch in s:
        if stack and stack[-1] + ch in ("AB", "CD"):
            stack.pop()
        else:
            stack.append(ch)
    return len(stack)


def _min_length_brute(s: str) -> int:
    previous = None
    while previous != s:
        previous, s = s, s.replace("AB", "").replace("CD", "")
    return len(s)


MIN_LENGTH_REMOVING = ProblemSource(
    title="Minimum String Length After Removing Substrings",
    statement="""
`s` consists of uppercase English letters. In one operation you may delete any occurrence of the substring `"AB"` or `"CD"`; the remaining parts
join together, possibly creating new occurrences. Return the minimum possible length of the resulting string.
""",
    constraints="""
- `1 <= s.length <= 100`
- uppercase English letters only
""",
    signature=function("minLength", [("s", "string")], "int"),
    reference=_min_length,
    brute=_min_length_brute,
    examples=[Example(["ABFCACDB"], "Remove AB, then CD, then AB: \"FC\" remains."), Example(["ACBBD"], "Nothing can be removed.")],
    edge_cases=[["A"], ["AB"], ["CABD"], ["BA"]],
    generator=lambda rng: [word(rng, rng.randint(1, 100), rng.choice(["ABCD", "ABCDE", "ABCDXYZ"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Valid Subarrays


def _valid_subarrays(nums: list[int]) -> int:
    count = 0
    stack: list[int] = []
    for x in nums:
        while stack and stack[-1] > x:
            stack.pop()
        stack.append(x)
        count += len(stack)
    return count


def _valid_subarrays_brute(nums: list[int]) -> int:
    n = len(nums)
    return sum(1 for i in range(n) for j in range(i, n) if nums[i] == min(nums[i : j + 1]))


VALID_SUBARRAYS = ProblemSource(
    title="Number of Valid Subarrays",
    statement="""
Return the number of non-empty contiguous subarrays of `nums` whose leftmost element is not larger than any other element of the subarray.
""",
    constraints="""
- `1 <= nums.length <= 5 * 10^4`
- `0 <= nums[i] <= 10^5`
""",
    signature=function("validSubarrays", [("nums", "int[]")], "int"),
    reference=_valid_subarrays,
    brute=lambda nums: _valid_subarrays_brute(nums) if len(nums) <= 150 else NotImplemented,
    examples=[Example([[1, 4, 2, 5, 3]], "[1],[4],[2],[5],[3],[1,4],[2,5],[1,4,2],[2,5,3],[1,4,2,5],[1,4,2,5,3]: 11."), Example([[3, 2, 1]]), Example([[2, 2, 2]])],
    edge_cases=[[[0]], [[1, 2, 3, 4]], [[100000, 0, 100000]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=10**4), 0, rng.choice([5, 10**5]))],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Visible People in a Queue


def _can_see_persons_count(heights: list[int]) -> list[int]:
    answer = [0] * len(heights)
    stack: list[int] = []
    for i in range(len(heights) - 1, -1, -1):
        while stack and stack[-1] < heights[i]:
            stack.pop()
            answer[i] += 1
        if stack:
            answer[i] += 1
        stack.append(heights[i])
    return answer


def _visible_brute(heights: list[int]) -> list[int]:
    n = len(heights)
    return [sum(1 for j in range(i + 1, n) if max(heights[i + 1 : j], default=0) < min(heights[i], heights[j])) for i in range(n)]


VISIBLE_PEOPLE = ProblemSource(
    title="Number of Visible People in a Queue",
    statement="""
`heights` (all distinct) lists people standing in a queue from left to right. Person `i` can see person `j > i` if everyone standing between
them is shorter than both of them. Return, for every person, how many people to their right they can see.
""",
    constraints="""
- `1 <= heights.length <= 10^5`
- `1 <= heights[i] <= 10^5`, all distinct
""",
    signature=function("canSeePersonsCount", [("heights", "int[]")], "int[]"),
    reference=_can_see_persons_count,
    brute=lambda heights: _visible_brute(heights) if len(heights) <= 150 else NotImplemented,
    examples=[Example([[10, 6, 8, 5, 11, 9]], "Person 0 sees 6, 8 and 11."), Example([[5, 1, 2, 3, 10]])],
    edge_cases=[[[1]], [[1, 2, 3]], [[3, 2, 1]]],
    generator=lambda rng: [sample(rng, range(1, 10**5 + 1), pick_n(rng, 1, 20, big=10**4))],
    random_count=8,
)


# ---------------------------------------------------------------- Parsing A Boolean Expression


def _parse_bool_expr(expression: str) -> bool:
    stack: list[str] = []
    for ch in expression:
        if ch == ",":
            continue
        if ch != ")":
            stack.append(ch)
            continue
        values = []
        while stack[-1] != "(":
            values.append(stack.pop() == "t")
        stack.pop()
        op = stack.pop()
        result = not values[0] if op == "!" else all(values) if op == "&" else any(values)
        stack.append("t" if result else "f")
    return stack[-1] == "t"


def _parse_bool_brute(expression: str) -> bool:
    def parse(i: int) -> tuple[bool, int]:
        ch = expression[i]
        if ch in "tf":
            return ch == "t", i + 1
        values, i = [], i + 2  # skip operator and "("
        while True:
            value, i = parse(i)
            values.append(value)
            if expression[i] == ")":
                break
            i += 1  # skip ","
        combine = {"!": lambda v: not v[0], "&": all, "|": any}[ch]
        return combine(values), i + 1

    return parse(0)[0]


def _bool_expr(rng: random.Random, depth: int) -> str:
    if depth == 0 or rng.random() < 0.25:
        return rng.choice("tf")
    op = rng.choice("!&|")
    count = 1 if op == "!" else rng.randint(1, 4)
    return f"{op}({','.join(_bool_expr(rng, depth - 1) for _ in range(count))})"


PARSE_BOOLEAN = ProblemSource(
    title="Parsing A Boolean Expression",
    statement="""
Evaluate a boolean expression built from:
- `'t'` (true) and `'f'` (false);
- `'!(e)'`: logical NOT of one sub-expression;
- `'&(e1,e2,...)'`: logical AND of one or more sub-expressions;
- `'|(e1,e2,...)'`: logical OR of one or more sub-expressions.

The expression is always valid.
""",
    constraints="""
- `1 <= expression.length <= 2 * 10^4`
- characters are among `(),!&|tf`
""",
    signature=function("parseBoolExpr", [("expression", "string")], "bool"),
    reference=_parse_bool_expr,
    brute=_parse_bool_brute,
    brute_input_limit=6000,
    examples=[Example(["&(|(f))"], "|(f) is false, so the AND is false."), Example(["|(f,f,f,t)"]), Example(["!(&(f,t))"])],
    edge_cases=[["t"], ["f"], ["!(t)"], ["&(t,t,t)"]],
    generator=lambda rng: [_bool_expr(rng, rng.randint(1, 6))],
    random_count=10,
)


# ---------------------------------------------------------------- Remove Duplicate Letters


def _remove_duplicate_letters(s: str) -> str:
    last = {ch: i for i, ch in enumerate(s)}
    stack: list[str] = []
    for i, ch in enumerate(s):
        if ch in stack:
            continue
        while stack and stack[-1] > ch and last[stack[-1]] > i:
            stack.pop()
        stack.append(ch)
    return "".join(stack)


def _remove_letters_brute(s: str) -> str:
    out = ""
    while s:
        needed = set(s)
        pick = min(c for c in needed if needed <= set(s[s.index(c) :]))
        out += pick
        s = s[s.index(pick) + 1 :].replace(pick, "")
    return out


REMOVE_DUPLICATE_LETTERS = ProblemSource(
    title="Remove Duplicate Letters",
    statement="""
Delete letters from `s` so that every distinct letter appears exactly once. Among all possible results, return the lexicographically smallest.
""",
    constraints="""
- `1 <= s.length <= 10^4`
- lowercase English letters only
""",
    signature=function("removeDuplicateLetters", [("s", "string")], "string"),
    reference=_remove_duplicate_letters,
    brute=_remove_letters_brute,
    brute_input_limit=3000,
    examples=[Example(["bcabc"]), Example(["cbacdcbc"], "\"acdb\".")],
    edge_cases=[["a"], ["aaaa"], ["abcd"], ["dcba"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 20, big=10**4), rng.choice(["abcd", "abcdefg", "abcdefghijklmnopqrstuvwxyz"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Valid Parentheses


def _longest_valid_parentheses(s: str) -> int:
    best = 0
    stack = [-1]
    for i, ch in enumerate(s):
        if ch == "(":
            stack.append(i)
        else:
            stack.pop()
            if stack:
                best = max(best, i - stack[-1])
            else:
                stack.append(i)
    return best


def _longest_valid_brute(s: str) -> int:
    n = len(s)
    for length in range(n - n % 2, 0, -2):
        for i in range(n - length + 1):
            depth = 0
            for ch in s[i : i + length]:
                depth += 1 if ch == "(" else -1
                if depth < 0:
                    break
            if depth == 0:
                return length
    return 0


LONGEST_VALID_PARENTHESES = ProblemSource(
    title="Longest Valid Parentheses",
    statement="""
`s` contains only `(` and `)`. Return the length of the longest contiguous substring that is a well-formed (balanced) parentheses string.
""",
    constraints="""
- `0 <= s.length <= 3 * 10^4`
- `s[i]` is `(` or `)`
""",
    signature=function("longestValidParentheses", [("s", "string")], "int"),
    reference=_longest_valid_parentheses,
    brute=lambda s: _longest_valid_brute(s) if len(s) <= 200 else NotImplemented,
    examples=[Example(["(()"], "\"()\"."), Example([")()())"], "\"()()\"."), Example([""])],
    edge_cases=[["("], ["()"], ["()(()"], ["(()())"]],
    generator=lambda rng: [_paren_string(rng, pick_n(rng, 1, 30, big=10**4), rng.choice(["()", "(()", "())"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Next Greater Element IV


def _second_greater_element(nums: list[int]) -> list[int]:
    answer = [-1] * len(nums)
    first: list[int] = []  # waiting for their first greater element
    second: list[int] = []  # waiting for their second
    for i, x in enumerate(nums):
        while second and nums[second[-1]] < x:
            answer[second.pop()] = x
        moved = []
        while first and nums[first[-1]] < x:
            moved.append(first.pop())
        second += moved[::-1]
        first.append(i)
    return answer


def _second_greater_brute(nums: list[int]) -> list[int]:
    out = []
    for i, x in enumerate(nums):
        greater = [y for y in nums[i + 1 :] if y > x]
        out.append(greater[1] if len(greater) >= 2 else -1)
    return out


NEXT_GREATER_IV = ProblemSource(
    title="Next Greater Element IV",
    statement="""
For each `nums[i]`, its *second greater* element is `nums[j]` where `j > i`, `nums[j] > nums[i]`, and exactly one index `k` with `i < k < j` has
`nums[k] > nums[i]`. Return the second greater element of every position, or `-1` where none exists.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `0 <= nums[i] <= 10^9`
""",
    signature=function("secondGreaterElement", [("nums", "int[]")], "int[]"),
    reference=_second_greater_element,
    brute=lambda nums: _second_greater_brute(nums) if len(nums) <= 300 else NotImplemented,
    examples=[Example([[2, 4, 0, 9, 6]], "For 2, the greater elements are 4, 9, 6: the second is 9."), Example([[3, 3]])],
    edge_cases=[[[1]], [[1, 2, 3]], [[3, 2, 1]], [[1, 5, 5, 5]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=10**4), 0, rng.choice([6, 10**9]))],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Width Ramp


def _max_width_ramp(nums: list[int]) -> int:
    candidates: list[int] = []
    for i, x in enumerate(nums):
        if not candidates or nums[candidates[-1]] > x:
            candidates.append(i)
    best = 0
    for j in range(len(nums) - 1, -1, -1):
        while candidates and nums[candidates[-1]] <= nums[j]:
            best = max(best, j - candidates.pop())
    return best


def _ramp_brute(nums: list[int]) -> int:
    n = len(nums)
    return max((j - i for i in range(n) for j in range(i, n) if nums[i] <= nums[j]), default=0)


MAX_WIDTH_RAMP = ProblemSource(
    title="Maximum Width Ramp",
    statement="""
A *ramp* is a pair of indices `i < j` with `nums[i] <= nums[j]`; its width is `j - i`. Return the maximum width of a ramp in `nums`, or `0` if
there is none.
""",
    constraints="""
- `2 <= nums.length <= 5 * 10^4`
- `0 <= nums[i] <= 5 * 10^4`
""",
    signature=function("maxWidthRamp", [("nums", "int[]")], "int"),
    reference=_max_width_ramp,
    brute=lambda nums: _ramp_brute(nums) if len(nums) <= 300 else NotImplemented,
    examples=[Example([[6, 0, 8, 2, 1, 5]], "(1, 5): 0 <= 5."), Example([[9, 8, 1, 0, 1, 9, 4, 0, 4, 1]])],
    edge_cases=[[[1, 0]], [[0, 1]], [[5, 5]], [[3, 2, 1, 0]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 2, 20, big=10**4), 0, rng.choice([10, 5 * 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Basic Calculator II


def _calculate_ii(s: str) -> int:
    stack: list[int] = []
    number, op = 0, "+"
    for i, ch in enumerate(s):
        if ch.isdigit():
            number = number * 10 + int(ch)
        if ch in "+-*/" or i == len(s) - 1:
            if op == "+":
                stack.append(number)
            elif op == "-":
                stack.append(-number)
            elif op == "*":
                stack.append(stack.pop() * number)
            else:
                left = stack.pop()
                quotient = abs(left) // number  # truncate toward zero
                stack.append(quotient if left >= 0 else -quotient)
            number, op = 0, ch
    return sum(stack)


def _calculate_ii_brute(s: str) -> int:
    total = 0
    for sign, term in re.findall(r"([+-]?)([^+-]+)", s.replace(" ", "")):
        factors = re.split(r"([*/])", term)
        value = int(factors[0])
        for op, operand in zip(factors[1::2], factors[2::2], strict=True):
            value = value * int(operand) if op == "*" else value // int(operand)
        total += -value if sign == "-" else value
    return total


def _expression_ii(rng: random.Random) -> str:
    parts = [str(rng.randint(0, 20))]
    for _ in range(rng.randint(0, rng.choice([3, 12]))):
        op = rng.choice("+-*/")
        parts += [f" {op} " if rng.random() < 0.5 else op, str(rng.randint(1, 20) if op == "/" else rng.randint(0, 20))]
    return "".join(parts)


BASIC_CALCULATOR_II = ProblemSource(
    title="Basic Calculator II",
    statement="""
Evaluate `s`, which contains non-negative integers, the operators `+ - * /` and spaces, with the usual precedence (`*` and `/` before `+` and
`-`). Integer division truncates toward zero. Return the result.

Don't use any built-in function that evaluates strings as expressions.
""",
    constraints="""
- `1 <= s.length <= 3 * 10^5`
- `s` is a valid expression with no unary operators and no division by zero
- every intermediate result and the answer fit in a signed 32-bit integer
""",
    signature=function("calculate", [("s", "string")], "int"),
    reference=_calculate_ii,
    brute=_calculate_ii_brute,
    examples=[Example(["3+2*2"]), Example([" 3/2 "]), Example([" 3+5 / 2 "])],
    edge_cases=[["0"], ["14-3/2"], ["2147483647"], ["1*2*3*4*5-6/7"]],
    generator=lambda rng: [_expression_ii(rng)],
    random_count=10,
)


# ---------------------------------------------------------------- Remove All Adjacent Duplicates in String II


def _remove_duplicates_k(s: str, k: int) -> str:
    stack: list[list] = []  # [char, run length]
    for ch in s:
        if stack and stack[-1][0] == ch:
            stack[-1][1] += 1
            if stack[-1][1] == k:
                stack.pop()
        else:
            stack.append([ch, 1])
    return "".join(ch * count for ch, count in stack)


def _remove_k_brute(s: str, k: int) -> str:
    pattern = re.compile(rf"(.)\1{{{k - 1}}}")
    while pattern.search(s):
        s = pattern.sub("", s, count=1)
    return s


REMOVE_ADJACENT_II = ProblemSource(
    title="Remove All Adjacent Duplicates in String II",
    statement="""
A *`k`-duplicate removal* deletes `k` adjacent equal letters from `s`, joining the remaining parts. Repeat removals until none is possible and
return the final string (it is unique).
""",
    constraints="""
- `1 <= s.length <= 10^5`
- `2 <= k <= 10^4`
- lowercase English letters only
""",
    signature=function("removeDuplicates", [("s", "string"), ("k", "int")], "string"),
    reference=_remove_duplicates_k,
    brute=_remove_k_brute,
    brute_input_limit=1500,
    examples=[Example(["abcd", 2], "Nothing to remove."), Example(["deeedbbcccbdaa", 3], "Remove eee and ccc, then bbb, then ddd: \"aa\"."), Example(["pbbcggttciiippooaais", 2])],
    edge_cases=[["a", 2], ["aa", 2], ["aaa", 2], ["abbbba", 4]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 30, big=10**4), rng.choice(["ab", "abc"])), rng.randint(2, 4)],
    random_count=8,
)


# ---------------------------------------------------------------- Simplify Path


def _simplify_path(path: str) -> str:
    stack: list[str] = []
    for part in path.split("/"):
        if part == "..":
            if stack:
                stack.pop()
        elif part and part != ".":
            stack.append(part)
    return "/" + "/".join(stack)


def _path_gen(rng: random.Random) -> list:
    parts = [rng.choice(["a", "bb", "c_1", ".", "..", "...", "", "home"]) for _ in range(rng.randint(0, 10))]
    return ["/" + "/".join(parts) + rng.choice(["", "/", "//"])]


SIMPLIFY_PATH = ProblemSource(
    title="Simplify Path",
    statement="""
`path` is an absolute Unix-style path (it starts with `/`). Return its canonical form:
- `.` means the current directory and `..` the parent directory (the parent of the root is the root);
- runs of slashes such as `//` count as one slash;
- any other name, including `...`, is a normal directory name.

The canonical path starts with a single `/`, separates names with single slashes, and has no trailing slash (unless it is just `/`).
""",
    constraints="""
- `1 <= path.length <= 3000`
- `path` consists of English letters, digits, `.`, `/` and `_`, and starts with `/`
""",
    signature=function("simplifyPath", [("path", "string")], "string"),
    reference=_simplify_path,
    brute=lambda path: "/" + posixpath.normpath(path).lstrip("/"),
    examples=[Example(["/home/"]), Example(["/home//foo/"]), Example(["/.../a/../b/c/../d/./"], "\"...\" is a directory name.")],
    edge_cases=[["/"], ["/../"], ["//a//b/.."], ["/a/./b/../../c/"]],
    generator=_path_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Sum of Subarray Minimums


def _sum_subarray_mins(arr: list[int]) -> int:
    n = len(arr)
    left, right = [0] * n, [0] * n
    stack: list[int] = []
    for i in range(n):  # left[i]: subarrays ending at i where arr[i] is the (leftmost-strict) minimum
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        left[i] = i - (stack[-1] if stack else -1)
        stack.append(i)
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        right[i] = (stack[-1] if stack else n) - i
        stack.append(i)
    return sum(arr[i] * left[i] * right[i] for i in range(n)) % _MOD


def _subarray_mins_brute(arr: list[int]) -> int:
    total = 0
    for i in range(len(arr)):
        low = arr[i]
        for j in range(i, len(arr)):
            low = min(low, arr[j])
            total += low
    return total % _MOD


SUBARRAY_MINIMUMS = ProblemSource(
    title="Sum of Subarray Minimums",
    statement="""
Return the sum of `min(b)` over every non-empty contiguous subarray `b` of `arr`, modulo `10^9 + 7`.
""",
    constraints="""
- `1 <= arr.length <= 3 * 10^4`
- `1 <= arr[i] <= 3 * 10^4`
""",
    signature=function("sumSubarrayMins", [("arr", "int[]")], "int"),
    reference=_sum_subarray_mins,
    brute=_subarray_mins_brute,
    brute_input_limit=2500,
    examples=[Example([[3, 1, 2, 4]], "Minimums: 3,1,2,4,1,1,2,1,1,1 sum to 17."), Example([[11, 81, 94, 43, 3]])],
    edge_cases=[[[1]], [[5, 5, 5]], [[30000] * 50]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 20, big=3 * 10**4), 1, rng.choice([5, 3 * 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Car Fleet


def _car_fleet(target: int, position: list[int], speed: list[int]) -> int:
    fleets = 0
    lead_distance, lead_speed = 0, 0  # arrival time of the current lead fleet, as a fraction
    for p, v in sorted(zip(position, speed, strict=True), reverse=True):
        distance = target - p
        if fleets == 0 or distance * lead_speed > lead_distance * v:  # arrives strictly later: a new fleet
            fleets += 1
            lead_distance, lead_speed = distance, v
    return fleets


def _car_fleet_brute(target: int, position: list[int], speed: list[int]) -> int:
    arrivals = [Fraction(target - p, v) for p, v in zip(position, speed, strict=True)]
    order = sorted(range(len(position)), key=lambda i: -position[i])
    fleets = 0
    for rank, i in enumerate(order):
        ahead = [arrivals[j] for j in order[:rank]]
        if all(arrivals[i] > t for t in ahead):
            fleets += 1
    return fleets


def _car_gen(rng: random.Random) -> list:
    target = rng.randint(2, rng.choice([30, 10**6]))
    n = min(target, pick_n(rng, 1, 12, big=10**4))
    position = sample(rng, range(target), n)
    return [target, position, [rng.randint(1, rng.choice([5, 10**6])) for _ in range(n)]]


CAR_FLEET = ProblemSource(
    title="Car Fleet",
    statement="""
`n` cars drive toward `target` on a one-lane road. Car `i` starts at `position[i]` (all distinct) and drives at `speed[i]`. A car can never pass
another; when it catches up with a slower car it slows down and they drive together as one *fleet*. A car that catches up exactly at `target`
still joins that fleet. Return the number of fleets that arrive at `target`.
""",
    constraints="""
- `1 <= n <= 10^5`
- `0 <= position[i] < target <= 10^6`, positions distinct
- `0 < speed[i] <= 10^6`
""",
    signature=function("carFleet", [("target", "int"), ("position", "int[]"), ("speed", "int[]")], "int"),
    reference=_car_fleet,
    brute=lambda target, position, speed: _car_fleet_brute(target, position, speed) if len(position) <= 400 else NotImplemented,
    examples=[Example([12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]], "Cars at 10 and 8 meet at 12; car 0 alone; cars at 5 and 3 meet at 6."), Example([10, [3], [3]]), Example([100, [0, 2, 4], [4, 2, 1]])],
    edge_cases=[[1, [0], [1]], [10, [0, 5], [2, 1]], [10, [0, 5], [1, 2]]],
    generator=_car_gen,
    random_count=8,
)


PROBLEMS = [
    VALID_PARENTHESES,
    BASIC_CALCULATOR,
    REMOVE_ADJACENT,
    MIN_REMOVE_VALID,
    EXCLUSIVE_TIME,
    FLATTEN_NESTED,
    QUEUE_USING_STACKS,
    DECODE_STRING,
    DAILY_TEMPERATURES,
    MIN_LENGTH_REMOVING,
    VALID_SUBARRAYS,
    VISIBLE_PEOPLE,
    PARSE_BOOLEAN,
    REMOVE_DUPLICATE_LETTERS,
    LONGEST_VALID_PARENTHESES,
    NEXT_GREATER_IV,
    MAX_WIDTH_RAMP,
    BASIC_CALCULATOR_II,
    REMOVE_ADJACENT_II,
    SIMPLIFY_PATH,
    SUBARRAY_MINIMUMS,
    CAR_FLEET,
]
