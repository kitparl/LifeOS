"""Pattern 5: In-Place Manipulation of a Linked List. Original statements; outputs come from `reference`."""

from __future__ import annotations

from app.modules.dsa.content.model import Example, ProblemSource, function, ints, pick_n
from app.modules.dsa.judge.codec import ListNode

PATTERN_NUMBER = 5

LIST_NOTE = "The list is given (and your answer is shown) as its values from head to tail."


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


def _list_gen(lo: int, hi: int, big: int, vmin: int = -1000, vmax: int = 1000):
    return lambda rng: [ints(rng, pick_n(rng, lo, hi, big=big), vmin, vmax)]


# ---------------------------------------------------------------- Reverse Linked List


def _reverse(head: ListNode | None) -> ListNode | None:
    prev = None
    while head:
        head.next, prev, head = prev, head, head.next
    return prev


REVERSE_LIST = ProblemSource(
    title="Reverse Linked List",
    statement=f"""
Reverse a singly linked list by rewiring its `next` pointers, and return the new head.

{LIST_NOTE} Can you do it both iteratively and recursively?
""",
    constraints="""
- the list has between `0` and `5000` nodes
- `-5000 <= Node.val <= 5000`
""",
    signature=function("reverseList", [("head", "ListNode")], "ListNode"),
    reference=_reverse,
    brute=lambda head: _build(_values(head)[::-1]),
    examples=[Example([[1, 2, 3, 4, 5]]), Example([[1, 2]]), Example([[]], "An empty list stays empty.")],
    edge_cases=[[[7]], [[5, 5, 5]]],
    generator=_list_gen(0, 40, 3000, -5000, 5000),
    random_count=7,
)


# ---------------------------------------------------------------- Reorder List


def _reorder(head: ListNode | None) -> ListNode | None:
    if not head or not head.next:
        return head
    slow = fast = head
    while fast.next and fast.next.next:
        slow, fast = slow.next, fast.next.next
    second, slow.next = _reverse(slow.next), None
    first = head
    while second:
        first.next, second.next, first, second = second, first.next, first.next, second.next
    return head


def _reorder_brute(head: ListNode | None) -> ListNode | None:
    values, out = _values(head), []
    lo, hi = 0, len(values) - 1
    while lo <= hi:
        out.append(values[lo])
        if lo != hi:
            out.append(values[hi])
        lo, hi = lo + 1, hi - 1
    return _build(out)


REORDER_LIST = ProblemSource(
    title="Reorder List",
    statement=f"""
A list `L0 -> L1 -> ... -> Ln-1 -> Ln` must be rearranged **in place** into
`L0 -> Ln -> L1 -> Ln-1 -> L2 -> Ln-2 -> ...`, alternating from the front and the back.

Rewire the nodes themselves (don't just change their values) and return the head. {LIST_NOTE}
""",
    constraints="""
- the list has between `1` and `5 * 10^4` nodes
- `1 <= Node.val <= 1000`
""",
    signature=function("reorderList", [("head", "ListNode")], "ListNode"),
    reference=_reorder,
    brute=_reorder_brute,
    examples=[Example([[1, 2, 3, 4]], "Becomes 1, 4, 2, 3."), Example([[1, 2, 3, 4, 5]], "Becomes 1, 5, 2, 4, 3.")],
    edge_cases=[[[1]], [[1, 2]], [[1, 2, 3]]],
    generator=_list_gen(1, 40, 3000, 1, 1000),
    random_count=7,
)


# ---------------------------------------------------------------- Reverse Nodes in k-Group


def _reverse_k_group(head: ListNode | None, k: int) -> ListNode | None:
    dummy = ListNode(0, head)
    group_prev = dummy
    while True:
        kth = group_prev
        for _ in range(k):
            kth = kth.next
            if not kth:
                return dummy.next
        group_next = kth.next
        prev, cur = group_next, group_prev.next
        while cur is not group_next:
            cur.next, prev, cur = prev, cur, cur.next
        first = group_prev.next
        group_prev.next = kth
        group_prev = first


def _reverse_k_brute(head: ListNode | None, k: int) -> ListNode | None:
    values = _values(head)
    out = []
    for i in range(0, len(values), k):
        chunk = values[i : i + k]
        out += chunk[::-1] if len(chunk) == k else chunk
    return _build(out)


