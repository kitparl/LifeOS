"""Generated driver programs, executed with local toolchains (a language is skipped if missing).

The live go-judge test (test_dsa_judge_live.py) covers the same programs inside the sandbox.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from app.modules.dsa.judge import drivers
from app.modules.dsa.judge.signature import parse_spec

TWO_SUM = {
    "kind": "function",
    "name": "twoSum",
    "params": [{"name": "nums", "type": "int[]"}, {"name": "target", "type": "int"}],
    "returns": "int[]",
}
SORT_COLORS = {
    "kind": "function",
    "name": "sortColors",
    "params": [{"name": "nums", "type": "int[]"}],
    "returns": "void",
    "mutates": "nums",
}
REVERSE_LIST = {
    "kind": "function",
    "name": "reverseList",
    "params": [{"name": "head", "type": "ListNode"}],
    "returns": "ListNode",
}
INVERT_TREE = {
    "kind": "function",
    "name": "invertTree",
    "params": [{"name": "root", "type": "TreeNode"}],
    "returns": "TreeNode",
}
GROUP_ANAGRAMS = {
    "kind": "function",
    "name": "groupAnagrams",
    "params": [{"name": "strs", "type": "string[]"}],
    "returns": "string[][]",
}
COUNT_X = {"kind": "function", "name": "countX", "params": [{"name": "board", "type": "char[][]"}], "returns": "int"}
MEAN = {"kind": "function", "name": "mean", "params": [{"name": "nums", "type": "long[]"}], "returns": "double"}
MERGE_K = {
    "kind": "function",
    "name": "mergeKLists",
    "params": [{"name": "lists", "type": "ListNode[]"}],
    "returns": "ListNode",
}
MIN_STACK = {
    "kind": "class",
    "name": "MinStack",
    "constructor": [],
    "methods": [
        {"name": "push", "params": [{"name": "val", "type": "int"}], "returns": "void"},
        {"name": "pop", "params": [], "returns": "void"},
        {"name": "top", "params": [], "returns": "int"},
        {"name": "getMin", "params": [], "returns": "int"},
    ],
}

HAS_CYCLE = {
    "kind": "function",
    "name": "hasCycle",
    "params": [{"name": "head", "type": "ListNode"}, {"name": "pos", "type": "int"}],
    "returns": "bool",
    "links": [{"kind": "cycle", "list": "head", "pos": "pos"}],
}
INTERSECT = {
    "kind": "function",
    "name": "getIntersectionNode",
    "params": [
        {"name": "headA", "type": "ListNode"},
        {"name": "headB", "type": "ListNode"},
        {"name": "shared", "type": "int[]"},
    ],
    "returns": "ListNode",
    "links": [{"kind": "join", "a": "headA", "b": "headB", "shared": "shared"}],
}
SPLIT_CIRCULAR = {
    "kind": "function",
    "name": "splitCircular",
    "params": [{"name": "head", "type": "ListNode"}],
    "returns": "ListNode[]",
    "links": [{"kind": "circular", "list": "head"}],
    "circular_output": True,
}
REMOVE_ELEMENT = {
    "kind": "function",
    "name": "removeElement",
    "params": [{"name": "nums", "type": "int[]"}, {"name": "val", "type": "int"}],
    "returns": "int",
    "mutates": "nums",
}
CUBE_SUM = {"kind": "function", "name": "cubeSum", "params": [{"name": "cube", "type": "int[][][]"}], "returns": "long"}
TREE_BOX = {  # a design method returning a tree: an empty tree must encode as [] in every language
    "kind": "class",
    "name": "TreeBox",
    "constructor": [],
    "methods": [{"name": "echo", "params": [{"name": "root", "type": "TreeNode"}], "returns": "TreeNode"}],
}

SOLUTIONS: dict[str, dict[str, str]] = {
    "twoSum": {
        "python": "class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, x in enumerate(nums):\n            if target - x in seen:\n                return [seen[target - x], i]\n            seen[x] = i\n",
        "javascript": "var twoSum = function(nums, target) {\n  const seen = new Map();\n  for (let i = 0; i < nums.length; i++) {\n    if (seen.has(target - nums[i])) return [seen.get(target - nums[i]), i];\n    seen.set(nums[i], i);\n  }\n};\n",
        "cpp": "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        unordered_map<int,int> seen;\n        for (int i = 0; i < (int)nums.size(); ++i) {\n            auto it = seen.find(target - nums[i]);\n            if (it != seen.end()) return {it->second, i};\n            seen[nums[i]] = i;\n        }\n        return {};\n    }\n};\n",
        "java": "import java.util.HashMap;\npublic class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        HashMap<Integer,Integer> seen = new HashMap<>();\n        for (int i = 0; i < nums.length; i++) {\n            if (seen.containsKey(target - nums[i])) return new int[]{seen.get(target - nums[i]), i};\n            seen.put(nums[i], i);\n        }\n        return new int[0];\n    }\n}\n",
    },
    "sortColors": {
        "python": "class Solution:\n    def sortColors(self, nums):\n        nums.sort()\n",
        "javascript": "var sortColors = function(nums) { nums.sort((a, b) => a - b); };\n",
        "cpp": "class Solution {\npublic:\n    void sortColors(vector<int>& nums) { sort(nums.begin(), nums.end()); }\n};\n",
        "java": "class Solution {\n    public void sortColors(int[] nums) { java.util.Arrays.sort(nums); }\n}\n",
    },
    "reverseList": {
        "python": "class Solution:\n    def reverseList(self, head):\n        prev = None\n        while head:\n            head.next, prev, head = prev, head, head.next\n        return prev\n",
        "javascript": "var reverseList = function(head) {\n  let prev = null;\n  while (head) { const n = head.next; head.next = prev; prev = head; head = n; }\n  return prev;\n};\n",
        "cpp": "class Solution {\npublic:\n    ListNode* reverseList(ListNode* head) {\n        ListNode* prev = nullptr;\n        while (head) { ListNode* n = head->next; head->next = prev; prev = head; head = n; }\n        return prev;\n    }\n};\n",
        "java": "class Solution {\n    public ListNode reverseList(ListNode head) {\n        ListNode prev = null;\n        while (head != null) { ListNode n = head.next; head.next = prev; prev = head; head = n; }\n        return prev;\n    }\n}\n",
    },
    "invertTree": {
        "python": "class Solution:\n    def invertTree(self, root):\n        if root:\n            root.left, root.right = self.invertTree(root.right), self.invertTree(root.left)\n        return root\n",
        "javascript": "var invertTree = function(root) {\n  if (root) { const l = root.left; root.left = invertTree(root.right); root.right = invertTree(l); }\n  return root;\n};\n",
        "cpp": "class Solution {\npublic:\n    TreeNode* invertTree(TreeNode* root) {\n        if (root) { TreeNode* l = root->left; root->left = invertTree(root->right); root->right = invertTree(l); }\n        return root;\n    }\n};\n",
        "java": "class Solution {\n    public TreeNode invertTree(TreeNode root) {\n        if (root != null) { TreeNode l = root.left; root.left = invertTree(root.right); root.right = invertTree(l); }\n        return root;\n    }\n}\n",
    },
    "groupAnagrams": {
        "python": "class Solution:\n    def groupAnagrams(self, strs):\n        groups = defaultdict(list)\n        for s in strs:\n            groups[''.join(sorted(s))].append(s)\n        return list(groups.values())\n",
        "javascript": "var groupAnagrams = function(strs) {\n  const m = new Map();\n  for (const s of strs) { const k = [...s].sort().join(''); if (!m.has(k)) m.set(k, []); m.get(k).push(s); }\n  return [...m.values()];\n};\n",
        "cpp": "class Solution {\npublic:\n    vector<vector<string>> groupAnagrams(vector<string>& strs) {\n        map<string, vector<string>> m;\n        vector<string> order;\n        for (auto& s : strs) { string k = s; sort(k.begin(), k.end()); if (!m.count(k)) order.push_back(k); m[k].push_back(s); }\n        vector<vector<string>> out;\n        for (auto& k : order) out.push_back(m[k]);\n        return out;\n    }\n};\n",
        "java": "import java.util.*;\nclass Solution {\n    public List<List<String>> groupAnagrams(String[] strs) {\n        Map<String, List<String>> m = new LinkedHashMap<>();\n        for (String s : strs) { char[] c = s.toCharArray(); Arrays.sort(c); m.computeIfAbsent(new String(c), k -> new ArrayList<>()).add(s); }\n        return new ArrayList<>(m.values());\n    }\n}\n",
    },
    "countX": {
        "python": "class Solution:\n    def countX(self, board):\n        return sum(row.count('X') for row in board)\n",
        "javascript": "var countX = function(board) { return board.flat().filter((c) => c === 'X').length; };\n",
        "cpp": "class Solution {\npublic:\n    int countX(vector<vector<char>>& board) { int n = 0; for (auto& r : board) for (char c : r) n += c == 'X'; return n; }\n};\n",
        "java": "class Solution {\n    public int countX(char[][] board) { int n = 0; for (char[] r : board) for (char c : r) if (c == 'X') n++; return n; }\n}\n",
    },
    "mean": {
        "python": "class Solution:\n    def mean(self, nums):\n        return sum(nums) / len(nums)\n",
        "javascript": "var mean = function(nums) { return nums.reduce((a, b) => a + b, 0) / nums.length; };\n",
        "cpp": "class Solution {\npublic:\n    double mean(vector<long long>& nums) { long long s = 0; for (auto x : nums) s += x; return (double)s / nums.size(); }\n};\n",
        "java": "class Solution {\n    public double mean(long[] nums) { long s = 0; for (long x : nums) s += x; return (double) s / nums.length; }\n}\n",
    },
    "mergeKLists": {
        "python": "class Solution:\n    def mergeKLists(self, lists):\n        vals = []\n        for node in lists:\n            while node:\n                vals.append(node.val)\n                node = node.next\n        dummy = tail = ListNode()\n        for v in sorted(vals):\n            tail.next = ListNode(v)\n            tail = tail.next\n        return dummy.next\n",
        "javascript": "var mergeKLists = function(lists) {\n  const vals = [];\n  for (let n of lists) while (n) { vals.push(n.val); n = n.next; }\n  vals.sort((a, b) => a - b);\n  const dummy = new ListNode(); let t = dummy;\n  for (const v of vals) { t.next = new ListNode(v); t = t.next; }\n  return dummy.next;\n};\n",
        "cpp": "class Solution {\npublic:\n    ListNode* mergeKLists(vector<ListNode*>& lists) {\n        vector<int> v;\n        for (auto n : lists) for (; n; n = n->next) v.push_back(n->val);\n        sort(v.begin(), v.end());\n        ListNode dummy; ListNode* t = &dummy;\n        for (int x : v) { t->next = new ListNode(x); t = t->next; }\n        return dummy.next;\n    }\n};\n",
        "java": "import java.util.*;\nclass Solution {\n    public ListNode mergeKLists(ListNode[] lists) {\n        List<Integer> v = new ArrayList<>();\n        for (ListNode n : lists) for (; n != null; n = n.next) v.add(n.val);\n        Collections.sort(v);\n        ListNode dummy = new ListNode(), t = dummy;\n        for (int x : v) { t.next = new ListNode(x); t = t.next; }\n        return dummy.next;\n    }\n}\n",
    },
    "MinStack": {
        "python": "class MinStack:\n    def __init__(self):\n        self.s = []\n    def push(self, val):\n        self.s.append((val, min(val, self.s[-1][1]) if self.s else val))\n    def pop(self):\n        self.s.pop()\n    def top(self):\n        return self.s[-1][0]\n    def getMin(self):\n        return self.s[-1][1]\n",
        "javascript": "class MinStack {\n  constructor() { this.s = []; }\n  push(v) { this.s.push([v, this.s.length ? Math.min(v, this.s[this.s.length - 1][1]) : v]); }\n  pop() { this.s.pop(); }\n  top() { return this.s[this.s.length - 1][0]; }\n  getMin() { return this.s[this.s.length - 1][1]; }\n}\n",
        "cpp": "class MinStack {\npublic:\n    vector<pair<int,int>> s;\n    MinStack() {}\n    void push(int v) { s.push_back({v, s.empty() ? v : min(v, s.back().second)}); }\n    void pop() { s.pop_back(); }\n    int top() { return s.back().first; }\n    int getMin() { return s.back().second; }\n};\n",
        "java": "import java.util.*;\nclass MinStack {\n    Deque<int[]> s = new ArrayDeque<>();\n    public MinStack() {}\n    public void push(int v) { s.push(new int[]{v, s.isEmpty() ? v : Math.min(v, s.peek()[1])}); }\n    public void pop() { s.pop(); }\n    public int top() { return s.peek()[0]; }\n    public int getMin() { return s.peek()[1]; }\n}\n",
    },
    "hasCycle": {
        "python": "class Solution:\n    def hasCycle(self, head):\n        slow = fast = head\n        while fast and fast.next:\n            slow, fast = slow.next, fast.next.next\n            if slow is fast:\n                return True\n        return False\n",
        "javascript": "var hasCycle = function(head) {\n  let s = head, f = head;\n  while (f && f.next) { s = s.next; f = f.next.next; if (s === f) return true; }\n  return false;\n};\n",
        "cpp": "class Solution {\npublic:\n    bool hasCycle(ListNode* head) {\n        ListNode *s = head, *f = head;\n        while (f && f->next) { s = s->next; f = f->next->next; if (s == f) return true; }\n        return false;\n    }\n};\n",
        "java": "class Solution {\n    public boolean hasCycle(ListNode head) {\n        ListNode s = head, f = head;\n        while (f != null && f.next != null) { s = s.next; f = f.next.next; if (s == f) return true; }\n        return false;\n    }\n}\n",
    },
    "getIntersectionNode": {
        "python": "class Solution:\n    def getIntersectionNode(self, headA, headB):\n        a, b = headA, headB\n        while a is not b:\n            a = a.next if a else headB\n            b = b.next if b else headA\n        return a\n",
        "javascript": "var getIntersectionNode = function(headA, headB) {\n  let a = headA, b = headB;\n  while (a !== b) { a = a ? a.next : headB; b = b ? b.next : headA; }\n  return a;\n};\n",
        "cpp": "class Solution {\npublic:\n    ListNode* getIntersectionNode(ListNode* headA, ListNode* headB) {\n        ListNode *a = headA, *b = headB;\n        while (a != b) { a = a ? a->next : headB; b = b ? b->next : headA; }\n        return a;\n    }\n};\n",
        "java": "class Solution {\n    public ListNode getIntersectionNode(ListNode headA, ListNode headB) {\n        ListNode a = headA, b = headB;\n        while (a != b) { a = a != null ? a.next : headB; b = b != null ? b.next : headA; }\n        return a;\n    }\n}\n",
    },
    "splitCircular": {
        "python": "class Solution:\n    def splitCircular(self, head):\n        nodes = [head]\n        while nodes[-1].next is not head:\n            nodes.append(nodes[-1].next)\n        k = (len(nodes) + 1) // 2\n        first, second = nodes[:k], nodes[k:]\n        first[-1].next = first[0]\n        if second:\n            second[-1].next = second[0]\n        return [first[0], second[0] if second else None]\n",
        "javascript": "var splitCircular = function(head) {\n  const nodes = [head];\n  while (nodes[nodes.length - 1].next !== head) nodes.push(nodes[nodes.length - 1].next);\n  const k = Math.ceil(nodes.length / 2);\n  const a = nodes.slice(0, k), b = nodes.slice(k);\n  a[a.length - 1].next = a[0];\n  if (b.length) b[b.length - 1].next = b[0];\n  return [a[0], b.length ? b[0] : null];\n};\n",
        "cpp": "class Solution {\npublic:\n    vector<ListNode*> splitCircular(ListNode* head) {\n        vector<ListNode*> n{head};\n        while (n.back()->next != head) n.push_back(n.back()->next);\n        size_t k = (n.size() + 1) / 2;\n        n[k - 1]->next = n[0];\n        ListNode* second = nullptr;\n        if (k < n.size()) { n.back()->next = n[k]; second = n[k]; }\n        return {n[0], second};\n    }\n};\n",
        "java": "import java.util.*;\nclass Solution {\n    public ListNode[] splitCircular(ListNode head) {\n        List<ListNode> n = new ArrayList<>(List.of(head));\n        while (n.get(n.size() - 1).next != head) n.add(n.get(n.size() - 1).next);\n        int k = (n.size() + 1) / 2;\n        n.get(k - 1).next = n.get(0);\n        ListNode second = null;\n        if (k < n.size()) { n.get(n.size() - 1).next = n.get(k); second = n.get(k); }\n        return new ListNode[]{n.get(0), second};\n    }\n}\n",
    },
    "removeElement": {
        "python": "class Solution:\n    def removeElement(self, nums, val):\n        k = 0\n        for x in nums:\n            if x != val:\n                nums[k] = x\n                k += 1\n        return k\n",
        "javascript": "var removeElement = function(nums, val) {\n  let k = 0;\n  for (const x of nums) if (x !== val) nums[k++] = x;\n  return k;\n};\n",
        "cpp": "class Solution {\npublic:\n    int removeElement(vector<int>& nums, int val) {\n        int k = 0;\n        for (int x : nums) if (x != val) nums[k++] = x;\n        return k;\n    }\n};\n",
        "java": "class Solution {\n    public int removeElement(int[] nums, int val) {\n        int k = 0;\n        for (int x : nums) if (x != val) nums[k++] = x;\n        return k;\n    }\n}\n",
    },
    "cubeSum": {
        "python": "class Solution:\n    def cubeSum(self, cube):\n        return sum(x for plane in cube for row in plane for x in row)\n",
        "javascript": "var cubeSum = function(cube) { return cube.flat(2).reduce((a, b) => a + b, 0); };\n",
        "cpp": "class Solution {\npublic:\n    long long cubeSum(vector<vector<vector<int>>>& cube) {\n        long long s = 0;\n        for (auto& p : cube) for (auto& r : p) for (int x : r) s += x;\n        return s;\n    }\n};\n",
        "java": "class Solution {\n    public long cubeSum(int[][][] cube) {\n        long s = 0;\n        for (int[][] p : cube) for (int[] r : p) for (int x : r) s += x;\n        return s;\n    }\n}\n",
    },
}

SOLUTIONS["TreeBox"] = {
    "python": "class TreeBox:\n    def echo(self, root):\n        return root\n",
    "javascript": "class TreeBox {\n  echo(root) { return root; }\n}\n",
    "cpp": "class TreeBox {\npublic:\n    TreeNode* echo(TreeNode* root) { return root; }\n};\n",
    "java": "class TreeBox {\n    public TreeNode echo(TreeNode root) { return root; }\n}\n",
}

CASES = [
    (TWO_SUM, [[[2, 7, 11, 15], 9], [[3, 3], 6]], [[0, 1], [0, 1]]),
    (SORT_COLORS, [[[2, 0, 2, 1, 1, 0]], [[0]]], [[0, 0, 1, 1, 2, 2], [0]]),
    (REVERSE_LIST, [[[1, 2, 3]], [[]]], [[3, 2, 1], []]),
    (INVERT_TREE, [[[4, 2, 7, 1, 3, 6, 9]], [[]], [[1, None, 2]]], [[4, 7, 2, 9, 6, 3, 1], [], [1, 2]]),
    (
        GROUP_ANAGRAMS,
        [[["eat", "tea", "tan", "ate", "nat", "bat", 'é"q']]],
        [[["eat", "tea", "ate"], ["tan", "nat"], ["bat"], ['é"q']]],
    ),
    (COUNT_X, [[[["X", "."], [".", "X"]]]], [2]),
    (MEAN, [[[1, 2, 3, 4]], [[5000000000, 5000000000]]], [2.5, 5000000000.0]),
    (MERGE_K, [[[[1, 4, 5], [1, 3, 4], [2, 6]]], [[]]], [[1, 1, 2, 3, 4, 4, 5, 6], []]),
    (HAS_CYCLE, [[[3, 2, 0, -4], 1], [[1, 2], 0], [[1], -1], [[], -1]], [True, True, False, False]),
    (INTERSECT, [[[4, 1], [5, 6, 1], [8, 4, 5]], [[2, 6, 4], [1, 5], []], [[], [3], [7]]], [[8, 4, 5], [], [7]]),
    (SPLIT_CIRCULAR, [[[1, 5, 7]], [[2, 6, 1, 5]], [[9]]], [[[1, 5], [7]], [[2, 6], [1, 5]], [[9], []]]),
    (REMOVE_ELEMENT, [[[3, 2, 2, 3], 3], [[], 1]], [[2, [2, 2, 2, 3]], [0, []]]),
    (CUBE_SUM, [[[[[1, 2], [3]], [[4]]]], [[]]], [10, 0]),
    (TREE_BOX, [{"ops": ["TreeBox", "echo", "echo"], "args": [[], [[]], [[1, None, 2]]]}], [[None, [], [1, None, 2]]]),
    (
        MIN_STACK,
        [
            {
                "ops": ["MinStack", "push", "push", "push", "getMin", "pop", "top", "getMin"],
                "args": [[], [-2], [0], [-3], [], [], [], []],
            }
        ],
        [[None, None, None, None, -3, None, 0, -2]],
    ),
]

TOOLCHAIN = {
    "python": ["python3"],
    "javascript": ["node"],
    "cpp": ["g++"],
    "java": ["javac", "java", "jar"],
}


def _available(language: str) -> bool:
    if not all(shutil.which(tool) for tool in TOOLCHAIN[language]):
        return False
    if language == "java":  # macOS ships a /usr/bin/javac stub without a JDK
        return subprocess.run(["javac", "-version"], capture_output=True).returncode == 0
    return True


def _run_local(language: str, files: dict[str, str], tests: list, workdir: Path) -> list[dict]:
    for name, content in files.items():
        (workdir / name).write_text(content, encoding="utf-8")
    (workdir / "tests.json").write_text(json.dumps(tests), encoding="utf-8")
    if language == "cpp":
        subprocess.run(
            ["g++", "-O1", "-std=c++17", "-o", "main", "main.cpp"], cwd=workdir, check=True, capture_output=True
        )
        cmd = ["./main"]
    elif language == "java":
        subprocess.run(["javac", "-d", "out", "Main.java"], cwd=workdir, check=True, capture_output=True)
        cmd = ["java", "-cp", "out", "Main"]
    elif language == "python":
        cmd = ["python3", "main.py"]
    else:
        cmd = ["node", "main.js"]
    subprocess.run(cmd, cwd=workdir, check=True, capture_output=True, timeout=60)
    lines = (workdir / "result.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


@pytest.mark.parametrize("language", ["python", "javascript", "cpp", "java"])
@pytest.mark.parametrize(("spec", "tests", "expected"), CASES, ids=[c[0]["name"] for c in CASES])
def test_generated_program_runs_solution(language, spec, tests, expected, tmp_path):
    if not _available(language):
        pytest.skip(f"{language} toolchain not installed")
    parse_spec(spec)
    files = drivers.program(language, spec, SOLUTIONS[spec["name"]][language])
    results = _run_local(language, files, tests, tmp_path)
    assert [r["i"] for r in results] == list(range(len(tests)))
    assert all(r["ok"] for r in results), results
    assert [r["out"] for r in results] == expected
    assert all(r["ms"] >= 0 for r in results)


@pytest.mark.parametrize("language", ["python", "javascript", "cpp", "java"])
def test_exception_is_reported_per_test(language, tmp_path):
    if not _available(language):
        pytest.skip(f"{language} toolchain not installed")
    throwing = {
        "python": "class Solution:\n    def twoSum(self, nums, target):\n        if target < 0:\n            raise ValueError('neg')\n        return [0, 1]\n",
        "javascript": "var twoSum = function(nums, target) { if (target < 0) throw new Error('neg'); return [0, 1]; };\n",
        "cpp": 'class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) { if (target < 0) throw runtime_error("neg"); return {0, 1}; }\n};\n',
        "java": 'class Solution {\n    public int[] twoSum(int[] nums, int target) { if (target < 0) throw new IllegalStateException("neg"); return new int[]{0, 1}; }\n}\n',
    }[language]
    files = drivers.program(language, TWO_SUM, throwing)
    results = _run_local(language, files, [[[1, 2], -1], [[1, 2], 3]], tmp_path)
    assert results[0]["ok"] is False and "neg" in results[0]["err"]
    assert results[1] == {**results[1], "ok": True, "out": [0, 1]}


@pytest.mark.parametrize("language", ["python", "javascript", "cpp", "java"])
@pytest.mark.parametrize("spec", [c[0] for c in CASES], ids=[c[0]["name"] for c in CASES])
def test_starter_mentions_name(language, spec):
    code = drivers.starter(language, spec)
    assert spec["name"] in code


def test_java_hoists_imports_and_strips_public():
    files = drivers.program("java", TWO_SUM, SOLUTIONS["twoSum"]["java"])
    source = files["Main.java"]
    assert source.index("import java.util.HashMap;") < source.index("class ListNode")
    assert "public class Solution" not in source
    assert source.count("public class Main") == 1


@pytest.mark.parametrize("spec", [REVERSE_LIST, INVERT_TREE, MERGE_K, INTERSECT, TREE_BOX], ids=lambda s: s["name"])
def test_java_encodes_node_results_with_encnode(spec):
    """Regression: Java wrote a null ListNode/TreeNode result as null instead of []. Checkable without a JDK."""
    source = drivers.program("java", spec, SOLUTIONS[spec["name"]]["java"])["Main.java"]
    assert "encNode(res, " in source  # the generated call site, not the runtime helper
    assert "enc(res, r);" not in source and "enc(res, obj." not in source


def test_unknown_language():
    with pytest.raises(ValueError):
        drivers.starter("cobol", TWO_SUM)
