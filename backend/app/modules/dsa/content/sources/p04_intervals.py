"""Pattern 4: Intervals. Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import bisect
import heapq
import string
from collections import Counter

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ops, pick_n

PATTERN_NUMBER = 4


def _random_intervals(rng, n: int, hi: int, max_len: int) -> list[list[int]]:
    out = []
    for _ in range(n):
        start = rng.randint(0, hi)
        out.append([start, start + rng.randint(0, max_len)])
    return out


def _disjoint_sorted(rng, n: int, hi: int) -> list[list[int]]:
    """n disjoint, sorted intervals within [0, hi] (end >= start; gaps of at least 1)."""
    points = sorted(rng.sample(range(0, hi + 1), min(2 * n, hi + 1)))
    out = [[points[i], points[i + 1]] for i in range(0, len(points) - 1, 2)]
    return [iv for k, iv in enumerate(out) if k == 0 or iv[0] > out[k - 1][1]]


# ---------------------------------------------------------------- Merge Intervals


def _merge(intervals: list[list[int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for start, end in sorted(intervals):
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out


def _merge_brute(intervals: list[list[int]]) -> list[list[int]]:
    groups = [list(iv) for iv in intervals]
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                a, b = groups[i], groups[j]
                if a[0] <= b[1] and b[0] <= a[1]:
                    groups[i] = [min(a[0], b[0]), max(a[1], b[1])]
                    groups.pop(j)
                    changed = True
                    break
            if changed:
                break
    return groups


MERGE_INTERVALS = ProblemSource(
    title="Merge Intervals",
    statement="""
Given an array of closed intervals `intervals[i] = [start_i, end_i]`, merge every group of overlapping
intervals and return the resulting non-overlapping intervals, which together cover exactly the same
points. Intervals that merely touch (like `[1, 4]` and `[4, 5]`) overlap.

The intervals in your answer may be in any order.
""",
    constraints="""
- `1 <= intervals.length <= 10^4`
- `0 <= start_i <= end_i <= 10^4`
""",
    signature=function("merge", [("intervals", "int[][]")], "int[][]"),
    reference=_merge,
    brute=_merge_brute,
    brute_input_limit=400,
    compare="unordered",
    examples=[
        Example([[[1, 3], [2, 6], [8, 10], [15, 18]]], "[1,3] and [2,6] overlap, giving [1,6]."),
        Example([[[1, 4], [4, 5]]], "Touching intervals merge into [1,5]."),
        Example([[[4, 7], [1, 4]]], "The input isn't necessarily sorted."),
    ],
    edge_cases=[
        [[[1, 1]]],
        [[[1, 4], [2, 3]]],
        [[[1, 2], [3, 4]]],
        [[[5, 5], [5, 5]]],
        [[[1, 10], [2, 3], [4, 5], [11, 12]]],
    ],
    generator=lambda rng: [
        _random_intervals(rng, pick_n(rng, 1, 30, big=2500), rng.choice([30, 10**4 - 50]), rng.choice([3, 50]))
    ],
    random_count=9,
)


# ---------------------------------------------------------------- Insert Interval


def _insert(intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:
    out, i, n = [], 0, len(intervals)
    start, end = newInterval
    while i < n and intervals[i][1] < start:
        out.append(intervals[i])
        i += 1
    while i < n and intervals[i][0] <= end:
        start, end = min(start, intervals[i][0]), max(end, intervals[i][1])
        i += 1
    out.append([start, end])
    out.extend(intervals[i:])
    return out


def _insert_gen(rng):
    hi = rng.choice([40, 10**5])
    intervals = _disjoint_sorted(rng, pick_n(rng, 0, 15, big=2500), hi)
    start = rng.randint(0, hi)
    return [intervals, [start, min(hi, start + rng.randint(0, hi // 4))]]


INSERT_INTERVAL = ProblemSource(
    title="Insert Interval",
    statement="""
