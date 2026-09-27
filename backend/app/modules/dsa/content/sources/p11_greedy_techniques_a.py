"""Pattern 11: Greedy Techniques (part 1 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import heapq
import itertools
from collections import Counter
from functools import cache

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, word

PATTERN_NUMBER = 11


# ---------------------------------------------------------------- Jump Game I


def _can_jump(nums: list[int]) -> bool:
    reach = 0
    for i, x in enumerate(nums):
        if i > reach:
            return False
        reach = max(reach, i + x)
    return True


def _can_jump_brute(nums: list[int]) -> bool:
    ok = [False] * len(nums)
    ok[-1] = True
    for i in range(len(nums) - 2, -1, -1):
        ok[i] = any(ok[j] for j in range(i + 1, min(len(nums), i + nums[i] + 1)))
    return ok[0]


JUMP_GAME = ProblemSource(
    title="Jump Game I",
    statement="""
You start at index `0` of `nums`. From index `i` you may jump forward by any number of steps from `1` up to `nums[i]`.
Return `true` if you can reach the last index.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `0 <= nums[i] <= 10^5`
""",
    signature=function("canJump", [("nums", "int[]")], "bool"),
    reference=_can_jump,
    brute=_can_jump_brute,
    brute_input_limit=400,
    examples=[Example([[2, 3, 1, 1, 4]], "Jump 1 step to index 1, then 3 steps to the end."), Example([[3, 2, 1, 0, 4]], "Every path gets stuck at index 3.")],
    edge_cases=[[[0]], [[0, 1]], [[1, 0]], [[2, 0, 0]], [[1, 1, 0, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 30, big=4000), 0, rng.choice([2, 3, 10]))],
    random_count=9,
)


# ---------------------------------------------------------------- Boats to Save People


def _num_rescue_boats(people: list[int], limit: int) -> int:
    people = sorted(people)
    lo, hi, boats = 0, len(people) - 1, 0
    while lo <= hi:
        if people[lo] + people[hi] <= limit:
            lo += 1
        hi -= 1
        boats += 1
    return boats


def _boats_brute(people: list[int], limit: int) -> int:
    @cache
    def best(rest: tuple[int, ...]) -> int:
        if not rest:
            return 0
        first, others = rest[0], rest[1:]
        options = [1 + best(others)]
        for i, w in enumerate(others):
            if first + w <= limit:
                options.append(1 + best(others[:i] + others[i + 1 :]))
        return min(options)

    return best(tuple(sorted(people)))


def _boats_gen(rng):
    limit = rng.randint(1, rng.choice([10, 3 * 10**4]))
    return [ints(rng, pick_n(rng, 1, 9, big=4000), 1, limit), limit]


BOATS = ProblemSource(
    title="Boats to Save People",
    statement="""
`people[i]` is the weight of person `i`. Every boat can carry at most two people at the same time, as long as their total
weight is at most `limit`. Return the minimum number of boats needed to carry everyone. (No single person is heavier than
`limit`.)
""",
    constraints="""
- `1 <= people.length <= 5 * 10^4`
- `1 <= people[i] <= limit <= 3 * 10^4`
""",
    signature=function("numRescueBoats", [("people", "int[]"), ("limit", "int")], "int"),
    reference=_num_rescue_boats,
    brute=_boats_brute,
    brute_input_limit=45,
    examples=[Example([[1, 2], 3], "Both people fit in one boat."), Example([[3, 2, 2, 1], 3], "(1, 2), (2) and (3)."), Example([[3, 5, 3, 4], 5], "Everyone needs their own boat.")],
    edge_cases=[[[1], 1], [[5, 5], 10], [[1, 1, 1, 1], 2], [[2, 49, 10, 30, 20], 50]],
    generator=_boats_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Gas Stations


def _can_complete_circuit(gas: list[int], cost: list[int]) -> int:
    if sum(gas) < sum(cost):
        return -1
    start = tank = 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:
            start, tank = i + 1, 0
    return start


def _circuit_brute(gas: list[int], cost: list[int]) -> int:
    n = len(gas)
    for s in range(n):
        tank = 0
        for step in range(n):
            i = (s + step) % n
            tank += gas[i] - cost[i]
            if tank < 0:
                break
        else:
            return s
    return -1


def _gas_gen(rng):
    n = pick_n(rng, 1, 12, big=4000)
    return [ints(rng, n, 0, 10), ints(rng, n, 0, 10)]


GAS_STATIONS = ProblemSource(
    title="Gas Stations",
    statement="""
