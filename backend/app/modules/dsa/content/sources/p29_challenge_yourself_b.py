"""Pattern 29: Challenge Yourself (part 2 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import bisect
import itertools
import random
import re
from collections import Counter, deque
from functools import cache

from app.modules.dsa.content.model import (
    Example,
    ProblemSource,
    design,
    function,
    ints,
    ops,
    pick_n,
    random_tree,
    sample,
    word,
)
from app.modules.dsa.content.sources.p02_fast_and_slow_pointers import CYCLE_NOTE, _cycle_gen, _nodes
from app.modules.dsa.content.sources.p20_tree_dfs_a import _all_nodes, _parents, _random_bst
from app.modules.dsa.judge.codec import ListNode, TreeNode

PATTERN_NUMBER = 29


# ---------------------------------------------------------------- 4Sum


def _four_sum(nums: list[int], target: int) -> list[list[int]]:
    values = sorted(nums)
    n = len(values)
    out = []
    for i in range(n - 3):
        if i and values[i] == values[i - 1]:
            continue
        for j in range(i + 1, n - 2):
            if j > i + 1 and values[j] == values[j - 1]:
                continue
            lo, hi = j + 1, n - 1
            while lo < hi:
                total = values[i] + values[j] + values[lo] + values[hi]
                if total < target:
                    lo += 1
                elif total > target:
                    hi -= 1
                else:
                    out.append([values[i], values[j], values[lo], values[hi]])
                    lo += 1
                    while lo < hi and values[lo] == values[lo - 1]:
                        lo += 1
    return out


def _four_sum_brute(nums: list[int], target: int) -> list[list[int]]:
    if len(nums) > 40:
        return NotImplemented
    return [list(q) for q in sorted({tuple(sorted(c)) for c in itertools.combinations(nums, 4) if sum(c) == target})]


FOUR_SUM = ProblemSource(
    title="4Sum",
    statement="""
Return every distinct quadruplet `[a, b, c, d]` of elements from four different positions of `nums` with `a + b + c + d == target`. Quadruplets
with the same values count once; the quadruplets and the values within each may be in any order.
""",
    constraints="""
- `1 <= nums.length <= 200`
- `-10^9 <= nums[i], target <= 10^9`
""",
    signature=function("fourSum", [("nums", "int[]"), ("target", "int")], "int[][]"),
    reference=_four_sum,
    brute=_four_sum_brute,
    compare="unordered_nested",
    examples=[Example([[1, 0, -1, 0, -2, 2], 0]), Example([[2, 2, 2, 2, 2], 8])],
    edge_cases=[[[1, 2, 3], 6], [[1000000000, 1000000000, 1000000000, 1000000000], -294967296], [[0, 0, 0, 0], 0]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 16, big=200), -(hi := rng.choice([5, 10**9])), hi), rng.randint(-2 * hi, 2 * hi) if hi > 5 else rng.randint(-6, 6)],
    random_count=8,
)


# ---------------------------------------------------------------- Loud and Rich


def _loud_and_rich(richer: list[list[int]], quiet: list[int]) -> list[int]:
    n = len(quiet)
    richer_than: list[list[int]] = [[] for _ in range(n)]
    for a, b in richer:
        richer_than[b].append(a)

    @cache
    def quietest(x: int) -> int:
        best = x
        for y in richer_than[x]:
            candidate = quietest(y)
            if quiet[candidate] < quiet[best]:
                best = candidate
        return best

    return [quietest(x) for x in range(n)]


def _loud_brute(richer: list[list[int]], quiet: list[int]) -> list[int]:
    n = len(quiet)
    out = []
    for x in range(n):
        group, changed = {x}, True
        while changed:  # everyone known to be at least as rich as x
            grown = group | {a for a, b in richer if b in group}
            changed = grown != group
            group = grown
        out.append(min(group, key=lambda p: quiet[p]))
    return out


def _loud_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 10, big=500)
    order = sample(rng, range(n), n)  # hidden wealth order: earlier = richer
    pairs = {tuple(sorted(sample(rng, range(n), 2))) for _ in range(rng.randint(0, 2 * n))} if n >= 2 else set()
    return [[[order[i], order[j]] for i, j in sorted(pairs)], sample(rng, range(n), n)]


LOUD_AND_RICH = ProblemSource(
    title="Loud and Rich",
    statement="""
People are labelled `0` to `n - 1`. `richer[i] = [a, b]` means `a` has strictly more money than `b` (the information is consistent), and
`quiet[x]` is person `x`'s quietness (all distinct). For each person `x`, return the quietest person among everyone known to have at least as
much money as `x` (including `x`), where "known" follows chains of `richer` facts.
""",
    constraints="""
- `1 <= n <= 500`, `0 <= richer.length <= n * (n - 1) / 2`
- `quiet` is a permutation of `0..n-1`; the richer relation is acyclic
""",
    signature=function("loudAndRich", [("richer", "int[][]"), ("quiet", "int[]")], "int[]"),
    reference=_loud_and_rich,
    brute=_loud_brute,
    brute_input_limit=3000,
    examples=[Example([[[1, 0], [2, 1], [3, 1], [3, 7], [4, 3], [5, 3], [6, 3]], [3, 2, 5, 4, 6, 1, 7, 0]]), Example([[], [0]])],
    edge_cases=[[[[0, 1]], [1, 0]], [[[0, 1]], [0, 1]]],
    generator=_loud_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Majority Element


def _majority_element(nums: list[int]) -> int:
    candidate, count = nums[0], 0
    for x in nums:  # Boyer-Moore voting
        if count == 0:
            candidate = x
        count += 1 if x == candidate else -1
    return candidate


def _majority_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 15, big=5 * 10**4)
    major = rng.randint(-(10**9), 10**9)
    count = rng.randint(n // 2 + 1, n)
    nums = [major] * count + ints(rng, n - count, -(10**9), 10**9)
    rng.shuffle(nums)
    return [nums]


MAJORITY_ELEMENT = ProblemSource(
    title="Majority Element",
    statement="""
