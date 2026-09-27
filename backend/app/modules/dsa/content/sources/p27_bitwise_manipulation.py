"""Pattern 27: Bitwise Manipulation. Original statements; outputs come from `reference`."""

from __future__ import annotations

import itertools
import random
from collections import Counter
from collections.abc import Callable
from functools import reduce

from app.modules.dsa.content.model import Example, ProblemSource, design, function, ints, ops, pick_n, sample, word

PATTERN_NUMBER = 27


# ---------------------------------------------------------------- Encode and Decode Strings


class _Codec:
    def encode(self, strs: list[str]) -> str:
        return "".join(f"{len(s)}#{s}" for s in strs)

    def decode(self, s: str) -> list[str]:
        out, i = [], 0
        while i < len(s):
            j = s.index("#", i)
            length = int(s[i:j])
            out.append(s[j + 1 : j + 1 + length])
            i = j + 1 + length
        return out


class _CodecBrute:
    def encode(self, strs: list[str]) -> str:
        return "".join(str(len(s)) + "#" + s for s in strs)

    def decode(self, s: str) -> list[str]:
        if not s:
            return []
        head, rest = s.split("#", 1)
        length = int(head)
        return [rest[:length], *self.decode(rest[length:])]


def _codec_gen(rng: random.Random) -> dict:
    calls: list[tuple[str, list]] = [("Codec", [])]
    for _ in range(rng.randint(1, 3)):
        strs = [word(rng, rng.randint(0, 12), "ab#3 ,") for _ in range(rng.randint(0, 6))]
        calls.append(("encode", [strs]) if rng.random() < 0.5 else ("decode", [_Codec().encode(strs)]))
    return ops(*calls)