REVERSE_K_GROUP = ProblemSource(
    title="Reverse Nodes in k-Group",
    statement=f"""
Split the list into consecutive groups of `k` nodes and reverse the nodes inside each full group. If the
last group has fewer than `k` nodes, leave it as it is.

Rewire the nodes (don't only swap values) and return the new head. {LIST_NOTE}

Can you use only `O(1)` extra memory?
""",
    constraints="""
- the list has `n` nodes, `1 <= k <= n <= 5000`
- `0 <= Node.val <= 1000`
""",
    signature=function("reverseKGroup", [("head", "ListNode"), ("k", "int")], "ListNode"),
    reference=_reverse_k_group,
    brute=_reverse_k_brute,
    examples=[
        Example([[1, 2, 3, 4, 5], 2], "Groups [1,2] and [3,4] flip; 5 is left alone."),
        Example([[1, 2, 3, 4, 5], 3]),
    ],
    edge_cases=[[[1], 1], [[1, 2], 2], [[1, 2, 3], 1], [[1, 2, 3, 4], 4]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 40, big=3000), 0, 1000)), rng.randint(1, min(len(v), 8))],
    random_count=8,
)


# ---------------------------------------------------------------- Reverse Linked List II


def _reverse_between(head: ListNode | None, left: int, right: int) -> ListNode | None:
    dummy = ListNode(0, head)
    before = dummy
    for _ in range(left - 1):
        before = before.next
    cur = before.next
    for _ in range(right - left):
        moved = cur.next
        cur.next = moved.next
        moved.next = before.next
        before.next = moved
    return dummy.next


def _reverse_between_brute(head: ListNode | None, left: int, right: int) -> ListNode | None:
    v = _values(head)
    return _build(v[: left - 1] + v[left - 1 : right][::-1] + v[right:])


def _between_gen(rng):
    v = ints(rng, pick_n(rng, 1, 40, big=500), -500, 500)
    left = rng.randint(1, len(v))
    return [v, left, rng.randint(left, len(v))]