`intervals` is a list of non-overlapping closed intervals sorted by their start. Insert `newInterval`
into it, merging where necessary, so that the result is still sorted by start and non-overlapping.
Intervals that touch at an endpoint overlap. Return the result.
""",
    constraints="""
- `0 <= intervals.length <= 10^4`
- `intervals` is sorted by start and non-overlapping
- `0 <= start <= end <= 10^5` for every interval, including `newInterval`
""",
    signature=function("insert", [("intervals", "int[][]"), ("newInterval", "int[]")], "int[][]"),
    reference=_insert,
    brute=lambda intervals, newInterval: _merge(intervals + [newInterval]),
    examples=[
        Example([[[1, 3], [6, 9]], [2, 5]], "[2,5] overlaps [1,3], giving [1,5]."),
        Example([[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]], "[4,8] swallows [3,5], [6,7] and [8,10]."),
    ],
    edge_cases=[
        [[], [5, 7]],
        [[[1, 5]], [2, 3]],
        [[[1, 5]], [6, 8]],
        [[[3, 5]], [0, 1]],
        [[[1, 5]], [5, 7]],
        [[[1, 2], [5, 6]], [3, 4]],
    ],
    generator=_insert_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Meeting Rooms II


def _min_meeting_rooms(intervals: list[list[int]]) -> int:
    ends: list[int] = []
    for start, end in sorted(intervals):
        if ends and ends[0] <= start:
            heapq.heapreplace(ends, end)
        else:
            heapq.heappush(ends, end)
    return len(ends)


def _rooms_brute(intervals: list[list[int]]) -> int:
    events = sorted([(s, 1) for s, _ in intervals] + [(e, -1) for _, e in intervals])
    best = cur = 0
    for _, delta in events:
        cur += delta
        best = max(best, cur)
    return best


MEETING_ROOMS_II = ProblemSource(
    title="Meeting Rooms II",
    statement="""
Each meeting `intervals[i] = [start_i, end_i]` occupies a room from `start_i` up to (but not including)
`end_i`, so a meeting ending at time `t` frees its room for another meeting starting at `t`.

Return the minimum number of rooms needed to hold all the meetings.
""",
    constraints="""
- `1 <= intervals.length <= 10^4`
- `0 <= start_i < end_i <= 10^6`
""",
    signature=function("minMeetingRooms", [("intervals", "int[][]")], "int"),
    reference=_min_meeting_rooms,
    brute=_rooms_brute,
    examples=[
        Example(
            [[[0, 30], [5, 10], [15, 20]]], "[0,30] overlaps both others, which don't overlap each other: 2 rooms."
        ),
        Example([[[7, 10], [2, 4]]], "They never overlap: 1 room."),
        Example([[[1, 5], [5, 10]]], "The second meeting reuses the room freed at time 5."),
    ],
    edge_cases=[[[[0, 1]]], [[[1, 2], [1, 2], [1, 2]]], [[[1, 10], [2, 3], [3, 4], [4, 5]]]],
    generator=lambda rng: [
        [
            [s, s + rng.randint(1, 40)]
            for s in (rng.randint(0, rng.choice([60, 10**6 - 50])) for _ in range(pick_n(rng, 1, 30, big=2500)))
        ]
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Interval List Intersections


def _interval_intersection(firstList: list[list[int]], secondList: list[list[int]]) -> list[list[int]]:
    i = j = 0
    out = []
    while i < len(firstList) and j < len(secondList):
        lo = max(firstList[i][0], secondList[j][0])
        hi = min(firstList[i][1], secondList[j][1])
        if lo <= hi:
            out.append([lo, hi])
        if firstList[i][1] < secondList[j][1]:
            i += 1
        else:
            j += 1
    return out


def _intersection_brute(firstList: list[list[int]], secondList: list[list[int]]) -> list[list[int]]:
    out = []
    for a in firstList:
        for b in secondList:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if lo <= hi:
                out.append([lo, hi])
    return sorted(out)


INTERVAL_INTERSECTIONS = ProblemSource(
    title="Interval List Intersections",
    statement="""
