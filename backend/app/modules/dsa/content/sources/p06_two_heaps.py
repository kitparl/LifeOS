"""Pattern 6: Two Heaps. Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import bisect
import heapq
import itertools
from collections import Counter
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ints, ops, pick_n, word

PATTERN_NUMBER = 6


# ---------------------------------------------------------------- Find Median from a Data Stream


class _MedianFinder:
    def __init__(self) -> None:
        self.low: list[int] = []  # max-heap (negated)
        self.high: list[int] = []

    def addNum(self, num: int) -> None:
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def findMedian(self) -> float:
        if len(self.low) > len(self.high):
            return float(-self.low[0])
        return (-self.low[0] + self.high[0]) / 2


class _MedianFinderBrute:
    def __init__(self) -> None:
        self.values: list[int] = []

    def addNum(self, num: int) -> None:
        bisect.insort(self.values, num)

    def findMedian(self) -> float:
        n = len(self.values)
        return float(self.values[n // 2]) if n % 2 else (self.values[n // 2 - 1] + self.values[n // 2]) / 2


def _median_gen(rng):
    calls = [("MedianFinder", [])]
    added = 0
    for _ in range(pick_n(rng, 1, 30, big=1500)):
        if added and rng.random() < 0.35:
            calls.append(("findMedian", []))
        else:
            calls.append(("addNum", [rng.randint(-10**5, 10**5)]))
            added += 1
    calls.append(("findMedian", []) if added else ("addNum", [0]))
    return ops(*calls)


MEDIAN_FINDER = ProblemSource(
    title="Find Median from a Data Stream",
    statement="""
The *median* of a sorted list is its middle value; for an even number of values it is the mean of the
two middle values.

Design `MedianFinder`:
- `MedianFinder()` starts with no numbers.
- `addNum(num)` adds an integer from the stream.
- `findMedian()` returns the median of all numbers added so far (answers within `10^-5` are accepted).

`findMedian` is only called after at least one number has been added. Aim for `O(log n)` per `addNum`
and `O(1)` per `findMedian`.

**Test format:** a list of operations with their arguments; the expected output lists each operation's
return value (`null` for the constructor and `addNum`).
""",
    constraints="""
- `-10^5 <= num <= 10^5`
- at most `5 * 10^4` calls in total
""",
    signature=design("MedianFinder", [], [("addNum", [("num", "int")], "void"), ("findMedian", [], "double")]),
    reference=_MedianFinder,
    brute=_MedianFinderBrute,
    compare="float_tolerance",
    examples=[
        Example(
            ops(("MedianFinder", []), ("addNum", [1]), ("addNum", [2]), ("findMedian", []), ("addNum", [3]), ("findMedian", [])),
            "After 1, 2 the median is 1.5; after 1, 2, 3 it is 2.",
        ),
        Example(ops(("MedianFinder", []), ("addNum", [-5]), ("findMedian", []))),
    ],
    edge_cases=[
        ops(("MedianFinder", []), ("addNum", [7]), ("addNum", [7]), ("findMedian", [])),
        ops(("MedianFinder", []), ("addNum", [5]), ("addNum", [1]), ("addNum", [9]), ("addNum", [3]), ("findMedian", [])),
    ],
    generator=_median_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximize Capital


def _find_maximized_capital(k: int, w: int, profits: list[int], capital: list[int]) -> int:
    projects = sorted(zip(capital, profits, strict=True))
    available: list[int] = []
    i = 0
    for _ in range(k):
        while i < len(projects) and projects[i][0] <= w:
            heapq.heappush(available, -projects[i][1])
            i += 1
        if not available:
            break
        w -= heapq.heappop(available)
    return w


def _capital_brute(k: int, w: int, profits: list[int], capital: list[int]) -> int:
    best = w

    def dfs(left: int, money: int, used: frozenset[int]) -> None:
        nonlocal best
        best = max(best, money)
        if left == 0:
            return
        for i in range(len(profits)):
            if i not in used and capital[i] <= money:
                dfs(left - 1, money + profits[i], used | {i})

    dfs(k, w, frozenset())
    return best


def _capital_gen(rng):
    n = pick_n(rng, 1, 6, big=3000)
    return [rng.randint(1, n), rng.randint(0, 5), ints(rng, n, 0, 20), ints(rng, n, 0, 25)]


MAXIMIZE_CAPITAL = ProblemSource(
    title="Maximize Capital",
    statement="""
You start with `w` capital and may complete at most `k` distinct projects, one at a time. Project `i`
can be started only when your current capital is at least `capital[i]`; finishing it adds `profits[i]`
to your capital (the required capital is not spent).

Return the maximum capital you can have after completing at most `k` projects.
""",
    constraints="""
