"""Pattern 1: Two Pointers (part 2 of 2). Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import itertools
import math
import string

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, word
from app.modules.dsa.judge.codec import ListNode

PATTERN_NUMBER = 1


def _values(head: ListNode | None) -> list[int]:
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


def _build(values: list[int]) -> ListNode | None:
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


# ---------------------------------------------------------------- Intersection of Two Linked Lists


def _intersection(headA: ListNode | None, headB: ListNode | None) -> ListNode | None:
    a, b = headA, headB
    while a is not b:
        a = a.next if a else headB
        b = b.next if b else headA
    return a


def _intersection_brute(headA: ListNode | None, headB: ListNode | None) -> ListNode | None:
    seen = set()
    while headA:
        seen.add(id(headA))
        headA = headA.next
    while headB:
        if id(headB) in seen:
            return headB
        headB = headB.next
    return None


def _intersection_gen(rng):
    na, nb, ns = pick_n(rng, 0, 30, big=1500), pick_n(rng, 0, 30, big=1500), pick_n(rng, 0, 30, big=1500)
    values = rng.sample(range(1, 10**5), na + nb + ns)
    return [values[:na], values[na : na + nb], values[na + nb :]]


INTERSECTION = ProblemSource(
    title="Intersection of Two Linked Lists",
    statement="""
You are given the heads of two singly linked lists, `headA` and `headB`. From some node onward the two
lists may **share the same nodes** (the same objects in memory, not merely equal values). Return the first
shared node, or `null` if the lists never meet.

The lists contain no cycles, and you must not change their structure.

**How the tests describe the lists:** each test gives `headA`'s own nodes, `headB`'s own nodes and the
`shared` tail. The judge builds the shared tail once and attaches it to the end of both lists; `shared`
is **not** passed to your function. Your answer is shown as the values from the returned node to the
end of the list.

Can you do it in `O(m + n)` time and `O(1)` memory?
""",
    constraints="""
- each part has between `0` and `1500` nodes
- `1 <= Node.val <= 10^5`, and all values in a test are distinct
""",
    signature=function(
        "getIntersectionNode",
        [("headA", "ListNode"), ("headB", "ListNode"), ("shared", "int[]")],
        "ListNode",
        links=[{"kind": "join", "a": "headA", "b": "headB", "shared": "shared"}],
    ),
    reference=_intersection,
    brute=_intersection_brute,
    examples=[
        Example([[4, 1], [5, 6, 1], [8, 4, 5]], "The lists meet at the node holding 8."),
        Example([[1, 9, 1], [3], [2, 4]], "They meet at the node holding 2."),
        Example([[2, 6, 4], [1, 5], []], "No shared tail, so the answer is null (shown as [])."),
    ],
    edge_cases=[[[], [], [7]], [[], [3], [7]], [[1], [2], []], [[], [], []], [[5, 6], [], [1]]],
    generator=_intersection_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Partition Labels


def _partition_labels(s: str) -> list[int]:
    last = {c: i for i, c in enumerate(s)}
    sizes, start, end = [], 0, 0
    for i, c in enumerate(s):
        end = max(end, last[c])
        if i == end:
            sizes.append(end - start + 1)
            start = i + 1
    return sizes


def _partition_labels_brute(s: str) -> list[int]:
    sizes, start = [], 0
    while start < len(s):
        end = start
        while any(c in s[end + 1 :] for c in s[start : end + 1]):
            end += 1
        sizes.append(end - start + 1)
        start = end + 1
    return sizes


PARTITION_LABELS = ProblemSource(
    title="Partition Labels",
    statement="""
Split the lowercase string `s` into as many consecutive pieces as possible so that every letter appears
in **at most one** piece. Joined back in order, the pieces must give `s` again.

Return the sizes of the pieces, in order.
""",
    constraints="""
- `1 <= s.length <= 5000`
- `s` consists of lowercase English letters
""",
    signature=function("partitionLabels", [("s", "string")], "int[]"),
    reference=_partition_labels,
    brute=_partition_labels_brute,
    brute_input_limit=400,
    examples=[
        Example(["ababcbacadefegdehijhklij"], 'Pieces: "ababcbaca", "defegde", "hijhklij".'),
        Example(["eccbbbbdec"], "Every letter's occurrences overlap, so there is one piece."),
    ],
    edge_cases=[["a"], ["ab"], ["aa"], ["abcabc"], ["abcdef"], ["caedbdedda"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 40, big=5000), string.ascii_lowercase[: rng.randint(2, 26)])],
    random_count=8,
)


# ---------------------------------------------------------------- Remove Element


def _remove_element(nums: list[int], val: int) -> int:
    k = 0
    for x in nums:
        if x != val:
            nums[k] = x
            k += 1
    return k


def _remove_element_brute(nums: list[int], val: int) -> int:
    kept = [x for x in nums if x != val]
    nums[: len(kept)] = kept
    return len(kept)


REMOVE_ELEMENT = ProblemSource(
    title="Remove Element",
    statement="""