Return the element that appears more than `n / 2` times in `nums` (it always exists). Aim for linear time and `O(1)` extra space.
""",
    constraints="""
- `1 <= n <= 5 * 10^4`
- `-10^9 <= nums[i] <= 10^9`
""",
    signature=function("majorityElement", [("nums", "int[]")], "int"),
    reference=_majority_element,
    brute=lambda nums: Counter(nums).most_common(1)[0][0],
    examples=[Example([[3, 2, 3]]), Example([[2, 2, 1, 1, 1, 2, 2]])],
    edge_cases=[[[7]], [[1, 1, 2]], [[-5, 3, -5]]],
    generator=_majority_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Permutations II


def _permute_unique(nums: list[int]) -> list[list[int]]:
    counts = Counter(nums)
    out: list[list[int]] = []
    path: list[int] = []

    def build() -> None:
        if len(path) == len(nums):
            out.append(path[:])
            return
        for x in list(counts):
            if counts[x]:
                counts[x] -= 1
                path.append(x)
                build()
                path.pop()
                counts[x] += 1

    build()
    return out


PERMUTATIONS_II = ProblemSource(
    title="Permutations II",
    statement="""
`nums` may contain duplicates. Return all **distinct** permutations of it, in any order.
""",
    constraints="""
- `1 <= nums.length <= 8`
- `-10 <= nums[i] <= 10`
""",
    signature=function("permuteUnique", [("nums", "int[]")], "int[][]"),
    reference=_permute_unique,
    brute=lambda nums: [list(p) for p in set(itertools.permutations(nums))],
    compare="unordered",
    examples=[Example([[1, 1, 2]]), Example([[1, 2, 3]])],
    edge_cases=[[[0]], [[5, 5, 5]], [[-10, 10]]],
    generator=lambda rng: [ints(rng, rng.randint(1, 7), -rng.choice([1, 10]), rng.choice([1, 10]))],
    random_count=8,
)


# ---------------------------------------------------------------- Number of Provinces


def _find_circle_num(isConnected: list[list[int]]) -> int:
    n = len(isConnected)
    seen: set[int] = set()
    provinces = 0
    for city in range(n):
        if city in seen:
            continue
        provinces += 1
        stack = [city]
        seen.add(city)
        while stack:
            c = stack.pop()
            for other in range(n):
                if isConnected[c][other] and other not in seen:
                    seen.add(other)
                    stack.append(other)
    return provinces


def _provinces_brute(isConnected: list[list[int]]) -> int:
    n = len(isConnected)
    reach = [row[:] for row in isConnected]
    for k, i, j in itertools.product(range(n), repeat=3):  # transitive closure
        if reach[i][k] and reach[k][j]:
            reach[i][j] = 1
    return len({tuple(row) for row in reach})


def _provinces_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 10, big=200)
    grid = [[int(i == j) for j in range(n)] for i in range(n)]
    for _ in range(rng.randint(0, n)):
        if n >= 2:
            a, b = sample(rng, range(n), 2)
            grid[a][b] = grid[b][a] = 1
    return [grid]


PROVINCES = ProblemSource(
    title="Number of Provinces",
    statement="""
`isConnected` is an `n x n` matrix where `isConnected[i][j] == 1` means cities `i` and `j` are directly connected. A *province* is a group of
cities connected directly or indirectly, with no other city outside the group connected to it. Return the number of provinces.
""",
    constraints="""
- `1 <= n <= 200`
- the matrix is symmetric with `isConnected[i][i] == 1`
""",
    signature=function("findCircleNum", [("isConnected", "int[][]")], "int"),
    reference=_find_circle_num,
    brute=_provinces_brute,
    brute_input_limit=1000,
    examples=[Example([[[1, 1, 0], [1, 1, 0], [0, 0, 1]]]), Example([[[1, 0, 0], [0, 1, 0], [0, 0, 1]]])],
    edge_cases=[[[[1]]], [[[1, 1], [1, 1]]]],
    generator=_provinces_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Linked List Cycle II


def _detect_cycle(head: ListNode | None) -> int:
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:  # Floyd: a pointer from head and one from the meeting point meet at the entry
            entry, index = head, 0
            while entry is not slow:
                entry, slow, index = entry.next, slow.next, index + 1
            return index
    return -1


def _detect_cycle_brute(head: ListNode | None) -> int:
    seen: dict[int, int] = {}
    index = 0
    while head:
        if id(head) in seen:
            return seen[id(head)]
        seen[id(head)] = index
        head, index = head.next, index + 1
    return -1


LINKED_LIST_CYCLE_II = ProblemSource(
    title="Linked List Cycle II",
    statement="""
Given the head of a singly linked list, find the node where its cycle begins (the first node reached twice when following `next`).

*Adapted I/O:* return that node's 0-based **index** in the list, or `-1` if there is no cycle. Don't modify the list, and try to use `O(1)` extra
memory.
"""
    + CYCLE_NOTE,
    constraints="""
- the list has between `0` and `10^4` nodes
- `-10^5 <= Node.val <= 10^5`
- `pos` is `-1` or a valid index in the list
""",
    signature=function("detectCycle", [("head", "ListNode"), ("pos", "int")], "int", links=[{"kind": "cycle", "list": "head", "pos": "pos"}]),
    reference=_detect_cycle,
    brute=_detect_cycle_brute,
    examples=[Example([[3, 2, 0, -4], 1], "The tail links back to index 1."), Example([[1, 2], 0]), Example([[1], -1], "No cycle.")],
    edge_cases=[[[], -1], [[1], 0], [[5, 5, 5], 2]],
    generator=_cycle_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Number of Flips to Make the Binary String Alternating


def _min_flips(s: str) -> int:
    n = len(s)
    doubled = s + s  # every rotation is a window of length n
    mismatch_a = mismatch_b = 0  # against "0101..." and "1010..."
    best = n
    for i, ch in enumerate(doubled):
        mismatch_a += ch != "01"[i % 2]
        mismatch_b += ch != "10"[i % 2]
        if i >= n:
            gone = doubled[i - n]
            mismatch_a -= gone != "01"[(i - n) % 2]
            mismatch_b -= gone != "10"[(i - n) % 2]
        if i >= n - 1:
            best = min(best, mismatch_a, mismatch_b)
    return best


def _flips_brute(s: str) -> int:
    n = len(s)
    best = n
    for k in range(n):
        t = s[k:] + s[:k]
        for pattern in ("01", "10"):
            best = min(best, sum(t[i] != pattern[i % 2] for i in range(n)))
    return best


MIN_FLIPS_ALTERNATING = ProblemSource(
    title="Minimum Flips to Make the Binary String Alternate",
    statement="""