ENCODE_DECODE_STRINGS = ProblemSource(
    title="Encode and Decode Strings",
    statement="""
*Adapted I/O:* design `Codec`, which turns a list of strings into one string and back. The strings may contain any characters, including the
`#` and digits. Because the judge compares encoded strings directly, the format is fixed: each string is written as its **length**, then `#`,
then the string itself, all concatenated. For example `["ab", "", "#1"]` becomes `"2#ab0#2##1"`.

- `encode(strs)` returns the encoded string.
- `decode(s)` returns the list encoded by `s`.
""" + """

**Test format:** a list of operations with their arguments; the expected output lists each operation's return value (`null` for the
constructor).
""",
    constraints="""
- `0 <= strs.length <= 200`, `0 <= strs[i].length <= 200`
- `strs[i]` contains any printable ASCII characters
""",
    signature=design("Codec", [], [("encode", [("strs", "string[]")], "string"), ("decode", [("s", "string")], "string[]")]),
    reference=_Codec,
    brute=_CodecBrute,
    is_variant=True,
    examples=[
        Example(ops(("Codec", []), ("encode", [["lint", "code", "love", "you"]]), ("decode", ["4#lint4#code4#love3#you"]))),
        Example(ops(("Codec", []), ("encode", [["ab", "", "#1"]]), ("decode", ["2#ab0#2##1"])), "Lengths make '#' and digits inside strings safe."),
    ],
    edge_cases=[ops(("Codec", []), ("encode", [[]]), ("decode", [""]), ("encode", [[""]]))],
    generator=_codec_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Reverse Bits


def _reverse_bits(n: int) -> int:
    out = 0
    for _ in range(32):
        out = out << 1 | n & 1
        n >>= 1
    return out


REVERSE_BITS = ProblemSource(
    title="Reverse Bits",
    statement="""
`n` is an unsigned 32-bit integer (given as a non-negative number). Reverse the order of its 32 bits and return the resulting unsigned value.
""",
    constraints="""
- `0 <= n <= 2^32 - 1`
""",
    signature=function("reverseBits", [("n", "long")], "long"),
    reference=_reverse_bits,
    brute=lambda n: int(format(n, "032b")[::-1], 2),
    examples=[Example([43261596], "00000010100101000001111010011100 -> 00111001011110000010100101000000 = 964176192."), Example([4294967293])],
    edge_cases=[[0], [1], [4294967295], [2147483648]],
    generator=lambda rng: [rng.randint(0, 2**32 - 1)],
    random_count=8,
)


# ---------------------------------------------------------------- Find the Difference


def _find_the_difference(s: str, t: str) -> str:
    return chr(reduce(lambda acc, ch: acc ^ ord(ch), s + t, 0))


FIND_THE_DIFFERENCE = ProblemSource(
    title="Find the Difference",
    statement="""
`t` was made by shuffling `s` and inserting one extra letter at a random position. Return that extra letter.
""",
    constraints="""
- `0 <= s.length <= 1000`, `t.length == s.length + 1`
- lowercase English letters
""",
    signature=function("findTheDifference", [("s", "string"), ("t", "string")], "char"),
    reference=_find_the_difference,
    brute=lambda s, t: next(iter(Counter(t) - Counter(s))),
    examples=[Example(["abcd", "abcde"]), Example(["", "y"]), Example(["aab", "abab"], "The extra letter can repeat an existing one.")],
    edge_cases=[["a", "aa"], ["z", "za"]],
    generator=lambda rng: [(s := word(rng, rng.randint(0, rng.choice([8, 1000])), "abcz")), "".join(sample(rng, list(s + rng.choice("abcz")), len(s) + 1))],
    random_count=8,
)


# ---------------------------------------------------------------- Complement of Base 10 Integer


def _bitwise_complement(n: int) -> int:
    mask = 1
    while mask <= n:
        mask <<= 1
    return (mask - 1) ^ n if n else 1


COMPLEMENT_BASE_10 = ProblemSource(
    title="Complement of Base 10 Integer",
    statement="""
The *complement* of an integer flips every bit of its binary representation (without leading zeros): `5` is `101`, whose complement `010` is
`2`. Return the complement of `n` (the complement of `0` is `1`).
""",
    constraints="""
- `0 <= n < 10^9`
""",
    signature=function("bitwiseComplement", [("n", "int")], "int"),
    reference=_bitwise_complement,
    brute=lambda n: int("".join("1" if b == "0" else "0" for b in format(n, "b")), 2),
    examples=[Example([5]), Example([7]), Example([10], "1010 -> 0101.")],
    edge_cases=[[0], [1], [999999999]],
    generator=lambda rng: [rng.randint(0, rng.choice([64, 10**9 - 1]))],
    random_count=8,
)


# ---------------------------------------------------------------- Flipping an Image


def _flip_and_invert_image(image: list[list[int]]) -> list[list[int]]:
    return [[bit ^ 1 for bit in reversed(row)] for row in image]


FLIPPING_IMAGE = ProblemSource(
    title="Flipping an Image",
    statement="""
`image` is an `n x n` binary matrix. Flip every row horizontally (reverse it), then invert it (`0` becomes `1` and `1` becomes `0`). Return the
result.
""",
    constraints="""
- `1 <= n <= 20`
- `image[i][j]` is `0` or `1`
""",
    signature=function("flipAndInvertImage", [("image", "int[][]")], "int[][]"),
    reference=_flip_and_invert_image,
    brute=lambda image: [[1 - row[len(row) - 1 - j] for j in range(len(row))] for row in image],
    examples=[Example([[[1, 1, 0], [1, 0, 1], [0, 0, 0]]]), Example([[[1, 1, 0, 0], [1, 0, 0, 1], [0, 1, 1, 1], [1, 0, 1, 0]]])],
    edge_cases=[[[[0]]], [[[1]]]],
    generator=lambda rng: [[[rng.randint(0, 1) for _ in range(n)] for _ in range(n)] for n in [rng.randint(1, 20)]],
    random_count=6,
)


# ---------------------------------------------------------------- Single Number


def _single_number(nums: list[int]) -> int:
    return reduce(lambda a, b: a ^ b, nums, 0)


def _single_gen(repeat: int) -> Callable[[random.Random], list]:
    def gen(rng: random.Random) -> list:
        values = sample(rng, range(-(hi := rng.choice([20, 3 * 10**4])), hi + 1), pick_n(rng, 1, 8, big=3000))
        nums = [v for v in values[1:] for _ in range(repeat)] + [values[0]]
        rng.shuffle(nums)
        return [nums]

    return gen


SINGLE_NUMBER = ProblemSource(
    title="Single Number",
    statement="""
Every element of `nums` appears twice except for one, which appears once. Return that one. Use linear time and only constant extra space.
""",
    constraints="""
- `1 <= nums.length <= 3 * 10^4`
- `-3 * 10^4 <= nums[i] <= 3 * 10^4`
""",
    signature=function("singleNumber", [("nums", "int[]")], "int"),
    reference=_single_number,
    brute=lambda nums: next(x for x, c in Counter(nums).items() if c == 1),
    examples=[Example([[2, 2, 1]]), Example([[4, 1, 2, 1, 2]]), Example([[1]])],
    edge_cases=[[[-30000, 5, 5]], [[0, 7, 7]]],
    generator=_single_gen(2),
    random_count=8,
)


# ---------------------------------------------------------------- Single Number II


def _single_number_ii(nums: list[int]) -> int:
    ones = twos = 0
    for x in nums:  # count each bit modulo 3 across two masks
        ones = (ones ^ x) & ~twos
        twos = (twos ^ x) & ~ones
    return ones


SINGLE_NUMBER_II = ProblemSource(
    title="Single Number II",
    statement="""
Every element of `nums` appears three times except for one, which appears exactly once. Return that one, using linear time and constant extra
space.
""",
    constraints="""
- `1 <= nums.length <= 3 * 10^4`
- `-2^31 <= nums[i] <= 2^31 - 1`
""",
    signature=function("singleNumber", [("nums", "int[]")], "int"),
    reference=_single_number_ii,
    brute=lambda nums: next(x for x, c in Counter(nums).items() if c == 1),
    examples=[Example([[2, 2, 3, 2]]), Example([[0, 1, 0, 1, 0, 1, 99]])],
    edge_cases=[[[-2147483648]], [[-1, -1, -1, 2147483647]], [[-2, -2, 1, 1, -3, 1, -3, -3, -4, -2]]],
    generator=_single_gen(3),
    random_count=8,
)


# ---------------------------------------------------------------- Find the Longest Substring Having Vowels in Even Counts


def _find_the_longest_substring(s: str) -> int:
    first_at = {0: -1}
    mask = best = 0
    for i, ch in enumerate(s):
        if ch in "aeiou":
            mask ^= 1 << "aeiou".index(ch)
        if mask in first_at:
            best = max(best, i - first_at[mask])
        else:
            first_at[mask] = i
    return best


def _vowels_brute(s: str) -> int:
    n = len(s)
    if n > 150:
        return NotImplemented
    return max((j - i for i in range(n) for j in range(i, n + 1) if all(s[i:j].count(v) % 2 == 0 for v in "aeiou")), default=0)


EVEN_VOWELS = ProblemSource(
    title="Find the Longest Substring Having Vowels in Even Counts",
    statement="""
Return the length of the longest substring of `s` in which each vowel (`a, e, i, o, u`) appears an even number of times (zero counts as even).
""",
    constraints="""
- `1 <= s.length <= 5 * 10^5`
- lowercase English letters
""",
    signature=function("findTheLongestSubstring", [("s", "string")], "int"),
    reference=_find_the_longest_substring,
    brute=_vowels_brute,
    examples=[Example(["eleetminicoworoep"], "\"leetminicowor\"."), Example(["leetcodeisgreat"]), Example(["bcbcbc"])],
    edge_cases=[["a"], ["aa"], ["b"], ["aeiou"]],
    generator=lambda rng: [word(rng, pick_n(rng, 1, 30, big=10**4), rng.choice(["aeb", "aeioubcd"]))],
    random_count=8,
)


# ---------------------------------------------------------------- Longest Subarray With Maximum Bitwise AND


def _longest_subarray_max_and(nums: list[int]) -> int:
    top = max(nums)  # AND never exceeds its operands, so the best subarrays are runs of the maximum
    best = run = 0
    for x in nums:
        run = run + 1 if x == top else 0
        best = max(best, run)
    return best


def _max_and_brute(nums: list[int]) -> int:
    n = len(nums)
    if n > 100:
        return NotImplemented
    ands = {(i, j): reduce(lambda a, b: a & b, nums[i:j]) for i in range(n) for j in range(i + 1, n + 1)}
    best = max(ands.values())
    return max(j - i for (i, j), v in ands.items() if v == best)


MAX_AND_SUBARRAY = ProblemSource(
    title="Longest Subarray With Maximum Bitwise AND",
    statement="""
Let `k` be the largest bitwise AND of any non-empty contiguous subarray of `nums`. Return the length of the longest subarray whose bitwise AND
equals `k`.
""",
    constraints="""
- `1 <= nums.length <= 10^5`
- `1 <= nums[i] <= 10^6`
""",
    signature=function("longestSubarray", [("nums", "int[]")], "int"),
    reference=_longest_subarray_max_and,
    brute=_max_and_brute,
    examples=[Example([[1, 2, 3, 3, 2, 2]], "The maximum AND is 3, reached by [3,3]."), Example([[1, 2, 3, 4]])],
    edge_cases=[[[7]], [[5, 5, 5]], [[1, 1, 2, 1, 1]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 25, big=10**4), 1, rng.choice([3, 10**6]))],
    random_count=8,
)