Gas stations stand around a circular route. Station `i` gives you `gas[i]` units of gas, and driving from station `i` to the
next station (`i + 1`, wrapping from the last back to `0`) uses `cost[i]` units. Your car's tank is unlimited and starts empty.

Return the index of a station where you can start and drive once around the whole circuit, or `-1` if no start works. If
several starts work, any of them is accepted.
""",
    constraints="""
- `1 <= n <= 10^5`, `gas.length == cost.length == n`
- `0 <= gas[i], cost[i] <= 10^4`
""",
    signature=function("canCompleteCircuit", [("gas", "int[]"), ("cost", "int[]")], "int"),
    reference=_can_complete_circuit,
    brute=_circuit_brute,
    brute_input_limit=400,
    compare="checker",
    checker="gas_station_start",
    examples=[Example([[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]], "Start at station 3 with 4 units and never run out."), Example([[2, 3, 4], [3, 4, 3]], "The route needs more gas than all stations give.")],
    edge_cases=[[[5], [4]], [[0], [1]], [[1, 1], [1, 1]], [[3, 1, 1], [1, 2, 2]]],
    generator=_gas_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Two City Scheduling


def _two_city_cost(costs: list[list[int]]) -> int:
    ordered = sorted(costs, key=lambda c: c[0] - c[1])
    half = len(costs) // 2
    return sum(c[0] for c in ordered[:half]) + sum(c[1] for c in ordered[half:])


def _two_city_brute(costs: list[list[int]]) -> int:
    n = len(costs)
    return min(
        sum(costs[i][0] if i in group else costs[i][1] for i in range(n)) for group in map(set, itertools.combinations(range(n), n // 2))
    )


TWO_CITY = ProblemSource(
    title="Two City Scheduling",
    statement="""
`2n` people must be interviewed; flying person `i` to city A costs `costs[i][0]` and to city B costs `costs[i][1]`. Exactly `n`
people must go to each city. Return the minimum total cost.
""",
    constraints="""
- `costs.length == 2n`, `2 <= costs.length <= 100`
- `1 <= costs[i][0], costs[i][1] <= 1000`
""",
    signature=function("twoCitySchedCost", [("costs", "int[][]")], "int"),
    reference=_two_city_cost,
    brute=_two_city_brute,
    brute_input_limit=120,
    examples=[Example([[[10, 20], [30, 200], [400, 50], [30, 20]]], "People 0 and 1 go to A, 2 and 3 to B: 10 + 30 + 50 + 20 = 110."), Example([[[259, 770], [448, 54], [926, 667], [184, 139], [840, 118], [577, 469]]])],
    edge_cases=[[[[1, 2], [2, 1]]], [[[5, 5], [5, 5]]]],
    generator=lambda rng: [[[rng.randint(1, 1000), rng.randint(1, 1000)] for _ in range(2 * rng.randint(1, rng.choice([5, 50])))]],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Number of Refueling Stops


def _min_refuel_stops(target: int, startFuel: int, stations: list[list[int]]) -> int:
    heap: list[int] = []
    fuel, stops, i = startFuel, 0, 0
    while fuel < target:
        while i < len(stations) and stations[i][0] <= fuel:
            heapq.heappush(heap, -stations[i][1])
            i += 1
        if not heap:
            return -1
        fuel -= heapq.heappop(heap)
        stops += 1
    return stops


def _refuel_brute(target: int, startFuel: int, stations: list[list[int]]) -> int:
    reach = [startFuel] + [0] * len(stations)  # reach[k] = furthest distance with k stops
    for pos, gas in stations:
        for k in range(len(stations) - 1, -1, -1):
            if reach[k] >= pos:
                reach[k + 1] = max(reach[k + 1], reach[k] + gas)
    return next((k for k, r in enumerate(reach) if r >= target), -1)


def _refuel_gen(rng):
    target = rng.randint(1, rng.choice([50, 10**6]))
    positions = sorted(set(ints(rng, pick_n(rng, 0, 10, big=400), 1, max(1, target - 1))))
    return [target, rng.randint(1, max(1, target // 3)), [[p, rng.randint(1, max(1, target // 4))] for p in positions]]


REFUEL_STOPS = ProblemSource(
    title="Minimum Number of Refueling Stops",
    statement="""