- `1 <= k <= 10^5`, `0 <= w <= 10^9`
- `1 <= profits.length == capital.length <= 10^5`
- `0 <= profits[i] <= 10^4`, `0 <= capital[i] <= 10^9`
""",
    signature=function("findMaximizedCapital", [("k", "int"), ("w", "int"), ("profits", "int[]"), ("capital", "int[]")], "int"),
    reference=_find_maximized_capital,
    brute=_capital_brute,
    brute_input_limit=60,
    examples=[
        Example([2, 0, [1, 2, 3], [0, 1, 1]], "Do project 0 (capital becomes 1), then project 2: 4."),
        Example([3, 0, [1, 2, 3], [0, 1, 2]], "All three projects can be done in order: 6."),
    ],
    edge_cases=[[1, 0, [5], [1]], [1, 3, [5], [3]], [2, 1, [0, 0], [0, 0]], [5, 0, [1, 1], [0, 0]]],
    generator=_capital_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Sliding Window Median


def _median_sliding_window(nums: list[int], k: int) -> list[float]:
    window = sorted(nums[:k])
    out = []
    for i in range(k, len(nums) + 1):
        out.append(float(window[k // 2]) if k % 2 else (window[k // 2 - 1] + window[k // 2]) / 2)
        if i == len(nums):
            break
        window.pop(bisect.bisect_left(window, nums[i - k]))
        bisect.insort(window, nums[i])
    return out


def _median_window_brute(nums: list[int], k: int) -> list[float]:
    out = []
    for i in range(len(nums) - k + 1):
        w = sorted(nums[i : i + k])
        out.append(float(w[k // 2]) if k % 2 else (w[k // 2 - 1] + w[k // 2]) / 2)
    return out


def _median_window_gen(rng):
    nums = ints(rng, pick_n(rng, 1, 30, big=2000), -(2**31), 2**31 - 1) if rng.random() < 0.3 else ints(rng, pick_n(rng, 1, 30, big=2500), -50, 50)
    return [nums, rng.randint(1, len(nums))]


SLIDING_WINDOW_MEDIAN = ProblemSource(
    title="Sliding Window Median",
    statement="""
A window of size `k` slides over `nums` from left to right, one position at a time. Return the median of
the window at each of its `nums.length - k + 1` positions. (For an even `k`, the median is the mean of the
two middle values.) Answers within `10^-5` are accepted.
""",
    constraints="""
- `1 <= k <= nums.length <= 10^5`
- `-2^31 <= nums[i] <= 2^31 - 1`
""",
    signature=function("medianSlidingWindow", [("nums", "int[]"), ("k", "int")], "double[]"),
    reference=_median_sliding_window,
    brute=_median_window_brute,
    compare="float_tolerance",
    examples=[
        Example([[1, 3, -1, -3, 5, 3, 6, 7], 3], "Medians: 1, -1, -1, 3, 5, 6."),
        Example([[1, 2, 3, 4, 2, 3, 1, 4, 2], 3]),
    ],
    edge_cases=[[[5], 1], [[1, 4], 2], [[2147483647, 2147483647], 2], [[-2147483648, -2147483648, 2147483647], 2]],
    generator=_median_window_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Schedule Tasks on Minimum Machines


def _minimum_machines(tasks: list[list[int]]) -> int:
    ends: list[int] = []
    for start, end in sorted(tasks):
        if ends and ends[0] <= start:
            heapq.heapreplace(ends, end)
        else:
            heapq.heappush(ends, end)
    return len(ends)


def _machines_brute(tasks: list[list[int]]) -> int:
    return max(sum(s <= t < e for s, e in tasks) for t in {s for s, _ in tasks})


SCHEDULE_TASKS = ProblemSource(
    title="Schedule Tasks on Minimum Machines",
    statement="""
Each task `tasks[i] = [start_i, end_i]` must run on one machine from time `start_i` up to (but not
including) `end_i`. A machine runs one task at a time, and a task ending at time `t` frees its machine for
a task starting at `t`.

Return the minimum number of machines needed to run all the tasks.
""",
    constraints="""
- `1 <= tasks.length <= 10^4`
- `0 <= start_i < end_i <= 10^9`
""",
    signature=function("minimumMachines", [("tasks", "int[][]")], "int"),
    reference=_minimum_machines,
    brute=_machines_brute,
    brute_input_limit=800,
    examples=[
        Example([[[1, 7], [2, 5], [4, 6], [8, 9], [9, 10]]], "At time 4 three tasks overlap."),
        Example([[[1, 2], [2, 3], [3, 4]]], "Each task starts when the previous one ends."),
    ],
    edge_cases=[[[[0, 1]]], [[[0, 10], [0, 10], [0, 10]]], [[[5, 6], [1, 2]]]],
    generator=lambda rng: [[[s, s + rng.randint(1, 30)] for s in (rng.randint(0, rng.choice([50, 10**9 - 50])) for _ in range(pick_n(rng, 1, 30, big=2000)))]],
    random_count=8,
)


# ---------------------------------------------------------------- Meeting Rooms III


def _most_booked(n: int, meetings: list[list[int]]) -> int:
    free = list(range(n))
    busy: list[tuple[int, int]] = []
    count = [0] * n
    for start, end in sorted(meetings):
        while busy and busy[0][0] <= start:
            heapq.heappush(free, heapq.heappop(busy)[1])
        if free:
            room = heapq.heappop(free)
            heapq.heappush(busy, (end, room))
        else:
            finish, room = heapq.heappop(busy)
            heapq.heappush(busy, (finish + end - start, room))
        count[room] += 1
    return count.index(max(count))


def _most_booked_brute(n: int, meetings: list[list[int]]) -> int:
    pending = sorted(meetings)
    room_free_at = [0] * n
    count = [0] * n
    t = 0
    queue: list[list[int]] = []
    while pending or queue:
        while pending and pending[0][0] <= t:
            queue.append(pending.pop(0))
        while queue:
            rooms = [r for r in range(n) if room_free_at[r] <= t]
            if not rooms:
                break
            start, end = queue.pop(0)
            room_free_at[rooms[0]] = t + (end - start)
            count[rooms[0]] += 1
        t += 1
    return count.index(max(count))


def _rooms_gen(rng):
    n = rng.randint(1, 5)
    hi = rng.choice([40, 5000])
    starts = rng.sample(range(0, hi), min(hi, pick_n(rng, 1, 12, big=400)))
    return [n, [[s, s + rng.randint(1, 20)] for s in starts]]


MEETING_ROOMS_III = ProblemSource(
    title="Meeting Rooms III",
    statement="""