# ---------------------------------------------------------------- Count Triplets That Can Form Two Arrays of Equal XOR


def _count_triplets(arr: list[int]) -> int:
    # a == b  <=>  arr[i..k] XORs to 0; every such (i, k) gives k - i choices of j
    seen_count = {0: 1}
    seen_index_sum = {0: -1}  # sum of (prefix index) over equal prefixes, with prefix index -1 for the empty prefix
    prefix = total = 0
    for k, x in enumerate(arr):
        prefix ^= x
        c, s = seen_count.get(prefix, 0), seen_index_sum.get(prefix, 0)
        total += c * k - s - c  # sum over earlier i' of (k - i' - 1), where i' is the prefix end index
        seen_count[prefix] = c + 1
        seen_index_sum[prefix] = s + k
    return total


def _triplets_brute(arr: list[int]) -> int:
    n = len(arr)
    if n > 40:
        return NotImplemented
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j, n):
                a = reduce(lambda x, y: x ^ y, arr[i:j])
                b = reduce(lambda x, y: x ^ y, arr[j : k + 1])
                count += a == b
    return count


XOR_TRIPLETS = ProblemSource(
    title="Count Triplets That Can Form Two Arrays of Equal XOR",
    statement="""
For indices `i < j <= k`, let `a = arr[i] ^ ... ^ arr[j - 1]` and `b = arr[j] ^ ... ^ arr[k]`. Return the number of triplets `(i, j, k)` with
`a == b`.
""",
    constraints="""
- `1 <= arr.length <= 300`
- `1 <= arr[i] <= 10^8`
""",
    signature=function("countTriplets", [("arr", "int[]")], "int"),
    reference=_count_triplets,
    brute=_triplets_brute,
    examples=[Example([[2, 3, 1, 6, 7]], "(0,1,2), (0,2,2), (2,3,4), (2,4,4)."), Example([[1, 1, 1, 1, 1]])],
    edge_cases=[[[1]], [[5, 5]], [[7, 7, 7]]],
    generator=lambda rng: [ints(rng, rng.randint(1, rng.choice([12, 300])), 1, rng.choice([3, 10**8]))],
    random_count=8,
)