A car starts at position `0` with `startFuel` liters and wants to reach position `target`; it uses one liter per mile and has an
unlimited tank. `stations[i] = [position_i, fuel_i]` describes stations along the way, sorted by position. Stopping at a station
lets you take all of its fuel.

Return the minimum number of stops needed to reach `target`, or `-1` if it is impossible. Reaching a station or the target with
exactly 0 liters left is fine.
""",
    constraints="""
- `1 <= target, startFuel <= 10^9`
- `0 <= stations.length <= 500`
- `1 <= position_1 < position_2 < ... < target`, `1 <= fuel_i < 10^9`
""",
    signature=function("minRefuelStops", [("target", "int"), ("startFuel", "int"), ("stations", "int[][]")], "int"),
    reference=_min_refuel_stops,
    brute=_refuel_brute,
    examples=[Example([1, 1, []], "No stops needed."), Example([100, 1, [[10, 100]]], "The first station is out of reach."), Example([100, 10, [[10, 60], [20, 30], [30, 30], [60, 40]]], "Stop at 10 and 60.")],
    edge_cases=[[10, 10, [[5, 1]]], [10, 5, [[5, 5]]], [10, 4, [[5, 5]]]],
    generator=_refuel_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Largest Palindromic Number


def _largest_palindromic(num: str) -> str:
    counts = Counter(num)
    half = "".join(d * (counts[d] // 2) for d in "9876543210")
    half = half.lstrip("0")
    middle = next((d for d in "9876543210" if counts[d] % 2), "")
    result = half + middle + half[::-1]
    return result or "0"


def _largest_palindromic_brute(num: str) -> str:
    best = -1
    for r in range(1, len(num) + 1):
        for combo in set(itertools.permutations(num, r)):
            s = "".join(combo)
            if s == s[::-1] and (s == "0" or s[0] != "0"):
                best = max(best, int(s))
    return str(best)


LARGEST_PALINDROMIC = ProblemSource(
    title="Largest Palindromic Number",
    statement="""
`num` is a string of digits. Using some of its digits (at least one, each at most once, in any order), build the largest
palindromic integer possible and return it as a string. The result must not have leading zeros (the single digit `"0"` is fine).
""",
    constraints="""
- `1 <= num.length <= 10^5`
- `num` consists of digits
""",
    signature=function("largestPalindromic", [("num", "string")], "string"),
    reference=_largest_palindromic,
    brute=_largest_palindromic_brute,
    brute_input_limit=8,
    examples=[Example(["444947137"], "\"7449447\"."), Example(["00009"], "\"9\"; zeros can't lead."), Example(["00"], "\"0\".")],
    edge_cases=[["0"], ["5"], ["11"], ["1001"], ["900"], ["12321"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 6, big=15000), rng.choice(["0123456789", "009", "12"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Jump Game II


def _jump(nums: list[int]) -> int:
    jumps = end = reach = 0
    for i in range(len(nums) - 1):
        reach = max(reach, i + nums[i])
        if i == end:
            jumps, end = jumps + 1, reach
    return jumps


def _jump_brute(nums: list[int]) -> int:
    best = [0] + [10**9] * (len(nums) - 1)
    for i in range(len(nums)):
        for j in range(i + 1, min(len(nums), i + nums[i] + 1)):
            best[j] = min(best[j], best[i] + 1)
    return best[-1]


def _reachable_gen(rng):
    nums = ints(rng, pick_n(rng, 1, 30, big=4000), 1, rng.choice([3, 6, 1000]))
    return [nums]


JUMP_GAME_II = ProblemSource(
    title="Jump Game II",
    statement="""