You may repeatedly (1) move the first character of the binary string `s` to its end, at no cost, and (2) flip any single character, at a cost of
one. Return the minimum number of flips needed to make `s` *alternating* (no two adjacent characters equal).
""",
    constraints="""
- `1 <= s.length <= 10^5`
- `s[i]` is `0` or `1`
""",
    signature=function("minFlips", [("s", "string")], "int"),
    reference=_min_flips,
    brute=lambda s: _flips_brute(s) if len(s) <= 200 else NotImplemented,
    examples=[Example(["111000"], "Rotate twice to \"100011\", then flip two characters."), Example(["010"]), Example(["1110"])],
    edge_cases=[["0"], ["00"], ["01"], ["0110"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 25, big=10**4), "01")],
    random_count=8,
)


# ---------------------------------------------------------------- Lemonade Change


def _lemonade_change(bills: list[int]) -> bool:
    fives = tens = 0
    for bill in bills:
        if bill == 5:
            fives += 1
        elif bill == 10:
            fives, tens = fives - 1, tens + 1
        elif tens:
            fives, tens = fives - 1, tens - 1
        else:
            fives -= 3
        if fives < 0:
            return False
    return True


def _lemonade_brute(bills: list[int]) -> bool:
    """Try every way of making change (not just the greedy one); succeed if any works."""
    if len(bills) > 20:
        return NotImplemented

    @cache
    def go(i: int, fives: int, tens: int) -> bool:
        if i == len(bills):
            return True
        bill = bills[i]
        if bill == 5:
            return go(i + 1, fives + 1, tens)
        if bill == 10:
            return fives >= 1 and go(i + 1, fives - 1, tens + 1)
        return (tens >= 1 and fives >= 1 and go(i + 1, fives - 1, tens - 1)) or (fives >= 3 and go(i + 1, fives - 3, tens))

    return go(0, 0, 0)


LEMONADE_CHANGE = ProblemSource(
    title="Lemonade Change",
    statement="""
Lemonade costs `$5`. Customers queue up and each pays with one `$5`, `$10` or `$20` bill (`bills[i]`). You start with no change and must give each
customer correct change. Return `true` if you can serve everyone.
""",
    constraints="""
- `1 <= bills.length <= 10^5`
- `bills[i]` is `5`, `10` or `20`
""",
    signature=function("lemonadeChange", [("bills", "int[]")], "bool"),
    reference=_lemonade_change,
    brute=_lemonade_brute,
    examples=[Example([[5, 5, 5, 10, 20]]), Example([[5, 5, 10, 10, 20]], "The last customer needs $15 but you hold two $10 bills.")],
    edge_cases=[[[5]], [[10]], [[5, 5, 5, 5, 20, 20]]],
    generator=lambda rng: [[5] + [rng.choice([5, 5, 5, 10, 10, 20]) for _ in range(rng.randint(0, rng.choice([8, 19, 1000])))]],
    random_count=10,
)


# ---------------------------------------------------------------- Find All Numbers Disappeared in an Array


def _find_disappeared_numbers(nums: list[int]) -> list[int]:
    marks = nums[:]
    for x in marks:  # mark index |x| - 1 as seen by making it negative
        marks[abs(x) - 1] = -abs(marks[abs(x) - 1])
    return [i + 1 for i, v in enumerate(marks) if v > 0]


DISAPPEARED_NUMBERS = ProblemSource(
    title="Find All Numbers Disappeared in an Array",
    statement="""