There are `n` rooms numbered `0` to `n - 1`. `meetings[i] = [start_i, end_i]` is a meeting over the
half-open time `[start_i, end_i)`, and all start times are distinct. Meetings are allocated in order of
their original start time:

1. A meeting takes the free room with the **lowest number**.
2. If no room is free, the meeting waits until a room frees up and keeps its original **duration**. If
   several meetings are waiting, the one with the earliest original start goes first.
3. When a room frees up, it becomes available at that exact moment.

Return the number of the room that held the most meetings; break ties by the lowest room number.
""",
    constraints="""
- `1 <= n <= 100`
- `1 <= meetings.length <= 10^5`
- `0 <= start_i < end_i <= 5 * 10^5`, and all `start_i` are distinct
""",
    signature=function("mostBooked", [("n", "int"), ("meetings", "int[][]")], "int"),
    reference=_most_booked,
    brute=_most_booked_brute,
    brute_input_limit=150,
    examples=[
        Example([2, [[0, 10], [1, 5], [2, 7], [3, 4]]], "Rooms 0 and 1 each hold two meetings; the lower number wins."),
        Example([3, [[1, 20], [2, 10], [3, 5], [4, 9], [6, 8]]], "Rooms 1 and 2 hold two meetings each; room 1 wins."),
    ],
    edge_cases=[[1, [[0, 1]]], [1, [[5, 6], [0, 10]]], [3, [[0, 1], [1, 2], [2, 3]]]],
    generator=_rooms_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Minimum Cost to Connect Sticks


def _connect_sticks(sticks: list[int]) -> int:
    heap = list(sticks)
    heapq.heapify(heap)
    cost = 0
    while len(heap) > 1:
        merged = heapq.heappop(heap) + heapq.heappop(heap)
        cost += merged
        heapq.heappush(heap, merged)
    return cost


@cache
def _sticks_brute_cached(sticks: tuple[int, ...]) -> int:
    if len(sticks) <= 1:
        return 0
    best = float("inf")
    for i, j in itertools.combinations(range(len(sticks)), 2):
        rest = [s for k, s in enumerate(sticks) if k not in (i, j)]
        merged = sticks[i] + sticks[j]
        best = min(best, merged + _sticks_brute_cached(tuple(sorted(rest + [merged]))))
    return int(best)


CONNECT_STICKS = ProblemSource(
    title="Minimum Cost to Connect Sticks",
    statement="""
You have sticks with positive integer lengths `sticks[i]`. Joining two sticks of lengths `x` and `y`
costs `x + y` and produces one stick of that length. Keep joining until one stick remains.

Return the minimum total cost.
""",
    constraints="""
- `1 <= sticks.length <= 10^4`
- `1 <= sticks[i] <= 10^4`
""",
    signature=function("connectSticks", [("sticks", "int[]")], "int"),
    reference=_connect_sticks,
    brute=lambda sticks: _sticks_brute_cached(tuple(sorted(sticks))),
    brute_input_limit=24,
    examples=[
        Example([[2, 4, 3]], "Join 2 + 3 = 5 (cost 5), then 5 + 4 = 9 (cost 9): total 14."),
        Example([[1, 8, 3, 5]], "Total 30."),
        Example([[5]], "Nothing to join."),
    ],
    edge_cases=[[[1, 1]], [[10000, 10000]], [[1, 2, 3, 4, 5, 6]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 6, big=4000), 1, rng.choice([9, 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Happy String


def _longest_happy(a: int, b: int, c: int) -> str:
    heap = [(-n, ch) for n, ch in ((a, "a"), (b, "b"), (c, "c")) if n]
    heapq.heapify(heap)
    out: list[str] = []
    while heap:
        n, ch = heapq.heappop(heap)
        if len(out) >= 2 and out[-1] == out[-2] == ch:
            if not heap:
                break
            n2, ch2 = heapq.heappop(heap)
            out.append(ch2)
            if n2 + 1:
                heapq.heappush(heap, (n2 + 1, ch2))
            heapq.heappush(heap, (n, ch))
        else:
            out.append(ch)
            if n + 1:
                heapq.heappush(heap, (n + 1, ch))
    return "".join(out)


def _happy_brute(a: int, b: int, c: int) -> str:
    @cache
    def best(x: int, y: int, z: int, last: str, run: int) -> str:
        options = [""]
        for ch, left in (("a", x), ("b", y), ("c", z)):
            if left == 0 or (ch == last and run == 2):
                continue
            nx, ny, nz = x - (ch == "a"), y - (ch == "b"), z - (ch == "c")
            options.append(ch + best(nx, ny, nz, ch, run + 1 if ch == last else 1))
        return max(options, key=len)

    return best(a, b, c, "", 0)


HAPPY_STRING = ProblemSource(
    title="Longest Happy String",
    statement="""