You start at index `0` of `nums`. From index `i` you may jump forward by `1` to `nums[i]` steps. The last index is always reachable.
Return the minimum number of jumps needed to reach it.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `0 <= nums[i] <= 1000`
- the last index is reachable
""",
    signature=function("jump", [("nums", "int[]")], "int"),
    reference=_jump,
    brute=_jump_brute,
    brute_input_limit=500,
    examples=[Example([[2, 3, 1, 1, 4]], "Index 0 -> 1 -> 4: two jumps."), Example([[2, 3, 0, 1, 4]])],
    edge_cases=[[[0]], [[1, 0]], [[5, 0, 0, 0, 0]], [[1, 1, 1, 1]]],
    generator=_reachable_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Number of Steps to Reduce a Binary Number to One


def _num_steps(s: str) -> int:
    steps, carry = 0, 0
    for bit in reversed(s[1:]):
        if int(bit) + carry == 1:
            steps += 2
            carry = 1
        else:
            steps += 1
    return steps + carry


def _num_steps_brute(s: str) -> int:
    n, steps = int(s, 2), 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else n + 1
        steps += 1
    return steps


STEPS_BINARY = ProblemSource(
    title="Number of Steps to Reduce a Binary Number to One",
    statement="""
`s` is the binary representation of a positive integer. Repeat until the number is `1`: if it is even, divide it by 2;
otherwise add 1. Return how many steps this takes.
""",
    constraints="""
- `1 <= s.length <= 500`
- `s` consists of `0` and `1`, and `s[0] == '1'`
""",
    signature=function("numSteps", [("s", "string")], "int"),
    reference=_num_steps,
    brute=_num_steps_brute,
    examples=[Example(["1101"], "13 -> 14 -> 7 -> 8 -> 4 -> 2 -> 1: six steps."), Example(["10"]), Example(["1"])],
    edge_cases=[["11"], ["111"], ["1000"], ["1" * 500]],
    generator=lambda rng: ["1" + word(rng, rng.randint(0, rng.choice([10, 499])), "01")],
    random_count=8,
)


# ---------------------------------------------------------------- Rearranging Fruits


def _min_cost_fruits(basket1: list[int], basket2: list[int]) -> int:
    counts = Counter(basket1)
    counts.subtract(basket2)
    extra = []
    for fruit, diff in counts.items():
        if diff % 2:
            return -1
        extra += [fruit] * (abs(diff) // 2)
    extra.sort()
    cheapest = min(min(basket1), min(basket2))
    return sum(min(x, 2 * cheapest) for x in extra[: len(extra) // 2])


def _fruits_brute(basket1: list[int], basket2: list[int]) -> int:
    start = (tuple(sorted(basket1)), tuple(sorted(basket2)))
    dist = {start: 0}
    frontier = [(0, start)]
    while frontier:
        cost, (a, b) = heapq.heappop(frontier)
        if a == b:
            return cost
        if cost > dist[(a, b)]:
            continue
        for i in range(len(a)):
            for j in range(len(b)):
                na, nb = list(a), list(b)
                na[i], nb[j] = b[j], a[i]
                state = (tuple(sorted(na)), tuple(sorted(nb)))
                c = cost + min(a[i], b[j])
                if c < dist.get(state, 10**18):
                    dist[state] = c
                    heapq.heappush(frontier, (c, state))
    return -1


def _fruits_gen(rng):
    n = pick_n(rng, 1, 4, big=3000)
    pool = ints(rng, 2 * n, 1, rng.choice([4, 10**9]))
    rng.shuffle(pool)
    a, b = pool[:n], pool[n:]
    if rng.random() < 0.5:
        return [a, b]
    common = ints(rng, n, 1, 6)
    return [common[:], sorted(common, reverse=True)]


REARRANGE_FRUITS = ProblemSource(
    title="Rearranging Fruits",
    statement="""
