"""Pattern 22: Trie. Original statements; outputs come from `reference`."""

from __future__ import annotations

import bisect
import itertools
import random
import re
from collections import Counter

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ops, pick_n, word

PATTERN_NUMBER = 22


def _insert(root: dict, text: str, payload: object = True) -> dict:
    node = root
    for ch in text:
        node = node.setdefault(ch, {})
    node["$"] = payload
    return node


def _vocabulary(rng: random.Random, count: int, alphabet: str, max_len: int) -> list[str]:
    """Words that often share prefixes: each new word extends or trims an earlier one."""
    words: list[str] = []
    for _ in range(count):
        if words and rng.random() < 0.6:
            base = rng.choice(words)
            words.append(base[: rng.randint(0, len(base))] + word(rng, rng.randint(0, 3), alphabet) or base)
        else:
            words.append(word(rng, rng.randint(1, max_len), alphabet))
    return [w for w in words if w]


# ---------------------------------------------------------------- Implement Trie


class _Trie:
    def __init__(self) -> None:
        self.root: dict = {}

    def insert(self, word: str) -> None:
        _insert(self.root, word)

    def _walk(self, text: str) -> dict | None:
        node = self.root
        for ch in text:
            if ch not in node:
                return None
            node = node[ch]
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and "$" in node

    def startsWith(self, prefix: str) -> bool:  # noqa: N802 - judge method name
        return self._walk(prefix) is not None


class _TrieBrute:
    def __init__(self) -> None:
        self.words: set[str] = set()

    def insert(self, word: str) -> None:
        self.words.add(word)

    def search(self, word: str) -> bool:
        return word in self.words

    def startsWith(self, prefix: str) -> bool:  # noqa: N802
        return any(w.startswith(prefix) for w in self.words)


def _trie_ops_gen(rng: random.Random) -> dict:
    alphabet = "abc" if rng.random() < 0.7 else "abcdefghijklmnopqrstuvwxyz"
    pool = _vocabulary(rng, 12, alphabet, 5)
    calls: list[tuple[str, list]] = [("Trie", [])]
    for _ in range(pick_n(rng, 1, 20, big=300)):
        op = rng.choice(["insert", "insert", "search", "startsWith"])
        text = rng.choice(pool) if rng.random() < 0.7 else word(rng, rng.randint(1, 5), alphabet)
        calls.append((op, [text[: rng.randint(1, len(text))] if op == "startsWith" else text]))
    return ops(*calls)