Given an integer array `nums` and a value `val`, remove every occurrence of `val` **in place** and return
`k`, the number of elements that are not equal to `val`.

After your function returns, the first `k` positions of `nums` must hold exactly the elements that are
not `val`, in **any order**. Whatever is left in the positions after `k` is ignored.
""",
    constraints="""
- `0 <= nums.length <= 5000`
- `0 <= nums[i] <= 50`
- `0 <= val <= 100`
""",
    signature=function("removeElement", [("nums", "int[]"), ("val", "int")], "int", mutates="nums"),
    reference=_remove_element,
    brute=_remove_element_brute,
    compare="checker",
    checker="k_prefix_unordered",
    examples=[
        Example([[3, 2, 2, 3], 3], "k = 2 and the first two elements are 2 and 2."),
        Example([[0, 1, 2, 2, 3, 0, 4, 2], 2], "k = 5; the first five elements are 0, 1, 3, 0, 4 in any order."),
    ],
    edge_cases=[[[], 0], [[1], 1], [[1], 2], [[4, 4, 4], 4], [[5, 6, 7], 8]],
    generator=lambda rng: [ints(rng, pick_n(rng, 0, 40, big=5000), 0, 5), rng.randint(0, 6)],
    random_count=8,
)


# ---------------------------------------------------------------- String Compression


def _compress(chars: list[str]) -> int:
    write = read = 0
    while read < len(chars):
        start = read
        while read < len(chars) and chars[read] == chars[start]:
            read += 1
        chars[write] = chars[start]
        write += 1
        if read - start > 1:
            for digit in str(read - start):
                chars[write] = digit
                write += 1
    return write


def _compress_brute(chars: list[str]) -> int:
    encoded = ""
    for c, grp in itertools.groupby(chars):
        count = len(list(grp))
        encoded += c + (str(count) if count > 1 else "")
    chars[: len(encoded)] = list(encoded)
    return len(encoded)


def _compress_gen(rng):
    out = []
    for _ in range(pick_n(rng, 1, 30, big=600)):
        out += [rng.choice("abcXY1!")] * rng.choice([1, 1, 2, 3, 9, 10, 12, 100])
    return [out[:2000]]


STRING_COMPRESSION = ProblemSource(
    title="String Compression",
    statement="""
You are given an array of characters `chars`. Compress it **in place** with this rule: every maximal run
of the same character becomes the character followed by the run length, and the length is omitted
when it is 1. A length of 10 or more is written as several digit characters.

For example `a a b b c c c` becomes `a 2 b 2 c 3`.

Write the compressed characters into the start of `chars` and return the new length `k`. Only the first
`k` characters are checked. Use `O(1)` extra space.
""",
    constraints="""
- `1 <= chars.length <= 2000`
- `chars[i]` is an English letter, a digit or a symbol
""",
    signature=function("compress", [("chars", "char[]")], "int", mutates="chars"),
    reference=_compress,
    brute=_compress_brute,
    compare="checker",
    checker="k_prefix",
    examples=[
        Example([["a", "a", "b", "b", "c", "c", "c"]], "The first 6 characters become a, 2, b, 2, c, 3."),
        Example([["a"]], "A single character stays as is."),
        Example([["a", "b", "b", "b", "b", "b", "b", "b", "b", "b", "b", "b", "b"]], "12 b's become b, 1, 2."),
    ],
    edge_cases=[[["a", "a"]], [["a", "b", "c"]], [["1", "1", "1"]], [["a"] * 100], [["x"] * 10 + ["y"]]],
    generator=_compress_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Rotate Array


def _rotate(nums: list[int], k: int) -> None:
    n = len(nums)
    k %= n

    def reverse(lo: int, hi: int) -> None:
        while lo < hi:
            nums[lo], nums[hi] = nums[hi], nums[lo]
            lo, hi = lo + 1, hi - 1

    reverse(0, n - 1)
    reverse(0, k - 1)
    reverse(k, n - 1)


def _rotate_brute(nums: list[int], k: int) -> None:
    for _ in range(k % len(nums)):
        nums.insert(0, nums.pop())


ROTATE_ARRAY = ProblemSource(
    title="Rotate Array",
    statement="""