Two baskets each hold `n` fruits; `basket1[i]` and `basket2[i]` are fruit costs. Any number of times you may swap the `i`-th fruit of
basket 1 with the `j`-th fruit of basket 2; a swap costs `min(basket1[i], basket2[j])`.

The baskets are *equal* when sorting both gives the same array. Return the minimum total cost to make them equal, or `-1` if it's
impossible.
""",
    constraints="""
- `1 <= n <= 10^5`
- `1 <= basket1[i], basket2[i] <= 10^9`
""",
    signature=function("minCost", [("basket1", "int[]"), ("basket2", "int[]")], "long"),
    reference=_min_cost_fruits,
    brute=_fruits_brute,
    brute_input_limit=30,
    examples=[Example([[4, 2, 2, 2], [1, 4, 1, 2]], "Swap a 2 from basket 1 with a 1 from basket 2 (cost 1)."), Example([[2, 3, 4, 1], [3, 2, 5, 1]], "4 and 5 can never be paired up.")],
    edge_cases=[[[1], [1]], [[1], [2]], [[5, 5], [8, 8]], [[1, 8, 8], [1, 9, 9]]],
    generator=_fruits_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Swap


def _maximum_swap(num: int) -> int:
    digits = list(str(num))
    last = {d: i for i, d in enumerate(digits)}
    for i, d in enumerate(digits):
        for bigger in "9876543210":
            if bigger <= d:
                break
            if last.get(bigger, -1) > i:
                j = last[bigger]
                digits[i], digits[j] = digits[j], digits[i]
                return int("".join(digits))
    return num


def _maximum_swap_brute(num: int) -> int:
    digits = list(str(num))
    best = num
    for i, j in itertools.combinations(range(len(digits)), 2):
        d = digits[:]
        d[i], d[j] = d[j], d[i]
        best = max(best, int("".join(d)))
    return best


MAXIMUM_SWAP = ProblemSource(
    title="Maximum Swap",
    statement="""
You may swap two digits of the non-negative integer `num` **at most once**. Return the largest number you can get.
""",
    constraints="""
- `0 <= num <= 10^8`
""",
    signature=function("maximumSwap", [("num", "int")], "int"),
    reference=_maximum_swap,
    brute=_maximum_swap_brute,
    examples=[Example([2736], "Swap 2 and 7: 7236."), Example([9973], "Already the largest.")],
    edge_cases=[[0], [10], [98368], [1993], [100000000]],
    generator=lambda rng: [rng.randint(0, rng.choice([999, 10**8]))],
    random_count=8,
)


# ---------------------------------------------------------------- Can Place Flowers


def _can_place_flowers(flowerbed: list[int], n: int) -> bool:
    bed = [0] + flowerbed + [0]
    for i in range(1, len(bed) - 1):
        if bed[i - 1] == bed[i] == bed[i + 1] == 0:
            bed[i] = 1
            n -= 1
    return n <= 0


def _flowers_brute(flowerbed: list[int], n: int) -> bool:
    free = [i for i, x in enumerate(flowerbed) if x == 0]
    for r in range(min(n, len(free)), len(free) + 1):
        for spots in itertools.combinations(free, r):
            bed = flowerbed[:]
            for s in spots:
                bed[s] = 1
            if all(not (bed[i] and bed[i + 1]) for i in range(len(bed) - 1)) and r >= n:
                return True
    return n == 0


def _bed_gen(rng):
    bed, prev = [], 0
    for _ in range(pick_n(rng, 1, 14, big=4000)):
        x = 0 if prev else int(rng.random() < 0.3)
        bed.append(x)
        prev = x
    return [bed, rng.randint(0, 4)]


CAN_PLACE_FLOWERS = ProblemSource(
    title="Can Place Flowers",
    statement="""
