"""Pattern 26: Custom Data Structures. Original statements; outputs come from `reference`.

Every problem here is a design problem: `reference` is an efficient class and `brute` a deliberately naive one.
"""

from __future__ import annotations

import bisect
import heapq
import random
from collections import Counter, OrderedDict, defaultdict, deque
from collections.abc import Callable

from app.modules.dsa.content.model import Example, ProblemSource, design, ops, pick_n, word

PATTERN_NUMBER = 26

_FORMAT = """
**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the
constructor and for methods that return nothing)."""


def _calls(rng: random.Random, ctor: tuple[str, list], step: Callable[[random.Random], tuple[str, list] | None], big: int = 300) -> dict:
    """Constructor followed by randomly generated operations (`step` returns None to skip a draw)."""
    calls = [ctor]
    for _ in range(pick_n(rng, 1, 25, big=big)):
        call = step(rng)
        if call is not None:
            calls.append(call)
    return ops(*calls)


# ---------------------------------------------------------------- Snapshot Array


class _SnapshotArray:
    def __init__(self, length: int) -> None:
        self.history: list[list[tuple[int, int]]] = [[(-1, 0)] for _ in range(length)]  # (snap_id, value)
        self.snap_id = 0

    def set(self, index: int, val: int) -> None:
        history = self.history[index]
        if history[-1][0] == self.snap_id:
            history[-1] = (self.snap_id, val)
        else:
            history.append((self.snap_id, val))

    def snap(self) -> int:
        self.snap_id += 1
        return self.snap_id - 1

    def get(self, index: int, snap_id: int) -> int:
        history = self.history[index]
        return history[bisect.bisect_right(history, (snap_id, float("inf"))) - 1][1]


class _SnapshotArrayBrute:
    def __init__(self, length: int) -> None:
        self.current = [0] * length
        self.snaps: list[list[int]] = []

    def set(self, index: int, val: int) -> None:
        self.current[index] = val

    def snap(self) -> int:
        self.snaps.append(self.current[:])
        return len(self.snaps) - 1

    def get(self, index: int, snap_id: int) -> int:
        return self.snaps[snap_id][index]


def _snapshot_gen(rng: random.Random) -> dict:
    length = rng.randint(1, rng.choice([4, 1000]))
    state = {"snaps": 0}

    def step(r: random.Random) -> tuple[str, list] | None:
        roll = r.random()
        if roll < 0.4:
            return ("set", [r.randrange(length), r.randint(0, 10**9)])
        if roll < 0.65:
            state["snaps"] += 1
            return ("snap", [])
        if state["snaps"]:
            return ("get", [r.randrange(length), r.randrange(state["snaps"])])
        return None

    return _calls(rng, ("SnapshotArray", [length]), step)


SNAPSHOT_ARRAY = ProblemSource(
    title="Snapshot Array",
    statement="""
Design `SnapshotArray`, an array that can take snapshots of itself:
- `SnapshotArray(length)` creates an array of `length` zeros.
- `set(index, val)` sets the element at `index`.
- `snap()` takes a snapshot and returns its id: the number of earlier `snap` calls.
- `get(index, snap_id)` returns the value at `index` when snapshot `snap_id` was taken.

Store only what changes: memory should not grow with `length * snaps`.
""" + _FORMAT,
    constraints="""
- `1 <= length <= 5 * 10^4`, `0 <= val <= 10^9`
- `get` only uses existing snapshot ids; at most `5 * 10^4` calls
""",
    signature=design("SnapshotArray", [("length", "int")], [("set", [("index", "int"), ("val", "int")], "void"), ("snap", [], "int"), ("get", [("index", "int"), ("snap_id", "int")], "int")]),
    reference=_SnapshotArray,
    brute=_SnapshotArrayBrute,
    examples=[
        Example(ops(("SnapshotArray", [3]), ("set", [0, 5]), ("snap", []), ("set", [0, 6]), ("get", [0, 0])), "Snapshot 0 saw index 0 as 5."),
        Example(ops(("SnapshotArray", [1]), ("snap", []), ("snap", []), ("set", [0, 4]), ("snap", []), ("get", [0, 1]), ("get", [0, 2]))),
    ],
    edge_cases=[ops(("SnapshotArray", [2]), ("set", [1, 7]), ("set", [1, 8]), ("snap", []), ("get", [1, 0]), ("get", [0, 0]))],
    generator=_snapshot_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Time-Based Key-Value Store


class _TimeMap:
    def __init__(self) -> None:
        self.times: dict[str, list[int]] = defaultdict(list)
        self.values: dict[str, list[str]] = defaultdict(list)

    def set(self, key: str, value: str, timestamp: int) -> None:
        self.times[key].append(timestamp)
        self.values[key].append(value)

    def get(self, key: str, timestamp: int) -> str:
        i = bisect.bisect_right(self.times[key], timestamp)
        return self.values[key][i - 1] if i else ""


class _TimeMapBrute:
    def __init__(self) -> None:
        self.entries: list[tuple[str, str, int]] = []

    def set(self, key: str, value: str, timestamp: int) -> None:
        self.entries.append((key, value, timestamp))

    def get(self, key: str, timestamp: int) -> str:
        best = max(((t, v) for k, v, t in self.entries if k == key and t <= timestamp), default=None)
        return best[1] if best else ""


def _timemap_gen(rng: random.Random) -> dict:
    keys = [word(rng, rng.randint(1, 3), "ab") for _ in range(rng.randint(1, 3))]
    clock = {"t": 0}

    def step(r: random.Random) -> tuple[str, list]:
        clock["t"] += r.randint(1, 5)
        if r.random() < 0.5:
            return ("set", [r.choice(keys), word(r, r.randint(1, 4), "xyz"), clock["t"]])
        return ("get", [r.choice(keys + ["q"]), r.randint(0, clock["t"] + 3)])

    return _calls(rng, ("TimeMap", []), step)


TIME_MAP = ProblemSource(
    title="Time-Based Key-Value Store",
    statement="""
Design `TimeMap`, a key-value store that keeps every value a key has had:
- `set(key, value, timestamp)` stores `value` for `key` at `timestamp`.
- `get(key, timestamp)` returns the value set for `key` at the largest timestamp `<= timestamp`, or `""` if there is none.

Timestamps passed to `set` are strictly increasing across all calls.
""" + _FORMAT,
    constraints="""
- keys and values are short lowercase strings
- `1 <= timestamp <= 10^7`; at most `2 * 10^5` calls
""",
    signature=design("TimeMap", [], [("set", [("key", "string"), ("value", "string"), ("timestamp", "int")], "void"), ("get", [("key", "string"), ("timestamp", "int")], "string")]),
    reference=_TimeMap,
    brute=_TimeMapBrute,
    examples=[
        Example(ops(("TimeMap", []), ("set", ["foo", "bar", 1]), ("get", ["foo", 1]), ("get", ["foo", 3]), ("set", ["foo", "bar2", 4]), ("get", ["foo", 4]), ("get", ["foo", 5]))),
        Example(ops(("TimeMap", []), ("set", ["a", "x", 5]), ("get", ["a", 4]), ("get", ["b", 9])), "Nothing was set at or before time 4."),
    ],
    edge_cases=[ops(("TimeMap", []), ("get", ["k", 1]))],
    generator=_timemap_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Implement LRU Cache


class _LRUCache:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.data: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key]

    def put(self, key: int, value: int) -> None:
        self.data[key] = value
        self.data.move_to_end(key)
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)


