"""Pattern 24: Knowing What to Track (part 1 of 2). Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import math
import random
from collections import Counter, defaultdict

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ints, ops, pick_n, sample, word

PATTERN_NUMBER = 24
_MOD = 10**9 + 7


def _shuffled(rng: random.Random, text: str) -> str:
    return "".join(sample(rng, list(text), len(text)))


# ---------------------------------------------------------------- Valid Anagram


def _is_anagram(s: str, t: str) -> bool:
    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - 97] += 1
    for ch in t:
        counts[ord(ch) - 97] -= 1
    return not any(counts)


def _anagram_pair_gen(rng: random.Random) -> list:
    s = word(rng, rng.randint(1, rng.choice([8, 500])), rng.choice(["ab", "abcdefghijklmnopqrstuvwxyz"]))
    t = _shuffled(rng, s)
    if rng.random() < 0.5:
        i = rng.randrange(len(t))
        t = t[:i] + rng.choice("abz") + t[i + 1 :] if rng.random() < 0.7 else t + "a"
    return [s, t]


VALID_ANAGRAM = ProblemSource(
    title="Valid Anagram",
    statement="""
Return `true` if `t` is an anagram of `s`: it uses exactly the same letters, the same number of times, in any order.
""",
    constraints="""
- `1 <= s.length, t.length <= 5 * 10^4`
- lowercase English letters
""",
    signature=function("isAnagram", [("s", "string"), ("t", "string")], "bool"),
    reference=_is_anagram,
    brute=lambda s, t: sorted(s) == sorted(t),
    examples=[Example(["anagram", "nagaram"]), Example(["rat", "car"])],
    edge_cases=[["a", "a"], ["a", "ab"], ["ab", "ba"], ["aab", "abb"]],
    generator=_anagram_pair_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Group Anagrams


def _group_anagrams(strs: list[str]) -> list[list[str]]:
    groups: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for s in strs:
        key = [0] * 26
        for ch in s:
            key[ord(ch) - 97] += 1
        groups[tuple(key)].append(s)
    return list(groups.values())


def _group_brute(strs: list[str]) -> list[list[str]]:
    out: list[list[str]] = []
    for s in strs:
        for group in out:
            if sorted(group[0]) == sorted(s):
                group.append(s)
                break
        else:
            out.append([s])
    return out


def _group_gen(rng: random.Random) -> list:
    stems = [word(rng, rng.randint(0, 4), "abc") for _ in range(rng.randint(1, 5))]
    return [[_shuffled(rng, rng.choice(stems)) for _ in range(rng.randint(1, rng.choice([8, 100])))]]


GROUP_ANAGRAMS = ProblemSource(
    title="Group Anagrams",
    statement="""
Group the strings of `strs` so that anagrams of each other are in the same group. Return the groups in any order; the strings within a group
may also be in any order. Duplicate strings stay as separate entries.
""",
    constraints="""
- `1 <= strs.length <= 10^4`
- `0 <= strs[i].length <= 100`, lowercase letters
""",
    signature=function("groupAnagrams", [("strs", "string[]")], "string[][]"),
    reference=_group_anagrams,
    brute=_group_brute,
    brute_input_limit=3000,
    compare="unordered_nested",
    examples=[Example([["eat", "tea", "tan", "ate", "nat", "bat"]], "[[\"bat\"],[\"nat\",\"tan\"],[\"ate\",\"eat\",\"tea\"]]."), Example([[""]]), Example([["a"]])],
    edge_cases=[[["", ""]], [["ab", "ba", "ab"]], [["a", "b"]]],
    generator=_group_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Palindrome Permutation


def _can_permute_palindrome(s: str) -> bool:
    odd = 0
    for count in Counter(s).values():
        odd += count % 2
    return odd <= 1


def _permute_brute(s: str) -> bool:
    if len(s) > 8:
        return NotImplemented
    return any(p == p[::-1] for p in itertools.permutations(s))


PALINDROME_PERMUTATION = ProblemSource(
    title="Palindrome Permutation",
    statement="""