You are given two lists of closed intervals, `firstList` and `secondList`. Within each list the intervals
are pairwise disjoint and sorted by start.

Return the intersections of the two lists: every non-empty overlap `[max(a_start, b_start), min(a_end, b_end)]`
between an interval of the first list and an interval of the second, sorted by start. An overlap may be a
single point, such as `[5, 5]`.
""",
    constraints="""
- `0 <= firstList.length, secondList.length <= 1000`
- each list is sorted and pairwise disjoint
- `0 <= start <= end <= 10^9`
""",
    signature=function("intervalIntersection", [("firstList", "int[][]"), ("secondList", "int[][]")], "int[][]"),
    reference=_interval_intersection,
    brute=_intersection_brute,
    brute_input_limit=600,
    examples=[
        Example(
            [[[0, 2], [5, 10], [13, 23], [24, 25]], [[1, 5], [8, 12], [15, 24], [25, 26]]],
            "Six overlaps, including the single points [5,5], [24,24] and [25,25].",
        ),
        Example([[[1, 3], [5, 9]], []], "An empty list has no intersections."),
    ],
    edge_cases=[[[], []], [[[1, 7]], [[3, 10]]], [[[1, 1]], [[1, 1]]], [[[0, 5]], [[1, 2], [3, 4]]]],
    generator=lambda rng: [
        _disjoint_sorted(rng, pick_n(rng, 0, 12, big=800), rng.choice([40, 10**9])),
        _disjoint_sorted(rng, pick_n(rng, 0, 12, big=800), rng.choice([40, 10**9])),
    ],
    random_count=9,
)


# ---------------------------------------------------------------- Employee Free Time


def _employee_free_time(schedule: list[list[list[int]]]) -> list[list[int]]:
    events = sorted(iv for person in schedule for iv in person)
    free, end = [], events[0][1]
    for start, finish in events[1:]:
        if start > end:
            free.append([end, start])
        end = max(end, finish)
    return free


def _free_time_brute(schedule: list[list[list[int]]]) -> list[list[int]]:
    busy = _merge([iv for person in schedule for iv in person])
    return [[busy[i][1], busy[i + 1][0]] for i in range(len(busy) - 1)]


def _schedule_gen(rng):
    hi = rng.choice([40, 10**8])
    people = [_disjoint_sorted(rng, pick_n(rng, 1, 6, big=120), hi) for _ in range(pick_n(rng, 1, 5, big=15))]
    people = [p for p in people if p] or [[[0, 1]]]
    for person in people:
        for iv in person:
            if iv[0] == iv[1]:
                iv[1] += 1
    return [people]


EMPLOYEE_FREE_TIME = ProblemSource(
    title="Employee Free Time",
    statement="""
`schedule[i]` lists the working intervals `[start, end]` of employee `i`; each employee's intervals are
sorted and don't overlap, and every interval has positive length.

Return the intervals of time when **every** employee is free: the finite, positive-length gaps between
the moments when someone is working. Don't include the unbounded time before the first interval or after
the last one. Return the gaps sorted by start.
""",
    constraints="""