Rotate the integer array `nums` to the right by `k` steps **in place**: each step moves the last element
to the front. `k` may be larger than the length of the array.

Can you do it with `O(1)` extra space?
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-2^31 <= nums[i] <= 2^31 - 1`
- `0 <= k <= 10^5`
""",
    signature=function("rotate", [("nums", "int[]"), ("k", "int")], "void", mutates="nums"),
    reference=_rotate,
    brute=_rotate_brute,
    examples=[
        Example([[1, 2, 3, 4, 5, 6, 7], 3], "After 3 steps: 5, 6, 7, 1, 2, 3, 4."),
        Example([[-1, -100, 3, 99], 2]),
    ],
    edge_cases=[[[1], 0], [[1], 5], [[1, 2], 1], [[1, 2], 2], [[1, 2, 3], 100000], [[2147483647, -2147483648], 1]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 40, big=2500), -(2**31), 2**31 - 1), rng.randint(0, 10**5)],
    random_count=8,
)


# ---------------------------------------------------------------- Next Permutation


def _next_permutation(nums: list[int]) -> None:
    i = len(nums) - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = len(nums) - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    nums[i + 1 :] = reversed(nums[i + 1 :])


def _next_permutation_brute(nums: list[int]) -> None:
    perms = sorted(set(itertools.permutations(nums)))
    idx = perms.index(tuple(nums))
    nums[:] = perms[(idx + 1) % len(perms)]


NEXT_PERMUTATION = ProblemSource(
    title="Next Permutation",
    statement="""
The *next permutation* of an integer array is the arrangement of the same values that comes right after
it in lexicographic (dictionary) order. If the array is already the largest arrangement, the next one
wraps around to the smallest, i.e. the values sorted in ascending order.

Rearrange `nums` into its next permutation **in place**, using only constant extra memory.
""",
    constraints="""
- `1 <= nums.length <= 3000`
- `0 <= nums[i] <= 100`
""",
    signature=function("nextPermutation", [("nums", "int[]")], "void", mutates="nums"),
    reference=_next_permutation,
    brute=_next_permutation_brute,
    brute_input_limit=24,
    examples=[
        Example([[1, 2, 3]], "The next arrangement is 1, 3, 2."),
        Example([[3, 2, 1]], "Already the largest, so wrap around to 1, 2, 3."),
        Example([[1, 1, 5]], "Next is 1, 5, 1."),
    ],
    edge_cases=[[[1]], [[1, 1]], [[1, 3, 2]], [[2, 3, 1]], [[1, 5, 8, 4, 7, 6, 5, 3, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 7, big=3000), 0, rng.choice([3, 100]))],
    random_count=8,
)


# ---------------------------------------------------------------- Remove Duplicates from Sorted Array


def _remove_duplicates(nums: list[int]) -> int:
    k = 0
    for x in nums:
        if k == 0 or nums[k - 1] != x:
            nums[k] = x
            k += 1
    return k


def _remove_duplicates_brute(nums: list[int]) -> int:
    unique = sorted(set(nums))
    nums[: len(unique)] = unique
    return len(unique)


REMOVE_DUPLICATES = ProblemSource(
    title="Remove Duplicates from Sorted Array",
    statement="""
`nums` is sorted in non-decreasing order. Remove the duplicates **in place** so that each distinct value
appears once, keeping the values in their original order, and return `k`, the number of distinct values.

After your function returns, the first `k` positions of `nums` must hold the distinct values in
increasing order. Positions after `k` are ignored.
""",
    constraints="""
- `1 <= nums.length <= 3 * 10^4`
- `-100 <= nums[i] <= 100`
- `nums` is sorted in non-decreasing order
""",
    signature=function("removeDuplicates", [("nums", "int[]")], "int", mutates="nums"),
    reference=_remove_duplicates,
    brute=_remove_duplicates_brute,
    compare="checker",
    checker="k_prefix",
    examples=[
        Example([[1, 1, 2]], "k = 2 with 1, 2 at the front."),
        Example([[0, 0, 1, 1, 1, 2, 2, 3, 3, 4]], "k = 5 with 0, 1, 2, 3, 4 at the front."),
    ],
    edge_cases=[[[1]], [[5, 5, 5, 5]], [[-100, 100]], [[-3, -3, -2, -1, -1]]],
    generator=lambda rng: [sorted(ints(rng, pick_n(rng, 1, 40, big=5000), -100, rng.choice([-95, 100])))],
    random_count=8,
)


# ---------------------------------------------------------------- Reverse Vowels of a String

_VOWELS = set("aeiouAEIOU")


def _reverse_vowels(s: str) -> str:
    chars, lo, hi = list(s), 0, len(s) - 1
    while lo < hi:
        if chars[lo] not in _VOWELS:
            lo += 1
        elif chars[hi] not in _VOWELS:
            hi -= 1
        else:
            chars[lo], chars[hi] = chars[hi], chars[lo]
            lo, hi = lo + 1, hi - 1
    return "".join(chars)


def _reverse_vowels_brute(s: str) -> str:
    vowels = [c for c in s if c in _VOWELS]
    return "".join(vowels.pop() if c in _VOWELS else c for c in s)


REVERSE_VOWELS = ProblemSource(
    title="Reverse Vowels of a String",
    statement="""
Given a string `s`, reverse the order of just its vowels and return the result. The vowels are `a`, `e`,
`i`, `o` and `u`, in either lowercase or uppercase; all other characters stay where they are.
""",
    constraints="""
- `1 <= s.length <= 3 * 10^5`
- `s` consists of printable ASCII characters
""",
    signature=function("reverseVowels", [("s", "string")], "string"),
    reference=_reverse_vowels,
    brute=_reverse_vowels_brute,
    examples=[
        Example(["IceCreAm"], 'The vowels I, e, e, A become A, e, e, I: "AceCreIm".'),
        Example(["leetcode"], '"leotcede"'),
    ],
    edge_cases=[["a"], ["b"], ["aA"], ["xyz"], ["Ab,cE"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 40, big=12000), "aeiouAEbcdXY ,!")],
    random_count=8,
)


# ---------------------------------------------------------------- Is Subsequence


def _is_subsequence(s: str, t: str) -> bool:
    i = 0
    for c in t:
        if i < len(s) and s[i] == c:
            i += 1
    return i == len(s)


def _subseq_gen(rng):
    t = word(rng, pick_n(rng, 0, 40, big=12000), "abc")
    if rng.random() < 0.5 and t:
        s = "".join(c for c in t if rng.random() < 0.3)
    else:
        s = word(rng, pick_n(rng, 0, 8, big=60), "abc")
    return [s, t]


IS_SUBSEQUENCE = ProblemSource(
    title="Is Subsequence",
    statement="""
Given two strings `s` and `t`, return `true` if `s` is a subsequence of `t`: `s` can be obtained from `t`
by deleting zero or more characters without changing the order of the rest.
""",
    constraints="""
- `0 <= s.length <= 100`
- `0 <= t.length <= 10^4`
- both strings consist of lowercase English letters
""",
    signature=function("isSubsequence", [("s", "string"), ("t", "string")], "bool"),
    reference=_is_subsequence,
    brute=lambda s, t: (lambda it: all(c in it for c in s))(iter(t)),
    examples=[
        Example(["abc", "ahbgdc"], "a, b and c appear in order in t."),
        Example(["axc", "ahbgdc"], "There is no x in t."),
    ],
    edge_cases=[["", ""], ["", "abc"], ["a", ""], ["aa", "a"], ["abc", "abc"], ["b", "abc"]],
    generator=_subseq_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Merge Strings Alternately


def _merge_alternately(word1: str, word2: str) -> str:
    out, i = [], 0
    while i < len(word1) or i < len(word2):
        if i < len(word1):
            out.append(word1[i])
        if i < len(word2):
            out.append(word2[i])
        i += 1
    return "".join(out)


MERGE_ALTERNATELY = ProblemSource(
    title="Merge Strings Alternately",
    statement="""
Merge two strings by taking characters alternately, starting with `word1`. When one string runs out,
append the rest of the other string. Return the merged string.
""",
    constraints="""
- `1 <= word1.length, word2.length <= 100`
- both strings consist of lowercase English letters
""",
    signature=function("mergeAlternately", [("word1", "string"), ("word2", "string")], "string"),
    reference=_merge_alternately,
    brute=lambda word1, word2: "".join(a + b for a, b in itertools.zip_longest(word1, word2, fillvalue="")),
    examples=[
        Example(["abc", "pqr"], 'a p b q c r -> "apbqcr".'),
        Example(["ab", "pqrs"], 'After a p b q, the rest of word2 ("rs") is appended.'),
        Example(["abcd", "pq"]),
    ],
    edge_cases=[["a", "b"], ["a", "bcd"], ["xyz", "q"]],
    generator=lambda rng: [word(rng, rng.randint(1, 100), "abcxyz"), word(rng, rng.randint(1, 100), "pqrs")],
    random_count=7,
)


# ---------------------------------------------------------------- Compare Version Numbers


def _compare_versions(version1: str, version2: str) -> int:
    a, b = version1.split("."), version2.split(".")
    for i in range(max(len(a), len(b))):
        x = int(a[i]) if i < len(a) else 0
        y = int(b[i]) if i < len(b) else 0
        if x != y:
            return -1 if x < y else 1
    return 0


def _compare_versions_brute(version1: str, version2: str) -> int:
    a = [int(x) for x in version1.split(".")]
    b = [int(x) for x in version2.split(".")]
    n = max(len(a), len(b))
    a, b = a + [0] * (n - len(a)), b + [0] * (n - len(b))
    return (a > b) - (a < b)


def _version_gen(rng):
    def version():
        return ".".join(
            rng.choice(["0", "1", "01", "001", "2", "10", str(rng.randint(0, 999))]) for _ in range(rng.randint(1, 5))
        )

    v1 = version()
    v2 = v1 if rng.random() < 0.2 else version()
    return [v1, v2]


COMPARE_VERSIONS = ProblemSource(
    title="Compare Version Numbers",
    statement="""
A version string is a list of revisions separated by dots, such as `"1.02.0"`. Each revision is a
non-negative integer written in decimal and may have leading zeros (`"01"` equals `1`).

Compare two versions revision by revision from left to right. A missing revision counts as `0`, so
`"1.0"` and `"1"` are equal.

Return `-1` if `version1` is smaller, `1` if it is larger, and `0` if they are equal.
""",
    constraints="""
- `1 <= version.length <= 500`
- versions contain only digits and dots, and every revision is non-empty
- each revision fits in a 32-bit integer
""",
    signature=function("compareVersion", [("version1", "string"), ("version2", "string")], "int"),
    reference=_compare_versions,
    brute=_compare_versions_brute,
    examples=[
        Example(["1.2", "1.10"], "Second revisions: 2 < 10."),
        Example(["1.01", "1.001"], "Both second revisions equal 1."),
        Example(["1.0", "1.0.0.0"], "Missing revisions count as 0."),
    ],
    edge_cases=[["0", "0"], ["1", "0.9"], ["0.1", "0.0.1"], ["7.5.2.4", "7.5.3"], ["1.0.1", "1"]],
    generator=_version_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Move Zeroes


def _move_zeroes(nums: list[int]) -> None:
    k = 0
    for i, x in enumerate(nums):
        if x != 0:
            nums[k], nums[i] = nums[i], nums[k]
            k += 1


def _move_zeroes_brute(nums: list[int]) -> None:
    nonzero = [x for x in nums if x != 0]
    nums[:] = nonzero + [0] * (len(nums) - len(nonzero))


MOVE_ZEROES = ProblemSource(
    title="Move Zeroes",
    statement="""
Move every `0` in `nums` to the end of the array **in place**, keeping the relative order of the non-zero
values. Don't make a copy of the array.
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-2^31 <= nums[i] <= 2^31 - 1`
""",
    signature=function("moveZeroes", [("nums", "int[]")], "void", mutates="nums"),
    reference=_move_zeroes,
    brute=_move_zeroes_brute,
    examples=[Example([[0, 1, 0, 3, 12]], "Non-zero values keep their order: 1, 3, 12, 0, 0."), Example([[0]])],
    edge_cases=[[[1]], [[0, 0, 1]], [[1, 0, 0]], [[4, 2, 4, 0, 0, 3, 0, 5, 1, 0]]],
    generator=lambda rng: [[x if rng.random() < 0.6 else 0 for x in ints(rng, pick_n(rng, 1, 40, big=3000), -9, 9)]],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Subarray of 1's After Deleting One Element


def _longest_after_delete(nums: list[int]) -> int:
    best = lo = zeros = 0
    for hi, x in enumerate(nums):
        zeros += x == 0
        while zeros > 1:
            zeros -= nums[lo] == 0
            lo += 1
        best = max(best, hi - lo)
    return best


def _longest_after_delete_brute(nums: list[int]) -> int:
    best = 0
    for d in range(len(nums)):
        rest = nums[:d] + nums[d + 1 :]
        run = 0
        for x in rest:
            run = run + 1 if x == 1 else 0
            best = max(best, run)
    return best


LONGEST_AFTER_DELETE = ProblemSource(
    title="Longest Subarray of 1's After Deleting One Element",
    statement="""