Return `true` if some rearrangement of the letters of `s` is a palindrome.
""",
    constraints="""
- `1 <= s.length <= 5000`
- lowercase English letters
""",
    signature=function("canPermutePalindrome", [("s", "string")], "bool"),
    reference=_can_permute_palindrome,
    brute=_permute_brute,
    examples=[Example(["code"]), Example(["aab"], "\"aba\"."), Example(["carerac"])],
    edge_cases=[["a"], ["ab"], ["aabb"], ["abcabcd"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([8, 5000])), rng.choice(["ab", "abc", "abcdefg"]))],
    random_count=10,
)


# ---------------------------------------------------------------- Design Tic-Tac-Toe


class _TicTacToe:
    def __init__(self, n: int) -> None:
        self.n = n
        self.rows = [0] * n
        self.cols = [0] * n
        self.diagonal = self.anti = 0

    def move(self, row: int, col: int, player: int) -> int:
        delta = 1 if player == 1 else -1
        self.rows[row] += delta
        self.cols[col] += delta
        if row == col:
            self.diagonal += delta
        if row + col == self.n - 1:
            self.anti += delta
        if self.n in (abs(self.rows[row]), abs(self.cols[col]), abs(self.diagonal), abs(self.anti)):
            return player
        return 0


class _TicTacToeBrute:
    def __init__(self, n: int) -> None:
        self.n = n
        self.board = [[0] * n for _ in range(n)]

    def move(self, row: int, col: int, player: int) -> int:
        self.board[row][col] = player
        n, b = self.n, self.board
        lines = [b[row], [b[i][col] for i in range(n)], [b[i][i] for i in range(n)], [b[i][n - 1 - i] for i in range(n)]]
        return player if any(all(v == player for v in line) for line in lines) else 0


def _tictactoe_gen(rng: random.Random) -> dict:
    n = rng.randint(1, rng.choice([3, 6]))
    cells = sample(rng, [(i, j) for i in range(n) for j in range(n)], n * n)
    calls: list[tuple[str, list]] = [("TicTacToe", [n])]
    board: dict[tuple[int, int], int] = {}
    for k, (i, j) in enumerate(cells):
        player = 1 + k % 2
        calls.append(("move", [i, j, player]))
        board[(i, j)] = player
        if _wins(board, n, i, j, player):
            break  # no moves after a win
    return ops(*calls)


def _wins(board: dict[tuple[int, int], int], n: int, i: int, j: int, player: int) -> bool:
    lines = [[(i, c) for c in range(n)], [(r, j) for r in range(n)], [(d, d) for d in range(n)], [(d, n - 1 - d) for d in range(n)]]
    return any(all(board.get(cell) == player for cell in line) for line in lines)


TIC_TAC_TOE = ProblemSource(
    title="Design Tic-Tac-Toe",
    statement="""
Design an `n x n` tic-tac-toe game between players `1` and `2`. Moves are always valid (on an empty cell), and no moves are made after someone
wins. A player wins by filling an entire row, column, or either diagonal.

- `TicTacToe(n)` creates the board.
- `move(row, col, player)` places `player`'s mark and returns `player` if that move wins, otherwise `0`.

Aim for `O(1)` per move.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor).
""",
    constraints="""