A string is *happy* if it contains only the letters `a`, `b` and `c` and never contains `"aaa"`, `"bbb"`
or `"ccc"` as a substring.

Given `a`, `b` and `c`, build the **longest** happy string that uses at most `a` letters `a`, at most `b`
letters `b` and at most `c` letters `c`. Any longest happy string is accepted; return `""` if none exists.
""",
    constraints="""
- `0 <= a, b, c <= 100`
- `a + b + c > 0`
""",
    signature=function("longestDiverseString", [("a", "int"), ("b", "int"), ("c", "int")], "string"),
    reference=_longest_happy,
    brute=_happy_brute,
    brute_input_limit=12,
    compare="checker",
    checker="happy_string",
    examples=[
        Example([1, 1, 7], "\"ccaccbcc\" (length 8) is one longest answer; \"ccbccacc\" is another."),
        Example([7, 1, 0], "\"aabaa\" is the only longest answer."),
    ],
    edge_cases=[[1, 0, 0], [3, 0, 0], [0, 0, 5], [2, 2, 1], [4, 4, 3], [100, 100, 100], [100, 0, 1]],
    generator=lambda rng: [rng.randint(0, 6), rng.randint(0, 6), rng.randint(1, 6)] if rng.random() < 0.6 else [rng.randint(0, 100), rng.randint(0, 100), rng.randint(1, 100)],
    random_count=9,
)


# ---------------------------------------------------------------- Maximum Average Pass Ratio


def _max_average_ratio(classes: list[list[int]], extraStudents: int) -> float:
    def gain(p: int, t: int) -> float:
        return (p + 1) / (t + 1) - p / t

    heap = [(-gain(p, t), p, t) for p, t in classes]
    heapq.heapify(heap)
    for _ in range(extraStudents):
        _, p, t = heapq.heappop(heap)
        heapq.heappush(heap, (-gain(p + 1, t + 1), p + 1, t + 1))
    return sum(p / t for _, p, t in heap) / len(classes)


def _pass_ratio_brute(classes: list[list[int]], extraStudents: int) -> float:
    best = 0.0
    for split in itertools.product(range(extraStudents + 1), repeat=len(classes)):
        if sum(split) == extraStudents:
            best = max(best, sum((p + x) / (t + x) for (p, t), x in zip(classes, split, strict=True)) / len(classes))
    return best


def _pass_gen(rng):
    classes = []
    for _ in range(pick_n(rng, 1, 3, big=2000)):
        total = rng.randint(1, 10**5 if rng.random() < 0.3 else 20)
        classes.append([rng.randint(1, total), total])
    return [classes, rng.randint(1, 4) if len(classes) <= 3 else rng.randint(1, 3000)]


PASS_RATIO = ProblemSource(
    title="Maximum Average Pass Ratio",
    statement="""
A school has several classes; `classes[i] = [pass_i, total_i]` means `pass_i` of the `total_i` students in
class `i` will pass the exam. You also have `extraStudents` brilliant students who are guaranteed to pass,
and you must assign each of them to some class.

The *pass ratio* of a class is its passing students divided by its total students. Return the maximum
possible **average** pass ratio over all classes. Answers within `10^-5` are accepted.
""",
    constraints="""
- `1 <= classes.length <= 10^5`
- `1 <= pass_i <= total_i <= 10^5`
- `1 <= extraStudents <= 10^5`
""",
    signature=function("maxAverageRatio", [("classes", "int[][]"), ("extraStudents", "int")], "double"),
    reference=_max_average_ratio,
    brute=_pass_ratio_brute,
    brute_input_limit=40,
    compare="float_tolerance",
    examples=[
        Example([[[1, 2], [3, 5], [2, 2]], 2], "Put both extra students in the first class: (3/4 + 3/5 + 2/2) / 3 = 0.78333."),
        Example([[[2, 4], [3, 9], [4, 5], [2, 10]], 4]),
    ],
    edge_cases=[[[[1, 1]], 5], [[[1, 2]], 1], [[[1, 3], [1, 3]], 2]],
    generator=_pass_gen,
    random_count=8,
)


# ---------------------------------------------------------------- The Number of the Smallest Unoccupied Chair


def _smallest_chair(times: list[list[int]], targetFriend: int) -> int:
    order = sorted(range(len(times)), key=lambda i: times[i][0])
    free = list(range(len(times)))
    leaving: list[tuple[int, int]] = []
    for i in order:
        arrive, leave = times[i]
        while leaving and leaving[0][0] <= arrive:
            heapq.heappush(free, heapq.heappop(leaving)[1])
        chair = heapq.heappop(free)
        if i == targetFriend:
            return chair
        heapq.heappush(leaving, (leave, chair))
    raise AssertionError("target never arrives")


def _chair_brute(times: list[list[int]], targetFriend: int) -> int:
    occupied: dict[int, int] = {}
    for t in range(max(leave for _, leave in times) + 1):
        for chair in [c for c, friend in occupied.items() if times[friend][1] == t]:
            del occupied[chair]
        for friend, (arrive, _) in enumerate(times):
            if arrive == t:
                chair = next(c for c in range(len(times)) if c not in occupied)
                if friend == targetFriend:
                    return chair
                occupied[chair] = friend
    raise AssertionError("target never arrives")


def _chair_gen(rng):
    n = pick_n(rng, 2, 10, big=2000)
    hi = rng.choice([30, 10**5])
    arrivals = rng.sample(range(1, hi), min(n, hi - 1))
    times = [[a, a + rng.randint(1, max(1, hi // 5))] for a in arrivals]
    return [times, rng.randrange(len(times))]


SMALLEST_CHAIR = ProblemSource(
    title="The Number of the Smallest Unoccupied Chair",
    statement="""