A flowerbed is a row of plots, `1` for planted and `0` for empty; no two flowers are adjacent yet, and flowers may never be planted in
adjacent plots. Return `true` if `n` new flowers can be planted.
""",
    constraints="""
- `1 <= flowerbed.length <= 2 * 10^4`
- `flowerbed[i]` is `0` or `1`, with no two adjacent `1`s
- `0 <= n <= flowerbed.length`
""",
    signature=function("canPlaceFlowers", [("flowerbed", "int[]"), ("n", "int")], "bool"),
    reference=_can_place_flowers,
    brute=_flowers_brute,
    brute_input_limit=50,
    examples=[Example([[1, 0, 0, 0, 1], 1]), Example([[1, 0, 0, 0, 1], 2])],
    edge_cases=[[[0], 1], [[1], 1], [[0], 0], [[0, 0], 2], [[0, 0, 0], 2]],
    generator=_bed_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Largest Odd Number in String


def _largest_odd(num: str) -> str:
    for i in range(len(num) - 1, -1, -1):
        if int(num[i]) % 2:
            return num[: i + 1]
    return ""


LARGEST_ODD = ProblemSource(
    title="Largest Odd Number in String",
    statement="""
`num` is a large integer written as a string without leading zeros. Return the largest odd integer that is a non-empty **substring** of
`num`, as a string, or `""` if there is none.
""",
    constraints="""
- `1 <= num.length <= 10^5`
- `num` consists of digits with no leading zeros
""",
    signature=function("largestOddNumber", [("num", "string")], "string"),
    reference=_largest_odd,
    brute=lambda num: max((num[i:j] for i in range(len(num)) for j in range(i + 1, len(num) + 1) if int(num[j - 1]) % 2 and num[i] != "0"), key=lambda t: (len(t), t), default=""),
    brute_input_limit=60,
    examples=[Example(["52"], "\"5\" is the only odd substring without a leading zero."), Example(["4206"]), Example(["35427"])],
    edge_cases=[["1"], ["2"], ["10"], ["2468013"]],
    generator=lambda rng: [(lambda s: ("1" + s[1:]) if s.startswith("0") else s)(word(rng, pick_n(rng, 1, 20, big=15000), rng.choice(["0123456789", "02468", "2461"])))],
    random_count=8,
)


# ---------------------------------------------------------------- Assign Cookies


def _find_content_children(g: list[int], s: list[int]) -> int:
    g, s = sorted(g), sorted(s)
    child = 0
    for cookie in s:
        if child < len(g) and cookie >= g[child]:
            child += 1
    return child


def _cookies_brute(g: list[int], s: list[int]) -> int:
    best = 0
    for r in range(min(len(g), len(s)), 0, -1):
        for kids in itertools.combinations(sorted(g), r):
            if all(c >= k for c, k in zip(sorted(s)[-r:], kids, strict=True)):
                return r
    return best


ASSIGN_COOKIES = ProblemSource(
    title="Assign Cookies",
    statement="""
Child `i` is content with a cookie of size at least `g[i]`; cookie `j` has size `s[j]`. Each child gets at most one cookie and each cookie
goes to at most one child. Return the maximum number of content children.
""",
    constraints="""