You are given a binary array `nums`. You **must** delete exactly one element from it.

Return the length of the longest non-empty run of consecutive `1`s in the array after the deletion, or
`0` if there is none.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `nums[i]` is `0` or `1`
""",
    signature=function("longestSubarray", [("nums", "int[]")], "int"),
    reference=_longest_after_delete,
    brute=_longest_after_delete_brute,
    brute_input_limit=400,
    examples=[
        Example([[1, 1, 0, 1]], "Deleting the 0 leaves three 1s in a row."),
        Example([[0, 1, 1, 1, 0, 1, 1, 0, 1]], "Deleting the 0 at index 4 leaves [1,1,1,1,1]."),
        Example([[1, 1, 1]], "One element must be deleted, leaving 2."),
    ],
    edge_cases=[[[0]], [[1]], [[0, 0]], [[1, 0]], [[0, 1, 0]]],
    generator=lambda rng: [
        [1 if rng.random() < rng.choice([0.5, 0.9]) else 0 for _ in range(pick_n(rng, 1, 40, big=8000))]
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Backspace String Compare


def _backspace_compare(s: str, t: str) -> bool:
    def next_index(text: str, i: int) -> int:
        skip = 0
        while i >= 0:
            if text[i] == "#":
                skip += 1
            elif skip:
                skip -= 1
            else:
                return i
            i -= 1
        return -1

    i, j = len(s) - 1, len(t) - 1
    while True:
        i, j = next_index(s, i), next_index(t, j)
        if i < 0 or j < 0:
            return i < 0 and j < 0
        if s[i] != t[j]:
            return False
        i, j = i - 1, j - 1


def _backspace_brute(s: str, t: str) -> bool:
    def typed(text: str) -> str:
        out: list[str] = []
        for c in text:
            if c == "#":
                if out:
                    out.pop()
            else:
                out.append(c)
        return "".join(out)

    return typed(s) == typed(t)


def _backspace_gen(rng):
    s = word(rng, pick_n(rng, 1, 20, big=200), "ab##")
    t = s if rng.random() < 0.3 else word(rng, pick_n(rng, 1, 20, big=200), "ab##")
    if rng.random() < 0.3:
        t = t + "c#"
    return [s, t]


BACKSPACE_COMPARE = ProblemSource(
    title="Backspace String Compare",
    statement="""