Chairs numbered `0, 1, 2, ...` stand in a row. `times[i] = [arriving_i, leaving_i]` gives when friend `i`
arrives and leaves a party; all arrival times are distinct. An arriving friend takes the **lowest-numbered
unoccupied** chair. A friend leaving at time `t` frees their chair at `t`, so another friend arriving at `t`
can take it.

Return the chair number that friend `targetFriend` sits on.
""",
    constraints="""
- `2 <= times.length <= 10^4`
- `1 <= arriving_i < leaving_i <= 10^5`, arrival times are distinct
- `0 <= targetFriend < times.length`
""",
    signature=function("smallestChair", [("times", "int[][]"), ("targetFriend", "int")], "int"),
    reference=_smallest_chair,
    brute=_chair_brute,
    brute_input_limit=120,
    examples=[
        Example([[[1, 4], [2, 3], [4, 6]], 1], "Friend 0 takes chair 0 at time 1, friend 1 takes chair 1 at time 2."),
        Example([[[3, 10], [1, 5], [2, 6]], 0], "Chairs 0 and 1 are taken when friend 0 arrives at time 3."),
    ],
    edge_cases=[[[[1, 2], [2, 3]], 1], [[[1, 5], [2, 3], [3, 4]], 2]],
    generator=_chair_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Largest Number After Digit Swaps by Parity


def _largest_integer(num: int) -> int:
    digits = [int(d) for d in str(num)]
    odd = sorted((d for d in digits if d % 2), reverse=True)
    even = sorted((d for d in digits if d % 2 == 0), reverse=True)
    oi = ei = 0
    out = []
    for d in digits:
        if d % 2:
            out.append(odd[oi])
            oi += 1
        else:
            out.append(even[ei])
            ei += 1
    return int("".join(map(str, out)))


def _largest_integer_brute(num: int) -> int:
    digits = list(str(num))
    best = num
    for perm in set(itertools.permutations(digits)):
        if all(int(a) % 2 == int(b) % 2 for a, b in zip(perm, digits, strict=True)):
            best = max(best, int("".join(perm)))
    return best


DIGIT_SWAPS_PARITY = ProblemSource(
    title="Largest Number After Digit Swaps by Parity",
    statement="""
Given a positive integer `num`, you may swap any two of its digits that have the **same parity** (both odd
or both even), as many times as you like. Return the largest number you can obtain.
""",
    constraints="""
- `1 <= num <= 10^9`
""",
    signature=function("largestInteger", [("num", "int")], "int"),
    reference=_largest_integer,
    brute=_largest_integer_brute,
    brute_input_limit=7,
    examples=[Example([1234], "Swap 3 with 1 and 4 with 2: 3412."), Example([65875], "87655.")],
    edge_cases=[[1], [10], [247], [1000000000], [135792468]],
    generator=lambda rng: [rng.choice([rng.randint(1, 10**6), rng.randint(1, 10**9)])],
    random_count=8,
)


# ---------------------------------------------------------------- Find Right Interval


def _find_right_interval(intervals: list[list[int]]) -> list[int]:
    starts = sorted((s, i) for i, (s, _) in enumerate(intervals))
    keys = [s for s, _ in starts]
    out = []
    for _, end in intervals:
        k = bisect.bisect_left(keys, end)
        out.append(starts[k][1] if k < len(starts) else -1)
    return out


def _right_interval_brute(intervals: list[list[int]]) -> list[int]:
    out = []
    for _, end in intervals:
        candidates = [(s, j) for j, (s, _) in enumerate(intervals) if s >= end]
        out.append(min(candidates)[1] if candidates else -1)
    return out


def _right_interval_gen(rng):
    hi = rng.choice([40, 10**6])
    starts = rng.sample(range(-hi, hi), min(pick_n(rng, 1, 15, big=2000), 2 * hi))
    return [[[s, min(hi, s + rng.randint(0, hi // 4))] for s in starts]]


FIND_RIGHT_INTERVAL = ProblemSource(
    title="Find Right Interval",
    statement="""
You are given intervals `intervals[i] = [start_i, end_i]` whose start points are all distinct. The *right
interval* of interval `i` is the interval `j` with the smallest `start_j` such that `start_j >= end_i`
(`j` may equal `i`).

Return an array whose `i`-th value is the index of the right interval of interval `i`, or `-1` if it has none.
""",
    constraints="""