# ---------------------------------------------------------------- Sum of All Subset XOR Totals


def _subset_xor_sum(nums: list[int]) -> int:
    # every bit present in some element is set in exactly half of the 2^n subsets
    return reduce(lambda a, b: a | b, nums, 0) << (len(nums) - 1)


def _subset_xor_brute(nums: list[int]) -> int:
    return sum(reduce(lambda a, b: a ^ b, combo, 0) for r in range(len(nums) + 1) for combo in itertools.combinations(nums, r))


SUBSET_XOR_SUM = ProblemSource(
    title="Sum of All Subset XOR Totals",
    statement="""
The *XOR total* of an array is the bitwise XOR of all its elements (`0` for an empty array). Return the sum of the XOR totals of every subset of
`nums` (subsets with the same elements at different indices count separately).
""",
    constraints="""
- `1 <= nums.length <= 12`
- `1 <= nums[i] <= 20`
""",
    signature=function("subsetXORSum", [("nums", "int[]")], "int"),
    reference=_subset_xor_sum,
    brute=_subset_xor_brute,
    examples=[Example([[1, 3]], "0 + 1 + 3 + (1 ^ 3) = 6."), Example([[5, 1, 6]]), Example([[3, 4, 5, 6, 7, 8]])],
    edge_cases=[[[1]], [[20] * 12]],
    generator=lambda rng: [ints(rng, rng.randint(1, 12), 1, 20)],
    random_count=8,
)