- `1 <= schedule.length <= 50`
- `1 <= schedule[i].length <= 120`
- `0 <= start < end <= 10^8`
""",
    signature=function("employeeFreeTime", [("schedule", "int[][][]")], "int[][]"),
    reference=_employee_free_time,
    brute=_free_time_brute,
    examples=[
        Example([[[[1, 2], [5, 6]], [[1, 3]], [[4, 10]]]], "Everyone is free from 3 to 4."),
        Example([[[[1, 3], [6, 7]], [[2, 4]], [[2, 5], [9, 12]]]], "Free from 5 to 6 and from 7 to 9."),
    ],
    edge_cases=[[[[[0, 1]]]], [[[[1, 2]], [[2, 3]]]], [[[[1, 2]], [[3, 4]]]], [[[[0, 10]], [[2, 3], [5, 6]]]]],
    generator=_schedule_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Task Scheduler


def _least_interval(tasks: list[str], n: int) -> int:
    counts = Counter(tasks).values()
    top = max(counts)
    ties = sum(1 for c in counts if c == top)
    return max(len(tasks), (top - 1) * (n + 1) + ties)


def _least_interval_brute(tasks: list[str], n: int) -> int:
    remaining = Counter(tasks)
    ready_at = {t: 0 for t in remaining}
    time = 0
    while remaining:
        available = [t for t in remaining if ready_at[t] <= time]
        if available:
            task = max(available, key=lambda t: (remaining[t], t))
            remaining[task] -= 1
            if remaining[task] == 0:
                del remaining[task]
            ready_at[task] = time + n + 1
        time += 1
    return time


TASK_SCHEDULER = ProblemSource(
    title="Task Scheduler",
    statement="""
A CPU must run the tasks in `tasks`, where each task is an uppercase letter; tasks may run in any order,
one per time unit. Two runs of the **same** letter must be at least `n` time units apart, so the CPU may
have to sit idle.

Return the minimum number of time units (including idle ones) needed to finish every task.
""",
    constraints="""
- `1 <= tasks.length <= 10^4`
- `tasks[i]` is an uppercase English letter
- `0 <= n <= 100`
""",
    signature=function("leastInterval", [("tasks", "char[]"), ("n", "int")], "int"),
    reference=_least_interval,
    brute=_least_interval_brute,
    brute_input_limit=400,
    examples=[
        Example([["A", "A", "A", "B", "B", "B"], 2], "A -> B -> idle -> A -> B -> idle -> A -> B takes 8 units."),
        Example([["A", "C", "A", "B", "D", "B"], 1], "A -> B -> C -> D -> A -> B needs no idling."),
        Example([["A", "A", "A", "B", "B", "B"], 3], "A -> B -> idle -> idle, twice, then A -> B: 10 units."),
    ],
    edge_cases=[
        [["A"], 0],
        [["A"], 100],
        [["A", "A"], 0],
        [["A", "B", "C"], 5],
        [["A", "A", "A", "A", "B", "B", "C"], 2],
    ],
    generator=lambda rng: [
        [rng.choice(letters) for _ in range(pick_n(rng, 1, 40, big=3000))]
        if (letters := string.ascii_uppercase[: rng.randint(1, 26)])
        else [],
        rng.randint(0, rng.choice([3, 100])),
    ],
    random_count=9,
)


# ---------------------------------------------------------------- Remove Covered Intervals


def _remove_covered(intervals: list[list[int]]) -> int:
    count, furthest = 0, -1
    for _, end in sorted(intervals, key=lambda iv: (iv[0], -iv[1])):
        if end > furthest:
            count += 1
            furthest = end
    return count


def _remove_covered_brute(intervals: list[list[int]]) -> int:
    return sum(
        not any(j != i and b[0] <= a[0] and a[1] <= b[1] for j, b in enumerate(intervals))
        for i, a in enumerate(intervals)
    )


def _unique_intervals(rng, n, hi):
    seen, out = set(), []
    while len(out) < n:
        a = rng.randint(0, hi - 1)
        iv = (a, rng.randint(a + 1, min(hi, a + rng.choice([3, 30, hi]))))
        if iv not in seen:
            seen.add(iv)
            out.append(list(iv))
    return out


REMOVE_COVERED = ProblemSource(
    title="Remove Covered Intervals",
    statement="""
All intervals in `intervals` are distinct and half-open, `[a, b)`. An interval `[a, b)` is *covered* by
another interval `[c, d)` when `c <= a` and `b <= d`.

Remove every interval that is covered by some other interval and return how many intervals remain.
""",
    constraints="""