- `1 <= intervals.length <= 2 * 10^4`
- `-10^6 <= start_i <= end_i <= 10^6`, and all starts are distinct
""",
    signature=function("findRightInterval", [("intervals", "int[][]")], "int[]"),
    reference=_find_right_interval,
    brute=_right_interval_brute,
    brute_input_limit=600,
    examples=[
        Example([[[1, 2]]], "No start is at least 2."),
        Example([[[3, 4], [2, 3], [1, 2]]], "Right intervals: none, [3,4], [2,3]."),
        Example([[[1, 4], [2, 3], [3, 4]]]),
    ],
    edge_cases=[[[[5, 5]]], [[[1, 1], [2, 2]]], [[[-5, 0], [0, 3]]]],
    generator=_right_interval_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Construct Target Array with Multiple Sums


def _is_possible(target: list[int]) -> bool:
    if len(target) == 1:
        return target[0] == 1
    total = sum(target)
    heap = [-x for x in target]
    heapq.heapify(heap)
    while -heap[0] > 1:
        largest = -heapq.heappop(heap)
        rest = total - largest
        if rest == 1:
            return True
        if rest == 0 or largest <= rest:
            return False
        previous = largest % rest
        if previous == 0:
            return False
        total = rest + previous
        heapq.heappush(heap, -previous)
    return True


def _is_possible_brute(target: list[int]) -> bool:
    goal = tuple(target)
    limit = sum(target)
    seen = set()
    frontier = [tuple([1] * len(target))]
    while frontier:
        state = frontier.pop()
        if state == goal:
            return True
        if state in seen:
            continue
        seen.add(state)
        s = sum(state)
        for i in range(len(state)):
            nxt = state[:i] + (s,) + state[i + 1 :]
            if sum(nxt) <= limit and all(a <= b for a, b in zip(nxt, goal, strict=True)):
                frontier.append(nxt)
    return False


def _target_gen(rng):
    n = rng.randint(1, 4) if rng.random() < 0.6 else rng.randint(1, 500)
    arr = [1] * n
    for _ in range(rng.randint(0, 6)):
        i = rng.randrange(n)
        arr[i] = sum(arr)
        if arr[i] > 10**9:
            break
    if rng.random() < 0.35:
        i = rng.randrange(n)
        arr[i] = max(1, arr[i] + rng.choice([-1, 1]))
    return [[min(x, 10**9) for x in arr]]


CONSTRUCT_TARGET = ProblemSource(
    title="Construct Target Array with Multiple Sums",
    statement="""
Start with an array `arr` of `n` ones. In one step you may pick any index `i` and replace `arr[i]` with the
**sum of all elements** of `arr`. Return `true` if some sequence of steps turns `arr` into the given array
`target`.
""",
    constraints="""
- `1 <= target.length <= 5 * 10^4`
- `1 <= target[i] <= 10^9`
""",
    signature=function("isPossible", [("target", "int[]")], "bool"),
    reference=_is_possible,
    brute=_is_possible_brute,
    brute_input_limit=12,
    examples=[
        Example([[9, 3, 5]], "[1,1,1] -> [1,1,3] -> [1,5,3] -> [9,5,3], reordered as needed."),
        Example([[1, 1, 1, 2]], "The sum is always at least 4 after a step, so a 2 can't appear."),
        Example([[8, 5]], "[1,1] -> [2,1] -> [2,3] -> [5,3] -> [5,8]."),
    ],
    edge_cases=[[[1]], [[2]], [[1, 1]], [[1, 1000000000]], [[2, 900000002]], [[5, 50]]],
    generator=_target_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Sort Characters By Frequency


def _frequency_sort(s: str) -> str:
    counts = Counter(s)
    heap = [(-n, ch) for ch, n in counts.items()]
    heapq.heapify(heap)
    out = []
    while heap:
        n, ch = heapq.heappop(heap)
        out.append(ch * -n)
    return "".join(out)


SORT_BY_FREQUENCY = ProblemSource(
    title="Sort Characters By Frequency",
    statement="""
Rearrange the characters of `s` so that characters are ordered by how often they appear, most frequent
first, with all copies of a character next to each other. Characters with the same frequency may come in
any order, and uppercase and lowercase letters are different characters. Any valid answer is accepted.
""",
    constraints="""