# ---------------------------------------------------------------- Find The K-th Lucky Number


def _kth_lucky_number(k: int) -> str:
    # lucky numbers of length L are the L-bit binary counts with 0 -> 4 and 1 -> 7; k + 1 in binary without its top bit
    return format(k + 1, "b")[1:].replace("0", "4").replace("1", "7")


def _lucky_brute(k: int) -> str:
    if k > 3000:
        return NotImplemented
    numbers = sorted(int("".join(p)) for length in range(1, 12) for p in itertools.product("47", repeat=length))
    return str(numbers[k - 1])


KTH_LUCKY = ProblemSource(
    title="Find The K-th Lucky Number",
    statement="""
A *lucky number* is a positive integer whose digits are all `4` or `7` (`4, 7, 44, 47, 74, ...`). Return the `k`-th smallest lucky number as a
string.
""",
    constraints="""
- `1 <= k <= 10^9`
""",
    signature=function("kthLuckyNumber", [("k", "int")], "string"),
    reference=_kth_lucky_number,
    brute=_lucky_brute,
    examples=[Example([4], "4, 7, 44, 47."), Example([10], "\"477\"."), Example([1000], "\"777747447\".")],
    edge_cases=[[1], [2], [3], [1000000000]],
    generator=lambda rng: [rng.randint(1, rng.choice([100, 3000, 10**9]))],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Number of K Consecutive Bit Flips


def _min_k_bit_flips(nums: list[int], k: int) -> int:
    n = len(nums)
    ends = [0] * (n + 1)  # flips that stop affecting index i
    active = flips = 0
    for i in range(n):
        active ^= ends[i]
        if nums[i] ^ active == 0:
            if i + k > n:
                return -1
            flips += 1
            active ^= 1
            ends[i + k] ^= 1
    return flips


def _k_flips_brute(nums: list[int], k: int) -> int:
    values = nums[:]
    flips = 0
    for i in range(len(values) - k + 1):  # left to right, each 0 must be fixed by the window starting there
        if values[i] == 0:
            flips += 1
            for j in range(i, i + k):
                values[j] ^= 1
    return flips if all(values) else -1


K_BIT_FLIPS = ProblemSource(
    title="Minimum Number of K Consecutive Bit Flips",
    statement="""
`nums` is a binary array. A *k-bit flip* chooses a contiguous subarray of length `k` and flips every bit in it. Return the minimum number of
k-bit flips needed so that the array has no `0`, or `-1` if that's impossible.
""",
    constraints="""
- `1 <= k <= nums.length <= 10^5`
- `nums[i]` is `0` or `1`
""",
    signature=function("minKBitFlips", [("nums", "int[]"), ("k", "int")], "int"),
    reference=_min_k_bit_flips,
    brute=_k_flips_brute,
    brute_input_limit=3000,
    examples=[Example([[0, 1, 0], 1]), Example([[1, 1, 0], 2], "The last 0 can't be fixed without breaking a 1."), Example([[0, 0, 0, 1, 0, 1, 1, 0], 3])],
    edge_cases=[[[1], 1], [[0], 1], [[0, 0], 2], [[0, 1], 2]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 20, big=10**4), 0, 1)), rng.randint(1, min(len(v), rng.choice([3, 50])))],
    random_count=10,
)


# ---------------------------------------------------------------- Minimum One Bit Operations to Make Integers Zero


def _minimum_one_bit_operations(n: int) -> int:
    # the answer is the inverse Gray code of n
    result = 0
    while n:
        result ^= n
        n >>= 1
    return result


def _one_bit_brute(n: int) -> int:
    if n > 3000:
        return NotImplemented
    limit = 1 << max(1, n.bit_length())
    dist = {n: 0}
    frontier = [n]
    while 0 not in dist:
        nxt = []
        for x in frontier:
            moves = [x ^ 1]
            low = (x & -x) if x else 0
            if low and low << 1 < limit * 2:
                moves.append(x ^ (low << 1))  # bit i+1 may flip when bit i is 1 and bits below are 0
            for y in moves:
                if y not in dist:
                    dist[y] = dist[x] + 1
                    nxt.append(y)
        frontier = nxt
    return dist[0]