- `1 <= intervals.length <= 1000`
- `0 <= a < b <= 10^5`, and all intervals are distinct
""",
    signature=function("removeCoveredIntervals", [("intervals", "int[][]")], "int"),
    reference=_remove_covered,
    brute=_remove_covered_brute,
    brute_input_limit=600,
    examples=[
        Example([[[1, 4], [3, 6], [2, 8]]], "[3,6) lies inside [2,8), leaving two intervals."),
        Example([[[1, 4], [2, 3]]], "[2,3) lies inside [1,4)."),
    ],
    edge_cases=[[[[0, 1]]], [[[1, 2], [1, 4], [3, 4]]], [[[1, 2], [2, 3]]], [[[0, 10], [5, 12]]]],
    generator=lambda rng: [
        _unique_intervals(rng, pick_n(rng, 1, 30, big=1000), hi)
        if (hi := rng.choice([30, 10**5])) > 30
        else _unique_intervals(rng, pick_n(rng, 1, 30), hi)
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Count Days Without Meetings


def _count_days(days: int, meetings: list[list[int]]) -> int:
    busy, end = 0, 0
    for start, finish in sorted(meetings):
        if finish <= end:
            continue
        busy += finish - max(start, end + 1) + 1
        end = finish
    return days - busy


def _count_days_brute(days: int, meetings: list[list[int]]) -> int:
    # Independent check: merge the closed day ranges (touching ranges stay separate but never overlap).
    return days - sum(end - start + 1 for start, end in _merge(meetings))


def _days_gen(rng):
    days = rng.choice([rng.randint(1, 60), rng.randint(1, 10**9)])
    meetings = []
    for _ in range(pick_n(rng, 1, 20, big=2500)):
        start = rng.randint(1, days)
        meetings.append([start, min(days, start + rng.randint(0, max(1, days // rng.choice([4, 50]))))])
    return [days, meetings]


COUNT_DAYS = ProblemSource(
    title="Count Days Without Meetings",
    statement="""
An employee is available on days `1` through `days`. `meetings[i] = [start_i, end_i]` is a meeting that
takes up every day from `start_i` to `end_i`, inclusive; meetings may overlap.

Return the number of available days with no meeting scheduled.
""",
    constraints="""
- `1 <= days <= 10^9`
- `1 <= meetings.length <= 10^5`
- `1 <= start_i <= end_i <= days`
""",
    signature=function("countDays", [("days", "int"), ("meetings", "int[][]")], "int"),
    reference=_count_days,
    brute=_count_days_brute,
    examples=[
        Example([10, [[5, 7], [1, 3], [9, 10]]], "Days 4 and 8 are free."),
        Example([5, [[2, 4], [1, 3]]], "Only day 5 is free."),
        Example([6, [[1, 6]]], "Every day has a meeting."),
    ],
    edge_cases=[[1, [[1, 1]]], [10, [[1, 1]]], [10, [[3, 5], [4, 4], [5, 7]]], [1000000000, [[1, 1000000000]]]],
    generator=_days_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Car Pooling


def _car_pooling(trips: list[list[int]], capacity: int) -> bool:
    changes = sorted([(start, num) for num, start, _ in trips] + [(end, -num) for num, _, end in trips])
    load = 0
    for _, delta in changes:
        load += delta
        if load > capacity:
            return False
    return True


def _car_pooling_brute(trips: list[list[int]], capacity: int) -> bool:
    last = max(end for _, _, end in trips)
    return all(sum(num for num, start, end in trips if start <= km < end) <= capacity for km in range(last + 1))


def _trips_gen(rng):
    trips = []
    for _ in range(pick_n(rng, 1, 15, big=1000)):
        start = rng.randint(0, 999)
        trips.append([rng.randint(1, 100), start, rng.randint(start + 1, min(1000, start + 60))])
    return [trips, rng.randint(1, 300)]


CAR_POOLING = ProblemSource(
    title="Car Pooling",
    statement="""