class _LRUCacheBrute:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.items: list[list[int]] = []  # least recently used first

    def get(self, key: int) -> int:
        for i, (k, v) in enumerate(self.items):
            if k == key:
                self.items.append(self.items.pop(i))
                return v
        return -1

    def put(self, key: int, value: int) -> None:
        self.items = [pair for pair in self.items if pair[0] != key] + [[key, value]]
        if len(self.items) > self.capacity:
            self.items.pop(0)


def _cache_gen(name: str) -> Callable[[random.Random], dict]:
    def gen(rng: random.Random) -> dict:
        capacity = rng.randint(1, rng.choice([3, 50]))
        keys = rng.randint(1, capacity + rng.choice([1, 4]))

        def step(r: random.Random) -> tuple[str, list]:
            if r.random() < 0.5:
                return ("put", [r.randrange(keys), r.randint(0, 10**5)])
            return ("get", [r.randrange(keys)])

        return _calls(rng, (name, [capacity]), step)

    return gen


LRU_CACHE = ProblemSource(
    title="Implement LRU Cache",
    statement="""
Design a Least Recently Used cache with a fixed capacity:
- `LRUCache(capacity)` creates the cache.
- `get(key)` returns the value for `key`, or `-1` if absent. A successful `get` counts as a use.
- `put(key, value)` inserts or updates `key` (also a use). If the cache then holds more than `capacity` keys, it evicts the least recently used
  one.

Both operations should run in `O(1)` average time.
""" + _FORMAT,
    constraints="""
- `1 <= capacity <= 3000`
- `0 <= key <= 10^4`, `0 <= value <= 10^5`; at most `2 * 10^5` calls
""",
    signature=design("LRUCache", [("capacity", "int")], [("get", [("key", "int")], "int"), ("put", [("key", "int"), ("value", "int")], "void")]),
    reference=_LRUCache,
    brute=_LRUCacheBrute,
    examples=[
        Example(ops(("LRUCache", [2]), ("put", [1, 1]), ("put", [2, 2]), ("get", [1]), ("put", [3, 3]), ("get", [2]), ("put", [4, 4]), ("get", [1]), ("get", [3]), ("get", [4])), "Key 2 is evicted, then key 1."),
        Example(ops(("LRUCache", [1]), ("put", [5, 1]), ("put", [5, 2]), ("get", [5]))),
    ],
    edge_cases=[ops(("LRUCache", [1]), ("get", [0]), ("put", [0, 0]), ("put", [1, 1]), ("get", [0]))],
    generator=_cache_gen("LRUCache"),
    random_count=8,
)


# ---------------------------------------------------------------- Insert Delete GetRandom O(1)