- `1 <= n <= 100`
- `player` is `1` or `2`; at most `n^2` calls
""",
    signature=design("TicTacToe", [("n", "int")], [("move", [("row", "int"), ("col", "int"), ("player", "int")], "int")]),
    reference=_TicTacToe,
    brute=_TicTacToeBrute,
    examples=[
        Example(ops(("TicTacToe", [3]), ("move", [0, 0, 1]), ("move", [0, 2, 2]), ("move", [2, 2, 1]), ("move", [1, 1, 2]), ("move", [2, 0, 1]), ("move", [1, 0, 2]), ("move", [2, 1, 1])), "Player 1 completes the bottom row."),
        Example(ops(("TicTacToe", [2]), ("move", [0, 1, 1]), ("move", [0, 0, 2]), ("move", [1, 0, 1])), "Player 1 completes the anti-diagonal."),
    ],
    edge_cases=[ops(("TicTacToe", [1]), ("move", [0, 0, 2]))],
    generator=_tictactoe_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Frequency Stack


class _FreqStack:
    def __init__(self) -> None:
        self.freq: Counter[int] = Counter()
        self.stacks: dict[int, list[int]] = defaultdict(list)  # frequency -> values pushed at that frequency
        self.top = 0

    def push(self, val: int) -> None:
        self.freq[val] += 1
        f = self.freq[val]
        self.stacks[f].append(val)
        self.top = max(self.top, f)

    def pop(self) -> int:
        val = self.stacks[self.top].pop()
        self.freq[val] -= 1
        if not self.stacks[self.top]:
            self.top -= 1
        return val


class _FreqStackBrute:
    def __init__(self) -> None:
        self.items: list[int] = []

    def push(self, val: int) -> None:
        self.items.append(val)

    def pop(self) -> int:
        counts = Counter(self.items)
        best = max(counts.values())
        index = max(i for i, v in enumerate(self.items) if counts[v] == best)
        return self.items.pop(index)


def _freq_gen(rng: random.Random) -> dict:
    calls: list[tuple[str, list]] = [("FreqStack", [])]
    size = 0
    for _ in range(pick_n(rng, 1, 25, big=300)):
        if size and rng.random() < 0.4:
            calls.append(("pop", []))
            size -= 1
        else:
            calls.append(("push", [rng.randint(0, rng.choice([3, 10**9]))]))
            size += 1
    return ops(*calls)


MAX_FREQ_STACK = ProblemSource(
    title="Maximum Frequency Stack",
    statement="""
Design a stack-like structure that pops the most frequent element:
- `push(val)` pushes `val`.
- `pop()` removes and returns the most frequent element; if several are tied, it removes the one pushed most recently among them.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor
and `push`). `pop` is only called when the stack is non-empty.
""",
    constraints="""
- `0 <= val <= 10^9`
- at most `2 * 10^4` calls
""",
    signature=design("FreqStack", [], [("push", [("val", "int")], "void"), ("pop", [], "int")]),
    reference=_FreqStack,
    brute=_FreqStackBrute,
    examples=[
        Example(ops(("FreqStack", []), ("push", [5]), ("push", [7]), ("push", [5]), ("push", [7]), ("push", [4]), ("push", [5]), ("pop", []), ("pop", []), ("pop", []), ("pop", [])), "Pops 5, 7, 5, 4."),
        Example(ops(("FreqStack", []), ("push", [1]), ("pop", []))),
    ],
    edge_cases=[ops(("FreqStack", []), ("push", [2]), ("push", [1]), ("pop", []), ("pop", []))],
    generator=_freq_gen,
    random_count=8,
)


# ---------------------------------------------------------------- First Unique Character in a String


def _first_uniq_char(s: str) -> int:
    counts = Counter(s)
    return next((i for i, ch in enumerate(s) if counts[ch] == 1), -1)


FIRST_UNIQUE_CHAR = ProblemSource(
    title="First Unique Character in a String",
    statement="""
Return the index of the first character in `s` that occurs exactly once, or `-1` if there is none.
""",
    constraints="""
- `1 <= s.length <= 10^5`
- lowercase English letters
""",
    signature=function("firstUniqChar", [("s", "string")], "int"),
    reference=_first_uniq_char,
    brute=lambda s: next((i for i, ch in enumerate(s) if s.count(ch) == 1), -1),
    brute_input_limit=3000,
    examples=[Example(["leetcode"]), Example(["loveleetcode"]), Example(["aabb"])],
    edge_cases=[["z"], ["zz"], ["abab" * 3 + "c"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([10, 1000])), rng.choice(["abc", "abcdefghij"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Find All Anagrams in a String


def _find_anagrams(s: str, p: str) -> list[int]:
    need = Counter(p)
    window: Counter[str] = Counter()
    out = []
    for i, ch in enumerate(s):
        window[ch] += 1
        if i >= len(p):
            window[s[i - len(p)]] -= 1
        if window == need:
            out.append(i - len(p) + 1)
    return out


FIND_ALL_ANAGRAMS = ProblemSource(
    title="Find All Anagrams in a String",
    statement="""