IMPLEMENT_TRIE = ProblemSource(
    title="Implement Trie",
    statement="""
Implement a trie (prefix tree) for lowercase words:
- `insert(word)` adds `word`.
- `search(word)` returns `true` if `word` was inserted before.
- `startsWith(prefix)` returns `true` if some inserted word starts with `prefix`.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor
and `insert`).
""",
    constraints="""
- `1 <= word.length, prefix.length <= 2000`, lowercase English letters
- at most `3 * 10^4` calls in total
""",
    signature=design("Trie", [], [("insert", [("word", "string")], "void"), ("search", [("word", "string")], "bool"), ("startsWith", [("prefix", "string")], "bool")]),
    reference=_Trie,
    brute=_TrieBrute,
    examples=[
        Example(ops(("Trie", []), ("insert", ["apple"]), ("search", ["apple"]), ("search", ["app"]), ("startsWith", ["app"]), ("insert", ["app"]), ("search", ["app"])), "\"app\" is only a word after it is inserted."),
        Example(ops(("Trie", []), ("insert", ["abc"]), ("startsWith", ["abcd"]), ("search", ["ab"]))),
    ],
    edge_cases=[ops(("Trie", []), ("search", ["a"]), ("startsWith", ["a"]), ("insert", ["a"]), ("search", ["a"]), ("startsWith", ["ab"]))],
    generator=_trie_ops_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Design Add and Search Words Data Structure


class _WordDictionary:
    def __init__(self) -> None:
        self.root: dict = {}

    def addWord(self, word: str) -> None:  # noqa: N802
        _insert(self.root, word)

    def search(self, word: str) -> bool:
        def match(node: dict, i: int) -> bool:
            if i == len(word):
                return "$" in node
            if word[i] == ".":
                return any(match(child, i + 1) for key, child in node.items() if key != "$")
            return word[i] in node and match(node[word[i]], i + 1)

        return match(self.root, 0)


class _WordDictionaryBrute:
    def __init__(self) -> None:
        self.words: set[str] = set()

    def addWord(self, word: str) -> None:  # noqa: N802
        self.words.add(word)

    def search(self, word: str) -> bool:
        pattern = re.compile(word.replace(".", "[a-z]"))
        return any(pattern.fullmatch(w) for w in self.words)


def _dictionary_gen(rng: random.Random) -> dict:
    pool = _vocabulary(rng, 10, "abcd", 5)
    calls: list[tuple[str, list]] = [("WordDictionary", [])]
    for _ in range(pick_n(rng, 1, 20, big=300)):
        if rng.random() < 0.45:
            calls.append(("addWord", [rng.choice(pool)]))
        else:
            text = rng.choice(pool) if rng.random() < 0.7 else word(rng, rng.randint(1, 5), "abcd")
            dots = "".join("." if rng.random() < 0.3 else ch for ch in text)
            calls.append(("search", [dots[:25]]))
    return ops(*calls)


WORD_DICTIONARY = ProblemSource(
    title="Design Add and Search Words Data Structure",
    statement="""
Design `WordDictionary`, which stores words and answers pattern queries:
- `addWord(word)` stores `word`.
- `search(word)` returns `true` if a stored word matches `word`, where each `.` in `word` matches any single letter.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor
and `addWord`).
""",
    constraints="""
- `1 <= word.length <= 25`; `addWord` words are lowercase, `search` words are lowercase letters or `.`
- at most `10^4` calls
""",
    signature=design("WordDictionary", [], [("addWord", [("word", "string")], "void"), ("search", [("word", "string")], "bool")]),
    reference=_WordDictionary,
    brute=_WordDictionaryBrute,
    examples=[
        Example(ops(("WordDictionary", []), ("addWord", ["bad"]), ("addWord", ["dad"]), ("addWord", ["mad"]), ("search", ["pad"]), ("search", ["bad"]), ("search", [".ad"]), ("search", ["b.."]))),
        Example(ops(("WordDictionary", []), ("addWord", ["a"]), ("search", ["."]), ("search", [".."]), ("search", ["a."]))),
    ],
    edge_cases=[ops(("WordDictionary", []), ("search", ["..."]), ("addWord", ["abc"]), ("search", ["..."]), ("search", ["ab"]))],
    generator=_dictionary_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Word Search II


def _find_words(board: list[list[str]], words: list[str]) -> list[str]:
    root: dict = {}
    for w in words:
        _insert(root, w, w)
    m, n = len(board), len(board[0])
    found: list[str] = []

    def walk(i: int, j: int, parent: dict) -> None:
        ch = board[i][j]
        node = parent[ch]
        if "$" in node:
            found.append(node.pop("$"))  # report each word once
        board[i][j] = "#"
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= a < m and 0 <= b < n and board[a][b] in node:
                walk(a, b, node)
        board[i][j] = ch
        if not node:
            parent.pop(ch)  # prune exhausted branches

    for i in range(m):
        for j in range(n):
            if board[i][j] in root:
                walk(i, j, root)
    return found


def _word_search_brute(board: list[list[str]], words: list[str]) -> list[str]:
    m, n = len(board), len(board[0])

    def exists(w: str) -> bool:
        def dfs(i: int, j: int, k: int, used: frozenset) -> bool:
            if board[i][j] != w[k]:
                return False
            if k == len(w) - 1:
                return True
            return any(
                dfs(a, b, k + 1, used | {(a, b)})
                for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1))
                if 0 <= a < m and 0 <= b < n and (a, b) not in used
            )

        return any(dfs(i, j, 0, frozenset({(i, j)})) for i in range(m) for j in range(n))

    return [w for w in words if exists(w)]