REVERSE_BETWEEN = ProblemSource(
    title="Reverse Linked List II",
    statement=f"""
Given the head of a list and positions `left <= right` (1-based), reverse the nodes from position `left`
through position `right` and return the head. The rest of the list keeps its order. {LIST_NOTE}

Can you do it in a single pass?
""",
    constraints="""
- the list has `n` nodes, `1 <= n <= 500`
- `-500 <= Node.val <= 500`
- `1 <= left <= right <= n`
""",
    signature=function("reverseBetween", [("head", "ListNode"), ("left", "int"), ("right", "int")], "ListNode"),
    reference=_reverse_between,
    brute=_reverse_between_brute,
    examples=[Example([[1, 2, 3, 4, 5], 2, 4], "Positions 2..4 flip: 1, 4, 3, 2, 5."), Example([[5], 1, 1])],
    edge_cases=[[[1, 2], 1, 2], [[1, 2, 3], 1, 1], [[1, 2, 3], 3, 3], [[1, 2, 3], 1, 3]],
    generator=_between_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Swapping Nodes in a Linked List


def _swap_nodes(head: ListNode | None, k: int) -> ListNode | None:
    first = head
    for _ in range(k - 1):
        first = first.next
    probe, second = first, head
    while probe.next:
        probe, second = probe.next, second.next
    first.val, second.val = second.val, first.val
    return head


def _swap_nodes_brute(head: ListNode | None, k: int) -> ListNode | None:
    v = _values(head)
    v[k - 1], v[-k] = v[-k], v[k - 1]
    return _build(v)


SWAP_KTH = ProblemSource(
    title="Swapping Nodes in a Linked List",
    statement=f"""
Given the head of a list and an integer `k`, swap the **values** of the `k`-th node from the beginning
and the `k`-th node from the end (both 1-based), and return the head. {LIST_NOTE}
""",
    constraints="""
- the list has `n` nodes, `1 <= k <= n <= 10^5`
- `0 <= Node.val <= 100`
""",
    signature=function("swapNodes", [("head", "ListNode"), ("k", "int")], "ListNode"),
    reference=_swap_nodes,
    brute=_swap_nodes_brute,
    examples=[
        Example([[1, 2, 3, 4, 5], 2], "Swap 2 and 4."),
        Example([[7, 9, 6, 6, 7, 8, 3, 0, 9, 5], 5], "Swap 7 (5th) and 8 (5th from the end)."),
    ],
    edge_cases=[[[1], 1], [[1, 2], 1], [[1, 2], 2], [[1, 2, 3], 2]],
    generator=lambda rng: [(v := ints(rng, pick_n(rng, 1, 40, big=5000), 0, 100)), rng.randint(1, len(v))],
    random_count=8,
)


# ---------------------------------------------------------------- Reverse Nodes In Even Length Groups


def _reverse_even_groups(head: ListNode | None) -> ListNode | None:
    prev, size = head, 2
    while prev.next:
        node, count = prev, 0
        while node.next and count < size:
            node, count = node.next, count + 1
        if count % 2 == 0:
            tail, cur, stop = prev.next, prev.next, node.next
            new_prev = stop
            while cur is not stop:
                cur.next, new_prev, cur = new_prev, cur, cur.next
            prev.next = new_prev
            prev = tail
        else:
            prev = node
        size += 1
    return head


def _reverse_even_brute(head: ListNode | None) -> ListNode | None:
    v, out, i, size = _values(head), [], 0, 1
    while i < len(v):
        group = v[i : i + size]
        out += group[::-1] if len(group) % 2 == 0 else group
        i += size
        size += 1
    return _build(out)


REVERSE_EVEN_GROUPS = ProblemSource(
    title="Reverse Nodes In Even Length Groups",
    statement=f"""
Split the list into consecutive groups whose intended sizes are `1, 2, 3, 4, ...`. The last group may be
shorter than intended if the list runs out of nodes.

Reverse the nodes of every group whose **actual** length is even, and return the head. {LIST_NOTE}
""",
    constraints="""
- the list has between `1` and `10^5` nodes
- `0 <= Node.val <= 10^5`
""",
    signature=function("reverseEvenLengthGroups", [("head", "ListNode")], "ListNode"),
    reference=_reverse_even_groups,
    brute=_reverse_even_brute,
    examples=[
        Example([[5, 2, 6, 3, 9, 1, 7, 3, 8, 4]], "Groups [5] [2,6] [3,9,1] [7,3,8,4]: the 2nd and 4th are reversed."),
        Example([[1, 1, 0, 6]], "The groups are [1], [1,0] and [6]; only [1,0] is reversed."),
        Example([[1, 1, 0, 6, 5]], "The last group [6,5] has even length and is reversed."),
    ],
    edge_cases=[[[1]], [[1, 2]], [[1, 2, 3]], [[1, 2, 3, 4, 5, 6]]],
    generator=_list_gen(1, 40, 4000, 0, 10**5),
    random_count=8,
)


# ---------------------------------------------------------------- Swap Nodes in Pairs


def _swap_pairs(head: ListNode | None) -> ListNode | None:
    dummy = ListNode(0, head)
    prev = dummy
    while prev.next and prev.next.next:
        a, b = prev.next, prev.next.next
        prev.next, a.next, b.next = b, b.next, a
        prev = a
    return dummy.next


def _swap_pairs_brute(head: ListNode | None) -> ListNode | None:
    v = _values(head)
    for i in range(0, len(v) - 1, 2):
        v[i], v[i + 1] = v[i + 1], v[i]
    return _build(v)


SWAP_PAIRS = ProblemSource(
    title="Swap Nodes in Pairs",
    statement=f"""
Swap every two adjacent nodes of the list and return the new head. Rewire the nodes; don't change the
values stored in them. {LIST_NOTE}
""",
    constraints="""
- the list has between `0` and `100` nodes
- `0 <= Node.val <= 100`
""",
    signature=function("swapPairs", [("head", "ListNode")], "ListNode"),
    reference=_swap_pairs,
    brute=_swap_pairs_brute,
    examples=[
        Example([[1, 2, 3, 4]], "Becomes 2, 1, 4, 3."),
        Example([[]]),
        Example([[1, 2, 3]], "The odd node at the end stays."),
    ],
    edge_cases=[[[1]], [[1, 2]]],
    generator=_list_gen(0, 20, 100, 0, 100),
    random_count=7,
)


# ---------------------------------------------------------------- Split Linked List in Parts


def _split_list(head: ListNode | None, k: int) -> list[ListNode | None]:
    length, node = 0, head
    while node:
        length, node = length + 1, node.next
    base, extra = divmod(length, k)
    parts, node = [], head
    for i in range(k):
        parts.append(node)
        for _ in range(base + (i < extra) - 1):
            node = node.next if node else None
        if node:
            node.next, node = None, node.next
    return parts


def _split_brute(head: ListNode | None, k: int) -> list[ListNode | None]:
    v = _values(head)
    base, extra = divmod(len(v), k)
    parts, i = [], 0
    for p in range(k):
        size = base + (p < extra)
        parts.append(_build(v[i : i + size]))
        i += size
    return parts


SPLIT_LIST_PARTS = ProblemSource(
    title="Split Linked List in Parts",
    statement=f"""
Split the list into `k` consecutive parts whose lengths differ by at most one, with longer parts first.
Some parts may be empty when the list has fewer than `k` nodes.

Return the `k` part heads in order (an empty part is `null`, shown as `[]`). {LIST_NOTE}
""",
    constraints="""
- the list has between `0` and `1000` nodes
- `0 <= Node.val <= 1000`
- `1 <= k <= 50`
""",
    signature=function("splitListToParts", [("head", "ListNode"), ("k", "int")], "ListNode[]"),
    reference=_split_list,
    brute=_split_brute,
    examples=[
        Example([[1, 2, 3], 5], "Three parts of one node, then two empty parts."),
        Example([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3], "Sizes 4, 3, 3."),
    ],
    edge_cases=[[[], 1], [[], 3], [[1], 1], [[1, 2], 1]],
    generator=lambda rng: [ints(rng, pick_n(rng, 0, 40, big=1000), 0, 1000), rng.randint(1, 50)],
    random_count=8,
)


# ---------------------------------------------------------------- Remove Linked List Elements


def _remove_elements(head: ListNode | None, val: int) -> ListNode | None:
    dummy = ListNode(0, head)
    node = dummy
    while node.next:
        if node.next.val == val:
            node.next = node.next.next
        else:
            node = node.next
    return dummy.next


REMOVE_ELEMENTS = ProblemSource(
    title="Remove Linked List Elements",
    statement=f"""
Remove every node whose value equals `val` and return the new head. {LIST_NOTE}
""",
    constraints="""
- the list has between `0` and `10^4` nodes
- `1 <= Node.val <= 50`
- `0 <= val <= 50`
""",
    signature=function("removeElements", [("head", "ListNode"), ("val", "int")], "ListNode"),
    reference=_remove_elements,
    brute=lambda head, val: _build([x for x in _values(head) if x != val]),
    examples=[
        Example([[1, 2, 6, 3, 4, 5, 6], 6]),
        Example([[], 1]),
        Example([[7, 7, 7, 7], 7], "Every node is removed."),
    ],
    edge_cases=[[[1], 1], [[1], 2], [[1, 2, 1], 1]],
    generator=lambda rng: [ints(rng, pick_n(rng, 0, 40, big=5000), 1, rng.choice([3, 50])), rng.randint(0, 3)],
    random_count=8,
)


# ---------------------------------------------------------------- Delete N Nodes After M Nodes of a Linked List


def _delete_nodes(head: ListNode | None, m: int, n: int) -> ListNode | None:
    node = head
    while node:
        for _ in range(m - 1):
            if not node.next:
                return head
            node = node.next
        gone = node.next
        for _ in range(n):
            if not gone:
                break
            gone = gone.next
        node.next = gone
        node = gone
    return head


def _delete_nodes_brute(head: ListNode | None, m: int, n: int) -> ListNode | None:
    v = _values(head)
    return _build([x for i, x in enumerate(v) if i % (m + n) < m])


DELETE_N_AFTER_M = ProblemSource(
    title="Delete N Nodes After M Nodes of a Linked List",
    statement=f"""
Walk through the list repeating this pattern until the end: **keep** the next `m` nodes, then **delete**
the following `n` nodes (or as many as remain). Return the head of the modified list. {LIST_NOTE}
""",
    constraints="""
- the list has between `1` and `10^4` nodes
- `1 <= Node.val <= 10^6`
- `1 <= m, n <= 1000`
""",
    signature=function("deleteNodes", [("head", "ListNode"), ("m", "int"), ("n", "int")], "ListNode"),
    reference=_delete_nodes,
    brute=_delete_nodes_brute,
    examples=[
        Example(
            [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 2, 3],
            "Keep 1,2, drop 3,4,5, keep 6,7, drop 8,9,10, keep 11,12, drop 13.",
        ),
        Example([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 1, 3], "Keep 1, 5 and 9."),
    ],
    edge_cases=[[[1], 1, 1], [[1, 2], 5, 1], [[1, 2, 3], 1, 1000]],
    generator=lambda rng: [ints(rng, pick_n(rng, 1, 40, big=4000), 1, 10**6), rng.randint(1, 6), rng.randint(1, 6)],
    random_count=8,
)


# ---------------------------------------------------------------- Remove Duplicates from Sorted List


def _delete_duplicates(head: ListNode | None) -> ListNode | None:
    node = head
    while node and node.next:
        if node.next.val == node.val:
            node.next = node.next.next
        else:
            node = node.next
    return head


REMOVE_SORTED_DUPLICATES = ProblemSource(
    title="Remove Duplicates from Sorted List",
    statement=f"""
The list is sorted. Delete nodes so that each value appears only once, and return the head of the
(still sorted) list. {LIST_NOTE}
""",
    constraints="""
- the list has between `0` and `300` nodes
- `-100 <= Node.val <= 100`
- the list is sorted in ascending order
""",
    signature=function("deleteDuplicates", [("head", "ListNode")], "ListNode"),
    reference=_delete_duplicates,
    brute=lambda head: _build(sorted(set(_values(head)))),
    examples=[Example([[1, 1, 2]]), Example([[1, 1, 2, 3, 3]])],
    edge_cases=[[[]], [[1]], [[2, 2, 2]]],
    generator=lambda rng: [sorted(ints(rng, pick_n(rng, 0, 30, big=300), -100, rng.choice([-95, 100])))],
    random_count=8,
)


# ---------------------------------------------------------------- Insert into a Sorted Circular Linked List


def _insert_circular(head: ListNode | None, insertVal: int) -> ListNode | None:
    node = ListNode(insertVal)
    if head is None:
        node.next = node
        return node
    cur = head
    while True:
        nxt = cur.next
        fits_inside = cur.val <= insertVal <= nxt.val
        at_wrap = cur.val > nxt.val and (insertVal >= cur.val or insertVal <= nxt.val)
        if fits_inside or at_wrap or nxt is head:
            cur.next, node.next = node, nxt
            return head
        cur = nxt


def _insert_circular_brute(head: ListNode | None, insertVal: int) -> ListNode | None:
    values = []
    node = head
    while node is not None:
        values.append(node.val)
        node = node.next
        if node is head:
            break
    if not values:
        out = _build([insertVal])
        out.next = out
        return out
    for i in range(len(values)):
        candidate = values[: i + 1] + [insertVal] + values[i + 1 :]
        if sum(candidate[k] > candidate[(k + 1) % len(candidate)] for k in range(len(candidate))) <= 1:
            break
    rebuilt = _build(candidate)
    tail = rebuilt
    while tail.next:
        tail = tail.next
    tail.next = rebuilt
    return rebuilt


def _circular_sorted_gen(rng):
    values = sorted(ints(rng, pick_n(rng, 0, 20, big=3000), -100, rng.choice([-95, 100])))
    if values:
        k = rng.randrange(len(values))
        values = values[k:] + values[:k]
    return [values, rng.randint(-105, 105)]


INSERT_SORTED_CIRCULAR = ProblemSource(
    title="Insert into a Sorted Circular Linked List",
    statement="""
You are given one node, `head`, of a **circular** linked list whose values are sorted in non-decreasing
order when read around the circle starting from the smallest value. `head` itself may be any node of the
circle, not necessarily the smallest.

Insert a new node with value `insertVal` so that the circle stays sorted, and return `head`. If several
places work, any of them is accepted. If the list is empty (`head` is `null`), create a one-node circular
list and return that node.

**How the tests describe the list:** the values are listed once, starting from `head`; the judge links
the last node back to the first. Your answer is shown as one lap of values starting from the returned node.
""",
    constraints="""
- the list has between `0` and `5 * 10^4` nodes
- `-10^6 <= Node.val, insertVal <= 10^6`
""",
    signature=function(
        "insert",
        [("head", "ListNode"), ("insertVal", "int")],
        "ListNode",
        links=[{"kind": "circular", "list": "head"}],
        circular_output=True,
    ),
    reference=_insert_circular,
    brute=_insert_circular_brute,
    compare="checker",
    checker="sorted_circular_insert",
    examples=[
        Example([[3, 4, 1], 2], "2 goes between 1 and 3: one lap from head is 3, 4, 1, 2."),
        Example([[], 1], "An empty list becomes a single node pointing to itself."),
        Example([[1], 0], "With a single node, 0 goes right after it."),
    ],
    edge_cases=[[[3, 3, 3], 3], [[3, 3, 3], 5], [[1, 3, 5], 6], [[1, 3, 5], 0], [[5, 1, 3], 4]],
    generator=_circular_sorted_gen,
    random_count=8,
)


# ---------------------------------------------------------------- Odd Even Linked List


def _odd_even(head: ListNode | None) -> ListNode | None:
    if not head:
        return head
    odd, even_head = head, head.next
    even = even_head
    while even and even.next:
        odd.next = even.next
        odd = odd.next
        even.next = odd.next
        even = even.next
    odd.next = even_head
    return head


ODD_EVEN = ProblemSource(
    title="Odd Even Linked List",
    statement=f"""
Rearrange the list so that all nodes at odd positions (1st, 3rd, 5th, ...) come first, followed by all
nodes at even positions, each group keeping its original relative order. Return the head. {LIST_NOTE}

Positions are counted from 1 and have nothing to do with the node values. Use `O(1)` extra space.
""",
    constraints="""
- the list has between `0` and `10^4` nodes
- `-10^6 <= Node.val <= 10^6`
""",
    signature=function("oddEvenList", [("head", "ListNode")], "ListNode"),
    reference=_odd_even,
    brute=lambda head: _build((v := _values(head))[0::2] + v[1::2]),
    examples=[
        Example([[1, 2, 3, 4, 5]], "Odd positions 1, 3, 5 then even positions 2, 4."),
        Example([[2, 1, 3, 5, 6, 4, 7]]),
    ],
    edge_cases=[[[]], [[1]], [[1, 2]]],
    generator=_list_gen(0, 40, 3000, -(10**6), 10**6),
    random_count=7,
)


# ---------------------------------------------------------------- Rotate List


def _rotate_right(head: ListNode | None, k: int) -> ListNode | None:
    if not head:
        return head
    length, tail = 1, head
    while tail.next:
        length, tail = length + 1, tail.next
    k %= length
    if k == 0:
        return head
    new_tail = head
    for _ in range(length - k - 1):
        new_tail = new_tail.next
    new_head = new_tail.next
    new_tail.next, tail.next = None, head
    return new_head


def _rotate_right_brute(head: ListNode | None, k: int) -> ListNode | None:
    v = _values(head)
    for _ in range(k % len(v) if v else 0):
        v.insert(0, v.pop())
    return _build(v)


ROTATE_LIST = ProblemSource(
    title="Rotate List",
    statement=f"""
Rotate the list to the right by `k` places: each rotation moves the last node to the front. `k` may be
much larger than the length of the list. Return the new head. {LIST_NOTE}
""",
    constraints="""
- the list has between `0` and `500` nodes
- `-100 <= Node.val <= 100`
- `0 <= k <= 2 * 10^9`
""",
    signature=function("rotateRight", [("head", "ListNode"), ("k", "int")], "ListNode"),
    reference=_rotate_right,
    brute=_rotate_right_brute,
    examples=[
        Example([[1, 2, 3, 4, 5], 2], "Two rotations: 4, 5, 1, 2, 3."),
        Example([[0, 1, 2], 4], "4 rotations of a 3-node list equal 1 rotation."),
    ],
    edge_cases=[[[], 0], [[], 7], [[1], 99], [[1, 2], 2000000000], [[1, 2, 3], 0]],
    generator=lambda rng: [
        ints(rng, pick_n(rng, 0, 40, big=500), -100, 100),
        rng.choice([rng.randint(0, 50), rng.randint(0, 2 * 10**9)]),
    ],
    random_count=8,
)


PROBLEMS = [
    REVERSE_LIST,
    REORDER_LIST,
    REVERSE_K_GROUP,
    REVERSE_BETWEEN,
    SWAP_KTH,
    REVERSE_EVEN_GROUPS,
    SWAP_PAIRS,
    SPLIT_LIST_PARTS,
    REMOVE_ELEMENTS,
    DELETE_N_AFTER_M,
    REMOVE_SORTED_DUPLICATES,
    INSERT_SORTED_CIRCULAR,
    ODD_EVEN,
    ROTATE_LIST,
]