Return the start indices of every substring of `s` that is an anagram of `p`, in any order.
""",
    constraints="""
- `1 <= s.length, p.length <= 3 * 10^4`
- lowercase English letters
""",
    signature=function("findAnagrams", [("s", "string"), ("p", "string")], "int[]"),
    reference=_find_anagrams,
    brute=lambda s, p: [i for i in range(len(s) - len(p) + 1) if sorted(s[i : i + len(p)]) == sorted(p)],
    brute_input_limit=3000,
    compare="unordered",
    examples=[Example(["cbaebabacd", "abc"], "\"cba\" at 0 and \"bac\" at 6."), Example(["abab", "ab"])],
    edge_cases=[["a", "a"], ["a", "ab"], ["aaaa", "aa"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([20, 1000])), "abc"), word(rng, rng.randint(1, 4), "abc")],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Palindrome by Concatenating Two-Letter Words


def _longest_palindrome_words(words: list[str]) -> int:
    counts = Counter(words)
    length, center = 0, False
    for w, c in counts.items():
        if w[0] == w[1]:
            length += 4 * (c // 2)
            center = center or c % 2 == 1
        elif w < w[::-1]:
            length += 4 * min(c, counts[w[::-1]])
    return length + (2 if center else 0)


def _palindrome_words_brute(words: list[str]) -> int:
    if len(words) > 7:
        return NotImplemented
    best = 0
    for r in range(len(words) + 1):
        for combo in itertools.permutations(words, r):
            text = "".join(combo)
            if text == text[::-1]:
                best = max(best, len(text))
    return best


PALINDROME_TWO_LETTERS = ProblemSource(
    title="Longest Palindrome by Concatenating Two-Letter Words",
    statement="""
Every string in `words` has exactly two letters. Pick some of them (each element at most once), arrange them in any order, and concatenate them
into a palindrome. Return the length of the longest palindrome you can build (`0` if none).
""",
    constraints="""
- `1 <= words.length <= 10^5`
- `words[i].length == 2`, lowercase letters
""",
    signature=function("longestPalindrome", [("words", "string[]")], "int"),
    reference=_longest_palindrome_words,
    brute=_palindrome_words_brute,
    examples=[Example([["lc", "cl", "gg"]], "\"lcggcl\"."), Example([["ab", "ty", "yt", "lc", "cl", "ab"]]), Example([["cc", "ll", "xx"]], "Only one doubled word fits in the middle.")],
    edge_cases=[[["ab"]], [["aa"]], [["aa", "aa", "aa"]], [["ab", "ba", "ba"]]],
    generator=lambda rng: [[word(rng, 2, rng.choice(["ab", "abc"])) for _ in range(rng.randint(1, rng.choice([7, 3000])))]],
    random_count=10,
)


# ---------------------------------------------------------------- Ransom Note


def _can_construct(ransomNote: str, magazine: str) -> bool:
    return not Counter(ransomNote) - Counter(magazine)


def _ransom_brute(ransomNote: str, magazine: str) -> bool:
    letters = list(magazine)
    for ch in ransomNote:
        if ch not in letters:
            return False
        letters.remove(ch)
    return True


RANSOM_NOTE = ProblemSource(
    title="Ransom Note",
    statement="""
Return `true` if `ransomNote` can be built from the letters of `magazine`, using each letter of `magazine` at most once.
""",
    constraints="""