class _RandomizedSet:
    def __init__(self) -> None:
        self.values: list[int] = []
        self.where: dict[int, int] = {}

    def insert(self, val: int) -> bool:
        if val in self.where:
            return False
        self.where[val] = len(self.values)
        self.values.append(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.where:
            return False
        i, last = self.where.pop(val), self.values.pop()
        if last != val:  # move the last element into the hole
            self.values[i] = last
            self.where[last] = i
        return True

    def getRandom(self) -> int:  # noqa: N802 - judge method name
        return random.choice(self.values)


class _RandomizedSetBrute:
    def __init__(self) -> None:
        self.values: set[int] = set()

    def insert(self, val: int) -> bool:
        added = val not in self.values
        self.values.add(val)
        return added

    def remove(self, val: int) -> bool:
        present = val in self.values
        self.values.discard(val)
        return present

    def getRandom(self) -> int:  # noqa: N802
        return next(iter(self.values))


def _randomized_gen(rng: random.Random) -> dict:
    present: set[int] = set()

    def step(r: random.Random) -> tuple[str, list] | None:
        roll = r.random()
        if roll < 0.15:
            return ("getRandom", []) if len(present) == 1 else None  # only when the answer is forced
        val = r.randint(-5, 5)
        if roll < 0.6:
            present.add(val)
            return ("insert", [val])
        present.discard(val)
        return ("remove", [val])

    return _calls(rng, ("RandomizedSet", []), step)


RANDOMIZED_SET = ProblemSource(
    title="Insert Delete GetRandom O(1)",
    statement="""
Design `RandomizedSet`, with every operation in average `O(1)` time:
- `insert(val)` adds `val` if absent; returns `true` if it was added.
- `remove(val)` removes `val` if present; returns `true` if it was removed.
- `getRandom()` returns a uniformly random element (the set is non-empty when it is called).

Since a judge can't check randomness from a single call, tests only call `getRandom` when the set holds exactly one element.
""" + _FORMAT,
    constraints="""
- `-2^31 <= val <= 2^31 - 1`
- at most `2 * 10^5` calls
""",
    signature=design("RandomizedSet", [], [("insert", [("val", "int")], "bool"), ("remove", [("val", "int")], "bool"), ("getRandom", [], "int")]),
    reference=_RandomizedSet,
    brute=_RandomizedSetBrute,
    examples=[
        Example(ops(("RandomizedSet", []), ("insert", [1]), ("remove", [2]), ("insert", [2]), ("remove", [1]), ("insert", [2]), ("getRandom", [])), "Only 2 remains, so getRandom must return 2."),
        Example(ops(("RandomizedSet", []), ("insert", [0]), ("insert", [0]), ("remove", [0]), ("remove", [0]))),
    ],
    edge_cases=[ops(("RandomizedSet", []), ("insert", [-2147483648]), ("getRandom", []))],
    generator=_randomized_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Min Stack


class _MinStack:
    def __init__(self) -> None:
        self.stack: list[tuple[int, int]] = []  # (value, minimum so far)

    def push(self, val: int) -> None:
        self.stack.append((val, min(val, self.stack[-1][1]) if self.stack else val))

    def pop(self) -> None:
        self.stack.pop()

    def top(self) -> int:
        return self.stack[-1][0]

    def getMin(self) -> int:  # noqa: N802
        return self.stack[-1][1]


class _MinStackBrute:
    def __init__(self) -> None:
        self.items: list[int] = []

    def push(self, val: int) -> None:
        self.items.append(val)

    def pop(self) -> None:
        self.items.pop()

    def top(self) -> int:
        return self.items[-1]

    def getMin(self) -> int:  # noqa: N802
        return min(self.items)


def _stack_gen(name: str, extra: list[str]) -> Callable[[random.Random], dict]:
    def gen(rng: random.Random) -> dict:
        size = {"n": 0}

        def step(r: random.Random) -> tuple[str, list]:
            if not size["n"] or r.random() < 0.45:
                size["n"] += 1
                return ("push", [r.randint(-(hi := r.choice([5, 2**31 - 1])), hi)])
            op = r.choice(["pop", "top", *extra])
            size["n"] -= op.startswith("pop")
            return (op, [])

        return _calls(rng, (name, []), step)

    return gen


MIN_STACK = ProblemSource(
    title="Min Stack",
    statement="""
Design a stack that also reports its minimum, with every operation in `O(1)` time:
- `push(val)`, `pop()` and `top()` behave like a normal stack.
- `getMin()` returns the smallest element currently in the stack.

`pop`, `top` and `getMin` are only called on a non-empty stack.
""" + _FORMAT,
    constraints="""
- `-2^31 <= val <= 2^31 - 1`; at most `3 * 10^4` calls
""",
    signature=design("MinStack", [], [("push", [("val", "int")], "void"), ("pop", [], "void"), ("top", [], "int"), ("getMin", [], "int")]),
    reference=_MinStack,
    brute=_MinStackBrute,
    examples=[Example(ops(("MinStack", []), ("push", [-2]), ("push", [0]), ("push", [-3]), ("getMin", []), ("pop", []), ("top", []), ("getMin", []))), Example(ops(("MinStack", []), ("push", [5]), ("getMin", []), ("push", [3]), ("getMin", []), ("pop", []), ("getMin", [])))],
    edge_cases=[ops(("MinStack", []), ("push", [1]), ("push", [1]), ("pop", []), ("getMin", []))],
    generator=_stack_gen("MinStack", ["getMin", "getMin"]),
    random_count=8,
)


# ---------------------------------------------------------------- Range Module


class _RangeModule:
    def __init__(self) -> None:
        self.starts: list[int] = []  # disjoint, sorted half-open intervals
        self.ends: list[int] = []

    def _cut(self, left: int, right: int) -> tuple[int, int]:
        """Indices of the stored intervals touching [left, right]."""
        return bisect.bisect_left(self.ends, left), bisect.bisect_right(self.starts, right)

    def addRange(self, left: int, right: int) -> None:  # noqa: N802
        i, j = self._cut(left, right)
        if i < j:
            left, right = min(left, self.starts[i]), max(right, self.ends[j - 1])
        self.starts[i:j], self.ends[i:j] = [left], [right]

    def queryRange(self, left: int, right: int) -> bool:  # noqa: N802
        i = bisect.bisect_right(self.starts, left) - 1
        return i >= 0 and self.ends[i] >= right

    def removeRange(self, left: int, right: int) -> None:  # noqa: N802
        i, j = bisect.bisect_right(self.ends, left), bisect.bisect_left(self.starts, right)
        keep_starts, keep_ends = [], []
        if i < j:
            if self.starts[i] < left:
                keep_starts.append(self.starts[i])
                keep_ends.append(left)
            if self.ends[j - 1] > right:
                keep_starts.append(right)
                keep_ends.append(self.ends[j - 1])
        self.starts[i:j], self.ends[i:j] = keep_starts, keep_ends


class _RangeModuleBrute:
    def __init__(self) -> None:
        self.tracked: set[int] = set()  # unit cells [x, x + 1)

    def addRange(self, left: int, right: int) -> None:  # noqa: N802
        self.tracked |= set(range(left, right))

    def queryRange(self, left: int, right: int) -> bool:  # noqa: N802
        return all(x in self.tracked for x in range(left, right))

    def removeRange(self, left: int, right: int) -> None:  # noqa: N802
        self.tracked -= set(range(left, right))


def _range_module_gen(rng: random.Random) -> dict:
    hi = rng.choice([12, 60])

    def step(r: random.Random) -> tuple[str, list]:
        left = r.randint(1, hi - 1)
        right = r.randint(left + 1, min(hi, left + r.choice([3, hi])))
        return (r.choice(["addRange", "addRange", "queryRange", "queryRange", "removeRange"]), [left, right])

    return _calls(rng, ("RangeModule", []), step)


RANGE_MODULE = ProblemSource(
    title="Range Module",
    statement="""
Design `RangeModule`, which tracks half-open ranges of real numbers `[left, right)`:
- `addRange(left, right)` starts tracking every number in `[left, right)`.
- `queryRange(left, right)` returns `true` if every number in `[left, right)` is currently tracked.
- `removeRange(left, right)` stops tracking every number in `[left, right)`.
""" + _FORMAT,
    constraints="""
- `1 <= left < right <= 10^9`; at most `10^4` calls
""",
    signature=design("RangeModule", [], [("addRange", [("left", "int"), ("right", "int")], "void"), ("queryRange", [("left", "int"), ("right", "int")], "bool"), ("removeRange", [("left", "int"), ("right", "int")], "void")]),
    reference=_RangeModule,
    brute=_RangeModuleBrute,
    examples=[Example(ops(("RangeModule", []), ("addRange", [10, 20]), ("removeRange", [14, 16]), ("queryRange", [10, 14]), ("queryRange", [13, 15]), ("queryRange", [16, 17]))), Example(ops(("RangeModule", []), ("addRange", [1, 3]), ("addRange", [3, 5]), ("queryRange", [2, 4])), "Adjacent ranges merge.")],
    edge_cases=[ops(("RangeModule", []), ("queryRange", [1, 2]), ("removeRange", [1, 2]), ("addRange", [1, 2]), ("queryRange", [1, 2]))],
    generator=_range_module_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Shortest Word Distance II


class _WordDistance:
    def __init__(self, wordsDict: list[str]) -> None:
        self.positions: dict[str, list[int]] = defaultdict(list)
        for i, w in enumerate(wordsDict):
            self.positions[w].append(i)

    def shortest(self, word1: str, word2: str) -> int:
        a, b = self.positions[word1], self.positions[word2]
        i = j = 0
        best = float("inf")
        while i < len(a) and j < len(b):  # merge two sorted position lists
            best = min(best, abs(a[i] - b[j]))
            if a[i] < b[j]:
                i += 1
            else:
                j += 1
        return int(best)


class _WordDistanceBrute:
    def __init__(self, wordsDict: list[str]) -> None:
        self.words = wordsDict

    def shortest(self, word1: str, word2: str) -> int:
        return min(abs(i - j) for i, a in enumerate(self.words) if a == word1 for j, b in enumerate(self.words) if b == word2)


def _word_distance_gen(rng: random.Random) -> dict:
    vocab = list(dict.fromkeys(word(rng, rng.randint(1, 3), "abc") for _ in range(rng.randint(2, 6))))
    if len(vocab) < 2:
        vocab.append("zz")
    words = vocab + [rng.choice(vocab) for _ in range(rng.randint(0, rng.choice([10, 300])))]
    rng.shuffle(words)

    def step(r: random.Random) -> tuple[str, list]:
        a, b = r.sample(vocab, 2)
        return ("shortest", [a, b])

    return _calls(rng, ("WordDistance", [words]), step, big=100)


WORD_DISTANCE_II = ProblemSource(
    title="Shortest Word Distance II",
    statement="""
Design `WordDistance`, which is built once from `wordsDict` and then answers many queries:
- `shortest(word1, word2)` returns the smallest distance between an index holding `word1` and an index holding `word2`.

Both words are in `wordsDict` and differ from each other.
""" + _FORMAT,
    constraints="""
- `1 <= wordsDict.length <= 3 * 10^4`
- at most `5000` calls to `shortest`
""",
    signature=design("WordDistance", [("wordsDict", "string[]")], [("shortest", [("word1", "string"), ("word2", "string")], "int")]),
    reference=_WordDistance,
    brute=_WordDistanceBrute,
    examples=[Example(ops(("WordDistance", [["practice", "makes", "perfect", "coding", "makes"]]), ("shortest", ["coding", "practice"]), ("shortest", ["makes", "coding"]))), Example(ops(("WordDistance", [["x", "y", "x", "x", "y"]]), ("shortest", ["x", "y"])))],
    edge_cases=[ops(("WordDistance", [["a", "b"]]), ("shortest", ["b", "a"]))],
    generator=_word_distance_gen,
    random_count=8,
)


# ---------------------------------------------------------------- LFU Cache


class _LFUCache:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.value: dict[int, int] = {}
        self.freq: dict[int, int] = {}
        self.buckets: dict[int, OrderedDict[int, None]] = defaultdict(OrderedDict)  # freq -> keys, least recent first
        self.min_freq = 0

    def _touch(self, key: int) -> None:
        f = self.freq[key]
        del self.buckets[f][key]
        if not self.buckets[f] and self.min_freq == f:
            self.min_freq += 1
        self.freq[key] = f + 1
        self.buckets[f + 1][key] = None

    def get(self, key: int) -> int:
        if key not in self.value:
            return -1
        self._touch(key)
        return self.value[key]

    def put(self, key: int, value: int) -> None:
        if key in self.value:
            self.value[key] = value
            self._touch(key)
            return
        if len(self.value) == self.capacity:
            evicted, _ = self.buckets[self.min_freq].popitem(last=False)
            del self.value[evicted], self.freq[evicted]
        self.value[key], self.freq[key] = value, 1
        self.buckets[1][key] = None
        self.min_freq = 1


class _LFUCacheBrute:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.entries: dict[int, list[int]] = {}  # key -> [value, uses, last use time]
        self.clock = 0

    def get(self, key: int) -> int:
        self.clock += 1
        if key not in self.entries:
            return -1
        entry = self.entries[key]
        entry[1] += 1
        entry[2] = self.clock
        return entry[0]

    def put(self, key: int, value: int) -> None:
        self.clock += 1
        if key in self.entries:
            entry = self.entries[key]
            entry[0], entry[1], entry[2] = value, entry[1] + 1, self.clock
            return
        if len(self.entries) == self.capacity:
            victim = min(self.entries, key=lambda k: (self.entries[k][1], self.entries[k][2]))
            del self.entries[victim]
        self.entries[key] = [value, 1, self.clock]


LFU_CACHE = ProblemSource(
    title="LFU Cache",
    statement="""
Design a Least Frequently Used cache with a fixed capacity. Every key has a *use counter*, set to `1` when the key is inserted and increased by
every `get` or `put` on it.
- `get(key)` returns the value, or `-1` if absent.
- `put(key, value)` updates an existing key, or inserts a new one. When inserting into a full cache, first evict the key with the smallest use
  counter; ties go to the least recently used of them.

Both operations should run in `O(1)` average time.
""" + _FORMAT,
    constraints="""
- `1 <= capacity <= 10^4`
- `0 <= key <= 10^5`, `0 <= value <= 10^9`; at most `2 * 10^5` calls
""",
    signature=design("LFUCache", [("capacity", "int")], [("get", [("key", "int")], "int"), ("put", [("key", "int"), ("value", "int")], "void")]),
    reference=_LFUCache,
    brute=_LFUCacheBrute,
    examples=[
        Example(ops(("LFUCache", [2]), ("put", [1, 1]), ("put", [2, 2]), ("get", [1]), ("put", [3, 3]), ("get", [2]), ("get", [3]), ("put", [4, 4]), ("get", [1]), ("get", [3]), ("get", [4])), "Key 2 (used once) goes first; later 1 and 3 tie and 1 is older."),
        Example(ops(("LFUCache", [1]), ("put", [1, 1]), ("put", [2, 2]), ("get", [1]), ("get", [2]))),
    ],
    edge_cases=[ops(("LFUCache", [2]), ("put", [1, 1]), ("put", [1, 5]), ("put", [2, 2]), ("put", [3, 3]), ("get", [1]), ("get", [2]))],
    generator=_cache_gen("LFUCache"),
    random_count=10,
)


# ---------------------------------------------------------------- Moving Average from Data Stream


class _MovingAverage:
    def __init__(self, size: int) -> None:
        self.window: deque[int] = deque(maxlen=size)
        self.total = 0

    def next(self, val: int) -> float:
        if len(self.window) == self.window.maxlen:
            self.total -= self.window[0]
        self.window.append(val)
        self.total += val
        return self.total / len(self.window)


class _MovingAverageBrute:
    def __init__(self, size: int) -> None:
        self.size = size
        self.values: list[int] = []

    def next(self, val: int) -> float:
        self.values.append(val)
        recent = self.values[-self.size :]
        return sum(recent) / len(recent)


MOVING_AVERAGE = ProblemSource(
    title="Moving Average from Data Stream",
    statement="""
Design `MovingAverage(size)`: `next(val)` adds `val` to the stream and returns the average of the last `size` values (or of all values so far, if
there are fewer). Answers within `10^-5` are accepted.
""" + _FORMAT,
    constraints="""
- `1 <= size <= 1000`, `-10^5 <= val <= 10^5`; at most `10^4` calls
""",
    signature=design("MovingAverage", [("size", "int")], [("next", [("val", "int")], "double")]),
    reference=_MovingAverage,
    brute=_MovingAverageBrute,
    compare="float_tolerance",
    examples=[Example(ops(("MovingAverage", [3]), ("next", [1]), ("next", [10]), ("next", [3]), ("next", [5])), "1, 5.5, 4.667, 6."), Example(ops(("MovingAverage", [1]), ("next", [-4]), ("next", [7])))],
    edge_cases=[ops(("MovingAverage", [1000]), ("next", [100000]))],
    generator=lambda rng: _calls(rng, ("MovingAverage", [rng.randint(1, rng.choice([4, 1000]))]), lambda r: ("next", [r.randint(-(10**5), 10**5)])),
    random_count=8,
)


# ---------------------------------------------------------------- Two Sum III - Data structure design


class _TwoSum:
    def __init__(self) -> None:
        self.counts: Counter[int] = Counter()

    def add(self, number: int) -> None:
        self.counts[number] += 1

    def find(self, value: int) -> bool:
        for x, c in self.counts.items():
            y = value - x
            if y in self.counts and (y != x or c > 1):
                return True
        return False


class _TwoSumBrute:
    def __init__(self) -> None:
        self.numbers: list[int] = []

    def add(self, number: int) -> None:
        self.numbers.append(number)

    def find(self, value: int) -> bool:
        n = self.numbers
        return any(n[i] + n[j] == value for i in range(len(n)) for j in range(i + 1, len(n)))


TWO_SUM_III = ProblemSource(
    title="Two Sum III - Data structure design",
    statement="""
Design `TwoSum`, which receives a stream of integers:
- `add(number)` adds `number` to the collection.
- `find(value)` returns `true` if two elements of the collection (at different positions) add up to `value`.
""" + _FORMAT,
    constraints="""
- `-10^5 <= number <= 10^5`, `-2^31 <= value <= 2^31 - 1`; at most `10^4` calls
""",
    signature=design("TwoSum", [], [("add", [("number", "int")], "void"), ("find", [("value", "int")], "bool")]),
    reference=_TwoSum,
    brute=_TwoSumBrute,
    examples=[Example(ops(("TwoSum", []), ("add", [1]), ("add", [3]), ("add", [5]), ("find", [4]), ("find", [7]))), Example(ops(("TwoSum", []), ("add", [2]), ("find", [4]), ("add", [2]), ("find", [4])), "A number can pair with itself only if added twice.")],
    edge_cases=[ops(("TwoSum", []), ("find", [0]))],
    generator=lambda rng: _calls(rng, ("TwoSum", []), lambda r: ("add", [r.randint(-5, 5)]) if r.random() < 0.55 else ("find", [r.randint(-10, 10)]), big=200),
    random_count=8,
)


# ---------------------------------------------------------------- Range Sum Query - Immutable


class _NumArray:
    def __init__(self, nums: list[int]) -> None:
        self.prefix = [0]
        for x in nums:
            self.prefix.append(self.prefix[-1] + x)

    def sumRange(self, left: int, right: int) -> int:  # noqa: N802
        return self.prefix[right + 1] - self.prefix[left]


class _NumArrayBrute:
    def __init__(self, nums: list[int]) -> None:
        self.nums = nums

    def sumRange(self, left: int, right: int) -> int:  # noqa: N802
        return sum(self.nums[left : right + 1])


def _num_array_gen(rng: random.Random) -> dict:
    nums = [rng.randint(-(10**5), 10**5) for _ in range(pick_n(rng, 1, 15, big=3000))]

    def step(r: random.Random) -> tuple[str, list]:
        left = r.randrange(len(nums))
        return ("sumRange", [left, r.randint(left, len(nums) - 1)])

    return _calls(rng, ("NumArray", [nums]), step, big=200)


RANGE_SUM_IMMUTABLE = ProblemSource(
    title="Range Sum Query - Immutable",
    statement="""
Design `NumArray(nums)`: `sumRange(left, right)` returns the sum of `nums[left..right]` (inclusive). The array never changes, and there may be
many queries, so each query should run in `O(1)`.
""" + _FORMAT,
    constraints="""
- `1 <= nums.length <= 10^4`, `-10^5 <= nums[i] <= 10^5`
- `0 <= left <= right < nums.length`; at most `10^4` calls
""",
    signature=design("NumArray", [("nums", "int[]")], [("sumRange", [("left", "int"), ("right", "int")], "int")]),
    reference=_NumArray,
    brute=_NumArrayBrute,
    examples=[Example(ops(("NumArray", [[-2, 0, 3, -5, 2, -1]]), ("sumRange", [0, 2]), ("sumRange", [2, 5]), ("sumRange", [0, 5]))), Example(ops(("NumArray", [[7]]), ("sumRange", [0, 0])))],
    generator=_num_array_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Design HashSet


class _MyHashSet:
    def __init__(self) -> None:
        self.buckets: list[list[int]] = [[] for _ in range(1024)]

    def add(self, key: int) -> None:
        bucket = self.buckets[key % 1024]
        if key not in bucket:
            bucket.append(key)

    def remove(self, key: int) -> None:
        bucket = self.buckets[key % 1024]
        if key in bucket:
            bucket.remove(key)

    def contains(self, key: int) -> bool:
        return key in self.buckets[key % 1024]


class _MyHashSetBrute:
    def __init__(self) -> None:
        self.keys: set[int] = set()

    def add(self, key: int) -> None:
        self.keys.add(key)

    def remove(self, key: int) -> None:
        self.keys.discard(key)

    def contains(self, key: int) -> bool:
        return key in self.keys


DESIGN_HASHSET = ProblemSource(
    title="Design HashSet",
    statement="""
Design a hash set without any built-in hash table library:
- `add(key)` inserts `key`.
- `remove(key)` removes `key` if present.
- `contains(key)` returns `true` if `key` is in the set.
""" + _FORMAT,
    constraints="""
- `0 <= key <= 10^6`; at most `10^4` calls
""",
    signature=design("MyHashSet", [], [("add", [("key", "int")], "void"), ("remove", [("key", "int")], "void"), ("contains", [("key", "int")], "bool")]),
    reference=_MyHashSet,
    brute=_MyHashSetBrute,
    examples=[Example(ops(("MyHashSet", []), ("add", [1]), ("add", [2]), ("contains", [1]), ("contains", [3]), ("add", [2]), ("contains", [2]), ("remove", [2]), ("contains", [2]))), Example(ops(("MyHashSet", []), ("add", [0]), ("add", [1024]), ("remove", [0]), ("contains", [1024])), "Colliding keys stay independent.")],
    edge_cases=[ops(("MyHashSet", []), ("remove", [5]), ("contains", [5]))],
    generator=lambda rng: _calls(rng, ("MyHashSet", []), lambda r: (r.choice(["add", "remove", "contains", "contains"]), [r.choice([r.randint(0, 3), r.randint(0, 3) * 1024, r.randint(0, 10**6)])])),
    random_count=8,
)


# ---------------------------------------------------------------- Max Stack


class _MaxStack:
    """Lazy deletion: a stack and a max-heap share entry ids; removed ids are skipped."""

    def __init__(self) -> None:
        self.stack: list[tuple[int, int]] = []  # (value, id)
        self.heap: list[tuple[int, int]] = []  # (-value, -id)
        self.removed: set[int] = set()
        self.next_id = 0

    def _clean(self) -> None:
        while self.stack and self.stack[-1][1] in self.removed:
            self.stack.pop()
        while self.heap and -self.heap[0][1] in self.removed:
            heapq.heappop(self.heap)

    def push(self, x: int) -> None:
        self.stack.append((x, self.next_id))
        heapq.heappush(self.heap, (-x, -self.next_id))
        self.next_id += 1

    def pop(self) -> int:
        self._clean()
        value, ident = self.stack.pop()
        self.removed.add(ident)
        return value

    def top(self) -> int:
        self._clean()
        return self.stack[-1][0]

    def peekMax(self) -> int:  # noqa: N802
        self._clean()
        return -self.heap[0][0]

    def popMax(self) -> int:  # noqa: N802
        self._clean()
        value, neg_id = heapq.heappop(self.heap)
        self.removed.add(-neg_id)
        return -value


class _MaxStackBrute:
    def __init__(self) -> None:
        self.items: list[int] = []

    def push(self, x: int) -> None:
        self.items.append(x)

    def pop(self) -> int:
        return self.items.pop()

    def top(self) -> int:
        return self.items[-1]

    def peekMax(self) -> int:  # noqa: N802
        return max(self.items)

    def popMax(self) -> int:  # noqa: N802
        best = max(self.items)
        index = len(self.items) - 1 - self.items[::-1].index(best)
        return self.items.pop(index)


MAX_STACK = ProblemSource(
    title="Max Stack",
    statement="""
Design a stack that supports finding and removing its maximum:
- `push(x)`, `pop()` and `top()` behave like a normal stack (`pop` returns the removed element).
- `peekMax()` returns the largest element.
- `popMax()` removes and returns the largest element; if several are tied, it removes the one closest to the top.

`top` should be `O(1)` and every other call `O(log n)`. Calls other than `push` only happen on a non-empty stack.
""" + _FORMAT,
    constraints="""
- `-10^7 <= x <= 10^7`; at most `10^5` calls
""",
    signature=design("MaxStack", [], [("push", [("x", "int")], "void"), ("pop", [], "int"), ("top", [], "int"), ("peekMax", [], "int"), ("popMax", [], "int")]),
    reference=_MaxStack,
    brute=_MaxStackBrute,
    examples=[Example(ops(("MaxStack", []), ("push", [5]), ("push", [1]), ("push", [5]), ("top", []), ("popMax", []), ("top", []), ("peekMax", []), ("pop", []), ("top", [])), "popMax removes the upper 5."), Example(ops(("MaxStack", []), ("push", [-1]), ("push", [-2]), ("peekMax", []), ("popMax", []), ("top", [])))],
    edge_cases=[ops(("MaxStack", []), ("push", [3]), ("popMax", []), ("push", [2]), ("top", []))],
    generator=_stack_gen("MaxStack", ["peekMax", "popMax"]),
    random_count=10,
)


# ---------------------------------------------------------------- Stream of Characters


class _StreamChecker:
    def __init__(self, words: list[str]) -> None:
        self.trie: dict = {}  # built from reversed words
        for w in words:
            node = self.trie
            for ch in reversed(w):
                node = node.setdefault(ch, {})
            node["$"] = True
        self.recent: deque[str] = deque(maxlen=max(map(len, words)))

    def query(self, letter: str) -> bool:
        self.recent.appendleft(letter)
        node = self.trie
        for ch in self.recent:
            node = node.get(ch)
            if node is None:
                return False
            if "$" in node:
                return True
        return False


class _StreamCheckerBrute:
    def __init__(self, words: list[str]) -> None:
        self.words = words
        self.stream = ""

    def query(self, letter: str) -> bool:
        self.stream += letter
        return any(self.stream.endswith(w) for w in self.words)


def _stream_gen(rng: random.Random) -> dict:
    words = list(dict.fromkeys(word(rng, rng.randint(1, 4), "abc") for _ in range(rng.randint(1, 6))))
    return _calls(rng, ("StreamChecker", [words]), lambda r: ("query", [r.choice("abc")]), big=200)


STREAM_OF_CHARACTERS = ProblemSource(
    title="Stream of Characters",
    statement="""
Design `StreamChecker(words)`. Letters arrive one at a time; `query(letter)` appends `letter` to the stream and returns `true` if some suffix of
the stream so far is one of the `words`.
""" + _FORMAT,
    constraints="""
- `1 <= words.length <= 2000`, `1 <= words[i].length <= 200`, lowercase letters
- at most `4 * 10^4` calls to `query`
""",
    signature=design("StreamChecker", [("words", "string[]")], [("query", [("letter", "char")], "bool")]),
    reference=_StreamChecker,
    brute=_StreamCheckerBrute,
    examples=[Example(ops(("StreamChecker", [["cd", "f", "kl"]]), ("query", ["a"]), ("query", ["b"]), ("query", ["c"]), ("query", ["d"]), ("query", ["e"]), ("query", ["f"]), ("query", ["g"]), ("query", ["h"]), ("query", ["i"]), ("query", ["j"]), ("query", ["k"]), ("query", ["l"]))), Example(ops(("StreamChecker", [["ab", "b"]]), ("query", ["b"]), ("query", ["a"]), ("query", ["b"])), "\"b\" matches on its own each time.")],
    edge_cases=[ops(("StreamChecker", [["a", "aa"]]), ("query", ["a"]), ("query", ["a"]), ("query", ["b"]))],
    generator=_stream_gen,
    random_count=8,
)


# ---------------------------------------------------------------- All O`one Data Structures


class _AllOne:
    """Keys bucketed by count; a sorted list of the non-empty counts gives min and max."""

    def __init__(self) -> None:
        self.count: dict[str, int] = {}
        self.bucket: dict[int, dict[str, None]] = defaultdict(dict)
        self.levels: list[int] = []

    def _move(self, key: str, old: int, new: int) -> None:
        if old:
            del self.bucket[old][key]
            if not self.bucket[old]:
                del self.bucket[old]
                self.levels.pop(bisect.bisect_left(self.levels, old))
        if new:
            if new not in self.bucket:
                bisect.insort(self.levels, new)
            self.bucket[new][key] = None
            self.count[key] = new
        else:
            del self.count[key]

    def inc(self, key: str) -> None:
        old = self.count.get(key, 0)
        self._move(key, old, old + 1)

    def dec(self, key: str) -> None:
        old = self.count[key]
        self._move(key, old, old - 1)

    def getMaxKey(self) -> str:  # noqa: N802
        return next(iter(self.bucket[self.levels[-1]])) if self.levels else ""

    def getMinKey(self) -> str:  # noqa: N802
        return next(iter(self.bucket[self.levels[0]])) if self.levels else ""


def _all_one_gen(rng: random.Random) -> dict:
    counts: Counter[str] = Counter()

    def step(r: random.Random) -> tuple[str, list]:
        roll = r.random()
        if roll < 0.45 or not +counts:
            key = r.choice(["a", "b", "c", "dd"])
            counts[key] += 1
            return ("inc", [key])
        if roll < 0.7:
            key = r.choice(sorted(+counts))
            counts[key] -= 1
            return ("dec", [key])
        return (r.choice(["getMaxKey", "getMinKey"]), [])

    return _calls(rng, ("AllOne", []), step)


ALL_ONE = ProblemSource(
    title="All O`one Data Structures",
    statement="""
Design `AllOne`, which stores string counts, with every operation in average `O(1)` time:
- `inc(key)` increases `key`'s count by 1 (inserting it with count 1 if absent).
- `dec(key)` decreases `key`'s count by 1, removing it at 0 (`key` is always present when `dec` is called).
- `getMaxKey()` returns a key with the largest count, or `""` if there are none.
- `getMinKey()` returns a key with the smallest count, or `""` if there are none.

When several keys tie, any of them is accepted.
""" + _FORMAT,
    constraints="""
- `1 <= key.length <= 10`, lowercase letters; at most `5 * 10^4` calls
""",
    signature=design("AllOne", [], [("inc", [("key", "string")], "void"), ("dec", [("key", "string")], "void"), ("getMaxKey", [], "string"), ("getMinKey", [], "string")]),
    reference=_AllOne,
    compare="checker",
    checker="all_one",
    examples=[
        Example(ops(("AllOne", []), ("inc", ["hello"]), ("inc", ["hello"]), ("getMaxKey", []), ("getMinKey", []), ("inc", ["leet"]), ("getMaxKey", []), ("getMinKey", []))),
        Example(ops(("AllOne", []), ("getMaxKey", []), ("inc", ["a"]), ("dec", ["a"]), ("getMinKey", [])), "Empty structure: \"\"."),
    ],
    generator=_all_one_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Finding MK Average


class _MKAverage:
    """Sorted window of the last m values; the middle part excludes the k smallest and k largest."""

    def __init__(self, m: int, k: int) -> None:
        self.m, self.k = m, k
        self.window: deque[int] = deque()
        self.ordered: list[int] = []

    def addElement(self, num: int) -> None:  # noqa: N802
        self.window.append(num)
        bisect.insort(self.ordered, num)
        if len(self.window) > self.m:
            self.ordered.pop(bisect.bisect_left(self.ordered, self.window.popleft()))

    def calculateMKAverage(self) -> int:  # noqa: N802
        if len(self.window) < self.m:
            return -1
        middle = self.ordered[self.k : self.m - self.k]
        return sum(middle) // len(middle)


class _MKAverageBrute:
    def __init__(self, m: int, k: int) -> None:
        self.m, self.k = m, k
        self.values: list[int] = []

    def addElement(self, num: int) -> None:  # noqa: N802
        self.values.append(num)

    def calculateMKAverage(self) -> int:  # noqa: N802
        if len(self.values) < self.m:
            return -1
        last = sorted(self.values[-self.m :])
        kept = last[self.k : len(last) - self.k]
        return sum(kept) // len(kept)


def _mk_gen(rng: random.Random) -> dict:
    m = rng.randint(3, rng.choice([6, 100]))
    k = rng.randint(1, (m - 1) // 2)
    return _calls(rng, ("MKAverage", [m, k]), lambda r: ("addElement", [r.randint(1, r.choice([10, 10**5]))]) if r.random() < 0.7 else ("calculateMKAverage", []))


MK_AVERAGE = ProblemSource(
    title="Finding MK Average",
    statement="""
Design `MKAverage(m, k)` over a stream of integers:
- `addElement(num)` appends `num` to the stream.
- `calculateMKAverage()` returns `-1` if fewer than `m` numbers have arrived. Otherwise, take the last `m` numbers, drop the `k` smallest and the
  `k` largest, and return the average of the rest rounded down.
""" + _FORMAT,
    constraints="""
- `3 <= m <= 10^5`, `1 <= k` and `2k < m`
- `1 <= num <= 10^5`; at most `10^5` calls
""",
    signature=design("MKAverage", [("m", "int"), ("k", "int")], [("addElement", [("num", "int")], "void"), ("calculateMKAverage", [], "int")]),
    reference=_MKAverage,
    brute=_MKAverageBrute,
    examples=[Example(ops(("MKAverage", [3, 1]), ("addElement", [3]), ("addElement", [1]), ("calculateMKAverage", []), ("addElement", [10]), ("calculateMKAverage", []), ("addElement", [5]), ("addElement", [5]), ("addElement", [5]), ("calculateMKAverage", [])), "The window [3,1,10] keeps only 3."), Example(ops(("MKAverage", [5, 2]), ("addElement", [1]), ("addElement", [2]), ("addElement", [3]), ("addElement", [4]), ("addElement", [5]), ("calculateMKAverage", [])))],
    edge_cases=[ops(("MKAverage", [3, 1]), ("calculateMKAverage", []))],
    generator=_mk_gen,
    random_count=8,
)


PROBLEMS = [
    SNAPSHOT_ARRAY,
    TIME_MAP,
    LRU_CACHE,
    RANDOMIZED_SET,
    MIN_STACK,
    RANGE_MODULE,
    WORD_DISTANCE_II,
    LFU_CACHE,
    MOVING_AVERAGE,
    TWO_SUM_III,
    RANGE_SUM_IMMUTABLE,
    DESIGN_HASHSET,
    MAX_STACK,
    STREAM_OF_CHARACTERS,
    ALL_ONE,
    MK_AVERAGE,
]