ONE_BIT_OPERATIONS = ProblemSource(
    title="Minimum One Bit Operations to Make Integers Zero",
    statement="""
Turn `n` into `0` using these operations any number of times:
- flip the rightmost bit (bit `0`);
- flip bit `i` if bit `i - 1` is `1` and bits `i - 2` down to `0` are all `0`.

Return the minimum number of operations.
""",
    constraints="""
- `0 <= n <= 10^9`
""",
    signature=function("minimumOneBitOperations", [("n", "int")], "int"),
    reference=_minimum_one_bit_operations,
    brute=_one_bit_brute,
    examples=[Example([3], "11 -> 01 -> 00."), Example([6], "110 -> 010 -> 011 -> 001 -> 000.")],
    edge_cases=[[0], [1], [2], [1000000000]],
    generator=lambda rng: [rng.randint(0, rng.choice([3000, 10**9]))],
    random_count=8,
)


# ---------------------------------------------------------------- Triples with Bitwise AND Equal To Zero


def _count_triplets_and(nums: list[int]) -> int:
    pair_ands = Counter(a & b for a in nums for b in nums)
    return sum(count for value, count in pair_ands.items() for c in nums if value & c == 0)


def _and_triples_brute(nums: list[int]) -> int:
    if len(nums) > 25:
        return NotImplemented
    return sum(1 for a in nums for b in nums for c in nums if a & b & c == 0)


AND_TRIPLES = ProblemSource(
    title="Triples with Bitwise AND Equal To Zero",
    statement="""
Count the index triples `(i, j, k)` — each index from `0` to `n - 1`, repeats allowed and order mattering — with
`nums[i] & nums[j] & nums[k] == 0`.
""",
    constraints="""
- `1 <= nums.length <= 1000`
- `0 <= nums[i] < 2^16`
""",
    signature=function("countTriplets", [("nums", "int[]")], "int"),
    reference=_count_triplets_and,
    brute=_and_triples_brute,
    examples=[Example([[2, 1, 3]]), Example([[0, 0, 0]], "All 27 triples.")],
    edge_cases=[[[1]], [[0]], [[65535, 65535]]],
    generator=lambda rng: [ints(rng, rng.randint(1, rng.choice([10, 200])), 0, rng.choice([7, 2**16 - 1]))],
    random_count=8,
    time_limit_ms=2000,
)


# ---------------------------------------------------------------- Power of Two


def _is_power_of_two(n: int) -> bool:
    return n > 0 and n & (n - 1) == 0


POWER_OF_TWO = ProblemSource(
    title="Power of Two",
    statement="""
Return `true` if `n` equals `2^x` for some integer `x >= 0`. Try to solve it without loops or recursion.
""",
    constraints="""
- `-2^31 <= n <= 2^31 - 1`
""",
    signature=function("isPowerOfTwo", [("n", "int")], "bool"),
    reference=_is_power_of_two,
    brute=lambda n: n in {2**x for x in range(31)},
    examples=[Example([1], "2^0."), Example([16]), Example([3])],
    edge_cases=[[0], [-16], [-2147483648], [1073741824], [2147483647]],
    generator=lambda rng: [rng.choice([2 ** rng.randint(0, 30), rng.randint(-(2**31), 2**31 - 1), 2 ** rng.randint(1, 30) + rng.choice([-1, 1])])],
    random_count=8,
)


# ---------------------------------------------------------------- Hamming Distance


def _hamming_distance(x: int, y: int) -> int:
    diff, count = x ^ y, 0
    while diff:
        diff &= diff - 1
        count += 1
    return count


HAMMING_DISTANCE = ProblemSource(
    title="Hamming Distance",
    statement="""
Return the number of bit positions at which `x` and `y` differ.
""",
    constraints="""
- `0 <= x, y <= 2^31 - 1`
""",
    signature=function("hammingDistance", [("x", "int"), ("y", "int")], "int"),
    reference=_hamming_distance,
    brute=lambda x, y: sum(a != b for a, b in zip(format(x, "031b"), format(y, "031b"), strict=True)),
    examples=[Example([1, 4], "001 vs 100."), Example([3, 1])],
    edge_cases=[[0, 0], [0, 2147483647], [2147483647, 2147483647]],
    generator=lambda rng: [rng.randint(0, 2**31 - 1), rng.randint(0, 2**31 - 1)],
    random_count=8,
)