Two strings `s` and `t` are typed into empty text editors, where `#` means a backspace: it deletes the
character before the cursor, and does nothing if the editor is empty.

Return `true` if both editors end up showing the same text.

Can you do it with `O(1)` extra space?
""",
    constraints="""
- `1 <= s.length, t.length <= 200`
- `s` and `t` contain lowercase letters and `#`
""",
    signature=function("backspaceCompare", [("s", "string"), ("t", "string")], "bool"),
    reference=_backspace_compare,
    brute=_backspace_brute,
    examples=[
        Example(["ab#c", "ad#c"], 'Both become "ac".'),
        Example(["ab##", "c#d#"], "Both become empty."),
        Example(["a#c", "b"], '"c" versus "b".'),
    ],
    edge_cases=[
        ["#", "#"],
        ["a", "a"],
        ["a#", "#"],
        ["xy#z", "xzz#"],
        ["bxj##tw", "bxo#j##tw"],
        ["y#fo##f", "y#f#o##f"],
    ],
    generator=_backspace_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Next Greater Element III


def _next_greater_iii(n: int) -> int:
    digits = list(str(n))
    i = len(digits) - 2
    while i >= 0 and digits[i] >= digits[i + 1]:
        i -= 1
    if i < 0:
        return -1
    j = len(digits) - 1
    while digits[j] <= digits[i]:
        j -= 1
    digits[i], digits[j] = digits[j], digits[i]
    digits[i + 1 :] = reversed(digits[i + 1 :])
    result = int("".join(digits))
    return result if result < 2**31 else -1


def _next_greater_iii_brute(n: int) -> int:
    candidates = [int("".join(p)) for p in itertools.permutations(str(n))]
    bigger = [c for c in candidates if n < c < 2**31]
    return min(bigger) if bigger else -1


NEXT_GREATER_III = ProblemSource(
    title="Next Greater Element III",
    statement="""