A car with `capacity` empty seats drives east only. `trips[i] = [numPassengers_i, from_i, to_i]` means
`numPassengers_i` people are picked up at kilometer `from_i` and dropped off at kilometer `to_i`
(passengers leave before new ones board at the same kilometer).

Return `true` if every trip can be completed without ever carrying more than `capacity` passengers.
""",
    constraints="""
- `1 <= trips.length <= 1000`
- `1 <= numPassengers_i <= 100`
- `0 <= from_i < to_i <= 1000`
- `1 <= capacity <= 10^5`
""",
    signature=function("carPooling", [("trips", "int[][]"), ("capacity", "int")], "bool"),
    reference=_car_pooling,
    brute=_car_pooling_brute,
    brute_input_limit=500,
    examples=[
        Example([[[2, 1, 5], [3, 3, 7]], 4], "Between km 3 and 5 there would be 5 passengers."),
        Example([[[2, 1, 5], [3, 3, 7]], 5], "The peak load is exactly 5."),
        Example([[[3, 2, 7], [3, 7, 9], [8, 3, 9]], 11]),
    ],
    edge_cases=[[[[1, 0, 1]], 1], [[[5, 0, 1]], 4], [[[2, 1, 3], [2, 3, 5]], 2], [[[100, 0, 1000]], 100]],
    generator=_trips_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Data Stream as Disjoint Intervals


class _SummaryRanges:
    def __init__(self) -> None:
        self.starts: list[int] = []
        self.ends: list[int] = []

    def addNum(self, value: int) -> None:
        i = bisect.bisect_right(self.starts, value)
        if i and self.ends[i - 1] >= value:
            return
        joins_left = i > 0 and self.ends[i - 1] == value - 1
        joins_right = i < len(self.starts) and self.starts[i] == value + 1
        if joins_left and joins_right:
            self.ends[i - 1] = self.ends[i]
            del self.starts[i], self.ends[i]
        elif joins_left:
            self.ends[i - 1] = value
        elif joins_right:
            self.starts[i] = value
        else:
            self.starts.insert(i, value)
            self.ends.insert(i, value)

    def getIntervals(self) -> list[list[int]]:
        return [[s, e] for s, e in zip(self.starts, self.ends, strict=True)]


class _SummaryRangesBrute:
    def __init__(self) -> None:
        self.values: set[int] = set()

    def addNum(self, value: int) -> None:
        self.values.add(value)

    def getIntervals(self) -> list[list[int]]:
        out: list[list[int]] = []
        for v in sorted(self.values):
            if out and out[-1][1] == v - 1:
                out[-1][1] = v
            else:
                out.append([v, v])
        return out


def _summary_gen(rng):
    hi = rng.choice([15, 60, 10**4])
    calls = [("SummaryRanges", [])]
    for _ in range(pick_n(rng, 1, 30, big=600)):
        calls.append(("addNum", [rng.randint(0, hi)]) if rng.random() < 0.7 else ("getIntervals", []))
    return ops(*calls)


SUMMARY_RANGES = ProblemSource(
    title="Data Stream as Disjoint Intervals",
    statement="""
Design a class that receives a stream of non-negative integers and can summarise the numbers seen so far
as a list of disjoint intervals.

Implement `SummaryRanges`:
- `SummaryRanges()` creates an empty summary.
- `addNum(value)` adds `value` to the stream (values may repeat).
- `getIntervals()` returns the numbers seen so far as disjoint closed intervals `[start, end]` of
  consecutive integers, sorted by start.

**Test format:** each test is a list of operations with their arguments; the expected output lists each
operation's return value (`null` for the constructor and `addNum`).
""",
    constraints="""