- `1 <= s.length <= 5 * 10^5`
- `s` consists of uppercase and lowercase English letters and digits
""",
    signature=function("frequencySort", [("s", "string")], "string"),
    reference=_frequency_sort,
    brute=lambda s: "".join(ch * n for ch, n in sorted(Counter(s).items(), key=lambda kv: (-kv[1], kv[0]))),
    compare="checker",
    checker="sort_by_frequency",
    examples=[
        Example(["tree"], "'e' appears twice; \"eert\" and \"eetr\" are both valid."),
        Example(["cccaaa"], "\"cccaaa\" and \"aaaccc\" are both valid; \"cacaca\" is not."),
        Example(["Aabb"], "\"bbAa\" or \"bbaA\"."),
    ],
    edge_cases=[["a"], ["ab"], ["0000z"], ["zzZZ"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 40, big=15000), "aabbbcXYZ0123")],
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Number of Events That Can Be Attended


def _max_events(events: list[list[int]]) -> int:
    events = sorted(events)
    heap: list[int] = []
    i = attended = 0
    day = 0
    while i < len(events) or heap:
        if not heap:
            day = max(day, events[i][0])
        while i < len(events) and events[i][0] <= day:
            heapq.heappush(heap, events[i][1])
            i += 1
        while heap and heap[0] < day:
            heapq.heappop(heap)
        if heap:
            heapq.heappop(heap)
            attended += 1
            day += 1
    return attended


def _max_events_brute(events: list[list[int]]) -> int:
    match_of_day: dict[int, int] = {}

    def augment(e: int, seen: set[int]) -> bool:
        start, end = events[e]
        for day in range(start, end + 1):
            if day in seen:
                continue
            seen.add(day)
            if day not in match_of_day or augment(match_of_day[day], seen):
                match_of_day[day] = e
                return True
        return False

    return sum(augment(e, set()) for e in range(len(events)))


def _events_gen(rng):
    hi = rng.choice([15, 10**5])
    out = []
    for _ in range(pick_n(rng, 1, 12, big=2000)):
        s = rng.randint(1, hi)
        out.append([s, min(hi, s + rng.randint(0, 5 if hi == 15 else 200))])
    return [out]


MAX_EVENTS = ProblemSource(
    title="Maximum Number of Events That Can Be Attended",
    statement="""
`events[i] = [startDay_i, endDay_i]` means event `i` runs every day from `startDay_i` to `endDay_i`,
inclusive. You can attend event `i` on any single day `d` with `startDay_i <= d <= endDay_i`, and you can
attend at most one event per day.

Return the maximum number of events you can attend.
""",
    constraints="""
- `1 <= events.length <= 10^5`
- `1 <= startDay_i <= endDay_i <= 10^5`
""",
    signature=function("maxEvents", [("events", "int[][]")], "int"),
    reference=_max_events,
    brute=_max_events_brute,
    brute_input_limit=200,
    examples=[
        Example([[[1, 2], [2, 3], [3, 4]]], "Attend one event on each of days 1, 2 and 3."),
        Example([[[1, 2], [2, 3], [3, 4], [1, 2]]], "All four fit: days 1, 2, 3 and 4."),
    ],
    edge_cases=[[[[1, 1]]], [[[1, 1], [1, 1]]], [[[1, 5], [1, 5], [1, 5]]], [[[1, 2], [1, 2], [1, 2]]]],
    generator=_events_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Furthest Building You Can Reach


def _furthest_building(heights: list[int], bricks: int, ladders: int) -> int:
    ladder_climbs: list[int] = []
    for i in range(len(heights) - 1):
        climb = heights[i + 1] - heights[i]
        if climb <= 0:
            continue
        heapq.heappush(ladder_climbs, climb)
        if len(ladder_climbs) > ladders:
            bricks -= heapq.heappop(ladder_climbs)
            if bricks < 0:
                return i
    return len(heights) - 1


def _furthest_brute(heights: list[int], bricks: int, ladders: int) -> int:
    best = 0
    for target in range(1, len(heights)):
        climbs = [heights[i + 1] - heights[i] for i in range(target) if heights[i + 1] > heights[i]]
        ok = False
        for use in itertools.combinations(range(len(climbs)), min(ladders, len(climbs))):
            if sum(c for k, c in enumerate(climbs) if k not in use) <= bricks:
                ok = True
                break
        if not ok:
            break
        best = target
    return best


FURTHEST_BUILDING = ProblemSource(
    title="Furthest Building You Can Reach",
    statement="""
You walk along buildings with heights `heights[0..n-1]`, starting at building `0`. Moving from building
`i` to `i + 1`:
- if `heights[i + 1] <= heights[i]`, it costs nothing;
- otherwise you must use either **one ladder** or `heights[i + 1] - heights[i]` **bricks**.

You have `bricks` bricks and `ladders` ladders. Return the index of the furthest building you can reach
when you use them optimally.
""",
    constraints="""
- `1 <= heights.length <= 10^5`
- `1 <= heights[i] <= 10^6`
- `0 <= bricks <= 10^9`, `0 <= ladders <= heights.length`
""",
    signature=function("furthestBuilding", [("heights", "int[]"), ("bricks", "int"), ("ladders", "int")], "int"),
    reference=_furthest_building,
    brute=_furthest_brute,
    brute_input_limit=50,
    examples=[
        Example([[4, 2, 7, 6, 9, 14, 12], 5, 1], "Use 5 bricks for 2 -> 7 and the ladder for 6 -> 9; building 4."),
        Example([[4, 12, 2, 7, 3, 18, 20, 3, 19], 10, 2], "Building 7."),
        Example([[14, 3, 19, 3], 17, 0], "Bricks cover 3 -> 19 exactly; building 3."),
    ],
    edge_cases=[[[1], 0, 0], [[1, 2], 0, 0], [[1, 2], 1, 0], [[1, 2], 0, 1], [[5, 4, 3], 0, 0]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 8, big=5000), 1, rng.choice([10, 10**6])), rng.randint(0, rng.choice([10, 10**7])), rng.randint(0, 3)],
    random_count=9,
)


# ---------------------------------------------------------------- Trapping Rain Water II


def _trap_rain_water(heightMap: list[list[int]]) -> int:
    m, n = len(heightMap), len(heightMap[0])
    if m < 3 or n < 3:
        return 0
    seen = [[False] * n for _ in range(m)]
    heap = []
    for i in range(m):
        for j in range(n):
            if i in (0, m - 1) or j in (0, n - 1):
                heapq.heappush(heap, (heightMap[i][j], i, j))
                seen[i][j] = True
    water = 0
    while heap:
        level, i, j = heapq.heappop(heap)
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x, y = i + di, j + dj
            if 0 <= x < m and 0 <= y < n and not seen[x][y]:
                seen[x][y] = True
                water += max(0, level - heightMap[x][y])
                heapq.heappush(heap, (max(level, heightMap[x][y]), x, y))
    return water


def _trap_brute(heightMap: list[list[int]]) -> int:
    m, n = len(heightMap), len(heightMap[0])
    inf = max(max(row) for row in heightMap)
    level = [[heightMap[i][j] if i in (0, m - 1) or j in (0, n - 1) else inf for j in range(n)] for i in range(m)]
    changed = True
    while changed:
        changed = False
        for i in range(1, m - 1):
            for j in range(1, n - 1):
                best = max(heightMap[i][j], min(level[i - 1][j], level[i + 1][j], level[i][j - 1], level[i][j + 1]))
                if best < level[i][j]:
                    level[i][j] = best
                    changed = True
    return sum(level[i][j] - heightMap[i][j] for i in range(m) for j in range(n))


TRAP_RAIN_II = ProblemSource(
    title="Trapping Rain Water II",
    statement="""
