"""Pattern 1: Two Pointers (part 1 of 2). Original statements; expected outputs come from `reference`."""

from __future__ import annotations

import itertools
import string
from collections import deque

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n, random_tree, word
from app.modules.dsa.judge.codec import ListNode

PATTERN_NUMBER = 1


# ---------------------------------------------------------------- 3Sum


def _three_sum(nums: list[int]) -> list[list[int]]:
    nums = sorted(nums)
    out: list[list[int]] = []
    for i in range(len(nums) - 2):
        if i and nums[i] == nums[i - 1]:
            continue
        lo, hi = i + 1, len(nums) - 1
        while lo < hi:
            total = nums[i] + nums[lo] + nums[hi]
            if total < 0:
                lo += 1
            elif total > 0:
                hi -= 1
            else:
                out.append([nums[i], nums[lo], nums[hi]])
                lo += 1
                while lo < hi and nums[lo] == nums[lo - 1]:
                    lo += 1
    return out


def _three_sum_brute(nums: list[int]) -> list[list[int]]:
    found = {tuple(sorted(c)) for c in itertools.combinations(nums, 3) if sum(c) == 0}
    return [list(t) for t in found]


THREE_SUM = ProblemSource(
    title="3Sum",
    statement="""
Given an integer array `nums`, find every group of three values that adds up to zero.

Each group must use three different positions of the array, and the answer must not contain the same
group of values twice (groups are compared as multisets, so `[-1, 0, 1]` and `[0, 1, -1]` are the same group).

Return the groups in any order; the values inside a group may also be in any order.
""",
    constraints="""
- `3 <= nums.length <= 1500`
- `-10^5 <= nums[i] <= 10^5`
""",
    signature=function("threeSum", [("nums", "int[]")], "int[][]"),
    reference=_three_sum,
    brute=_three_sum_brute,
    brute_input_limit=300,
    compare="unordered_nested",
    examples=[
        Example([[-1, 0, 1, 2, -1, -4]], "The zero-sum groups are [-1, -1, 2] and [-1, 0, 1]."),
        Example([[0, 1, 1]], "No three values add up to zero."),
        Example([[0, 0, 0]], "The only group is [0, 0, 0]."),
    ],
    edge_cases=[
        [[0, 0, 0, 0]],
        [[1, 2, -3]],
        [[-2, 0, 1, 1, 2]],
        [[5, 5, 5]],
        [[-1, -1, 2, 2, -1]],
        [[3, -3, 0, 3, -3, 0]],
    ],
    generator=lambda rng: [
        ints(
            rng,
            pick_n(rng, 3, 60, big=1500),
            -12 if rng.random() < 0.7 else -(10**5),
            12 if rng.random() < 0.7 else 10**5,
        )
    ],
    random_count=9,
)


# ---------------------------------------------------------------- Remove nth Node from End of List


def _remove_nth(head: ListNode | None, n: int) -> ListNode | None:
    dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n):
        fast = fast.next
    while fast.next:
        fast, slow = fast.next, slow.next
    slow.next = slow.next.next
    return dummy.next


def _remove_nth_brute(head: ListNode | None, n: int) -> ListNode | None:
    values = []
    while head:
        values.append(head.val)
        head = head.next
    del values[len(values) - n]
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def _remove_nth_gen(rng):
    size = pick_n(rng, 1, 200, big=2500)
    return [ints(rng, size, -100, 100), rng.randint(1, size)]


REMOVE_NTH = ProblemSource(
    title="Remove nth Node from End of List",
    statement="""
You are given the head of a singly linked list and an integer `n`. Remove the `n`-th node counting from
the end of the list (the last node is the 1st from the end) and return the head of the resulting list.

Try to do it in a single pass over the list.
""",
    constraints="""
- The list has `sz` nodes, `1 <= sz <= 5000`
- `-100 <= Node.val <= 100`
- `1 <= n <= sz`
""",
    signature=function("removeNthFromEnd", [("head", "ListNode"), ("n", "int")], "ListNode"),
    reference=_remove_nth,
    brute=_remove_nth_brute,
    examples=[
        Example([[1, 2, 3, 4, 5], 2], "The 2nd node from the end holds 4, so it is removed."),
        Example([[7], 1], "Removing the only node leaves an empty list."),
        Example([[1, 2], 1]),
    ],
    edge_cases=[[[1, 2], 2], [[5, 5, 5], 3], [[1, 2, 3], 2], [[-1, 0, 1, 2], 4]],
    generator=_remove_nth_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Sort Colors


def _sort_colors(nums: list[int]) -> None:
    low, mid, high = 0, 0, len(nums) - 1
    while mid <= high:
        if nums[mid] == 0:
            nums[low], nums[mid] = nums[mid], nums[low]
            low += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:
            nums[mid], nums[high] = nums[high], nums[mid]
            high -= 1


SORT_COLORS = ProblemSource(
    title="Sort Colors",
    statement="""
An array `nums` holds only the values `0`, `1` and `2`, standing for three colors. Rearrange the array
**in place** so that all `0`s come first, then all `1`s, then all `2`s.

Don't use a library sort. Can you do it in one pass with constant extra space?
""",
    constraints="""
- `1 <= nums.length <= 20000`
- `nums[i]` is `0`, `1` or `2`
""",
    signature=function("sortColors", [("nums", "int[]")], "void", mutates="nums"),
    reference=_sort_colors,
    brute=lambda nums: nums.sort(),
    examples=[Example([[2, 0, 2, 1, 1, 0]]), Example([[2, 0, 1]])],
    edge_cases=[[[0]], [[2, 2, 2]], [[1, 0]], [[2, 1, 0, 0, 1, 2]], [[1, 1, 1, 0]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 300, big=8000), 0, 2)],
    random_count=8,
)