Given a positive integer `n`, return the smallest integer that has **exactly the same digits** as `n`
(rearranged) and is strictly greater than `n`.

Return `-1` if no such integer exists, or if the answer does not fit in a signed 32-bit integer
(it must be at most `2^31 - 1`).
""",
    constraints="""
- `1 <= n <= 2^31 - 1`
""",
    signature=function("nextGreaterElement", [("n", "int")], "int"),
    reference=_next_greater_iii,
    brute=_next_greater_iii_brute,
    brute_input_limit=8,
    examples=[Example([12], "21 is the next arrangement."), Example([21], "21 is already the largest arrangement.")],
    edge_cases=[[1], [11], [230241], [2147483476], [2147483647], [1999999999], [101]],
    generator=lambda rng: [rng.choice([rng.randint(1, 10**7), rng.randint(10**8, 2**31 - 1)])],
    random_count=8,
)


# ---------------------------------------------------------------- Rotating the Box


def _rotate_the_box(box: list[list[str]]) -> list[list[str]]:
    rows, cols = len(box), len(box[0])
    for row in box:
        empty = cols - 1
        for c in range(cols - 1, -1, -1):
            if row[c] == "*":
                empty = c - 1
            elif row[c] == "#":
                row[c], row[empty] = ".", "#"
                empty -= 1
    return [[box[rows - 1 - r][c] for r in range(rows)] for c in range(cols)]


def _rotate_the_box_brute(box: list[list[str]]) -> list[list[str]]:
    settled = []
    for row in box:
        out, segment = [], []
        for cell in row + ["*"]:
            if cell == "*":
                stones = segment.count("#")
                out += ["."] * (len(segment) - stones) + ["#"] * stones + ["*"]
                segment = []
            else:
                segment.append(cell)
        settled.append(out[:-1])
    return [list(col)[::-1] for col in zip(*settled, strict=True)]


def _box_grid_gen(rng):
    rows, cols = pick_n(rng, 1, 12, big=60), pick_n(rng, 1, 12, big=60)
    return [[[rng.choice("..##*") for _ in range(cols)] for _ in range(rows)]]


ROTATING_THE_BOX = ProblemSource(
    title="Rotating the Box",
    statement="""
