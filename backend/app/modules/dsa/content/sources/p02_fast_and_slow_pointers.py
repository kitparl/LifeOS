"""Pattern 2: Fast and Slow Pointers. Original statements; expected outputs come from `reference`."""

from __future__ import annotations

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n
from app.modules.dsa.judge.codec import ListNode

PATTERN_NUMBER = 2

CYCLE_NOTE = """
**How the tests describe the list:** each test gives the node values of `head` and an index `pos`. The
judge links the last node's `next` to the node at index `pos` (0-based) to create a cycle; `pos = -1`
means there is no cycle. `pos` is **not** passed to your function.
"""


def _nodes(head: ListNode | None, limit: int = 10**6) -> list[ListNode]:
    """Distinct nodes reachable from head (stops when a node repeats)."""
    seen, out = set(), []
    while head is not None and id(head) not in seen and len(out) < limit:
        seen.add(id(head))
        out.append(head)
        head = head.next
    return out


def _cycle_gen(rng):
    n = pick_n(rng, 1, 40, big=3000)
    values = ints(rng, n, -(10**5), 10**5)
    return [values, -1 if rng.random() < 0.35 else rng.randrange(n)]


# ---------------------------------------------------------------- Happy Number


def _digit_square_sum(n: int) -> int:
    return sum(int(d) ** 2 for d in str(n))


def _is_happy(n: int) -> bool:
    slow, fast = n, _digit_square_sum(n)
    while fast != 1 and slow != fast:
        slow = _digit_square_sum(slow)
        fast = _digit_square_sum(_digit_square_sum(fast))
    return fast == 1


def _is_happy_brute(n: int) -> bool:
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = _digit_square_sum(n)
    return n == 1


HAPPY_NUMBER = ProblemSource(
    title="Happy Number",
    statement="""
Start with a positive integer `n` and repeatedly replace it with the sum of the squares of its digits.
The number is *happy* if this process eventually reaches `1`; otherwise it loops forever in a cycle that
never contains `1`.

Return `true` if `n` is happy.
""",
    constraints="""
- `1 <= n <= 2^31 - 1`
""",
    signature=function("isHappy", [("n", "int")], "bool"),
    reference=_is_happy,
    brute=_is_happy_brute,
    examples=[
        Example([19], "19 -> 82 -> 68 -> 100 -> 1."),
        Example([2], "2 -> 4 -> 16 -> 37 -> 58 -> 89 -> 145 -> 42 -> 20 -> 4 ... never reaches 1."),
    ],
    edge_cases=[[1], [7], [4], [10], [2147483647], [1111111]],
    generator=lambda rng: [rng.choice([rng.randint(1, 1000), rng.randint(1, 2**31 - 1)])],
    random_count=8,
)


# ---------------------------------------------------------------- Linked List Cycle


def _has_cycle(head: ListNode | None) -> bool:
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            return True
    return False


def _has_cycle_brute(head: ListNode | None) -> bool:
    seen = set()
    while head:
        if id(head) in seen:
            return True
        seen.add(id(head))
        head = head.next
    return False