`nums` has `n` elements, each between `1` and `n`. Return every number in `[1, n]` that does not appear in `nums`, in any order. Try `O(n)` time
without extra space (the output doesn't count).
""",
    constraints="""
- `1 <= n <= 10^5`
- `1 <= nums[i] <= n`
""",
    signature=function("findDisappearedNumbers", [("nums", "int[]")], "int[]"),
    reference=_find_disappeared_numbers,
    brute=lambda nums: sorted(set(range(1, len(nums) + 1)) - set(nums)),
    compare="unordered",
    examples=[Example([[4, 3, 2, 7, 8, 2, 3, 1]]), Example([[1, 1]])],
    edge_cases=[[[1]], [[2, 2]], [[3, 1, 2]]],
    generator=lambda rng: [ints(rng, (n := pick_n(rng, 1, 20, big=10**4)), 1, n)],
    random_count=8,
)


# ---------------------------------------------------------------- Find All Duplicates in an Array


def _find_duplicates(nums: list[int]) -> list[int]:
    marks, out = nums[:], []
    for x in marks:
        i = abs(x) - 1
        if marks[i] < 0:
            out.append(abs(x))
        else:
            marks[i] = -marks[i]
    return out


def _duplicates_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 20, big=10**4)
    doubled = rng.randint(0, n // 2)
    values = sample(rng, range(1, n + 1), n - doubled)  # n - doubled distinct values in 1..n ...
    nums = values + sample(rng, values, doubled)  # ... plus `doubled` of them repeated: length n
    rng.shuffle(nums)
    return [nums]


ALL_DUPLICATES = ProblemSource(
    title="Find All Duplicates in an Array",
    statement="""
`nums` has `n` elements, each between `1` and `n`, and every value appears once or twice. Return every value that appears twice, in any order,
in `O(n)` time using only constant extra space.
""",
    constraints="""
- `1 <= n <= 10^5`
- `1 <= nums[i] <= n`; each value appears at most twice
""",
    signature=function("findDuplicates", [("nums", "int[]")], "int[]"),
    reference=_find_duplicates,
    brute=lambda nums: [x for x, c in Counter(nums).items() if c == 2],
    compare="unordered",
    examples=[Example([[4, 3, 2, 7, 8, 2, 3, 1]]), Example([[1, 1, 2]]), Example([[1]])],
    edge_cases=[[[2, 2]], [[1, 2]]],
    generator=_duplicates_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Design In-Memory File System


class _FileSystem:
    def __init__(self) -> None:
        self.root: dict = {"dirs": {}, "content": None}

    def _walk(self, path: str, create: bool = False) -> dict:
        node = self.root
        for part in filter(None, path.split("/")):
            if part not in node["dirs"]:
                if not create:
                    raise KeyError(path)
                node["dirs"][part] = {"dirs": {}, "content": None}
            node = node["dirs"][part]
        return node

    def ls(self, path: str) -> list[str]:
        node = self._walk(path)
        if node["content"] is not None:
            return [path.rsplit("/", 1)[-1]]
        return sorted(node["dirs"])

    def mkdir(self, path: str) -> None:
        self._walk(path, create=True)

    def addContentToFile(self, filePath: str, content: str) -> None:  # noqa: N802
        node = self._walk(filePath, create=True)
        node["content"] = (node["content"] or "") + content

    def readContentFromFile(self, filePath: str) -> str:  # noqa: N802
        return self._walk(filePath)["content"]


class _FileSystemBrute:
    def __init__(self) -> None:
        self.dirs: set[str] = {""}
        self.files: dict[str, str] = {}

    def _add_dirs(self, path: str) -> None:
        parts = path.strip("/").split("/")
        for k in range(1, len(parts) + 1):
            self.dirs.add("/".join(parts[:k]))

    def ls(self, path: str) -> list[str]:
        key = path.strip("/")
        if key in self.files:
            return [key.rsplit("/", 1)[-1]]
        prefix = key + "/" if key else ""
        names = {p[len(prefix) :].split("/")[0] for p in list(self.dirs) + list(self.files) if p.startswith(prefix) and p != key and p}
        return sorted(names)

    def mkdir(self, path: str) -> None:
        self._add_dirs(path)

    def addContentToFile(self, filePath: str, content: str) -> None:  # noqa: N802
        key = filePath.strip("/")
        if "/" in key:
            self._add_dirs(key.rsplit("/", 1)[0])
        self.files[key] = self.files.get(key, "") + content

    def readContentFromFile(self, filePath: str) -> str:  # noqa: N802
        return self.files[filePath.strip("/")]


def _fs_gen(rng: random.Random) -> dict:
    names = ["a", "b", "c", "dd"]
    dirs: set[str] = {"/"}
    files: set[str] = set()
    calls: list[tuple[str, list]] = [("FileSystem", [])]
    for _ in range(pick_n(rng, 1, 20, big=200)):
        roll = rng.random()
        parent = rng.choice(sorted(dirs))
        child = (parent.rstrip("/") + "/" + rng.choice(names)) if parent != "/" else "/" + rng.choice(names)
        if roll < 0.3 and child not in files:
            calls.append(("mkdir", [child]))
            dirs.add(child)
        elif roll < 0.55 and child not in dirs:
            calls.append(("addContentToFile", [child, word(rng, rng.randint(1, 4), "xyz")]))
            files.add(child)
        elif roll < 0.8:
            calls.append(("ls", [rng.choice(sorted(dirs | files))]))
        elif files:
            calls.append(("readContentFromFile", [rng.choice(sorted(files))]))
    return ops(*calls)


IN_MEMORY_FS = ProblemSource(
    title="Design In-Memory File System",
    statement="""
Design an in-memory file system. Paths are absolute, like `"/a/b/c"`; the root is `"/"`.
- `ls(path)`: if `path` is a file, return a list with just its name; if it is a directory, return the names of its files and subdirectories in
  lexicographic order.
- `mkdir(path)`: create the directory `path`, including any missing parent directories.
- `addContentToFile(filePath, content)`: create the file if needed (with missing parent directories) and append `content` to it.
- `readContentFromFile(filePath)`: return the file's content.

Operations only refer to existing paths when they require one, and a name is never used for both a file and a directory.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor,
`mkdir` and `addContentToFile`).
""",
    constraints="""
- `1 <= path.length <= 100`, names are lowercase letters
- at most `300` calls
""",
    signature=design("FileSystem", [], [("ls", [("path", "string")], "string[]"), ("mkdir", [("path", "string")], "void"), ("addContentToFile", [("filePath", "string"), ("content", "string")], "void"), ("readContentFromFile", [("filePath", "string")], "string")]),
    reference=_FileSystem,
    brute=_FileSystemBrute,
    examples=[
        Example(ops(("FileSystem", []), ("ls", ["/"]), ("mkdir", ["/a/b/c"]), ("addContentToFile", ["/a/b/c/d", "hello"]), ("ls", ["/"]), ("readContentFromFile", ["/a/b/c/d"]))),
        Example(ops(("FileSystem", []), ("addContentToFile", ["/f", "ab"]), ("addContentToFile", ["/f", "cd"]), ("readContentFromFile", ["/f"]), ("ls", ["/f"])), "Content is appended; ls on a file lists just that file."),
    ],
    generator=_fs_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Design File System


class _SimpleFileSystem:
    def __init__(self) -> None:
        self.values: dict[str, int] = {"": -1}

    def createPath(self, path: str, value: int) -> bool:  # noqa: N802
        parent = path.rsplit("/", 1)[0]
        if path in self.values or parent not in self.values:
            return False
        self.values[path] = value
        return True

    def get(self, path: str) -> int:
        return self.values.get(path, -1) if path else -1


class _SimpleFileSystemBrute:
    def __init__(self) -> None:
        self.paths: list[tuple[str, int]] = []

    def createPath(self, path: str, value: int) -> bool:  # noqa: N802
        parts = path.split("/")[1:]
        if any(p == path for p, _ in self.paths):
            return False
        if len(parts) > 1 and not any(p == "/" + "/".join(parts[:-1]) for p, _ in self.paths):
            return False
        self.paths.append((path, value))
        return True

    def get(self, path: str) -> int:
        return next((v for p, v in self.paths if p == path), -1)


def _simple_fs_gen(rng: random.Random) -> dict:
    def path() -> str:
        return "".join("/" + rng.choice(["a", "b", "leet", "code"]) for _ in range(rng.randint(1, 3)))

    calls: list[tuple[str, list]] = [("FileSystem", [])]
    for _ in range(pick_n(rng, 1, 20, big=200)):
        calls.append(("createPath", [path(), rng.randint(1, 10**9)]) if rng.random() < 0.6 else ("get", [path()]))
    return ops(*calls)


DESIGN_FILE_SYSTEM = ProblemSource(
    title="Design File System",
    statement="""