# ---------------------------------------------------------------- Reverse Words in a String


def _reverse_words(s: str) -> str:
    words, i = [], len(s) - 1
    while i >= 0:
        while i >= 0 and s[i] == " ":
            i -= 1
        end = i
        while i >= 0 and s[i] != " ":
            i -= 1
        if end >= 0:
            words.append(s[i + 1 : end + 1])
    return " ".join(words)


def _words_gen(rng):
    parts = [
        word(rng, rng.randint(1, 6), string.ascii_letters + string.digits) for _ in range(pick_n(rng, 1, 40, big=2000))
    ]
    return ["".join(" " * rng.choice([0, 0, 1, 2]) + p for p in parts) + " " * rng.randint(0, 2)]


REVERSE_WORDS = ProblemSource(
    title="Reverse Words in a String",
    statement="""
A string `s` contains words separated by spaces; a word is a maximal run of non-space characters.
Return a string with the words in reverse order, joined by exactly one space.

`s` may have spaces at the start or end and several spaces between words; none of those extra
spaces should appear in the result.
""",
    constraints="""
- `1 <= s.length <= 10^4`
- `s` contains English letters, digits and spaces
- `s` contains at least one word
""",
    signature=function("reverseWords", [("s", "string")], "string"),
    reference=_reverse_words,
    brute=lambda s: " ".join(reversed(s.split())),
    examples=[
        Example(["the sky is blue"], "The four words in reverse order."),
        Example(["  hello world  "], "Leading and trailing spaces are dropped."),
        Example(["a good   example"], "Runs of spaces collapse to one."),
    ],
    edge_cases=[["x"], ["   x   "], ["ab  cd"], ["1 2 3 4 5"]],
    generator=_words_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Valid Palindrome


def _is_palindrome(s: str) -> bool:
    lo, hi = 0, len(s) - 1
    while lo < hi:
        while lo < hi and not s[lo].isalnum():
            lo += 1
        while lo < hi and not s[hi].isalnum():
            hi -= 1
        if s[lo].lower() != s[hi].lower():
            return False
        lo, hi = lo + 1, hi - 1
    return True


def _palindrome_gen(rng):
    alphabet = "abAB01 ,.:"
    half = word(rng, pick_n(rng, 1, 200, big=12000), alphabet)
    if rng.random() < 0.6:
        mirrored = "".join(c.swapcase() if rng.random() < 0.3 else c for c in reversed(half))
        return [half + rng.choice(["", "x", " "]) + mirrored]
    return [half]


VALID_PALINDROME = ProblemSource(
    title="Valid Palindrome",
    statement="""
Given a string `s`, keep only its letters and digits and treat uppercase and lowercase letters as equal.
Return `true` if what remains reads the same forwards and backwards, otherwise `false`.

A string with no letters or digits counts as a palindrome.
""",
    constraints="""
- `1 <= s.length <= 2 * 10^5`
- `s` contains printable ASCII characters
""",
    signature=function("isPalindrome", [("s", "string")], "bool"),
    reference=_is_palindrome,
    brute=lambda s: (t := [c.lower() for c in s if c.isalnum()]) == t[::-1],
    examples=[
        Example(["A man, a plan, a canal: Panama"], "After cleaning: amanaplanacanalpanama, a palindrome."),
        Example(["race a car"], "After cleaning: raceacar, which is not a palindrome."),
        Example([" "], "Nothing is left after cleaning, which counts as a palindrome."),
    ],
    edge_cases=[["0P"], ["a"], [".,"], ["ab_a"], ["No 'x' in Nixon"], ["aA"]],
    generator=_palindrome_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Valid Word Abbreviation


def _valid_abbreviation(word_: str, abbr: str) -> bool:
    i = j = 0
    while i < len(word_) and j < len(abbr):
        if abbr[j].isdigit():
            if abbr[j] == "0":
                return False
            num = 0
            while j < len(abbr) and abbr[j].isdigit():
                num = num * 10 + int(abbr[j])
                j += 1
            i += num
        else:
            if word_[i] != abbr[j]:
                return False
            i, j = i + 1, j + 1
    return i == len(word_) and j == len(abbr)


def _valid_abbreviation_brute(word_: str, abbr: str) -> bool:
    tokens, j = [], 0
    while j < len(abbr):
        if abbr[j].isdigit():
            k = j
            while k < len(abbr) and abbr[k].isdigit():
                k += 1
            if abbr[j] == "0":
                return False
            tokens.append(int(abbr[j:k]))
            j = k
        else:
            tokens.append(abbr[j])
            j += 1
    pos = 0
    for t in tokens:
        if isinstance(t, int):
            pos += t
        elif pos >= len(word_) or word_[pos] != t:
            return False
        else:
            pos += 1
    return pos == len(word_)


def _abbr_gen(rng):
    w = word(rng, pick_n(rng, 1, 20, big=2000), "abc")
    out, i = [], 0
    while i < len(w):
        if rng.random() < 0.4:
            k = rng.randint(1, len(w) - i)
            out.append(str(k))
            i += k
        else:
            out.append(w[i])
            i += 1
    abbr = "".join(out)
    tweak = rng.random()
    if tweak < 0.2:
        abbr = abbr + "1"
    elif tweak < 0.3:
        abbr = abbr.replace("1", "01", 1)
    elif tweak < 0.45 and abbr:
        idx = rng.randrange(len(abbr))
        if not abbr[idx].isdigit():
            abbr = abbr[:idx] + "z" + abbr[idx + 1 :]
    return [w, abbr]


VALID_WORD_ABBREVIATION = ProblemSource(
    title="Valid Word Abbreviation",
    statement="""
A word can be abbreviated by replacing any number of **non-adjacent**, non-empty runs of its letters with
the length of each run. For example `"internationalization"` can become `"i18n"` or `"i5a11o1"`.

A number in an abbreviation may not have leading zeros (`"a01"` is invalid), and a number never stands
for an empty run.

Given `word` and `abbr`, return `true` if `abbr` is a valid abbreviation of `word`.
""",
    constraints="""
- `1 <= word.length <= 2000`, lowercase English letters
- `1 <= abbr.length <= 2000`, lowercase English letters and digits
- every number in `abbr` fits in a 32-bit integer
""",
    signature=function("validWordAbbreviation", [("word", "string"), ("abbr", "string")], "bool"),
    reference=_valid_abbreviation,
    brute=_valid_abbreviation_brute,
    examples=[
        Example(["internationalization", "i12iz4n"], "i + 12 letters + iz + 4 letters + n spells the word."),
        Example(["apple", "a2e"], "a + 2 letters + e covers only 4 of the 5 letters."),
        Example(["substitution", "s010n"], "A number cannot start with 0."),
    ],
    edge_cases=[["a", "1"], ["a", "2"], ["ab", "a1"], ["ab", "b1"], ["word", "4"], ["word", "0word"], ["hello", "h3o"]],
    generator=_abbr_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Valid Palindrome II


def _valid_palindrome_ii(s: str) -> bool:
    def is_pal(lo: int, hi: int) -> bool:
        while lo < hi:
            if s[lo] != s[hi]:
                return False
            lo, hi = lo + 1, hi - 1
        return True

    lo, hi = 0, len(s) - 1
    while lo < hi:
        if s[lo] != s[hi]:
            return is_pal(lo + 1, hi) or is_pal(lo, hi - 1)
        lo, hi = lo + 1, hi - 1
    return True


def _valid_palindrome_ii_brute(s: str) -> bool:
    return s == s[::-1] or any((t := s[:i] + s[i + 1 :]) == t[::-1] for i in range(len(s)))


def _pal_ii_gen(rng):
    half = word(rng, pick_n(rng, 1, 30, big=12000), "abc")
    s = half + rng.choice(["", "a"]) + half[::-1]
    for _ in range(rng.choice([0, 1, 1, 2])):
        i = rng.randint(0, len(s))
        s = s[:i] + rng.choice("abc") + s[i:]
    return [s]


VALID_PALINDROME_II = ProblemSource(
    title="Valid Palindrome II",
    statement="""
Given a lowercase string `s`, return `true` if it can be made a palindrome by deleting **at most one**
character (deleting none is allowed).
""",
    constraints="""
- `1 <= s.length <= 10^5`
- `s` consists of lowercase English letters
""",
    signature=function("validPalindrome", [("s", "string")], "bool"),
    reference=_valid_palindrome_ii,
    brute=_valid_palindrome_ii_brute,
    brute_input_limit=400,
    examples=[
        Example(["aba"], "Already a palindrome."),
        Example(["abca"], "Deleting 'c' (or 'b') gives a palindrome."),
        Example(["abc"], "No single deletion works."),
    ],
    edge_cases=[["a"], ["ab"], ["deeee"], ["eeeed"], ["cbbcc"], ["abccdba"], ["ebcbbececabbacecbbcbe"]],
    generator=_pal_ii_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Lowest Common Ancestor of a Binary Tree III (adapted)


def _lca_iii(root, p: int, q: int) -> int:
    parent = {root.val: None}
    stack = [root]
    while stack:
        node = stack.pop()
        for child in (node.left, node.right):
            if child:
                parent[child.val] = node.val
                stack.append(child)
    ancestors = set()
    while p is not None:
        ancestors.add(p)
        p = parent[p]
    while q not in ancestors:
        q = parent[q]
    return q


def _lca_brute(root, p: int, q: int) -> int:
    def path(node, target):
        if node is None:
            return None
        if node.val == target:
            return [node.val]
        sub = path(node.left, target) or path(node.right, target)
        return [node.val, *sub] if sub else None

    a, b = path(root, p), path(root, q)
    common = [x for x, y in zip(a, b, strict=False) if x == y]
    return common[-1]


def _lca_gen(rng):
    n = pick_n(rng, 2, 60, big=1500)
    tree = random_tree(rng, n, -(10**4), 10**4, unique=True)
    values = [v for v in tree if v is not None]
    p, q = rng.sample(values, 2) if rng.random() < 0.9 else [values[0], values[0]]
    return [tree, p, q]


LCA_III = ProblemSource(
    title="Lowest Common Ancestor of a Binary Tree III",
    statement="""
*Adapted I/O:* the original version of this problem gives you two nodes that each have a `parent` pointer.
Here you receive the `root` of a binary tree whose node values are all distinct, plus two values `p` and
`q` that both occur in the tree.

Return the **value** of their lowest common ancestor: the deepest node that has both `p` and `q` in its
subtree (a node counts as being in its own subtree).

Aim for the parent-pointer technique: record each node's parent, walk up from `p`, then walk up from
`q` until you meet a node you have seen.
""",
    constraints="""
- The tree has between `2` and `3000` nodes
- `-10^4 <= Node.val <= 10^4`, all values distinct
- `p` and `q` are values in the tree (they may be equal)
""",
    signature=function("lowestCommonAncestor", [("root", "TreeNode"), ("p", "int"), ("q", "int")], "int"),
    reference=_lca_iii,
    brute=_lca_brute,
    is_variant=True,
    examples=[
        Example([[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1], "5 and 1 meet at the root, 3."),
        Example([[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 4], "5 is an ancestor of 4, so the answer is 5."),
        Example([[1, 2], 1, 2]),
    ],
    edge_cases=[
        [[1, 2], 2, 2],
        [[1, None, 2, None, 3], 3, 2],
        [[10, 20, 30, 40, 50], 40, 50],
        [[10, 20, 30, 40, 50], 40, 30],
    ],
    generator=_lca_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Strobogrammatic Number

_ROTATE = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}


def _is_strobogrammatic(num: str) -> bool:
    lo, hi = 0, len(num) - 1
    while lo <= hi:
        if _ROTATE.get(num[lo]) != num[hi]:
            return False
        lo, hi = lo + 1, hi - 1
    return True


def _strobo_gen(rng):
    n = pick_n(rng, 1, 20, big=50)
    if rng.random() < 0.6:
        half = word(rng, n // 2, "01689")
        middle = rng.choice("018") if n % 2 else ""
        num = half + middle + "".join(_ROTATE[c] for c in reversed(half))
        if num.startswith("0") and len(num) > 1:
            num = "1" + num[1:-1] + "1"
        if rng.random() < 0.3:
            i = rng.randrange(len(num))
            num = num[:i] + rng.choice("0123456789") + num[i + 1 :]
            if num.startswith("0") and len(num) > 1:
                num = "8" + num[1:]
        return [num]
    num = word(rng, n, "0123456789")
    return [("1" + num[1:]) if num.startswith("0") and n > 1 else num]


STROBOGRAMMATIC = ProblemSource(
    title="Strobogrammatic Number",
    statement="""
A number is *strobogrammatic* if it looks exactly the same after being rotated 180 degrees (turned upside
down). Under rotation `0 -> 0`, `1 -> 1`, `8 -> 8`, `6 -> 9` and `9 -> 6`; every other digit becomes
unreadable.

Given the number as a string `num`, return `true` if it is strobogrammatic.
""",
    constraints="""
- `1 <= num.length <= 50`
- `num` contains only digits and has no leading zeros except for `"0"` itself
""",
    signature=function("isStrobogrammatic", [("num", "string")], "bool"),
    reference=_is_strobogrammatic,
    brute=lambda num: "".join(_ROTATE.get(c, "x") for c in reversed(num)) == num,
    examples=[
        Example(["69"], "Rotated, 69 still reads 69."),
        Example(["88"]),
        Example(["962"], "2 is not readable upside down."),
    ],
    edge_cases=[["0"], ["1"], ["2"], ["6"], ["818"], ["619"], ["10"], ["96"]],
    generator=_strobo_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Number of Moves to Make Palindrome


def _min_moves_palindrome(s: str) -> int:
    chars, moves = list(s), 0
    while chars:
        j = len(chars) - 1 - chars[::-1].index(chars[0])
        if j == 0:  # the unique odd character: it will end up in the middle
            moves += len(chars) // 2
        else:
            moves += len(chars) - 1 - j
            chars.pop(j)
        chars.pop(0)
    return moves


def _min_moves_brute(s: str) -> int:
    seen, frontier = {s}, deque([(s, 0)])
    while frontier:
        cur, d = frontier.popleft()
        if cur == cur[::-1]:
            return d
        for i in range(len(cur) - 1):
            nxt = cur[:i] + cur[i + 1] + cur[i] + cur[i + 2 :]
            if nxt not in seen:
                seen.add(nxt)
                frontier.append((nxt, d + 1))
    raise ValueError("no palindrome reachable")


def _palindromable_gen(rng):
    half = list(word(rng, pick_n(rng, 1, 6, big=1000), "abcd"))
    letters = half + half + ([rng.choice("abcd")] if rng.random() < 0.5 else [])
    rng.shuffle(letters)
    return ["".join(letters)]


MIN_MOVES_PALINDROME = ProblemSource(
    title="Minimum Number of Moves to Make Palindrome",
    statement="""
You are given a lowercase string `s` whose letters can be rearranged into a palindrome. In one move you
may swap two **adjacent** characters.

Return the minimum number of moves needed to turn `s` into a palindrome.
""",
    constraints="""
- `1 <= s.length <= 2000`
- `s` consists of lowercase English letters
- `s` can always be rearranged into a palindrome
""",
    signature=function("minMovesToMakePalindrome", [("s", "string")], "int"),
    reference=_min_moves_palindrome,
    brute=_min_moves_brute,
    brute_input_limit=14,
    examples=[
        Example(["aabb"], "For example aabb -> abab -> abba takes 2 moves."),
        Example(["letelt"], "One optimal sequence is letelt -> letetl -> lettel (2 moves)."),
        Example(["a"]),
    ],
    edge_cases=[["aa"], ["aba"], ["baa"], ["abab"], ["aabbc"], ["cabab"], ["abcabc"]],
    generator=_palindromable_gen,
    random_count=9,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Next Palindrome Using Same Digits


def _next_permutation_list(a: list[str]) -> bool:
    i = len(a) - 2
    while i >= 0 and a[i] >= a[i + 1]:
        i -= 1
    if i < 0:
        return False
    j = len(a) - 1
    while a[j] <= a[i]:
        j -= 1
    a[i], a[j] = a[j], a[i]
    a[i + 1 :] = reversed(a[i + 1 :])
    return True


def _next_palindrome(num: str) -> str:
    n = len(num)
    half = list(num[: n // 2])
    if not _next_permutation_list(half):
        return ""
    middle = num[n // 2] if n % 2 else ""
    return "".join(half) + middle + "".join(reversed(half))


def _next_palindrome_brute(num: str) -> str:
    candidates = {"".join(p) for p in itertools.permutations(num)}
    larger = [c for c in candidates if c == c[::-1] and c[0] != "0" and int(c) > int(num)]
    return min(larger, key=int) if larger else ""


def _numeric_palindrome_gen(rng):
    n = pick_n(rng, 1, 8, big=10**4)
    half = word(rng, n // 2, "0123456789" if rng.random() < 0.7 else "12")
    if half.startswith("0"):
        half = rng.choice("123456789") + half[1:]
    middle = rng.choice("0123456789") if n % 2 else ""
    if not half and not middle:
        middle = "7"
    return [half + middle + half[::-1]]


NEXT_PALINDROME = ProblemSource(
    title="Next Palindrome Using Same Digits",
    statement="""
You are given a very large number `num` as a string, and `num` is a palindrome. Using exactly the same
multiset of digits (reordered as you like), find the **smallest palindrome strictly greater than `num`**.

Return it as a string, or return `""` if no such palindrome exists.
""",
    constraints="""
- `1 <= num.length <= 10^4`
- `num` is a palindrome made of digits, without leading zeros
""",
    signature=function("nextPalindrome", [("num", "string")], "string"),
    reference=_next_palindrome,
    brute=_next_palindrome_brute,
    brute_input_limit=10,
    examples=[
        Example(["1221"], "Rearranging to 2112 gives the next larger palindrome."),
        Example(["32123"], "32123 is already the largest palindrome from these digits."),
        Example(["45544554"], "The next larger palindrome is 54455445."),
    ],
    edge_cases=[["1"], ["11"], ["121"], ["1001"], ["9"], ["123321"], ["12344321"]],
    generator=_numeric_palindrome_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Count Subarrays With Fixed Bounds


def _count_fixed_bounds(nums: list[int], minK: int, maxK: int) -> int:
    total, bad, last_min, last_max = 0, -1, -1, -1
    for i, x in enumerate(nums):
        if x < minK or x > maxK:
            bad = i
        if x == minK:
            last_min = i
        if x == maxK:
            last_max = i
        total += max(0, min(last_min, last_max) - bad)
    return total


def _count_fixed_bounds_brute(nums: list[int], minK: int, maxK: int) -> int:
    count = 0
    for i in range(len(nums)):
        lo = hi = nums[i]
        for j in range(i, len(nums)):
            lo, hi = min(lo, nums[j]), max(hi, nums[j])
            count += lo == minK and hi == maxK
    return count


def _fixed_bounds_gen(rng):
    n = pick_n(rng, 2, 60, big=8000)
    nums = ints(rng, n, 1, 8)
    lo = rng.randint(1, 6)
    return [nums, lo, rng.randint(lo, 8)]


COUNT_FIXED_BOUNDS = ProblemSource(
    title="Count Subarrays With Fixed Bounds",
    statement="""
You are given an integer array `nums` and two integers `minK` and `maxK`.

A contiguous subarray is *fixed-bound* when its minimum equals `minK` **and** its maximum equals `maxK`.
Return how many fixed-bound subarrays `nums` has.
""",
    constraints="""
- `2 <= nums.length <= 2 * 10^4`
- `1 <= nums[i], minK, maxK <= 10^6`
- `minK <= maxK`
""",
    signature=function("countSubarrays", [("nums", "int[]"), ("minK", "int"), ("maxK", "int")], "long"),
    reference=_count_fixed_bounds,
    brute=_count_fixed_bounds_brute,
    brute_input_limit=400,
    examples=[
        Example([[1, 3, 5, 2, 7, 5], 1, 5], "The qualifying subarrays are [1,3,5] and [1,3,5,2]."),
        Example([[1, 1, 1, 1], 1, 1], "Every one of the 10 subarrays qualifies."),
    ],
    edge_cases=[[[2, 2], 1, 2], [[1, 5], 1, 5], [[5, 1], 1, 5], [[3, 1, 3], 1, 3], [[1, 9, 1], 1, 1]],
    generator=_fixed_bounds_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Find the Lexicographically Largest String From the Box II


def _last_substring(s: str) -> str:
    i, j, k, n = 0, 1, 0, len(s)
    while j + k < n:
        if s[i + k] == s[j + k]:
            k += 1
            continue
        if s[i + k] > s[j + k]:
            j = j + k + 1
        else:
            i = max(i + k + 1, j)
            j = i + 1
        k = 0
    return s[i:]


def _largest_from_box(word_: str, numFriends: int) -> str:
    if numFriends == 1:
        return word_
    return _last_substring(word_)[: len(word_) - numFriends + 1]


def _largest_from_box_brute(word_: str, numFriends: int) -> str:
    n, best = len(word_), ""
    for cuts in itertools.combinations(range(1, n), numFriends - 1):
        bounds = (0, *cuts, n)
        best = max(best, *(word_[a:b] for a, b in itertools.pairwise(bounds)))
    return best


def _box_gen(rng):
    w = word(rng, pick_n(rng, 1, 10, big=20000), "abc" if rng.random() < 0.7 else string.ascii_lowercase)
    return [w, rng.randint(1, len(w))]


LARGEST_FROM_BOX_II = ProblemSource(
    title="Find the Lexicographically Largest String From Box II",
    statement="""
You are given a lowercase string `word` and an integer `numFriends`.

A game splits `word` into exactly `numFriends` non-empty contiguous pieces and drops every piece into a
box. The game is played once for **every** possible split (each split is used exactly once).

Return the lexicographically largest string that ends up in the box.

Can you solve it in linear time?
""",
    constraints="""
- `1 <= word.length <= 2 * 10^4`
- `word` consists of lowercase English letters
- `1 <= numFriends <= word.length`
""",
    signature=function("answerString", [("word", "string"), ("numFriends", "int")], "string"),
    reference=_largest_from_box,
    brute=_largest_from_box_brute,
    brute_input_limit=24,
    examples=[
        Example(["dbca", 2], 'Possible splits: d|bca, db|ca, dbc|a. The largest piece is "dbc".'),
        Example(["gggg", 4], 'Every split gives four "g" pieces.'),
    ],
    edge_cases=[["a", 1], ["ab", 1], ["ab", 2], ["ba", 2], ["zazb", 2], ["abcab", 3]],
    generator=_box_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Get the Maximum Score

_MOD = 10**9 + 7


def _max_score(nums1: list[int], nums2: list[int]) -> int:
    i = j = 0
    s1 = s2 = 0
    while i < len(nums1) or j < len(nums2):
        if j == len(nums2) or (i < len(nums1) and nums1[i] < nums2[j]):
            s1 += nums1[i]
            i += 1
        elif i == len(nums1) or nums1[i] > nums2[j]:
            s2 += nums2[j]
            j += 1
        else:
            s1 = s2 = max(s1, s2) + nums1[i]
            i, j = i + 1, j + 1
    return max(s1, s2) % _MOD


def _max_score_brute(nums1: list[int], nums2: list[int]) -> int:
    arrays = (nums1, nums2)
    where = [{v: k for k, v in enumerate(a)} for a in arrays]
    memo: dict[tuple[int, int], int] = {}

    def best(side: int, k: int) -> int:
        if k == len(arrays[side]):
            return 0
        if (side, k) not in memo:
            value = arrays[side][k]
            options = [best(side, k + 1)]
            other = where[1 - side].get(value)
            if other is not None:
                options.append(best(1 - side, other + 1))
            memo[(side, k)] = value + max(options)
        return memo[(side, k)]

    return max(best(0, 0), best(1, 0)) % _MOD


def _sorted_distinct(rng, n, hi):
    return sorted(rng.sample(range(1, hi + 1), n))


def _max_score_gen(rng):
    hi = 30 if rng.random() < 0.6 else 10**7
    n1, n2 = pick_n(rng, 1, 25, big=2000), pick_n(rng, 1, 25, big=2000)
    return [_sorted_distinct(rng, min(n1, hi), hi), _sorted_distinct(rng, min(n2, hi), hi)]


MAX_SCORE = ProblemSource(
    title="Get the Maximum Score",
    statement="""
You are given two **strictly increasing** arrays `nums1` and `nums2`.

A valid path starts at index 0 of either array and moves left to right. Whenever you stand on a value
that appears in **both** arrays, you may switch to the other array at that value (the shared value is
counted once). The path ends when it walks off the end of the array it is on.

The score of a path is the sum of the distinct values on it. Return the maximum score over all valid
paths, modulo `10^9 + 7`.
""",
    constraints="""
- `1 <= nums1.length, nums2.length <= 10^4`
- `1 <= nums1[i], nums2[i] <= 10^7`
- both arrays are strictly increasing
""",
    signature=function("maxSum", [("nums1", "int[]"), ("nums2", "int[]")], "int"),
    reference=_max_score,
    brute=_max_score_brute,
    examples=[
        Example([[2, 4, 5, 8, 10], [4, 6, 8, 9]], "The best path is 2, 4, 6, 8, 10 for a score of 30."),
        Example([[1, 3, 5, 7, 9], [3, 5, 100]], "Switching at 3 or 5 to reach 100 gives 109."),
        Example([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]], "No shared values, so take the larger array: 40."),
    ],
    edge_cases=[[[1], [1]], [[1], [2]], [[5, 10], [1, 5, 6]], [[10**7], [9999999, 10**7]]],
    generator=_max_score_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Create Maximum Number


def _max_subsequence(nums: list[int], k: int) -> list[int]:
    drop, stack = len(nums) - k, []
    for x in nums:
        while drop and stack and stack[-1] < x:
            stack.pop()
            drop -= 1
        stack.append(x)
    return stack[:k]


def _merge_max(a: list[int], b: list[int]) -> list[int]:
    out = []
    while a or b:
        bigger = a if a > b else b
        out.append(bigger.pop(0))
    return out


def _create_max_number(nums1: list[int], nums2: list[int], k: int) -> list[int]:
    best: list[int] = []
    for i in range(max(0, k - len(nums2)), min(k, len(nums1)) + 1):
        candidate = _merge_max(_max_subsequence(nums1, i), _max_subsequence(nums2, k - i))
        best = max(best, candidate)
    return best


def _create_max_brute(nums1: list[int], nums2: list[int], k: int) -> list[int]:
    best: list[int] = []
    for i in range(0, k + 1):
        for c1 in itertools.combinations(range(len(nums1)), i):
            for c2 in itertools.combinations(range(len(nums2)), k - i):
                a, b = [nums1[x] for x in c1], [nums2[x] for x in c2]
                for mask in itertools.combinations(range(k), i):
                    merged, ai, bi = [], 0, 0
                    for pos in range(k):
                        if pos in mask:
                            merged.append(a[ai])
                            ai += 1
                        else:
                            merged.append(b[bi])
                            bi += 1
                    best = max(best, merged)
    return best


def _create_max_gen(rng):
    small = rng.random() < 0.5
    n1 = rng.randint(1, 4) if small else pick_n(rng, 1, 60, big=400)
    n2 = rng.randint(1, 4) if small else pick_n(rng, 1, 60, big=400)
    a, b = ints(rng, n1, 0, 9), ints(rng, n2, 0, 9)
    return [a, b, rng.randint(1, n1 + n2)]


CREATE_MAX_NUMBER = ProblemSource(
    title="Create Maximum Number",
    statement="""
You are given two arrays of digits `nums1` and `nums2` (each digit is 0-9) and an integer `k`.

Build a number of exactly `k` digits by choosing digits from both arrays. The digits you take from one
array must keep their original relative order, but you may interleave the two arrays freely.

Return the largest possible number as an array of its `k` digits.
""",
    constraints="""
- `1 <= nums1.length, nums2.length <= 400`
- `0 <= nums1[i], nums2[i] <= 9`
- `1 <= k <= nums1.length + nums2.length`
""",
    signature=function("maxNumber", [("nums1", "int[]"), ("nums2", "int[]"), ("k", "int")], "int[]"),
    reference=_create_max_number,
    brute=_create_max_brute,
    brute_input_limit=40,
    examples=[
        Example([[3, 4, 6, 5], [9, 1, 2, 5, 8, 3], 5], "The best 5-digit number is 98653."),
        Example([[6, 7], [6, 0, 4], 5], "All digits are used: 67604."),
        Example([[3, 9], [8, 9], 3], "The best is 989."),
    ],
    edge_cases=[[[1], [2], 1], [[1], [2], 2], [[0, 0], [0], 2], [[2, 5, 6, 4, 4, 0], [7, 3, 8, 0, 6, 5, 7, 6, 2], 15]],
    generator=_create_max_gen,
    random_count=8,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Append Characters to String to Make Subsequence


def _append_characters(s: str, t: str) -> int:
    j = 0
    for c in s:
        if j < len(t) and c == t[j]:
            j += 1
    return len(t) - j


def _append_brute(s: str, t: str) -> int:
    def is_subsequence(a: str, b: str) -> bool:
        it = iter(b)
        return all(c in it for c in a)

    return next(len(t) - k for k in range(len(t), -1, -1) if is_subsequence(t[:k], s))


APPEND_CHARACTERS = ProblemSource(
    title="Append Characters to String to Make Subsequence",
    statement="""
You are given two lowercase strings `s` and `t`. Return the minimum number of characters that must be
appended to the **end** of `s` so that `t` becomes a subsequence of `s`.

A subsequence keeps the relative order of characters but may skip some of them.
""",
    constraints="""
- `1 <= s.length, t.length <= 10^5`
- `s` and `t` consist of lowercase English letters
""",
    signature=function("appendCharacters", [("s", "string"), ("t", "string")], "int"),
    reference=_append_characters,
    brute=_append_brute,
    examples=[
        Example(["coaching", "coding"], '"co" ... "d" is missing, so append "ding" (4 characters).'),
        Example(["abcde", "a"], "t is already a subsequence."),
        Example(["z", "abcde"], "None of t can be matched, so all 5 characters are needed."),
    ],
    edge_cases=[["a", "a"], ["a", "b"], ["ab", "ba"], ["aaa", "aaaa"], ["abc", "abc"]],
    generator=lambda rng: [
        word(rng, pick_n(rng, 1, 40, big=12000), "abc"),
        word(rng, pick_n(rng, 1, 40, big=12000), "abc"),
    ],
    random_count=8,
)


# ---------------------------------------------------------------- Squares of a Sorted Array


def _sorted_squares(nums: list[int]) -> list[int]:
    out = [0] * len(nums)
    lo, hi = 0, len(nums) - 1
    for k in range(len(nums) - 1, -1, -1):
        if abs(nums[lo]) > abs(nums[hi]):
            out[k] = nums[lo] ** 2
            lo += 1
        else:
            out[k] = nums[hi] ** 2
            hi -= 1
    return out


SQUARES_SORTED = ProblemSource(
    title="Squares of a Sorted Array",
    statement="""
You are given an integer array `nums` sorted in non-decreasing order. Return an array of the squares of
each number, also sorted in non-decreasing order.

Sorting the squares works, but can you do it in `O(n)` time?
""",
    constraints="""
- `1 <= nums.length <= 10^4`
- `-10^4 <= nums[i] <= 10^4`
- `nums` is sorted in non-decreasing order
""",
    signature=function("sortedSquares", [("nums", "int[]")], "int[]"),
    reference=_sorted_squares,
    brute=lambda nums: sorted(x * x for x in nums),
    examples=[
        Example([[-4, -1, 0, 3, 10]], "Squares are 16, 1, 0, 9, 100; sorted: 0, 1, 9, 16, 100."),
        Example([[-7, -3, 2, 3, 11]]),
    ],
    edge_cases=[[[0]], [[-5]], [[-3, -2, -1]], [[1, 2, 3]], [[-10000, 10000]]],
    generator=lambda rng: [sorted(ints(rng, pick_n(rng, 1, 50, big=3000), -(10**4), 10**4))],
    random_count=8,
)


# ---------------------------------------------------------------- Reverse String


def _reverse_string(s: list[str]) -> None:
    lo, hi = 0, len(s) - 1
    while lo < hi:
        s[lo], s[hi] = s[hi], s[lo]
        lo, hi = lo + 1, hi - 1


REVERSE_STRING = ProblemSource(
    title="Reverse String",
    statement="""
You are given a string as an array of characters `s`. Reverse it **in place**, using only `O(1)` extra memory.
""",
    constraints="""
- `1 <= s.length <= 10^5`
- `s[i]` is a printable ASCII character
""",
    signature=function("reverseString", [("s", "char[]")], "void", mutates="s"),
    reference=_reverse_string,
    brute=lambda s: s.reverse(),
    examples=[Example([["h", "e", "l", "l", "o"]]), Example([["H", "a", "n", "n", "a", "h"]])],
    edge_cases=[[["a"]], [["a", "b"]], [["!", " ", "?"]]],
    generator=lambda rng: [list(word(rng, pick_n(rng, 1, 40, big=4000), string.ascii_letters + string.digits + " .,"))],
    random_count=7,
)


PROBLEMS = [
    THREE_SUM,
    REMOVE_NTH,
    SORT_COLORS,
    REVERSE_WORDS,
    VALID_PALINDROME,
    VALID_WORD_ABBREVIATION,
    VALID_PALINDROME_II,
    LCA_III,
    STROBOGRAMMATIC,
    MIN_MOVES_PALINDROME,
    NEXT_PALINDROME,
    COUNT_FIXED_BOUNDS,
    LARGEST_FROM_BOX_II,
    MAX_SCORE,
    CREATE_MAX_NUMBER,
    APPEND_CHARACTERS,
    SQUARES_SORTED,
    REVERSE_STRING,
]