- `1 <= ransomNote.length, magazine.length <= 10^5`
- lowercase English letters
""",
    signature=function("canConstruct", [("ransomNote", "string"), ("magazine", "string")], "bool"),
    reference=_can_construct,
    brute=_ransom_brute,
    brute_input_limit=3000,
    examples=[Example(["a", "b"]), Example(["aa", "ab"]), Example(["aa", "aab"])],
    edge_cases=[["abc", "cba"], ["z", "zzz"]],
    generator=lambda rng: [word(rng, rng.randint(1, 10), "abc"), word(rng, rng.randint(1, rng.choice([10, 500])), "abc")],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Number of Pushes to Type Word II


def _minimum_pushes(word_: str) -> int:
    counts = sorted(Counter(word_).values(), reverse=True)
    return sum(c * (i // 8 + 1) for i, c in enumerate(counts))


def _pushes_brute(word_: str) -> int:
    """Try every choice of which letters take the 8 single-push slots (up to 16 distinct letters)."""
    letters = sorted(set(word_))
    if len(letters) > 16:
        return NotImplemented
    counts = Counter(word_)
    best = None
    for first in itertools.combinations(letters, min(8, len(letters))):
        cost = sum(counts[ch] * (1 if ch in first else 2) for ch in letters)
        best = cost if best is None else min(best, cost)
    return best


MIN_PUSHES = ProblemSource(
    title="Minimum Number of Pushes to Type Word II",
    statement="""
A phone keypad has 8 keys (2 to 9). You may map each lowercase letter to exactly one key, any number of letters per key; typing the `k`-th letter
on a key takes `k` pushes. Choose the mapping that minimises the total pushes needed to type `word`, and return that minimum.
""",
    constraints="""
- `1 <= word.length <= 10^5`
- lowercase English letters
""",
    signature=function("minimumPushes", [("word", "string")], "int"),
    reference=_minimum_pushes,
    brute=_pushes_brute,
    examples=[Example(["abcde"], "Each letter gets its own key: 5."), Example(["xyzxyzxyzxyz"]), Example(["aabbccddeeffgghhiiiiii"], "The 9th letter needs a second push on some key.")],
    edge_cases=[["a"], ["abcdefghi"], ["abcdefghijklmnopqrstuvwxyz"]],
    generator=lambda rng: [word(rng, rng.randint(1, rng.choice([20, 2000])), "abcdefghijklmnop"[: rng.randint(1, 16)] if rng.random() < 0.6 else "abcdefghijklmnopqrstuvwxyz")],
    random_count=8,
)


# ---------------------------------------------------------------- Rank Teams by Votes


def _rank_teams(votes: list[str]) -> str:
    n = len(votes[0])
    tally = {team: [0] * n for team in votes[0]}
    for vote in votes:
        for position, team in enumerate(vote):
            tally[team][position] -= 1  # negative so that more votes sort first
    return "".join(sorted(votes[0], key=lambda t: (tally[t], t)))


def _rank_brute(votes: list[str]) -> str:
    teams = list(votes[0])

    def before(a: str, b: str) -> bool:
        for position in range(len(teams)):
            ca = sum(v[position] == a for v in votes)
            cb = sum(v[position] == b for v in votes)
            if ca != cb:
                return ca > cb
        return a < b

    ordered: list[str] = []
    for team in teams:  # insertion sort with the pairwise rule
        i = 0
        while i < len(ordered) and before(ordered[i], team):
            i += 1
        ordered.insert(i, team)
    return "".join(ordered)


def _votes_gen(rng: random.Random) -> list:
    teams = "".join(sample(rng, list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), rng.randint(1, rng.choice([4, 26]))))
    return [[_shuffled(rng, teams) for _ in range(rng.randint(1, rng.choice([5, 1000])))]]


RANK_TEAMS = ProblemSource(
    title="Rank Teams by Votes",
    statement="""
Each voter ranks every team (a string of distinct uppercase letters, first = best). Order teams by the number of first-place votes; break ties
using second-place votes, then third, and so on. If teams are still tied after all positions, order them alphabetically. Return the final
ranking as a string.
""",
    constraints="""