LINKED_LIST_CYCLE = ProblemSource(
    title="Linked List Cycle",
    statement="""
Given the head of a singly linked list, return `true` if following `next` pointers can ever bring you
back to a node you already visited (the list contains a cycle), and `false` if you eventually reach the end.
"""
    + CYCLE_NOTE
    + """
Can you solve it with `O(1)` extra memory?
""",
    constraints="""
- the list has between `0` and `10^4` nodes
- `-10^5 <= Node.val <= 10^5`
- `pos` is `-1` or a valid index in the list
""",
    signature=function(
        "hasCycle",
        [("head", "ListNode"), ("pos", "int")],
        "bool",
        links=[{"kind": "cycle", "list": "head", "pos": "pos"}],
    ),
    reference=_has_cycle,
    brute=_has_cycle_brute,
    examples=[
        Example([[3, 2, 0, -4], 1], "The tail links back to the node with value 2."),
        Example([[1, 2], 0], "The tail links back to the head."),
        Example([[1], -1], "No cycle."),
    ],
    edge_cases=[[[], -1], [[1], 0], [[1, 2], -1], [[5, 5, 5], 2]],
    generator=_cycle_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Middle of the Linked List


def _middle(head: ListNode | None) -> ListNode | None:
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    return slow


def _middle_brute(head: ListNode | None) -> ListNode | None:
    nodes = _nodes(head)
    return nodes[len(nodes) // 2]


MIDDLE = ProblemSource(
    title="Middle of the Linked List",
    statement="""
Given the head of a non-empty singly linked list, return its middle node. When the list has two middle
nodes (even length), return the **second** one.

The answer is shown as the values from the returned node to the end of the list.
""",
    constraints="""
- the list has between `1` and `3000` nodes
- `1 <= Node.val <= 100`
""",
    signature=function("middleNode", [("head", "ListNode")], "ListNode"),
    reference=_middle,
    brute=_middle_brute,
    examples=[
        Example([[1, 2, 3, 4, 5]], "The middle node holds 3."),
        Example([[1, 2, 3, 4, 5, 6]], "Two middles (3 and 4): return the second."),
    ],
    edge_cases=[[[1]], [[1, 2]], [[7, 8, 9]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 40, big=3000), 1, 100)],
    random_count=8,
)


# ---------------------------------------------------------------- Circular Array Loop


def _circular_array_loop(nums: list[int]) -> bool:
    n = len(nums)

    def step(i: int) -> int:
        return (i + nums[i]) % n

    for start in range(n):
        if nums[start] == 0:
            continue
        forward = nums[start] > 0
        slow = fast = start
        while True:
            nxt = step(fast)
            if (nums[nxt] > 0) != forward or nxt == fast:
                break
            fast = nxt
            nxt = step(fast)
            if (nums[nxt] > 0) != forward or nxt == fast:
                break
            fast = nxt
            slow = step(slow)
            if slow == fast:
                return True
        # mark this path as dead so it is not explored again
        i = start
        while nums[i] != 0 and (nums[i] > 0) == forward:
            nxt = step(i)
            nums[i] = 0
            i = nxt
    return False


def _circular_array_loop_brute(nums: list[int]) -> bool:
    n = len(nums)
    for start in range(n):
        forward, i, path = nums[start] > 0, start, []
        for _ in range(n + 1):
            path.append(i)
            nxt = (i + nums[i]) % n
            if (nums[nxt] > 0) != forward or nxt == i:
                break
            i = nxt
            if i == start:
                return True
    return False


def _circular_gen(rng):
    n = pick_n(rng, 1, 12, big=3000)
    return [[rng.choice([-1, 1]) * rng.randint(1, 1000 if rng.random() < 0.3 else 4) for _ in range(n)]]


CIRCULAR_ARRAY_LOOP = ProblemSource(
    title="Circular Array Loop",
    statement="""
You are playing a game on a **circular** array `nums` of non-zero integers. Standing at index `i`, you
move `nums[i]` steps: forward if it is positive, backward if it is negative, wrapping around the ends
(the step after the last index is index 0, and the step before index 0 is the last index).

A *cycle* is a sequence of indices you can follow that returns to where it started, where:
- following the moves from any index in the sequence repeats the sequence,
- every value along the cycle has the **same sign** (all forward or all backward),
- the cycle has length **greater than 1** (an index that moves to itself does not count).

Return `true` if the array contains such a cycle.
""",
    constraints="""
- `1 <= nums.length <= 3000`
- `-1000 <= nums[i] <= 1000`, `nums[i] != 0`
""",
    signature=function("circularArrayLoop", [("nums", "int[]")], "bool"),
    reference=_circular_array_loop,
    brute=_circular_array_loop_brute,
    examples=[
        Example([[2, -1, 1, 2, 2]], "Indices 0 -> 2 -> 3 -> 0 form a forward cycle."),
        Example([[-1, -2, -3, -4, -5, 6]], "The only loop is index 5 moving to itself, which has length 1."),
        Example([[1, -1, 5, 1, 4]], "0 -> 1 -> 0 mixes directions, but 3 -> 4 -> 3 is a valid forward cycle."),
    ],
    edge_cases=[[[1]], [[1, 1]], [[-2, 1, -1, -2, -2]], [[2, 2, 2, 2, 2, 4, 7]], [[-1, -1, -1]], [[3, 1, 2]]],
    generator=_circular_gen,
    random_count=9,
)


# ---------------------------------------------------------------- Find The Duplicate Number


def _find_duplicate(nums: list[int]) -> int:
    slow = fast = nums[0]
    while True:
        slow, fast = nums[slow], nums[nums[fast]]
        if slow == fast:
            break
    slow = nums[0]
    while slow != fast:
        slow, fast = nums[slow], nums[fast]
    return slow


def _find_duplicate_brute(nums: list[int]) -> int:
    seen = set()
    for x in nums:
        if x in seen:
            return x
        seen.add(x)
    raise ValueError("no duplicate")


def _duplicate_gen(rng):
    n = pick_n(rng, 1, 30, big=5000)
    dup = rng.randint(1, n)
    values = list(range(1, n + 1))
    extra = rng.randint(1, max(1, n // 3))
    for _ in range(extra):
        values[rng.randrange(len(values))] = dup
    values.append(dup)
    rng.shuffle(values)
    return [values]


FIND_DUPLICATE = ProblemSource(
    title="Find The Duplicate Number",
    statement="""
`nums` has `n + 1` integers, each in the range `[1, n]`, so at least one value repeats. Exactly one value
is repeated (it may appear two or more times). Return that value.

Don't modify `nums`, and use only `O(1)` extra space.
""",
    constraints="""
- `1 <= n <= 5000`, `nums.length == n + 1`
- `1 <= nums[i] <= n`
- exactly one value appears more than once
""",
    signature=function("findDuplicate", [("nums", "int[]")], "int"),
    reference=_find_duplicate,
    brute=_find_duplicate_brute,
    examples=[Example([[1, 3, 4, 2, 2]], "2 appears twice."), Example([[3, 1, 3, 4, 2]]), Example([[3, 3, 3, 3, 3]])],
    edge_cases=[[[1, 1]], [[2, 2, 2]], [[1, 4, 4, 2, 4]], [[2, 5, 9, 6, 9, 3, 8, 9, 7, 1]]],
    generator=_duplicate_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Palindrome Linked List


def _is_palindrome_list(head: ListNode | None) -> bool:
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    prev = None
    while slow:
        slow.next, prev, slow = prev, slow, slow.next
    left, right = head, prev
    while right:
        if left.val != right.val:
            return False
        left, right = left.next, right.next
    return True


def _is_palindrome_list_brute(head: ListNode | None) -> bool:
    values = [n.val for n in _nodes(head)]
    return values == values[::-1]


def _pal_list_gen(rng):
    half = ints(rng, pick_n(rng, 0, 20, big=2000), 0, 3)
    values = half + ints(rng, rng.randint(0, 1), 0, 3) + half[::-1]
    if values and rng.random() < 0.35:
        values[rng.randrange(len(values))] = rng.randint(0, 9)
    return [values or [1]]


PALINDROME_LIST = ProblemSource(
    title="Palindrome Linked List",
    statement="""
Given the head of a non-empty singly linked list, return `true` if its values read the same from front
to back as from back to front.

Can you do it in `O(n)` time and `O(1)` extra space?
""",
    constraints="""
- the list has between `1` and `5000` nodes
- `0 <= Node.val <= 9`
""",
    signature=function("isPalindrome", [("head", "ListNode")], "bool"),
    reference=_is_palindrome_list,
    brute=_is_palindrome_list_brute,
    examples=[Example([[1, 2, 2, 1]]), Example([[1, 2]])],
    edge_cases=[[[1]], [[1, 1]], [[1, 2, 1]], [[1, 2, 3, 2, 2]]],
    generator=_pal_list_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Linked List Cycle III (our definition)


def _cycle_length(head: ListNode | None) -> int:
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            length, node = 1, slow.next
            while node is not slow:
                length, node = length + 1, node.next
            return length
    return 0


def _cycle_length_brute(head: ListNode | None) -> int:
    index = {}
    i = 0
    while head:
        if id(head) in index:
            return i - index[id(head)]
        index[id(head)] = i
        head, i = head.next, i + 1
    return 0


CYCLE_III = ProblemSource(
    title="Linked List Cycle III",
    statement="""
*Our definition of this course-specific title.*

Given the head of a singly linked list, return the **number of nodes in its cycle**, or `0` if the list
has no cycle.
"""
    + CYCLE_NOTE
    + """
Use `O(1)` extra memory: detect the cycle with a slow and a fast pointer, then walk once around it.
""",
    constraints="""
- the list has between `0` and `10^4` nodes
- `-10^5 <= Node.val <= 10^5`
- `pos` is `-1` or a valid index in the list
""",
    signature=function(
        "cycleLength",
        [("head", "ListNode"), ("pos", "int")],
        "int",
        links=[{"kind": "cycle", "list": "head", "pos": "pos"}],
    ),
    reference=_cycle_length,
    brute=_cycle_length_brute,
    is_variant=True,
    examples=[
        Example([[3, 2, 0, -4], 1], "The cycle is 2 -> 0 -> -4 -> 2, which has 3 nodes."),
        Example([[1, 2], 0], "Both nodes are in the cycle."),
        Example([[1], -1], "No cycle."),
    ],
    edge_cases=[[[], -1], [[1], 0], [[1, 2, 3, 4, 5], 4], [[1, 2, 3, 4, 5], 0]],
    generator=_cycle_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Linked List Cycle IV (our definition)


def _remove_cycle(head: ListNode | None) -> ListNode | None:
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            break
    else:
        return head
    slow = head
    while slow is not fast:
        slow, fast = slow.next, fast.next
    start = slow
    while fast.next is not start:
        fast = fast.next
    fast.next = None
    return head


def _remove_cycle_brute(head: ListNode | None) -> ListNode | None:
    nodes = _nodes(head)
    if nodes and nodes[-1].next is not None:
        nodes[-1].next = None
    return head


CYCLE_IV = ProblemSource(
    title="Linked List Cycle IV",
    statement="""
*Our definition of this course-specific title.*

Given the head of a singly linked list that may contain a cycle, **break the cycle** by setting to
`null` the `next` pointer of the last node before the cycle repeats (the node whose `next` leads back
into the cycle). Every node must stay in the list. Return the head.

If there is no cycle, return the list unchanged. The answer is shown as the list's values; a list that
still has a cycle cannot be printed and fails the test.
"""
    + CYCLE_NOTE
    + """
Can you do it with `O(1)` extra memory?
""",
    constraints="""
- the list has between `0` and `10^4` nodes
- `-10^5 <= Node.val <= 10^5`
- `pos` is `-1` or a valid index in the list
""",
    signature=function(
        "removeCycle",
        [("head", "ListNode"), ("pos", "int")],
        "ListNode",
        links=[{"kind": "cycle", "list": "head", "pos": "pos"}],
    ),
    reference=_remove_cycle,
    brute=_remove_cycle_brute,
    is_variant=True,
    examples=[
        Example([[3, 2, 0, -4], 1], "Cutting -4 -> 2 leaves 3 -> 2 -> 0 -> -4."),
        Example([[1, 2], 0], "Cutting 2 -> 1 leaves 1 -> 2."),
        Example([[5, 6], -1], "No cycle; nothing changes."),
    ],
    edge_cases=[[[], -1], [[1], 0], [[1, 2, 3], 2], [[7, 7, 7, 7], 1]],
    generator=_cycle_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Maximum Twin Sum of a Linked List


def _pair_sum(head: ListNode | None) -> int:
    slow = fast = head
    prev = None
    while fast and fast.next:
        fast = fast.next.next
        slow.next, prev, slow = prev, slow, slow.next
    best = 0
    while slow:
        best = max(best, prev.val + slow.val)
        prev, slow = prev.next, slow.next
    return best


def _pair_sum_brute(head: ListNode | None) -> int:
    values = [n.val for n in _nodes(head)]
    return max(values[i] + values[-1 - i] for i in range(len(values) // 2))


TWIN_SUM = ProblemSource(
    title="Maximum Twin Sum of a Linked List",
    statement="""
A linked list has an **even** number of nodes `n`. For `0 <= i < n / 2`, node `i` and node `n - 1 - i`
(0-based) are *twins*, and their twin sum is the sum of their values.

Return the maximum twin sum in the list.
""",
    constraints="""
- the number of nodes is even and between `2` and `10^4`
- `1 <= Node.val <= 10^5`
""",
    signature=function("pairSum", [("head", "ListNode")], "int"),
    reference=_pair_sum,
    brute=_pair_sum_brute,
    examples=[
        Example([[5, 4, 2, 1]], "Twin sums are 5 + 1 = 6 and 4 + 2 = 6."),
        Example([[4, 2, 2, 3]], "Twin sums are 7 and 4."),
        Example([[1, 100000]]),
    ],
    edge_cases=[[[1, 1]], [[1, 2, 3, 4, 5, 6]], [[100000, 1, 1, 100000]]],
    generator=lambda rng: [ints(rng, 2 * pick_n(rng, 1, 20, big=1500), 1, 10**5)],
    random_count=8,
)


# ---------------------------------------------------------------- Split a Circular Linked List


def _split_circular(head: ListNode) -> list[ListNode | None]:
    slow = fast = head
    while fast.next is not head and fast.next.next is not head:
        slow, fast = slow.next, fast.next.next
    if fast.next is not head:
        fast = fast.next
    second = slow.next
    slow.next = head
    fast.next = second
    return [head, second]


def _split_circular_brute(head: ListNode) -> list[ListNode | None]:
    nodes = [head]
    while nodes[-1].next is not head:
        nodes.append(nodes[-1].next)
    k = (len(nodes) + 1) // 2
    first, second = nodes[:k], nodes[k:]
    first[-1].next = first[0]
    second[-1].next = second[0]
    return [first[0], second[0]]


SPLIT_CIRCULAR = ProblemSource(
    title="Split a Circular Linked List",
    statement="""
You are given the head of a **circular** singly linked list (the last node's `next` points back to the
head) with at least two nodes. Split it into two circular lists:

- the first contains the first `ceil(n / 2)` nodes in their original order,
- the second contains the remaining nodes in their original order.

Reuse the existing nodes (don't create new ones) and return `[firstHead, secondHead]`. Both results must
be circular.

**How the tests describe the list:** the values are listed once from the head; the judge links the last
node back to the head. Each returned list is shown as one lap of values starting from its head.
""",
    constraints="""
- the list has between `2` and `10^4` nodes
- `0 <= Node.val <= 10^9`
""",
    signature=function(
        "splitCircularLinkedList",
        [("list", "ListNode")],
        "ListNode[]",
        links=[{"kind": "circular", "list": "list"}],
        circular_output=True,
    ),
    reference=_split_circular,
    brute=_split_circular_brute,
    examples=[
        Example([[1, 5, 7]], "3 nodes: the first list gets ceil(3 / 2) = 2 nodes, [1, 5]; the second gets [7]."),
        Example([[2, 6, 1, 5]], "Four nodes split evenly: [2, 6] and [1, 5]."),
    ],
    edge_cases=[[[1, 2]], [[9, 9, 9]], [[1, 2, 3, 4, 5]], [[0, 1000000000]]],
    generator=lambda rng: [ints(rng, pick_n(rng, 2, 40, big=3000), 0, 10**9)],
    random_count=8,
)


PROBLEMS = [
    HAPPY_NUMBER,
    LINKED_LIST_CYCLE,
    MIDDLE,
    CIRCULAR_ARRAY_LOOP,
    FIND_DUPLICATE,
    PALINDROME_LIST,
    CYCLE_III,
    CYCLE_IV,
    TWIN_SUM,
    SPLIT_CIRCULAR,
]