# ---------------------------------------------------------------- Minimum Operations to Make the Integer Zero


def _make_the_integer_zero(num1: int, num2: int) -> int:
    for k in range(1, 61):
        target = num1 - k * num2  # must be a sum of exactly k powers of two
        if target < k:
            continue
        if bin(target).count("1") <= k:
            return k
    return -1


def _integer_zero_brute(num1: int, num2: int) -> int:
    """For each k, build k powers of two summing to num1 - k * num2 by splitting powers, starting from its binary form."""
    for k in range(1, 61):
        target = num1 - k * num2
        if target <= 0:
            continue
        powers = [1 << b for b in range(target.bit_length()) if target >> b & 1]
        while len(powers) < k and any(p > 1 for p in powers):
            big = max(powers)
            powers.remove(big)
            powers += [big // 2, big // 2]
        if len(powers) == k:
            return k
    return -1


INTEGER_ZERO = ProblemSource(
    title="Minimum Operations to Make the Integer Zero",
    statement="""
In one operation, pick any `i` in `[0, 60]` and subtract `2^i + num2` from `num1`. Return the minimum number of operations needed to make
`num1` equal to `0`, or `-1` if it's impossible.
""",
    constraints="""
- `1 <= num1 <= 10^9`
- `-10^9 <= num2 <= 10^9`
""",
    signature=function("makeTheIntegerZero", [("num1", "int"), ("num2", "int")], "int"),
    reference=_make_the_integer_zero,
    brute=_integer_zero_brute,
    examples=[Example([3, -2], "Subtract 2^2 - 2, 2^2 - 2, then 2^0 - 2."), Example([5, 7], "Every operation subtracts more than 5 can afford to reach 0 exactly.")],
    edge_cases=[[1, 0], [1, 1], [1000000000, -1000000000], [85, 42]],
    generator=lambda rng: [rng.randint(1, rng.choice([200, 10**9])), rng.randint(-(hi := rng.choice([50, 10**9])), hi)],
    random_count=10,
)


# ---------------------------------------------------------------- Single Number III


def _single_number_iii(nums: list[int]) -> list[int]:
    both = reduce(lambda a, b: a ^ b, nums, 0)
    low_bit = both & -both  # a bit where the two singles differ
    first = reduce(lambda a, b: a ^ b, (x for x in nums if x & low_bit), 0)
    return sorted([first, both ^ first])


def _single_iii_gen(rng: random.Random) -> list:
    values = sample(rng, range(-(hi := rng.choice([20, 2**31 - 1])), hi), pick_n(rng, 2, 8, big=3000))
    nums = [v for v in values[2:] for _ in range(2)] + values[:2]
    rng.shuffle(nums)
    return [nums]


SINGLE_NUMBER_III = ProblemSource(
    title="Single Number III",
    statement="""
In `nums`, exactly two elements appear once and every other element appears exactly twice. Return the two single elements, in any order. Use
linear time and constant extra space.
""",
    constraints="""
- `2 <= nums.length <= 3 * 10^4`
- `-2^31 <= nums[i] <= 2^31 - 1`
""",
    signature=function("singleNumber", [("nums", "int[]")], "int[]"),
    reference=_single_number_iii,
    brute=lambda nums: [x for x, c in Counter(nums).items() if c == 1],
    compare="unordered",
    examples=[Example([[1, 2, 1, 3, 2, 5]]), Example([[-1, 0]]), Example([[0, 1]])],
    edge_cases=[[[-2147483648, 2147483647]], [[4, 4, 7, 9]]],
    generator=_single_iii_gen,
    random_count=8,
)


PROBLEMS = [
    ENCODE_DECODE_STRINGS,
    REVERSE_BITS,
    FIND_THE_DIFFERENCE,
    COMPLEMENT_BASE_10,
    FLIPPING_IMAGE,
    SINGLE_NUMBER,
    SINGLE_NUMBER_II,
    EVEN_VOWELS,
    MAX_AND_SUBARRAY,
    XOR_TRIPLETS,
    SUBSET_XOR_SUM,
    KTH_LUCKY,
    K_BIT_FLIPS,
    ONE_BIT_OPERATIONS,
    AND_TRIPLES,
    POWER_OF_TWO,
    HAMMING_DISTANCE,
    INTEGER_ZERO,
    SINGLE_NUMBER_III,
]