You see a box from the side as an `m x n` grid of characters: `'#'` is a stone, `'*'` is a fixed obstacle
and `'.'` is empty space.

The box is rotated 90 degrees **clockwise**. Gravity then pulls every stone straight down (towards the
new bottom) until it lands on an obstacle, another stone or the floor. Obstacles never move, and the
rotation doesn't move stones sideways.

Return the resulting `n x m` grid.
""",
    constraints="""
- `1 <= m, n <= 500`
- every cell is `'#'`, `'*'` or `'.'`
""",
    signature=function("rotateTheBox", [("box", "char[][]")], "char[][]"),
    reference=_rotate_the_box,
    brute=_rotate_the_box_brute,
    examples=[
        Example([[["#", ".", "#"]]], "After rotating, both stones fall to the bottom."),
        Example([[["#", ".", "*", "."], ["#", "#", "*", "."]]], "The obstacles stop the stones in the middle row."),
    ],
    edge_cases=[
        [[["."]]],
        [[["#"]]],
        [[["*"]]],
        [[["#", "#", "*", ".", "*", "."], ["#", "#", "#", "*", ".", "."], ["#", "#", "#", ".", "#", "."]]],
    ],
    generator=_box_grid_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Count the Number of Fair Pairs


def _count_fair_pairs(nums: list[int], lower: int, upper: int) -> int:
    nums = sorted(nums)

    def pairs_at_most(limit: int) -> int:
        count, lo, hi = 0, 0, len(nums) - 1
        while lo < hi:
            if nums[lo] + nums[hi] <= limit:
                count += hi - lo
                lo += 1
            else:
                hi -= 1
        return count

    return pairs_at_most(upper) - pairs_at_most(lower - 1)


def _count_fair_pairs_brute(nums: list[int], lower: int, upper: int) -> int:
    return sum(lower <= a + b <= upper for a, b in itertools.combinations(nums, 2))


def _fair_gen(rng):
    nums = ints(rng, pick_n(rng, 1, 40, big=5000), -50, 50)
    lower = rng.randint(-100, 100)
    return [nums, lower, rng.randint(lower, 100)]


COUNT_FAIR_PAIRS = ProblemSource(
    title="Count the Number of Fair Pairs",
    statement="""