Design a file system that maps paths (like `"/leet/code"`) to integer values:
- `createPath(path, value)` creates `path` with `value` and returns `true`. It returns `false` (and changes nothing) if `path` already exists or
  its parent path doesn't exist. The parent of a top-level path like `"/leet"` is the root, which always exists.
- `get(path)` returns the value of `path`, or `-1` if it doesn't exist.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor).
""",
    constraints="""
- paths are `/`-separated lowercase names; `1 <= value <= 10^9`
- at most `10^4` calls
""",
    signature=design("FileSystem", [], [("createPath", [("path", "string"), ("value", "int")], "bool"), ("get", [("path", "string")], "int")]),
    reference=_SimpleFileSystem,
    brute=_SimpleFileSystemBrute,
    examples=[
        Example(ops(("FileSystem", []), ("createPath", ["/a", 1]), ("get", ["/a"]))),
        Example(ops(("FileSystem", []), ("createPath", ["/leet", 1]), ("createPath", ["/leet/code", 2]), ("get", ["/leet/code"]), ("createPath", ["/c/d", 1]), ("get", ["/c"])), "\"/c\" doesn't exist, so \"/c/d\" can't be created."),
    ],
    generator=_simple_fs_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Asteroid Collision


def _asteroid_collision(asteroids: list[int]) -> list[int]:
    stack: list[int] = []
    for a in asteroids:
        while a < 0 and stack and stack[-1] > 0:
            if stack[-1] < -a:
                stack.pop()  # the right-mover explodes; keep checking
                continue
            if stack[-1] == -a:
                stack.pop()
            a = 0  # the left-mover explodes
        if a:
            stack.append(a)
    return stack


def _asteroid_brute(asteroids: list[int]) -> list[int]:
    row = list(asteroids)
    changed = True
    while changed:  # resolve one adjacent collision at a time until none remain
        changed = False
        for i in range(len(row) - 1):
            if row[i] > 0 > row[i + 1]:
                a, b = row[i], -row[i + 1]
                row[i : i + 2] = [row[i]] if a > b else [] if a == b else [row[i + 1]]
                changed = True
                break
    return row


ASTEROID_COLLISION = ProblemSource(
    title="Asteroid Collision",
    statement="""
Asteroids move along a line at the same speed: the sign of `asteroids[i]` is its direction (positive = right, negative = left) and its absolute
value is its size. When two meet, the smaller explodes; if they are equal, both explode. Asteroids moving in the same direction never meet.
Return the asteroids left after all collisions, in order.
""",
    constraints="""
- `2 <= asteroids.length <= 10^4`
- `-1000 <= asteroids[i] <= 1000`, `asteroids[i] != 0`
""",
    signature=function("asteroidCollision", [("asteroids", "int[]")], "int[]"),
    reference=_asteroid_collision,
    brute=_asteroid_brute,
    brute_input_limit=1500,
    examples=[Example([[5, 10, -5]], "10 destroys -5."), Example([[8, -8]], "Equal sizes: both explode."), Example([[10, 2, -5]])],
    edge_cases=[[[-2, -1, 1, 2]], [[1, -1, -2]], [[-5, 5]]],
    generator=lambda rng: [[rng.choice([-1, 1]) * rng.randint(1, rng.choice([5, 1000])) for _ in range(pick_n(rng, 2, 20, big=10**4))]],
    random_count=8,
)


# ---------------------------------------------------------------- Rotting Oranges


def _oranges_rotting(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    queue = deque((i, j, 0) for i in range(m) for j in range(n) if grid[i][j] == 2)
    fresh = sum(row.count(1) for row in grid)
    grid = [row[:] for row in grid]
    minutes = 0
    while queue:
        i, j, t = queue.popleft()
        minutes = max(minutes, t)
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= a < m and 0 <= b < n and grid[a][b] == 1:
                grid[a][b] = 2
                fresh -= 1
                queue.append((a, b, t + 1))
    return -1 if fresh else minutes


def _rotting_brute(grid: list[list[int]]) -> int:
    state = [row[:] for row in grid]
    m, n = len(state), len(state[0])
    minutes = 0
    while True:  # simulate minute by minute
        to_rot = {(a, b) for i in range(m) for j in range(n) if state[i][j] == 2 for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)) if 0 <= a < m and 0 <= b < n and state[a][b] == 1}
        if not to_rot:
            return -1 if any(1 in row for row in state) else minutes
        for a, b in to_rot:
            state[a][b] = 2
        minutes += 1


ROTTING_ORANGES = ProblemSource(
    title="Rotting Oranges",
    statement="""
In the grid, `0` is empty, `1` a fresh orange and `2` a rotten one. Every minute, each fresh orange next to (up, down, left or right) a rotten one
becomes rotten. Return the number of minutes until no fresh orange remains, or `-1` if some can never rot.
""",
    constraints="""