def _board_gen(rng: random.Random) -> list:
    m, n = pick_n(rng, 1, 4, big=8), pick_n(rng, 1, 4, big=8)
    alphabet = "abc" if rng.random() < 0.6 else "abcdefgh"
    board = [[rng.choice(alphabet) for _ in range(n)] for _ in range(m)]
    words = set()
    for _ in range(rng.randint(1, 12)):
        if rng.random() < 0.6:  # trace a real path so that some words exist
            i, j, text, used = rng.randrange(m), rng.randrange(n), "", set()
            for _ in range(rng.randint(1, 6)):
                used.add((i, j))
                text += board[i][j]
                steps = [(a, b) for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)) if 0 <= a < m and 0 <= b < n and (a, b) not in used]
                if not steps:
                    break
                i, j = rng.choice(steps)
            words.add(text)
        else:
            words.add(word(rng, rng.randint(1, 6), alphabet))
    return [board, sorted(words)]


WORD_SEARCH_II = ProblemSource(
    title="Word Search II",
    statement="""
Return every word of `words` that can be traced on the letter `board`: a word is formed by moving between horizontally or vertically adjacent
cells, using each cell at most once per word. Return the found words in any order, each once.
""",
    constraints="""
- `1 <= m, n <= 12`
- `1 <= words.length <= 3 * 10^4`, `1 <= words[i].length <= 10`, words are distinct
- lowercase English letters only
""",
    signature=function("findWords", [("board", "char[][]"), ("words", "string[]")], "string[]"),
    reference=_find_words,
    brute=_word_search_brute,
    compare="unordered",
    examples=[
        Example([[["o", "a", "a", "n"], ["e", "t", "a", "e"], ["i", "h", "k", "r"], ["i", "f", "l", "v"]], ["oath", "pea", "eat", "rain"]], "\"oath\" and \"eat\"."),
        Example([[["a", "b"], ["c", "d"]], ["abcb"]], "It would need to reuse a cell."),
    ],
    edge_cases=[[[["a"]], ["a", "b", "aa"]], [[["a", "a"]], ["aa", "aaa"]]],
    generator=_board_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Search Suggestions System


def _suggested_products(products: list[str], searchWord: str) -> list[list[str]]:
    ordered = sorted(products)
    out, prefix, start = [], "", 0
    for ch in searchWord:
        prefix += ch
        start = bisect.bisect_left(ordered, prefix, start)
        out.append([p for p in ordered[start : start + 3] if p.startswith(prefix)])
    return out


def _suggestions_brute(products: list[str], searchWord: str) -> list[list[str]]:
    return [sorted(p for p in products if p.startswith(searchWord[:i]))[:3] for i in range(1, len(searchWord) + 1)]


SEARCH_SUGGESTIONS = ProblemSource(
    title="Search Suggestions System",
    statement="""
While `searchWord` is typed one letter at a time, suggest up to three products from `products` that start with the letters typed so far. When
more than three match, suggest the three lexicographically smallest. Return the list of suggestions after each typed letter.
""",
    constraints="""
- `1 <= products.length <= 1000`, products are distinct
- `1 <= products[i].length, searchWord.length <= 1000`
- lowercase English letters only
""",
    signature=function("suggestedProducts", [("products", "string[]"), ("searchWord", "string")], "string[][]"),
    reference=_suggested_products,
    brute=_suggestions_brute,
    examples=[Example([["mobile", "mouse", "moneypot", "monitor", "mousepad"], "mouse"]), Example([["havana"], "tatiana"], "Nothing starts with \"t\".")],
    edge_cases=[[["a"], "a"], [["a", "ab", "abc", "abcd"], "abc"], [["b"], "a"]],
    generator=lambda rng: [sorted(set(_vocabulary(rng, pick_n(rng, 1, 15, big=500), "abc", 6))), word(rng, rng.randint(1, 6), "abc")],
    random_count=8,
)


# ---------------------------------------------------------------- Replace Words


def _replace_words(dictionary: list[str], sentence: str) -> str:
    root: dict = {}
    for w in dictionary:
        _insert(root, w)

    def shortest_root(w: str) -> str:
        node = root
        for i, ch in enumerate(w):
            if ch not in node:
                return w
            node = node[ch]
            if "$" in node:
                return w[: i + 1]
        return w

    return " ".join(shortest_root(w) for w in sentence.split(" "))


def _replace_brute(dictionary: list[str], sentence: str) -> str:
    return " ".join(min((r for r in dictionary if w.startswith(r)), key=len, default=w) for w in sentence.split(" "))


def _replace_gen(rng: random.Random) -> list:
    roots = sorted(set(_vocabulary(rng, rng.randint(1, 8), "abc", 3)))
    words = [rng.choice(roots) + word(rng, rng.randint(0, 3), "abc") if rng.random() < 0.6 else word(rng, rng.randint(1, 5), "abc") for _ in range(rng.randint(1, 12))]
    return [roots, " ".join(words)]


REPLACE_WORDS = ProblemSource(
    title="Replace Words",
    statement="""
A *root* can be extended into longer *derivative* words (for example root `"help"` gives `"helpful"`). Replace every word of `sentence` that
starts with some root from `dictionary` by the **shortest** such root; leave other words unchanged. Return the resulting sentence.
""",
    constraints="""
- `1 <= dictionary.length <= 1000`, `1 <= dictionary[i].length <= 100`
- `sentence` has words of lowercase letters separated by single spaces, with no leading or trailing spaces
""",
    signature=function("replaceWords", [("dictionary", "string[]"), ("sentence", "string")], "string"),
    reference=_replace_words,
    brute=_replace_brute,
    examples=[Example([["cat", "bat", "rat"], "the cattle was rattled by the battery"], "\"the cat was rat by the bat\"."), Example([["a", "b", "c"], "aadsfasf absbs bbab cadsfafs"])],
    edge_cases=[[["a"], "a"], [["ab", "a"], "abc"], [["xyz"], "hello world"]],
    generator=_replace_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Top K Frequent Words


def _top_k_frequent(words: list[str], k: int) -> list[str]:
    counts = Counter(words)
    return sorted(counts, key=lambda w: (-counts[w], w))[:k]


def _top_words_brute(words: list[str], k: int) -> list[str]:
    distinct = sorted(set(words))
    out = []
    for _ in range(k):
        best = max(distinct, key=lambda w: (words.count(w), [-ord(c) for c in w] + [1]))
        out.append(best)
        distinct.remove(best)
    return out


def _top_words_gen(rng: random.Random) -> list:
    pool = sorted(set(_vocabulary(rng, rng.randint(1, 8), "abc", 4)))
    words = [rng.choice(pool) for _ in range(rng.randint(1, rng.choice([12, 500])))]
    return [words, rng.randint(1, len(set(words)))]


TOP_K_WORDS = ProblemSource(
    title="Top K Frequent Words",
    statement="""
Return the `k` most frequent words in `words`, sorted from most to least frequent; words with the same frequency are sorted lexicographically.
""",
    constraints="""
- `1 <= words.length <= 500`, `1 <= words[i].length <= 10`, lowercase letters
- `1 <= k <=` the number of distinct words
""",
    signature=function("topKFrequent", [("words", "string[]"), ("k", "int")], "string[]"),
    reference=_top_k_frequent,
    brute=_top_words_brute,
    examples=[Example([["i", "love", "leetcode", "i", "love", "coding"], 2], "\"i\" and \"love\" appear twice; \"i\" comes first alphabetically."), Example([["the", "day", "is", "sunny", "the", "the", "the", "sunny", "is", "is"], 4])],
    edge_cases=[[["a"], 1], [["b", "a", "c"], 3], [["aa", "a", "aa", "a"], 1]],
    generator=_top_words_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Lexicographical Numbers


def _lexical_order(n: int) -> list[int]:
    out, current = [], 1
    for _ in range(n):
        out.append(current)
        if current * 10 <= n:
            current *= 10
        else:
            while current % 10 == 9 or current + 1 > n:
                current //= 10
            current += 1
    return out


LEXICOGRAPHICAL_NUMBERS = ProblemSource(
    title="Lexicographical Numbers",
    statement="""
Return the integers from `1` to `n` sorted in lexicographical (dictionary) order of their decimal strings. Aim for `O(n)` time and `O(1)` extra
space.
""",
    constraints="""
- `1 <= n <= 5 * 10^4`
""",
    signature=function("lexicalOrder", [("n", "int")], "int[]"),
    reference=_lexical_order,
    brute=lambda n: sorted(range(1, n + 1), key=str),
    examples=[Example([13], "[1,10,11,12,13,2,3,4,5,6,7,8,9]."), Example([2])],
    edge_cases=[[1], [9], [10], [100], [199]],
    generator=lambda rng: [rng.randint(1, rng.choice([150, 5000]))],
    random_count=6,
)


# ---------------------------------------------------------------- Longest Common Prefix


def _longest_common_prefix(strs: list[str]) -> str:
    first, last = min(strs), max(strs)
    i = 0
    while i < min(len(first), len(last)) and first[i] == last[i]:
        i += 1
    return first[:i]


def _prefix_brute(strs: list[str]) -> str:
    prefix = ""
    for chars in zip(*strs, strict=False):
        if len(set(chars)) != 1:
            break
        prefix += chars[0]
    return prefix


def _prefix_gen(rng: random.Random) -> list:
    stem = word(rng, rng.randint(0, 4), "ab")
    return [[stem + word(rng, rng.randint(0, 3), "abc") for _ in range(rng.randint(1, rng.choice([5, 200])))]]


LONGEST_COMMON_PREFIX = ProblemSource(
    title="Longest Common Prefix",
    statement="""
Return the longest string that is a prefix of every string in `strs`, or `""` if they share no common prefix.
""",
    constraints="""
- `1 <= strs.length <= 200`
- `0 <= strs[i].length <= 200`, lowercase letters
""",
    signature=function("longestCommonPrefix", [("strs", "string[]")], "string"),
    reference=_longest_common_prefix,
    brute=_prefix_brute,
    examples=[Example([["flower", "flow", "flight"]]), Example([["dog", "racecar", "car"]])],
    edge_cases=[[[""]], [["a"]], [["ab", "a"]], [["", "b"]]],
    generator=_prefix_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Index Pairs of a String


def _index_pairs(text: str, words: list[str]) -> list[list[int]]:
    root: dict = {}
    for w in words:
        _insert(root, w)
    out = []
    for i in range(len(text)):
        node = root
        for j in range(i, len(text)):
            node = node.get(text[j])
            if node is None:
                break
            if "$" in node:
                out.append([i, j])
    return out


def _index_pairs_brute(text: str, words: list[str]) -> list[list[int]]:
    return sorted([i, i + len(w) - 1] for w in set(words) for i in range(len(text) - len(w) + 1) if text.startswith(w, i))


INDEX_PAIRS = ProblemSource(
    title="Index Pairs of a String",
    statement="""
Return every index pair `[i, j]` such that the substring `text[i..j]` (inclusive) is one of `words`. Sort the pairs by `i`, then by `j`.
""",
    constraints="""
- `1 <= text.length <= 100`
- `1 <= words.length <= 20`, `1 <= words[i].length <= 50`, words are distinct
- lowercase English letters only
""",
    signature=function("indexPairs", [("text", "string"), ("words", "string[]")], "int[][]"),
    reference=_index_pairs,
    brute=_index_pairs_brute,
    examples=[Example(["thestoryofleetcodeandme", ["story", "fleet", "leetcode"]]), Example(["ababa", ["aba", "ab"]], "Matches may overlap.")],
    edge_cases=[["a", ["a"]], ["a", ["b"]], ["aaa", ["a", "aa", "aaa"]]],
    generator=lambda rng: [word(rng, rng.randint(1, 100), "ab"), sorted(set(_vocabulary(rng, rng.randint(1, 20), "ab", 4)))],
    random_count=8,
)


# ---------------------------------------------------------------- K-th Smallest in Lexicographical Order


def _find_kth_number(n: int, k: int) -> int:
    def count_under(prefix: int) -> int:
        count, first, last = 0, prefix, prefix
        while first <= n:
            count += min(last, n) - first + 1
            first, last = first * 10, last * 10 + 9
        return count

    current = 1
    k -= 1
    while k:
        below = count_under(current)
        if below <= k:
            current, k = current + 1, k - below
        else:
            current, k = current * 10, k - 1
    return current


K_LEXICOGRAPHICAL = ProblemSource(
    title="K-th Smallest in Lexicographical Order",
    statement="""
Return the `k`-th smallest integer in `[1, n]` when the integers are ordered lexicographically as decimal strings.
""",
    constraints="""
- `1 <= k <= n <= 10^9`
""",
    signature=function("findKthNumber", [("n", "int"), ("k", "int")], "int"),
    reference=_find_kth_number,
    brute=lambda n, k: sorted(range(1, n + 1), key=str)[k - 1] if n <= 20000 else NotImplemented,
    examples=[Example([13, 2], "Order: 1, 10, 11, 12, 13, 2, ...; the second is 10."), Example([1, 1])],
    edge_cases=[[10, 3], [100, 10], [1000000000, 1000000000], [1000000000, 1]],
    generator=lambda rng: [(n := rng.randint(1, rng.choice([300, 20000, 10**9]))), rng.randint(1, n)],
    random_count=8,
)


# ---------------------------------------------------------------- Palindrome Pairs


def _palindrome_pairs(words: list[str]) -> list[list[int]]:
    index = {w[::-1]: i for i, w in enumerate(words)}
    out = []
    for i, w in enumerate(words):
        for cut in range(len(w) + 1):
            left, right = w[:cut], w[cut:]
            if left == left[::-1] and right in index and index[right] != i:
                out.append([index[right], i])  # reversed(right) + left + right
            if cut != len(w) and right == right[::-1] and left in index and index[left] != i:
                out.append([i, index[left]])  # left + right + reversed(left)
    return out


def _palindrome_pairs_brute(words: list[str]) -> list[list[int]]:
    return [[i, j] for i, j in itertools.permutations(range(len(words)), 2) if (s := words[i] + words[j]) == s[::-1]]


PALINDROME_PAIRS = ProblemSource(
    title="Palindrome Pairs",
    statement="""
`words` holds distinct strings. Return every pair of distinct indices `[i, j]` such that `words[i] + words[j]` is a palindrome. The pairs may be
returned in any order.
""",
    constraints="""
- `1 <= words.length <= 5000`
- `0 <= words[i].length <= 300`, lowercase letters, all distinct
""",
    signature=function("palindromePairs", [("words", "string[]")], "int[][]"),
    reference=_palindrome_pairs,
    brute=lambda words: _palindrome_pairs_brute(words) if len(words) <= 150 else NotImplemented,
    compare="unordered",
    examples=[Example([["abcd", "dcba", "lls", "s", "sssll"]], "\"dcbaabcd\", \"abcddcba\", \"slls\", \"llssssll\"."), Example([["bat", "tab", "cat"]]), Example([["a", ""]], "\"a\" + \"\" and \"\" + \"a\".")],
    edge_cases=[[["a"]], [["ab", "ba", "a", "b"]], [["", "aba", "xy"]]],
    generator=lambda rng: [list(dict.fromkeys(word(rng, rng.randint(0, 4), "ab") for _ in range(rng.randint(1, rng.choice([8, 60])))))],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Common Suffix Queries


def _string_indices(wordsContainer: list[str], wordsQuery: list[str]) -> list[int]:
    def better(i: int, j: int) -> int:
        """Prefer the shorter word, then the earlier index."""
        return i if (len(wordsContainer[i]), i) < (len(wordsContainer[j]), j) else j

    root: dict = {"best": 0}
    for i in range(1, len(wordsContainer)):
        root["best"] = better(root["best"], i)
    for i, w in enumerate(wordsContainer):
        node = root
        for ch in reversed(w):
            node = node.setdefault(ch, {"best": i})
            node["best"] = better(node["best"], i)
    out = []
    for q in wordsQuery:
        node = root
        for ch in reversed(q):
            if ch not in node:
                break
            node = node[ch]
        out.append(node["best"])
    return out


def _suffix_brute(wordsContainer: list[str], wordsQuery: list[str]) -> list[int]:
    def common_suffix(a: str, b: str) -> int:
        k = 0
        while k < min(len(a), len(b)) and a[-1 - k] == b[-1 - k]:
            k += 1
        return k

    return [min(range(len(wordsContainer)), key=lambda i: (-common_suffix(wordsContainer[i], q), len(wordsContainer[i]), i)) for q in wordsQuery]


SUFFIX_QUERIES = ProblemSource(
    title="Longest Common Suffix Queries",
    statement="""
For each `wordsQuery[i]`, find the word in `wordsContainer` sharing the longest common suffix with it. Break ties by choosing the shortest such
word, and then the one that appears earliest. Return the chosen indices (into `wordsContainer`), one per query. If no word shares a non-empty
suffix, the longest common suffix is `""`, which every word shares.
""",
    constraints="""
- `1 <= wordsContainer.length, wordsQuery.length <= 10^4`
- `1 <= word length <= 5 * 10^3`, lowercase letters
""",
    signature=function("stringIndices", [("wordsContainer", "string[]"), ("wordsQuery", "string[]")], "int[]"),
    reference=_string_indices,
    brute=_suffix_brute,
    brute_input_limit=4000,
    examples=[Example([["abcd", "bcd", "xbcd"], ["cd", "bcd", "xyz"]], "\"xyz\" shares nothing, so the shortest word, index 1, wins."), Example([["abcdefgh", "poiuygh", "ghghgh"], ["gh", "acbfgh", "acbfegh"]])],
    edge_cases=[[["a"], ["b"]], [["ab", "b"], ["b", "ab", "cab"]]],
    generator=lambda rng: [[word(rng, rng.randint(1, 5), "abc") for _ in range(rng.randint(1, 12))], [word(rng, rng.randint(1, 5), "abc") for _ in range(rng.randint(1, 12))]],
    random_count=8,
)


# ---------------------------------------------------------------- Map Sum Pairs


class _MapSum:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.root: dict = {"sum": 0}

    def insert(self, key: str, val: int) -> None:
        delta = val - self.values.get(key, 0)
        self.values[key] = val
        node = self.root
        node["sum"] += delta
        for ch in key:
            node = node.setdefault(ch, {"sum": 0})
            node["sum"] += delta

    def sum(self, prefix: str) -> int:
        node = self.root
        for ch in prefix:
            if ch not in node:
                return 0
            node = node[ch]
        return node["sum"]


class _MapSumBrute:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    def insert(self, key: str, val: int) -> None:
        self.values[key] = val

    def sum(self, prefix: str) -> int:
        return sum(v for k, v in self.values.items() if k.startswith(prefix))


def _map_sum_gen(rng: random.Random) -> dict:
    pool = _vocabulary(rng, 10, "abc", 5)
    calls: list[tuple[str, list]] = [("MapSum", [])]
    for _ in range(pick_n(rng, 1, 20, big=50)):
        if rng.random() < 0.5:
            calls.append(("insert", [rng.choice(pool), rng.randint(1, 1000)]))
        else:
            text = rng.choice(pool)
            calls.append(("sum", [text[: rng.randint(1, len(text))]]))
    return ops(*calls)


MAP_SUM = ProblemSource(
    title="Map Sum Pairs",
    statement="""
Design `MapSum`:
- `insert(key, val)` maps `key` to `val`, replacing any earlier value for the same key.
- `sum(prefix)` returns the sum of the values of all keys that start with `prefix`.

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the constructor
and `insert`).
""",
    constraints="""
- `1 <= key.length, prefix.length <= 50`, lowercase letters
- `1 <= val <= 1000`; at most `50` calls
""",
    signature=design("MapSum", [], [("insert", [("key", "string"), ("val", "int")], "void"), ("sum", [("prefix", "string")], "int")]),
    reference=_MapSum,
    brute=_MapSumBrute,
    examples=[Example(ops(("MapSum", []), ("insert", ["apple", 3]), ("sum", ["ap"]), ("insert", ["app", 2]), ("sum", ["ap"])), "3, then 3 + 2 = 5."), Example(ops(("MapSum", []), ("insert", ["a", 3]), ("insert", ["a", 5]), ("sum", ["a"])), "Re-inserting replaces the value.")],
    edge_cases=[ops(("MapSum", []), ("sum", ["z"]))],
    generator=_map_sum_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Check If a Word is a Prefix of Any Word in a Sentence


def _is_prefix_of_word(sentence: str, searchWord: str) -> int:
    for i, w in enumerate(sentence.split(" "), start=1):
        if w[: len(searchWord)] == searchWord:
            return i
    return -1


PREFIX_IN_SENTENCE = ProblemSource(
    title="Check If a Word is a Prefix of Any Word in a Sentence",
    statement="""
`sentence` is made of words separated by single spaces. Return the 1-based position of the first word that has `searchWord` as a prefix, or `-1`
if no word does.
""",
    constraints="""
- `1 <= sentence.length <= 100`, `1 <= searchWord.length <= 10`
- lowercase letters and single spaces; no leading or trailing spaces
""",
    signature=function("isPrefixOfWord", [("sentence", "string"), ("searchWord", "string")], "int"),
    reference=_is_prefix_of_word,
    brute=lambda sentence, searchWord: next((i + 1 for i, w in enumerate(sentence.split()) if w.startswith(searchWord)), -1),
    examples=[Example(["i love eating burger", "burg"]), Example(["this problem is an easy problem", "pro"], "The first match is word 2."), Example(["i am tired", "you"])],
    edge_cases=[["a", "a"], ["a", "aa"], ["ab ab", "ab"]],
    generator=lambda rng: [" ".join(word(rng, rng.randint(1, 5), "abc") for _ in range(rng.randint(1, 10))), word(rng, rng.randint(1, 3), "abc")],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Word With All Prefixes


def _longest_word(words: list[str]) -> str:
    root: dict = {}
    for w in words:
        _insert(root, w)
    best = ""
    stack = [(root, "")]
    while stack:  # only walk through nodes that end a word
        node, text = stack.pop()
        if len(text) > len(best) or (len(text) == len(best) and text < best):
            best = text
        stack += [(child, text + ch) for ch, child in node.items() if ch != "$" and "$" in child]
    return best


def _longest_word_brute(words: list[str]) -> str:
    present = set(words)
    good = [w for w in words if all(w[:i] in present for i in range(1, len(w) + 1))]
    return min(good, key=lambda w: (-len(w), w), default="")


def _prefix_chain_gen(rng: random.Random) -> list:
    words = set()
    for _ in range(rng.randint(1, rng.choice([6, 40]))):
        stem = word(rng, rng.randint(1, 6), "ab")
        cut = rng.randint(1, len(stem))
        words |= {stem[:i] for i in range(cut, len(stem) + 1)}
    return [sorted(words)]


LONGEST_WORD_PREFIXES = ProblemSource(
    title="Longest Word With All Prefixes",
    statement="""
Find the longest string in `words` such that **every** prefix of it is also in `words` (for example `"app"` qualifies only if `"a"` and `"ap"`
are present too). If several qualify, return the lexicographically smallest; if none does, return `""`.
""",
    constraints="""
- `1 <= words.length <= 10^5`, total length `<= 10^5`
- lowercase English letters
""",
    signature=function("longestWord", [("words", "string[]")], "string"),
    reference=_longest_word,
    brute=_longest_word_brute,
    examples=[Example([["k", "ki", "kir", "kira", "kiran"]]), Example([["a", "banana", "app", "appl", "ap", "apply", "apple"]], "\"apple\" and \"apply\" both qualify; \"apple\" is smaller."), Example([["abc", "bc", "ab", "qwe"]], "No word has all its prefixes.")],
    edge_cases=[[["a"]], [["b", "a"]], [["ab"]]],
    generator=_prefix_chain_gen,
    random_count=8,
)


PROBLEMS = [
    IMPLEMENT_TRIE,
    WORD_DICTIONARY,
    WORD_SEARCH_II,
    SEARCH_SUGGESTIONS,
    REPLACE_WORDS,
    TOP_K_WORDS,
    LEXICOGRAPHICAL_NUMBERS,
    LONGEST_COMMON_PREFIX,
    INDEX_PAIRS,
    K_LEXICOGRAPHICAL,
    PALINDROME_PAIRS,
    SUFFIX_QUERIES,
    MAP_SUM,
    PREFIX_IN_SENTENCE,
    LONGEST_WORD_PREFIXES,
]