Given an integer array `nums` and two integers `lower` and `upper`, count the index pairs `(i, j)` with
`i < j` and `lower <= nums[i] + nums[j] <= upper`.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `-10^9 <= nums[i] <= 10^9`
- `-10^9 <= lower <= upper <= 10^9`
""",
    signature=function("countFairPairs", [("nums", "int[]"), ("lower", "int"), ("upper", "int")], "long"),
    reference=_count_fair_pairs,
    brute=_count_fair_pairs_brute,
    brute_input_limit=400,
    examples=[
        Example([[0, 1, 7, 4, 4, 5], 3, 6], "The six fair pairs are (0,3), (0,4), (0,5), (1,3), (1,4), (1,5)."),
        Example([[1, 7, 9, 2, 5], 11, 11], "Only 2 + 9 = 11."),
    ],
    edge_cases=[[[5], 0, 10], [[1, 1], 2, 2], [[-1000000000, -1000000000], -1000000000, 1000000000], [[3, 3, 3], 6, 6]],
    generator=_fair_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Remove Duplicates from Sorted List II


def _delete_duplicates_ii(head: ListNode | None) -> ListNode | None:
    dummy = ListNode(0, head)
    prev = dummy
    while head:
        if head.next and head.val == head.next.val:
            while head.next and head.val == head.next.val:
                head = head.next
            prev.next = head.next
        else:
            prev = prev.next
        head = head.next
    return dummy.next


def _delete_duplicates_ii_brute(head: ListNode | None) -> ListNode | None:
    values = _values(head)
    return _build([v for v in values if values.count(v) == 1])


DELETE_DUPLICATES_II = ProblemSource(
    title="Remove Duplicates from Sorted List II",
    statement="""
The linked list starting at `head` is sorted. Delete **every** node whose value appears more than once,
so that only values that were unique in the original list remain. Return the head of the sorted result.
""",
    constraints="""
- the list has between `0` and `300` nodes
- `-100 <= Node.val <= 100`
- the list is sorted in ascending order
""",
    signature=function("deleteDuplicates", [("head", "ListNode")], "ListNode"),
    reference=_delete_duplicates_ii,
    brute=_delete_duplicates_ii_brute,
    examples=[
        Example([[1, 2, 3, 3, 4, 4, 5]], "3 and 4 appear twice, so all of their nodes are removed."),
        Example([[1, 1, 1, 2, 3]], "The leading 1s are removed."),
    ],
    edge_cases=[[[]], [[1]], [[1, 1]], [[1, 2, 2]], [[1, 1, 2, 2]], [[-100, 100]]],
    generator=lambda rng: [sorted(ints(rng, pick_n(rng, 0, 30, big=300), -100, rng.choice([-90, 100])))],
    random_count=8,
)


# ---------------------------------------------------------------- Sum of Square Numbers


def _judge_square_sum(c: int) -> bool:
    lo, hi = 0, math.isqrt(c)
    while lo <= hi:
        total = lo * lo + hi * hi
        if total == c:
            return True
        if total < c:
            lo += 1
        else:
            hi -= 1
    return False


def _judge_square_sum_brute(c: int) -> bool:
    return any(math.isqrt(c - a * a) ** 2 == c - a * a for a in range(math.isqrt(c) + 1))


SUM_OF_SQUARES = ProblemSource(
    title="Sum of Square Numbers",
    statement="""
Given a non-negative integer `c`, decide whether there are two integers `a` and `b` (both may be zero, and
they may be equal) with `a^2 + b^2 = c`.
""",
    constraints="""
- `0 <= c <= 2^31 - 1`
""",
    signature=function("judgeSquareSum", [("c", "int")], "bool"),
    reference=_judge_square_sum,
    brute=_judge_square_sum_brute,
    examples=[Example([5], "1^2 + 2^2 = 5."), Example([3], "No two squares add up to 3.")],
    edge_cases=[[0], [1], [2], [4], [2147483647], [2147395600], [999999999]],
    generator=lambda rng: [
        rng.choice(
            [rng.randint(0, 1000), rng.randint(0, 2**31 - 1), rng.randint(1, 30000) ** 2 + rng.randint(0, 30000) ** 2]
        )
    ],
    random_count=8,
)


PROBLEMS = [
    INTERSECTION,
    PARTITION_LABELS,
    REMOVE_ELEMENT,
    STRING_COMPRESSION,
    ROTATE_ARRAY,
    NEXT_PERMUTATION,
    REMOVE_DUPLICATES,
    REVERSE_VOWELS,
    IS_SUBSEQUENCE,
    MERGE_ALTERNATELY,
    COMPARE_VERSIONS,
    MOVE_ZEROES,
    LONGEST_AFTER_DELETE,
    BACKSPACE_COMPARE,
    NEXT_GREATER_III,
    ROTATING_THE_BOX,
    COUNT_FAIR_PAIRS,
    DELETE_DUPLICATES_II,
    SUM_OF_SQUARES,
]