`heightMap` is an `m x n` grid of cell heights forming a 2D elevation map. After heavy rain, water collects
in the low regions surrounded by higher cells; water can flow off the map from any border cell, and moves
between cells that share an edge.

Return the total volume of water trapped (one unit per cell per unit of height).
""",
    constraints="""
- `1 <= m, n <= 200`
- `0 <= heightMap[i][j] <= 2 * 10^4`
""",
    signature=function("trapRainWater", [("heightMap", "int[][]")], "int"),
    reference=_trap_rain_water,
    brute=_trap_brute,
    brute_input_limit=400,
    examples=[
        Example([[[1, 4, 3, 1, 3, 2], [3, 2, 1, 3, 2, 4], [2, 3, 3, 2, 3, 1]]], "Two small pools trap 1 + 3 = 4 units."),
        Example([[[3, 3, 3, 3, 3], [3, 2, 2, 2, 3], [3, 2, 1, 2, 3], [3, 2, 2, 2, 3], [3, 3, 3, 3, 3]]], "The basin holds 10 units."),
    ],
    edge_cases=[[[[5]]], [[[1, 2], [3, 4]]], [[[5, 5, 5], [5, 1, 5], [5, 5, 5]]], [[[5, 5, 5], [5, 1, 5], [5, 0, 5]]]],
    generator=lambda rng: [[ints(rng, cols, 0, rng.choice([5, 2 * 10**4])) for _ in range(rows)] for rows, cols in [(pick_n(rng, 1, 7, big=60), pick_n(rng, 1, 7, big=60))]],
    random_count=9,
)


# ---------------------------------------------------------------- Last Stone Weight


def _last_stone(stones: list[int]) -> int:
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        y, x = -heapq.heappop(heap), -heapq.heappop(heap)
        if y != x:
            heapq.heappush(heap, -(y - x))
    return -heap[0] if heap else 0


def _last_stone_brute(stones: list[int]) -> int:
    stones = list(stones)
    while len(stones) > 1:
        stones.sort()
        y, x = stones.pop(), stones.pop()
        if y != x:
            stones.append(y - x)
    return stones[0] if stones else 0


LAST_STONE = ProblemSource(
    title="Last Stone Weight",
    statement="""
Each turn, take the two heaviest stones, with weights `x <= y`, and smash them together: if `x == y`
both are destroyed, otherwise the lighter one is destroyed and the heavier one's weight becomes `y - x`.

Repeat until at most one stone is left. Return its weight, or `0` if no stones remain.
""",
    constraints="""
- `1 <= stones.length <= 30`
- `1 <= stones[i] <= 1000`
""",
    signature=function("lastStoneWeight", [("stones", "int[]")], "int"),
    reference=_last_stone,
    brute=_last_stone_brute,
    examples=[Example([[2, 7, 4, 1, 8, 1]], "8 and 7 -> 1, then 4 and 2 -> 2, 2 and 1 -> 1, 1 and 1 -> 0, leaving 1."), Example([[1]])],
    edge_cases=[[[3, 3]], [[10, 4]], [[1000] * 30]],
    generator=lambda rng: [ints(rng, rng.randint(1, 30), 1, rng.choice([5, 1000]))],
    random_count=8,
)


PROBLEMS = [
    MEDIAN_FINDER,
    MAXIMIZE_CAPITAL,
    SLIDING_WINDOW_MEDIAN,
    SCHEDULE_TASKS,
    MEETING_ROOMS_III,
    CONNECT_STICKS,
    HAPPY_STRING,
    PASS_RATIO,
    SMALLEST_CHAIR,
    DIGIT_SWAPS_PARITY,
    FIND_RIGHT_INTERVAL,
    CONSTRUCT_TARGET,
    SORT_BY_FREQUENCY,
    MAX_EVENTS,
    FURTHEST_BUILDING,
    TRAP_RAIN_II,
    LAST_STONE,
]