- `0 <= value <= 10^4`
- at most `3 * 10^4` calls in total
- at most `10^2` calls to `getIntervals`
""",
    signature=design("SummaryRanges", [], [("addNum", [("value", "int")], "void"), ("getIntervals", [], "int[][]")]),
    reference=_SummaryRanges,
    brute=_SummaryRangesBrute,
    examples=[
        Example(
            ops(
                ("SummaryRanges", []),
                ("addNum", [1]),
                ("getIntervals", []),
                ("addNum", [3]),
                ("getIntervals", []),
                ("addNum", [7]),
                ("addNum", [2]),
                ("getIntervals", []),
            ),
            "After adding 1, 3, 7 and 2 the summary is [1,3], [7,7].",
        ),
        Example(
            ops(("SummaryRanges", []), ("getIntervals", []), ("addNum", [5]), ("addNum", [5]), ("getIntervals", []))
        ),
    ],
    edge_cases=[
        ops(("SummaryRanges", []), ("addNum", [0]), ("addNum", [10000]), ("getIntervals", [])),
        ops(("SummaryRanges", []), ("addNum", [4]), ("addNum", [2]), ("addNum", [3]), ("getIntervals", [])),
    ],
    generator=_summary_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Minimum Interval to Include Each Query


def _min_interval(intervals: list[list[int]], queries: list[int]) -> list[int]:
    ordered = sorted(intervals)
    answer = [-1] * len(queries)
    heap: list[tuple[int, int]] = []
    i = 0
    for q, idx in sorted((q, idx) for idx, q in enumerate(queries)):
        while i < len(ordered) and ordered[i][0] <= q:
            left, right = ordered[i]
            heapq.heappush(heap, (right - left + 1, right))
            i += 1
        while heap and heap[0][1] < q:
            heapq.heappop(heap)
        if heap:
            answer[idx] = heap[0][0]
    return answer


def _min_interval_brute(intervals: list[list[int]], queries: list[int]) -> list[int]:
    return [min((r - left + 1 for left, r in intervals if left <= q <= r), default=-1) for q in queries]


def _min_interval_gen(rng):
    hi = rng.choice([40, 10**7])
    return [
        [
            [s, min(hi, s + rng.randint(0, hi // 8))]
            for s in (rng.randint(1, hi) for _ in range(pick_n(rng, 1, 20, big=1500)))
        ],
        [rng.randint(1, hi) for _ in range(pick_n(rng, 1, 20, big=1500))],
    ]


MIN_INTERVAL_QUERY = ProblemSource(
    title="Minimum Interval to Include Each Query",
    statement="""
The size of a closed interval `[left, right]` is `right - left + 1`, the number of integers it contains.

For each value `queries[j]`, find the smallest size among the intervals of `intervals` that contain it,
or `-1` if no interval contains it. Return the answers in the same order as the queries.
""",
    constraints="""
- `1 <= intervals.length, queries.length <= 10^5`
- `1 <= left <= right <= 10^7`
- `1 <= queries[j] <= 10^7`
""",
    signature=function("minInterval", [("intervals", "int[][]"), ("queries", "int[]")], "int[]"),
    reference=_min_interval,
    brute=_min_interval_brute,
    brute_input_limit=800,
    examples=[
        Example([[[1, 4], [2, 4], [3, 6], [4, 4]], [2, 3, 4, 5]], "Answers: 3 ([2,4]), 3, 1 ([4,4]), 4 ([3,6])."),
        Example([[[2, 3], [2, 5], [1, 8], [20, 25]], [2, 19, 5, 22]], "19 is in no interval."),
    ],
    edge_cases=[[[[1, 1]], [1, 2]], [[[1, 10], [5, 5]], [5, 5, 6]], [[[3, 3]], [1]]],
    generator=_min_interval_gen,
    random_count=8,
)


PROBLEMS = [
    MERGE_INTERVALS,
    INSERT_INTERVAL,
    MEETING_ROOMS_II,
    INTERVAL_INTERSECTIONS,
    EMPLOYEE_FREE_TIME,
    TASK_SCHEDULER,
    REMOVE_COVERED,
    COUNT_DAYS,
    CAR_POOLING,
    SUMMARY_RANGES,
    MIN_INTERVAL_QUERY,
]