- `1 <= m, n <= 10`
- `grid[i][j]` is `0`, `1` or `2`
""",
    signature=function("orangesRotting", [("grid", "int[][]")], "int"),
    reference=_oranges_rotting,
    brute=_rotting_brute,
    examples=[Example([[[2, 1, 1], [1, 1, 0], [0, 1, 1]]]), Example([[[2, 1, 1], [0, 1, 1], [1, 0, 1]]], "The bottom-left orange is cut off."), Example([[[0, 2]]], "No fresh oranges at all.")],
    edge_cases=[[[[0]]], [[[1]]], [[[2]]]],
    generator=lambda rng: [[[rng.choice([0, 1, 1, 1, 2]) for _ in range(n)] for _ in range(m)] for m, n in [(rng.randint(1, 10), rng.randint(1, 10))]],
    random_count=10,
)


# ---------------------------------------------------------------- Add Binary


def _add_binary(a: str, b: str) -> str:
    i, j, carry, out = len(a) - 1, len(b) - 1, 0, []
    while i >= 0 or j >= 0 or carry:
        total = carry + (int(a[i]) if i >= 0 else 0) + (int(b[j]) if j >= 0 else 0)
        out.append(str(total % 2))
        carry = total // 2
        i, j = i - 1, j - 1
    return "".join(reversed(out))


def _binary_string(rng: random.Random) -> str:
    n = rng.randint(1, rng.choice([8, 3000]))
    return "1" + word(rng, n - 1, "01") if n > 1 else rng.choice("01")


ADD_BINARY = ProblemSource(
    title="Add Binary",
    statement="""
`a` and `b` are binary strings without leading zeros (except `"0"` itself). Return their sum as a binary string.
""",
    constraints="""
- `1 <= a.length, b.length <= 10^4`
""",
    signature=function("addBinary", [("a", "string"), ("b", "string")], "string"),
    reference=_add_binary,
    brute=lambda a, b: bin(int(a, 2) + int(b, 2))[2:],
    examples=[Example(["11", "1"]), Example(["1010", "1011"])],
    edge_cases=[["0", "0"], ["1", "1"], ["1111", "1"]],
    generator=lambda rng: [_binary_string(rng), _binary_string(rng)],
    random_count=8,
)


# ---------------------------------------------------------------- Multiply Strings


def _multiply(num1: str, num2: str) -> str:
    result = [0] * (len(num1) + len(num2))
    for i in range(len(num1) - 1, -1, -1):
        for j in range(len(num2) - 1, -1, -1):
            total = result[i + j + 1] + int(num1[i]) * int(num2[j])
            result[i + j + 1] = total % 10
            result[i + j] += total // 10
    text = "".join(map(str, result)).lstrip("0")
    return text or "0"


def _number_string(rng: random.Random) -> str:
    n = rng.randint(1, rng.choice([5, 200]))
    return str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(n - 1)) if n > 1 else str(rng.randint(0, 9))


MULTIPLY_STRINGS = ProblemSource(
    title="Multiply Strings",
    statement="""
`num1` and `num2` are non-negative integers written as decimal strings without leading zeros (except `"0"`). Return their product as a string,
without converting the inputs to integers or using big-integer libraries.
""",
    constraints="""
- `1 <= num1.length, num2.length <= 200`
""",
    signature=function("multiply", [("num1", "string"), ("num2", "string")], "string"),
    reference=_multiply,
    brute=lambda num1, num2: str(int(num1) * int(num2)),
    examples=[Example(["2", "3"]), Example(["123", "456"])],
    edge_cases=[["0", "12345"], ["9", "9"], ["999", "999"]],
    generator=lambda rng: [_number_string(rng), _number_string(rng)],
    random_count=8,
)


# ---------------------------------------------------------------- Lowest Common Ancestor of a Binary Search Tree


def _lca_bst(root: TreeNode, p: int, q: int) -> int:
    node = root
    while True:
        if p < node.val and q < node.val:
            node = node.left
        elif p > node.val and q > node.val:
            node = node.right
        else:
            return node.val


def _lca_bst_brute(root: TreeNode, p: int, q: int) -> int:
    parent = _parents(root)
    by_value = {n.val: n for n in _all_nodes(root)}
    ancestors = set()
    node = by_value[p]
    while node is not None:
        ancestors.add(node)
        node = parent[node]
    node = by_value[q]
    while node not in ancestors:
        node = parent[node]
    return node.val


def _lca_bst_gen(rng: random.Random) -> list:
    tree = _random_bst(rng, pick_n(rng, 2, 15, big=3000), -(10**9), 10**9)
    p, q = sample(rng, [v for v in tree if v is not None], 2)
    return [tree, p, q]


LCA_BST = ProblemSource(
    title="Lowest Common Ancestor of a Binary Search Tree",
    statement="""
*Adapted I/O:* given a binary search tree with distinct values and the values `p` and `q` of two of its nodes, return the value of their lowest
common ancestor — the deepest node that has both as descendants (a node counts as its own descendant). Use the BST ordering.
""",
    constraints="""
- `2 <= number of nodes <= 10^5`
- `-10^9 <= Node.val <= 10^9`, distinct; `p != q`, both in the tree
""",
    signature=function("lowestCommonAncestor", [("root", "TreeNode"), ("p", "int"), ("q", "int")], "int"),
    reference=_lca_bst,
    brute=_lca_bst_brute,
    examples=[Example([[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8]), Example([[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4], "2 is an ancestor of 4."), Example([[2, 1], 2, 1])],
    edge_cases=[[[1, None, 2], 1, 2], [[3, 1, 5], 1, 5]],
    generator=_lca_bst_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Merge Two Sorted Lists


def _merge_two_lists(list1: ListNode | None, list2: ListNode | None) -> ListNode | None:
    dummy = tail = ListNode()
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next, list1 = list1, list1.next
        else:
            tail.next, list2 = list2, list2.next
        tail = tail.next
    tail.next = list1 or list2
    return dummy.next


def _merge_brute(list1: ListNode | None, list2: ListNode | None) -> ListNode | None:
    values = [n.val for n in _nodes(list1)] + [n.val for n in _nodes(list2)]
    head = None
    for v in sorted(values, reverse=True):
        head = ListNode(v, head)
    return head


MERGE_TWO_LISTS = ProblemSource(
    title="Merge Two Sorted Lists",
    statement="""
Merge the two sorted linked lists into one sorted list by splicing their nodes together, and return its head.
""",
    constraints="""