- `1 <= g.length <= 3 * 10^4`
- `0 <= s.length <= 3 * 10^4`
- `1 <= g[i], s[j] <= 2^31 - 1`
""",
    signature=function("findContentChildren", [("g", "int[]"), ("s", "int[]")], "int"),
    reference=_find_content_children,
    brute=_cookies_brute,
    brute_input_limit=50,
    examples=[Example([[1, 2, 3], [1, 1]], "Only the child with greed 1 is content."), Example([[1, 2], [1, 2, 3]])],
    edge_cases=[[[5], []], [[5], [4]], [[1, 1], [1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 7, big=3000), 1, rng.choice([6, 2**31 - 1])), ints(rng, pick_n(rng, 0, 7, big=3000), 1, rng.choice([6, 2**31 - 1]))],
    random_count=8,
)


# ---------------------------------------------------------------- Candy


def _candy(ratings: list[int]) -> int:
    n = len(ratings)
    give = [1] * n
    for i in range(1, n):
        if ratings[i] > ratings[i - 1]:
            give[i] = give[i - 1] + 1
    for i in range(n - 2, -1, -1):
        if ratings[i] > ratings[i + 1]:
            give[i] = max(give[i], give[i + 1] + 1)
    return sum(give)


def _candy_brute(ratings: list[int]) -> int:
    give = [1] * len(ratings)
    changed = True
    while changed:
        changed = False
        for i in range(len(ratings)):
            for j in (i - 1, i + 1):
                if 0 <= j < len(ratings) and ratings[i] > ratings[j] and give[i] <= give[j]:
                    give[i] = give[j] + 1
                    changed = True
    return sum(give)


CANDY = ProblemSource(
    title="Candy",
    statement="""
Children stand in a line with ratings `ratings`. Give each child candies so that every child gets at least one, and a child with a higher
rating than an **adjacent** child gets more candies than that neighbour. Return the minimum total number of candies.
""",
    constraints="""
- `1 <= ratings.length <= 2 * 10^4`
- `0 <= ratings[i] <= 2 * 10^4`
""",
    signature=function("candy", [("ratings", "int[]")], "int"),
    reference=_candy,
    brute=_candy_brute,
    brute_input_limit=300,
    examples=[Example([[1, 0, 2]], "2, 1, 2 candies."), Example([[1, 2, 2]], "1, 2, 1: equal neighbours don't need to differ.")],
    edge_cases=[[[5]], [[1, 2, 3, 4]], [[4, 3, 2, 1]], [[1, 3, 2, 2, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 30, big=5000), 0, rng.choice([3, 2 * 10**4]))],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Replacements to Sort the Array


def _minimum_replacement(nums: list[int]) -> int:
    ops, limit = 0, nums[-1]
    for x in reversed(nums[:-1]):
        parts = (x + limit - 1) // limit
        ops += parts - 1
        limit = x // parts
    return ops


def _replacement_brute(nums: list[int]) -> int:
    # dp over the largest allowed value for the element to the right
    @cache
    def best(i: int, limit: int) -> int:
        if i < 0:
            return 0
        x = nums[i]
        options = []
        for parts in range(1, x + 1):
            if (x + parts - 1) // parts <= limit:
                options.append(parts - 1 + best(i - 1, x // parts))
        return min(options)

    return best(len(nums) - 2, nums[-1])


MIN_REPLACEMENTS = ProblemSource(
    title="Minimum Replacements to Sort the Array",
    statement="""
In one operation you may replace any element of `nums` with two positive integers that add up to it (the array grows by one). Return the
minimum number of operations needed to make `nums` sorted in non-decreasing order.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^9`
""",
    signature=function("minimumReplacement", [("nums", "int[]")], "long"),
    reference=_minimum_replacement,
    brute=lambda nums: _replacement_brute(nums) if max(nums) <= 40 else NotImplemented,
    examples=[Example([[3, 9, 3]], "Split 9 into 3 + 3 + 3: two operations."), Example([[1, 2, 3, 4, 5]], "Already sorted.")],
    edge_cases=[[[7]], [[5, 1]], [[12, 9, 7, 6, 17, 19, 21]], [[1000000000, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 8, big=4000), 1, rng.choice([30, 10**9]))],
    random_count=8,
)


PROBLEMS = [
    JUMP_GAME,
    BOATS,
    GAS_STATIONS,
    TWO_CITY,
    REFUEL_STOPS,
    LARGEST_PALINDROMIC,
    JUMP_GAME_II,
    STEPS_BINARY,
    REARRANGE_FRUITS,
    MAXIMUM_SWAP,
    CAN_PLACE_FLOWERS,
    LARGEST_ODD,
    ASSIGN_COOKIES,
    CANDY,
    MIN_REPLACEMENTS,
]