- `1 <= votes.length <= 1000`, `1 <= votes[i].length <= 26`
- every vote ranks the same set of teams
""",
    signature=function("rankTeams", [("votes", "string[]")], "string"),
    reference=_rank_teams,
    brute=_rank_brute,
    brute_input_limit=4000,
    examples=[Example([["ABC", "ACB", "ABC", "ACB", "ACB"]], "A wins first place; C beats B on second places."), Example([["WXYZ", "XYZW"]]), Example([["ZMNAGUEDSJYLBOPHRQICWFXTVK"]])],
    edge_cases=[[["A"]], [["BCA", "CAB", "ABC"]]],
    generator=_votes_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Pairs of Songs With Total Durations Divisible by 60


def _num_pairs_divisible_by_60(time: list[int]) -> int:
    seen = [0] * 60
    count = 0
    for t in time:
        count += seen[(60 - t % 60) % 60]
        seen[t % 60] += 1
    return count


SONG_PAIRS = ProblemSource(
    title="Pairs of Songs With Total Durations Divisible by 60",
    statement="""
`time[i]` is the length of song `i` in seconds. Return the number of index pairs `i < j` whose total duration is divisible by `60`.
""",
    constraints="""
- `1 <= time.length <= 6 * 10^4`
- `1 <= time[i] <= 500`
""",
    signature=function("numPairsDivisibleBy60", [("time", "int[]")], "int"),
    reference=_num_pairs_divisible_by_60,
    brute=lambda time: sum((a + b) % 60 == 0 for a, b in itertools.combinations(time, 2)) if len(time) <= 400 else NotImplemented,
    examples=[Example([[30, 20, 150, 100, 40]], "(30,150), (20,100), (20,40)."), Example([[60, 60, 60]])],
    edge_cases=[[[1]], [[30, 30]], [[59, 1, 61]]],
    generator=lambda rng: [[rng.choice([30, 60, 90, rng.randint(1, 500)]) for _ in range(pick_n(rng, 1, 25, big=6000))]],
    random_count=8,
)


# ---------------------------------------------------------------- Count Anagrams


def _count_anagrams(s: str) -> int:
    total = 1
    for w in s.split(" "):
        ways = math.factorial(len(w))
        for c in Counter(w).values():
            ways //= math.factorial(c)
        total = total * ways % _MOD
    return total


def _count_anagrams_brute(s: str) -> int:
    words = s.split(" ")
    if any(len(w) > 7 for w in words):
        return NotImplemented
    return math.prod(len(set(itertools.permutations(w))) for w in words) % _MOD


COUNT_ANAGRAMS = ProblemSource(
    title="Count Anagrams",
    statement="""
`s` contains one or more words separated by single spaces. Another string is an *anagram* of `s` if its `i`-th word is a permutation of the
`i`-th word of `s` for every `i`. Return the number of distinct anagrams of `s` (including `s` itself), modulo `10^9 + 7`.
""",
    constraints="""
- `1 <= s.length <= 10^5`
- lowercase letters and single spaces, no leading or trailing space
""",
    signature=function("countAnagrams", [("s", "string")], "int"),
    reference=_count_anagrams,
    brute=_count_anagrams_brute,
    examples=[Example(["too hot"], "3 arrangements of \"too\" times 6 of \"hot\": 18."), Example(["aa"])],
    edge_cases=[["a"], ["ab ba"], ["abcdefghijklmnopqrstuvwxyz"]],
    generator=lambda rng: [" ".join(word(rng, rng.randint(1, rng.choice([7, 30])), rng.choice(["ab", "abcd", "abcdefgh"])) for _ in range(rng.randint(1, 6)))],
    random_count=8,
)


# ---------------------------------------------------------------- Divide Array Into Increasing Sequences


def _can_divide(nums: list[int], k: int) -> bool:
    most = max(Counter(nums).values())
    return most * k <= len(nums)


def _divide_brute(nums: list[int], k: int) -> bool:
    """Greedy deal: the i-th element goes to sequence i mod groups, where groups = the largest multiplicity."""
    groups = max(Counter(nums).values())
    sequences: list[list[int]] = [[] for _ in range(groups)]
    for i, x in enumerate(nums):
        sequences[i % groups].append(x)
    return all(len(seq) >= k and all(a < b for a, b in itertools.pairwise(seq)) for seq in sequences)


DIVIDE_INCREASING = ProblemSource(
    title="Divide Array Into Increasing Sequences",
    statement="""