- `0 <= nodes in each list <= 50`
- `-100 <= Node.val <= 100`; both lists are sorted in non-decreasing order
""",
    signature=function("mergeTwoLists", [("list1", "ListNode"), ("list2", "ListNode")], "ListNode"),
    reference=_merge_two_lists,
    brute=_merge_brute,
    examples=[Example([[1, 2, 4], [1, 3, 4]]), Example([[], []]), Example([[], [0]])],
    edge_cases=[[[5], [1, 2, 3]], [[-100, 100], [0]]],
    generator=lambda rng: [sorted(ints(rng, rng.randint(0, 50), -100, 100)), sorted(ints(rng, rng.randint(0, 50), -100, 100))],
    random_count=8,
)


# ---------------------------------------------------------------- Balanced Binary Tree


def _is_balanced(root: TreeNode | None) -> bool:
    def height(node: TreeNode | None) -> int:
        """Height, or -1 as soon as some subtree is unbalanced."""
        if node is None:
            return 0
        left, right = height(node.left), height(node.right)
        if left < 0 or right < 0 or abs(left - right) > 1:
            return -1
        return 1 + max(left, right)

    return height(root) >= 0


def _balanced_brute(root: TreeNode | None) -> bool:
    def depth(node: TreeNode | None) -> int:
        return 0 if node is None else 1 + max(depth(node.left), depth(node.right))

    return all(abs(depth(n.left) - depth(n.right)) <= 1 for n in _all_nodes(root))


def _balanced_gen(rng: random.Random) -> list:
    if rng.random() < 0.5:  # complete trees are balanced; random shapes usually aren't
        return [ints(rng, pick_n(rng, 0, 15, big=3000), -(10**4), 10**4)]
    return [random_tree(rng, pick_n(rng, 0, 10, big=500), -(10**4), 10**4)]


BALANCED_TREE = ProblemSource(
    title="Balanced Binary Tree",
    statement="""
Return `true` if the binary tree is height-balanced: at every node, the heights of the left and right subtrees differ by at most one.
""",
    constraints="""
- `0 <= number of nodes <= 5000`
- `-10^4 <= Node.val <= 10^4`
""",
    signature=function("isBalanced", [("root", "TreeNode")], "bool"),
    reference=_is_balanced,
    brute=_balanced_brute,
    brute_input_limit=6000,
    examples=[Example([[3, 9, 20, None, None, 15, 7]]), Example([[1, 2, 2, 3, 3, None, None, 4, 4]]), Example([[]])],
    edge_cases=[[[1]], [[1, 2]], [[1, 2, None, 3]]],
    generator=_balanced_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Profit in Job Scheduling


def _job_scheduling(startTime: list[int], endTime: list[int], profit: list[int]) -> int:
    jobs = sorted(zip(endTime, startTime, profit, strict=True))
    ends = [0]
    best = [0]  # best[k]: max profit using jobs ending by ends[k]
    for end, start, gain in jobs:
        k = bisect.bisect_right(ends, start) - 1
        candidate = best[k] + gain
        if candidate > best[-1]:
            ends.append(end)
            best.append(candidate)
    return best[-1]


def _jobs_brute(startTime: list[int], endTime: list[int], profit: list[int]) -> int:
    n = len(profit)
    if n > 14:
        return NotImplemented
    best = 0
    for mask in range(1 << n):
        chosen = sorted((startTime[i], endTime[i]) for i in range(n) if mask >> i & 1)
        if all(a[1] <= b[0] for a, b in itertools.pairwise(chosen)):
            best = max(best, sum(profit[i] for i in range(n) if mask >> i & 1))
    return best


def _jobs_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 12, big=5000)
    starts = [rng.randint(1, rng.choice([20, 10**9 - 100])) for _ in range(n)]
    ends = [s + rng.randint(1, rng.choice([5, 50])) for s in starts]
    return [starts, ends, ints(rng, n, 1, 10**4)]


JOB_SCHEDULING = ProblemSource(
    title="Maximum Profit in Job Scheduling",
    statement="""
Job `i` runs from `startTime[i]` to `endTime[i]` and earns `profit[i]`. Choose jobs with no overlapping time ranges (a job may start exactly when
another ends) to maximise total profit, and return that maximum.
""",
    constraints="""
- `1 <= n <= 5 * 10^4`
- `1 <= startTime[i] < endTime[i] <= 10^9`, `1 <= profit[i] <= 10^4`
""",
    signature=function("jobScheduling", [("startTime", "int[]"), ("endTime", "int[]"), ("profit", "int[]")], "int"),
    reference=_job_scheduling,
    brute=_jobs_brute,
    examples=[Example([[1, 2, 3, 3], [3, 4, 5, 6], [50, 10, 40, 70]], "Jobs 1 and 4: 120."), Example([[1, 2, 3, 4, 6], [3, 5, 10, 6, 9], [20, 20, 100, 70, 60]]), Example([[1, 1, 1], [2, 3, 4], [5, 6, 4]])],
    edge_cases=[[[1], [2], [5]], [[1, 2], [2, 3], [1, 1]]],
    generator=_jobs_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Height Trees


def _find_min_height_trees(n: int, edges: list[list[int]]) -> list[int]:
    if n <= 2:
        return list(range(n))
    adjacent: list[set[int]] = [set() for _ in range(n)]
    for a, b in edges:
        adjacent[a].add(b)
        adjacent[b].add(a)
    leaves = [v for v in range(n) if len(adjacent[v]) == 1]
    remaining = n
    while remaining > 2:  # peel leaves layer by layer; the last one or two nodes are the centres
        remaining -= len(leaves)
        nxt = []
        for leaf in leaves:
            (other,) = adjacent[leaf]
            adjacent[other].discard(leaf)
            if len(adjacent[other]) == 1:
                nxt.append(other)
        leaves = nxt
    return sorted(leaves)


def _mht_brute(n: int, edges: list[list[int]]) -> list[int]:
    adjacent: list[list[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)

    def height(root: int) -> int:
        dist = {root: 0}
        queue = deque([root])
        while queue:
            v = queue.popleft()
            for w in adjacent[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
        return max(dist.values())

    heights = [height(r) for r in range(n)]
    return [r for r in range(n) if heights[r] == min(heights)]


def _mht_gen(rng: random.Random) -> list:
    n = pick_n(rng, 1, 15, big=3000)
    labels = sample(rng, range(n), n)
    return [n, [[labels[rng.randint(max(0, i - rng.choice([1, 2, i])), i - 1)], labels[i]] for i in range(1, n)]]


MIN_HEIGHT_TREES = ProblemSource(
    title="Minimum Height Trees",
    statement="""