`nums` is sorted in non-decreasing order. Return `true` if it can be divided into one or more disjoint **strictly increasing** subsequences, each
of length at least `k`.
""",
    constraints="""
- `1 <= k <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^5`, sorted non-decreasing
""",
    signature=function("canDivideIntoSubsequences", [("nums", "int[]"), ("k", "int")], "bool"),
    reference=_can_divide,
    brute=_divide_brute,
    brute_input_limit=5000,
    examples=[Example([[1, 2, 2, 3, 3, 4, 4], 3], "[1,2,3,4] and [2,3,4]."), Example([[5, 6, 6, 7, 8], 3])],
    edge_cases=[[[1], 1], [[1, 1], 1], [[1, 1], 2]],
    generator=lambda rng: [(v := sorted(ints(rng, pick_n(rng, 1, 20, big=3000), 1, rng.choice([5, 10**5])))), rng.randint(1, max(1, len(v) // rng.choice([1, 2, 3])))],
    random_count=10,
)


# ---------------------------------------------------------------- Max Consecutive Ones


def _find_max_consecutive_ones(nums: list[int]) -> int:
    best = run = 0
    for x in nums:
        run = run + 1 if x else 0
        best = max(best, run)
    return best


MAX_CONSECUTIVE_ONES = ProblemSource(
    title="Max Consecutive Ones",
    statement="""
`nums` is a binary array. Return the length of the longest run of consecutive `1`s.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `nums[i]` is `0` or `1`
""",
    signature=function("findMaxConsecutiveOnes", [("nums", "int[]")], "int"),
    reference=_find_max_consecutive_ones,
    brute=lambda nums: max((len(run) for run in "".join(map(str, nums)).split("0")), default=0),
    examples=[Example([[1, 1, 0, 1, 1, 1]]), Example([[1, 0, 1, 1, 0, 1]])],
    edge_cases=[[[0]], [[1]], [[0, 0]]],
    generator=lambda rng: [[int(rng.random() < p) for _ in range(pick_n(rng, 1, 30, big=10**4))] for p in [rng.choice([0.5, 0.85])]],
    random_count=8,
)


# ---------------------------------------------------------------- Count and Say


def _count_and_say(n: int) -> str:
    term = "1"
    for _ in range(n - 1):
        term = "".join(f"{len(list(group))}{digit}" for digit, group in itertools.groupby(term))
    return term


def _count_and_say_brute(n: int) -> str:
    term = "1"
    for _ in range(n - 1):
        out, i = "", 0
        while i < len(term):
            j = i
            while j < len(term) and term[j] == term[i]:
                j += 1
            out += str(j - i) + term[i]
            i = j
        term = out
    return term


COUNT_AND_SAY = ProblemSource(
    title="Count and Say",
    statement="""
The *count-and-say* sequence starts with `"1"`. Each next term reads the previous one aloud, group by group of equal digits: `"1"` is one 1 →
`"11"`, which is two 1s → `"21"`, which is one 2, one 1 → `"1211"`, and so on. Return the `n`-th term.
""",
    constraints="""
- `1 <= n <= 30`
""",
    signature=function("countAndSay", [("n", "int")], "string"),
    reference=_count_and_say,
    brute=_count_and_say_brute,
    examples=[Example([4], "1, 11, 21, 1211."), Example([1])],
    edge_cases=[[2], [30]],
    generator=lambda rng: [rng.randint(1, 30)],
    random_count=6,
)


PROBLEMS = [
    VALID_ANAGRAM,
    GROUP_ANAGRAMS,
    PALINDROME_PERMUTATION,
    TIC_TAC_TOE,
    MAX_FREQ_STACK,
    FIRST_UNIQUE_CHAR,
    FIND_ALL_ANAGRAMS,
    PALINDROME_TWO_LETTERS,
    RANSOM_NOTE,
    MIN_PUSHES,
    RANK_TEAMS,
    SONG_PAIRS,
    COUNT_ANAGRAMS,
    DIVIDE_INCREASING,
    MAX_CONSECUTIVE_ONES,
    COUNT_AND_SAY,
]