An undirected tree has `n` nodes labelled `0` to `n - 1` and the given `edges`. Rooting it at a node gives a tree whose height is the number of
edges on the longest root-to-leaf path. Return every node whose rooted tree has the minimum possible height, in any order.
""",
    constraints="""
- `1 <= n <= 2 * 10^4`, `edges.length == n - 1`
- `edges` forms a tree
""",
    signature=function("findMinHeightTrees", [("n", "int"), ("edges", "int[][]")], "int[]"),
    reference=_find_min_height_trees,
    brute=lambda n, edges: _mht_brute(n, edges) if n <= 300 else NotImplemented,
    compare="unordered",
    examples=[Example([4, [[1, 0], [1, 2], [1, 3]]]), Example([6, [[3, 0], [3, 1], [3, 2], [3, 4], [5, 4]]], "Rooting at 3 or 4 gives height 2.")],
    edge_cases=[[1, []], [2, [[0, 1]]], [3, [[0, 1], [1, 2]]]],
    generator=_mht_gen,
    random_count=8,
)


# ---------------------------------------------------------------- String to Integer (atoi)


def _my_atoi(s: str) -> int:
    i, n = 0, len(s)
    while i < n and s[i] == " ":
        i += 1
    sign = 1
    if i < n and s[i] in "+-":
        sign = -1 if s[i] == "-" else 1
        i += 1
    value = 0
    while i < n and s[i].isdigit():
        value = value * 10 + int(s[i])
        i += 1
    return max(-(2**31), min(2**31 - 1, sign * value))


def _atoi_brute(s: str) -> int:
    match = re.match(r" *([+-]?\d+)", s)
    if not match:
        return 0
    return max(-(2**31), min(2**31 - 1, int(match.group(1))))


def _atoi_gen(rng: random.Random) -> list:
    parts = [" " * rng.randint(0, 3), rng.choice(["", "", "-", "+", "+-"]), "0" * rng.randint(0, 3)]
    parts.append(str(rng.randint(0, rng.choice([999, 2**31 + 5, 10**12]))) if rng.random() < 0.85 else "")
    parts.append(rng.choice(["", "abc", " 42", ".5", "-"]))
    if rng.random() < 0.15:
        parts.insert(0, rng.choice(["x", "."]))
    return ["".join(parts)]


ATOI = ProblemSource(
    title="String to Integer (atoi)",
    statement="""
Convert `s` to a 32-bit signed integer the way C's `atoi` does:

1. skip leading spaces (`' '` only);
2. read an optional `'+'` or `'-'` sign;
3. read as many consecutive digits as possible (leading zeros are fine); stop at the first non-digit;
4. if no digits were read, the result is `0`; otherwise clamp the value to `[-2^31, 2^31 - 1]`.

Return the result.
""",
    constraints="""
- `0 <= s.length <= 200`
- English letters, digits, `' '`, `'+'`, `'-'` and `'.'`
""",
    signature=function("myAtoi", [("s", "string")], "int"),
    reference=_my_atoi,
    brute=_atoi_brute,
    examples=[Example(["42"]), Example(["   -042"]), Example(["1337c0d3"]), ],
    edge_cases=[[""], ["words and 987"], ["-91283472332"], ["+-12"], ["   +0 123"], ["2147483648"]],
    generator=_atoi_gen,
    random_count=10,
)


# ---------------------------------------------------------------- Trapping Rain Water


def _trap(height: list[int]) -> int:
    left, right = 0, len(height) - 1
    left_max = right_max = water = 0
    while left < right:  # the lower side's running max bounds its water level
        if height[left] < height[right]:
            left_max = max(left_max, height[left])
            water += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            water += right_max - height[right]
            right -= 1
    return water


def _trap_brute(height: list[int]) -> int:
    return sum(max(0, min(max(height[: i + 1]), max(height[i:])) - h) for i, h in enumerate(height)) if len(height) <= 500 else NotImplemented


TRAPPING_RAIN_WATER = ProblemSource(
    title="Trapping Rain Water",
    statement="""
`height[i]` is the height of a bar of width 1 in an elevation map. Return how much rain water is trapped between the bars after it rains.
""",
    constraints="""
- `1 <= height.length <= 2 * 10^4`
- `0 <= height[i] <= 10^5`
""",
    signature=function("trap", [("height", "int[]")], "int"),
    reference=_trap,
    brute=_trap_brute,
    examples=[Example([[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]]), Example([[4, 2, 0, 3, 2, 5]])],
    edge_cases=[[[1]], [[3, 0, 3]], [[5, 4, 3, 2, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=2 * 10**4), 0, rng.choice([5, 10**5]))],
    random_count=8,
)


PROBLEMS = [
    FOUR_SUM,
    LOUD_AND_RICH,
    MAJORITY_ELEMENT,
    PERMUTATIONS_II,
    PROVINCES,
    LINKED_LIST_CYCLE_II,
    MIN_FLIPS_ALTERNATING,
    LEMONADE_CHANGE,
    DISAPPEARED_NUMBERS,
    ALL_DUPLICATES,
    IN_MEMORY_FS,
    DESIGN_FILE_SYSTEM,
    ASTEROID_COLLISION,
    ROTTING_ORANGES,
    ADD_BINARY,
    MULTIPLY_STRINGS,
    LCA_BST,
    MERGE_TWO_LISTS,
    BALANCED_TREE,
    JOB_SCHEDULING,
    MIN_HEIGHT_TREES,
    ATOI,
    TRAPPING_RAIN_WATER,
]
