"""Java 17 driver: hoisted imports + ListNode/TreeNode + user code + `public class Main` (JSON runtime + loop).

Everything lives in one `Main.java`, so the user's top-level classes must not be `public`; the
generator strips a leading `public` from top-level class declarations. Argument decoding is
generated per signature; result encoding is reflective, so any natural return type works
(`int[]`, `List<List<Integer>>`, `String`, ...).
"""

from __future__ import annotations

import re

from app.modules.dsa.judge.drivers.common import (
    ProgramFiles,
    Spec,
    hidden_params,
    mutate_hint,
    scalar_and_depth,
    visible_params,
)

_IMPORT_RE = re.compile(r"^\s*import\s+(static\s+)?[\w.]+(\.\*)?\s*;\s*$", re.M)
_PACKAGE_RE = re.compile(r"^\s*package\s+[\w.]+\s*;\s*$", re.M)
_PUBLIC_CLASS_RE = re.compile(r"^public\s+((?:final\s+|abstract\s+)*)(class|interface|enum|record)\b", re.M)

_HEADER = """\
import java.util.*;
import java.util.function.*;
import java.util.stream.*;
import java.io.*;
import java.math.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
"""

_NODES = """
class ListNode {
    int val;
    ListNode next;
    ListNode() {}
    ListNode(int val) { this.val = val; }
    ListNode(int val, ListNode next) { this.val = val; this.next = next; }
}

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;
    TreeNode() {}
    TreeNode(int val) { this.val = val; }
    TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
}
"""

_RUNTIME = r"""
    static final class J {
        static final int NUL = 0, BOOL = 1, NUM = 2, STR = 3, ARR = 4, OBJ = 5;
        int k = NUL;
        boolean b;
        String raw, s;
        List<J> a = new ArrayList<>();
        Map<String, J> o = new HashMap<>();
        J get(int i) { return a.get(i); }
        J at(String key) {
            J v = o.get(key);
            if (v == null) throw new RuntimeException("missing key " + key);
            return v;
        }
    }

    static final class Parser {
        final String in;
        int p = 0;
        Parser(String in) { this.in = in; }
        void ws() { while (p < in.length() && Character.isWhitespace(in.charAt(p))) p++; }
        String str() {
            p++;
            StringBuilder sb = new StringBuilder();
            while (in.charAt(p) != '"') {
                char c = in.charAt(p++);
                if (c != '\\') { sb.append(c); continue; }
                char e = in.charAt(p++);
                switch (e) {
                    case 'n': sb.append('\n'); break;
                    case 't': sb.append('\t'); break;
                    case 'r': sb.append('\r'); break;
                    case 'b': sb.append('\b'); break;
                    case 'f': sb.append('\f'); break;
                    case 'u': sb.append((char) Integer.parseInt(in.substring(p, p + 4), 16)); p += 4; break;
                    default: sb.append(e);
                }
            }
            p++;
            return sb.toString();
        }
        J value() {
            ws();
            J j = new J();
            char c = in.charAt(p);
            if (c == '[' || c == '{') {
                boolean arr = c == '[';
                j.k = arr ? J.ARR : J.OBJ;
                p++;
                ws();
                if (in.charAt(p) == (arr ? ']' : '}')) { p++; return j; }
                while (true) {
                    if (arr) j.a.add(value());
                    else {
                        ws();
                        String key = str();
                        ws();
                        p++;
                        j.o.put(key, value());
                    }
                    ws();
                    if (in.charAt(p) == ',') { p++; continue; }
                    p++;
                    return j;
                }
            }
            if (c == '"') { j.k = J.STR; j.s = str(); return j; }
            if (in.startsWith("true", p)) { p += 4; j.k = J.BOOL; j.b = true; return j; }
            if (in.startsWith("false", p)) { p += 5; j.k = J.BOOL; return j; }
            if (in.startsWith("null", p)) { p += 4; return j; }
            int start = p;
            while (p < in.length() && "+-.eE0123456789".indexOf(in.charAt(p)) >= 0) p++;
            j.k = J.NUM;
            j.raw = in.substring(start, p);
            return j;
        }
    }

    static int toInt(J j) { return Integer.parseInt(j.raw); }
    static long toLong(J j) { return Long.parseLong(j.raw); }
    static double toDouble(J j) { return Double.parseDouble(j.raw); }
    static boolean toBool(J j) { return j.b; }
    static String toStr(J j) { return j.s; }
    static char toChar(J j) { return j.s.isEmpty() ? '\0' : j.s.charAt(0); }
    static int[] toIntArr(J j) { int[] r = new int[j.a.size()]; for (int i = 0; i < r.length; i++) r[i] = toInt(j.get(i)); return r; }
    static long[] toLongArr(J j) { long[] r = new long[j.a.size()]; for (int i = 0; i < r.length; i++) r[i] = toLong(j.get(i)); return r; }
    static double[] toDoubleArr(J j) { double[] r = new double[j.a.size()]; for (int i = 0; i < r.length; i++) r[i] = toDouble(j.get(i)); return r; }
    static boolean[] toBoolArr(J j) { boolean[] r = new boolean[j.a.size()]; for (int i = 0; i < r.length; i++) r[i] = toBool(j.get(i)); return r; }
    static String[] toStrArr(J j) { String[] r = new String[j.a.size()]; for (int i = 0; i < r.length; i++) r[i] = toStr(j.get(i)); return r; }
    static char[] toCharArr(J j) { char[] r = new char[j.a.size()]; for (int i = 0; i < r.length; i++) r[i] = toChar(j.get(i)); return r; }
    static int[][] toIntArr2(J j) { int[][] r = new int[j.a.size()][]; for (int i = 0; i < r.length; i++) r[i] = toIntArr(j.get(i)); return r; }
    static long[][] toLongArr2(J j) { long[][] r = new long[j.a.size()][]; for (int i = 0; i < r.length; i++) r[i] = toLongArr(j.get(i)); return r; }
    static double[][] toDoubleArr2(J j) { double[][] r = new double[j.a.size()][]; for (int i = 0; i < r.length; i++) r[i] = toDoubleArr(j.get(i)); return r; }
    static boolean[][] toBoolArr2(J j) { boolean[][] r = new boolean[j.a.size()][]; for (int i = 0; i < r.length; i++) r[i] = toBoolArr(j.get(i)); return r; }
    static String[][] toStrArr2(J j) { String[][] r = new String[j.a.size()][]; for (int i = 0; i < r.length; i++) r[i] = toStrArr(j.get(i)); return r; }
    static int[][][] toIntArr3(J j) { int[][][] r = new int[j.a.size()][][]; for (int i = 0; i < r.length; i++) r[i] = toIntArr2(j.get(i)); return r; }
    static long[][][] toLongArr3(J j) { long[][][] r = new long[j.a.size()][][]; for (int i = 0; i < r.length; i++) r[i] = toLongArr2(j.get(i)); return r; }
    static double[][][] toDoubleArr3(J j) { double[][][] r = new double[j.a.size()][][]; for (int i = 0; i < r.length; i++) r[i] = toDoubleArr2(j.get(i)); return r; }
    static boolean[][][] toBoolArr3(J j) { boolean[][][] r = new boolean[j.a.size()][][]; for (int i = 0; i < r.length; i++) r[i] = toBoolArr2(j.get(i)); return r; }
    static String[][][] toStrArr3(J j) { String[][][] r = new String[j.a.size()][][]; for (int i = 0; i < r.length; i++) r[i] = toStrArr2(j.get(i)); return r; }
    static char[][][] toCharArr3(J j) { char[][][] r = new char[j.a.size()][][]; for (int i = 0; i < r.length; i++) r[i] = toCharArr2(j.get(i)); return r; }
    static char[][] toCharArr2(J j) { char[][] r = new char[j.a.size()][]; for (int i = 0; i < r.length; i++) r[i] = toCharArr(j.get(i)); return r; }
    static ListNode toList(J j) {
        ListNode dummy = new ListNode(), tail = dummy;
        for (J x : j.a) { tail.next = new ListNode(toInt(x)); tail = tail.next; }
        return dummy.next;
    }
    static ListNode[] toListArr(J j) { ListNode[] r = new ListNode[j.a.size()]; for (int i = 0; i < r.length; i++) r[i] = toList(j.get(i)); return r; }
    static TreeNode toTree(J j) {
        if (j.a.isEmpty()) return null;
        TreeNode[] nodes = new TreeNode[j.a.size()];
        for (int i = 0; i < nodes.length; i++) nodes[i] = j.get(i).k == J.NUL ? null : new TreeNode(toInt(j.get(i)));
        int k = 1;
        for (TreeNode n : nodes) {
            if (n == null) continue;
            n.left = k < nodes.length ? nodes[k] : null; k++;
            n.right = k < nodes.length ? nodes[k] : null; k++;
        }
        return nodes[0];
    }

    static final int MAX_NODES = 200000;
    static void quote(StringBuilder o, String s) {
        o.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"') o.append("\\\"");
            else if (c == '\\') o.append("\\\\");
            else if (c < 0x20) o.append(String.format("\\u%04x", (int) c));
            else o.append(c);
        }
        o.append('"');
    }
    static void enc(StringBuilder o, Object v) {
        if (v == null) { o.append("null"); return; }
        if (v instanceof Boolean || v instanceof Integer || v instanceof Long || v instanceof Short || v instanceof Byte) { o.append(v); return; }
        if (v instanceof Double || v instanceof Float) {
            double d = ((Number) v).doubleValue();
            if (Double.isNaN(d) || Double.isInfinite(d)) throw new RuntimeException("result is not a finite number");
            o.append(d);
            return;
        }
        if (v instanceof Character) { quote(o, String.valueOf(v)); return; }
        if (v instanceof CharSequence) { quote(o, v.toString()); return; }
        if (v instanceof ListNode) {
            o.append('[');
            int n = 0;
            for (ListNode h = (ListNode) v; h != null; h = h.next) {
                if (++n > MAX_NODES) throw new RuntimeException("linked list too long or has a cycle");
                if (n > 1) o.append(',');
                o.append(h.val);
            }
            o.append(']');
            return;
        }
        if (v instanceof TreeNode) {
            List<String> parts = new ArrayList<>();
            List<TreeNode> q = new ArrayList<>();
            q.add((TreeNode) v);
            for (int i = 0; i < q.size(); i++) {
                TreeNode n = q.get(i);
                if (n == null) { parts.add("null"); continue; }
                if (parts.size() > 2 * MAX_NODES) throw new RuntimeException("tree too large or has a cycle");
                parts.add(String.valueOf(n.val));
                q.add(n.left);
                q.add(n.right);
            }
            while (!parts.isEmpty() && parts.get(parts.size() - 1).equals("null")) parts.remove(parts.size() - 1);
            o.append('[').append(String.join(",", parts)).append(']');
            return;
        }
        if (v.getClass().isArray()) {
            o.append('[');
            int n = java.lang.reflect.Array.getLength(v);
            for (int i = 0; i < n; i++) { if (i > 0) o.append(','); enc(o, java.lang.reflect.Array.get(v, i)); }
            o.append(']');
            return;
        }
        if (v instanceof Iterable) {
            o.append('[');
            boolean first = true;
            for (Object x : (Iterable<?>) v) { if (!first) o.append(','); first = false; enc(o, x); }
            o.append(']');
            return;
        }
        throw new RuntimeException("cannot encode result of type " + v.getClass().getName());
    }
    // ListNode / TreeNode results: null is the empty list/tree, which the judge expects as [].
    static void encNode(StringBuilder o, Object v) {
        if (v == null) { o.append("[]"); return; }
        if (v instanceof ListNode[]) {
            ListNode[] lists = (ListNode[]) v;
            o.append('[');
            for (int i = 0; i < lists.length; i++) { if (i > 0) o.append(','); encNode(o, lists[i]); }
            o.append(']');
            return;
        }
        enc(o, v);
    }

    // Link directives: build cycles, circular lists and shared tails before calling user code.
    static List<ListNode> nodesOf(ListNode head) {
        List<ListNode> out = new ArrayList<>();
        for (; head != null; head = head.next) out.add(head);
        return out;
    }
    static void linkCycle(ListNode head, int pos) {
        List<ListNode> nodes = nodesOf(head);
        if (!nodes.isEmpty() && pos >= 0) nodes.get(nodes.size() - 1).next = nodes.get(pos);
    }
    static void linkCircular(ListNode head) {
        List<ListNode> nodes = nodesOf(head);
        if (!nodes.isEmpty()) nodes.get(nodes.size() - 1).next = nodes.get(0);
    }
    static ListNode appendList(ListNode head, ListNode tail) {
        List<ListNode> nodes = nodesOf(head);
        if (nodes.isEmpty()) return tail;
        nodes.get(nodes.size() - 1).next = tail;
        return head;
    }
    static ListNode fromValues(int[] values) {
        ListNode dummy = new ListNode(), tail = dummy;
        for (int v : values) { tail.next = new ListNode(v); tail = tail.next; }
        return dummy.next;
    }
    static void encCircular(StringBuilder o, Object v) {
        if (v instanceof ListNode || v == null) {
            ListNode head = (ListNode) v;
            o.append('[');
            int n = 0;
            for (ListNode node = head; node != null;) {
                if (++n > MAX_NODES) throw new RuntimeException("circular list too long");
                if (n > 1) o.append(',');
                o.append(node.val);
                node = node.next;
                if (node == head) { o.append(']'); return; }
            }
            if (n > 0) throw new RuntimeException("expected a circular list (the tail should point back to the head)");
            o.append(']');
            return;
        }
        Iterable<?> lists = v instanceof ListNode[] ? Arrays.asList((ListNode[]) v) : (Iterable<?>) v;
        o.append('[');
        boolean first = true;
        for (Object x : lists) { if (!first) o.append(','); first = false; encCircular(o, x); }
        o.append(']');
    }

    static String err(Throwable t) {
        String msg = t.getClass().getSimpleName() + (t.getMessage() == null ? "" : ": " + t.getMessage());
        return msg.length() > 500 ? msg.substring(0, 500) : msg;
    }

    public static void main(String[] args) throws Exception {
        Thread t = new Thread(null, () -> {
            try { runAll(); } catch (IOException e) { throw new UncheckedIOException(e); }
        }, "dsa", 256L << 20);
        t.start();
        t.join();
    }

    static void runAll() throws IOException {
        String text = new String(Files.readAllBytes(Paths.get("tests.json")), StandardCharsets.UTF_8);
        J tests = new Parser(text).value();
        try (BufferedWriter out = Files.newBufferedWriter(Paths.get("result.jsonl"), StandardCharsets.UTF_8)) {
            for (int i = 0; i < tests.a.size(); i++) {
                J input = tests.get(i);
                StringBuilder line = new StringBuilder("{\"i\":").append(i).append(',');
                try {
                    StringBuilder res = new StringBuilder();
                    double ms = runOne(input, res);
                    line.append("\"ok\":true,\"out\":").append(res).append(",\"ms\":").append(String.format(Locale.ROOT, "%.3f", ms)).append('}');
                } catch (Throwable e) {
                    line.append("\"ok\":false,\"err\":");
                    quote(line, err(e));
                    line.append('}');
                }
                out.write(line.toString());
                out.newLine();
                out.flush();
            }
        }
    }
"""

_SCALARS = {"int": "int", "long": "long", "double": "double", "bool": "boolean", "string": "String", "char": "char"}
_DECODER_NAMES = {"int": "Int", "long": "Long", "double": "Double", "bool": "Bool", "string": "Str", "char": "Char"}
_BOXED = {"int": "Integer", "long": "Long", "double": "Double", "boolean": "Boolean", "char": "Character"}


def java_type(type_: str) -> str:
    if type_ == "void":
        return "void"
    if type_ in ("ListNode", "TreeNode"):
        return type_
    if type_ == "ListNode[]":
        return "ListNode[]"
    base, depth = scalar_and_depth(type_)
    return _SCALARS[base] + "[]" * depth


def _return_type(type_: str) -> str:
    """Idiomatic starter return type; the encoder accepts arrays and Lists alike."""
    base, depth = scalar_and_depth(type_)
    if depth == 2 and base in _SCALARS:
        elem = _SCALARS[base]
        return f"List<List<{_BOXED.get(elem, elem)}>>"
    if depth == 1 and base == "string":
        return "List<String>"
    return java_type(type_)


def _decode(type_: str, source: str) -> str:
    if type_ == "ListNode":
        return f"toList({source})"
    if type_ == "TreeNode":
        return f"toTree({source})"
    if type_ == "ListNode[]":
        return f"toListArr({source})"
    base, depth = scalar_and_depth(type_)
    suffix = {0: "", 1: "Arr", 2: "Arr2", 3: "Arr3"}[depth]
    return f"to{_DECODER_NAMES[base]}{suffix}({source})"


def _params(params: list[dict]) -> str:
    return ", ".join(f"{java_type(p['type'])} {p['name']}" for p in params)


def starter(spec: Spec) -> str:
    if spec["kind"] == "function":
        hint = mutate_hint(spec)
        return (
            "class Solution {\n"
            f"    public {_return_type(spec['returns'])} {spec['name']}({_params(visible_params(spec))}) {{\n"
            f"        {'// ' + hint if hint else ''}\n"
            "    }\n"
            "}\n"
        )
    lines = [
        f"class {spec['name']} {{",
        "",
        f"    public {spec['name']}({_params(spec['constructor'])}) {{",
        "        ",
        "    }",
        "",
    ]
    for m in spec["methods"]:
        lines += [
            f"    public {_return_type(m['returns'])} {m['name']}({_params(m['params'])}) {{",
            "        ",
            "    }",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n}\n"


def _link_lines(spec: Spec, index: dict[str, int]) -> list[str]:
    lines = []
    for link in spec.get("links") or []:
        if link["kind"] == "cycle":
            lines.append(f"linkCycle(a{index[link['list']]}, a{index[link['pos']]});")
        elif link["kind"] == "circular":
            lines.append(f"linkCircular(a{index[link['list']]});")
        else:
            a, b, shared = index[link["a"]], index[link["b"]], index[link["shared"]]
            lines += [
                f"ListNode shared{shared} = fromValues(a{shared});",
                f"a{a} = appendList(a{a}, shared{shared});",
                f"a{b} = appendList(a{b}, shared{shared});",
            ]
    return lines


def _encoder(type_: str) -> str:
    """Name of the runtime encoder for a declared result type (node types map null to [])."""
    return "encNode" if type_ in ("ListNode", "TreeNode", "ListNode[]") else "enc"


def _function_body(spec: Spec) -> list[str]:
    index = {p["name"]: i for i, p in enumerate(spec["params"])}
    lines = [
        f"{java_type(p['type'])} a{i} = {_decode(p['type'], f'input.get({i})')};" for i, p in enumerate(spec["params"])
    ]
    lines += _link_lines(spec, index)
    hidden = hidden_params(spec)
    call = f"new Solution().{spec['name']}({', '.join(f'a{index[p]}' for p in index if p not in hidden)})"
    lines.append("long t0 = System.nanoTime();")
    mutates, returns = spec.get("mutates"), spec["returns"]
    if mutates and returns == "void":
        lines += [f"{call};", "long t1 = System.nanoTime();", f"enc(res, a{index[mutates]});"]
    elif mutates:
        lines += [
            f"Object r = {call};",
            "long t1 = System.nanoTime();",
            "res.append('[');",
            f"{_encoder(returns)}(res, r);",
            "res.append(',');",
            f"enc(res, a{index[mutates]});",
            "res.append(']');",
        ]
    else:
        encoder = "encCircular" if spec.get("circular_output") else _encoder(returns)
        lines += [f"Object r = {call};", "long t1 = System.nanoTime();", f"{encoder}(res, r);"]
    lines.append("return (t1 - t0) / 1e6;")
    return lines


def _class_body(spec: Spec) -> list[str]:
    name = spec["name"]
    lines = [
        'J ops = input.at("ops");',
        'J args = input.at("args");',
        'res.append("[null");',
        "long t0 = System.nanoTime();",
    ]
    ctor = [_decode(p["type"], f"args.get(0).get({i})") for i, p in enumerate(spec["constructor"])]
    lines.append(f"{name} obj = new {name}({', '.join(ctor)});")
    lines += [
        "for (int k = 1; k < ops.a.size(); k++) {",
        "    String op = ops.get(k).s;",
        "    J m = args.get(k);",
        "    res.append(',');",
        "    switch (op) {",
    ]
    for method in spec["methods"]:
        margs = ", ".join(_decode(p["type"], f"m.get({i})") for i, p in enumerate(method["params"]))
        call = f"obj.{method['name']}({margs})"
        lines.append(f'        case "{method["name"]}":')
        if method["returns"] == "void":
            lines += [f"            {call};", '            res.append("null");']
        else:
            lines.append(f"            {_encoder(method['returns'])}(res, {call});")
        lines.append("            break;")
    lines += [
        '        default: throw new RuntimeException("unknown op: " + op);',
        "    }",
        "}",
        "long t1 = System.nanoTime();",
        "res.append(']');",
        "return (t1 - t0) / 1e6;",
    ]
    return lines


def _split_user_code(user_code: str) -> tuple[list[str], str]:
    imports = [m.group(0).strip() for m in _IMPORT_RE.finditer(user_code)]
    body = _IMPORT_RE.sub("", _PACKAGE_RE.sub("", user_code))
    body = _PUBLIC_CLASS_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}", body)
    return imports, body


def program(spec: Spec, user_code: str) -> ProgramFiles:
    imports, body = _split_user_code(user_code)
    run_one = _function_body(spec) if spec["kind"] == "function" else _class_body(spec)
    run_one_src = "\n".join(f"        {line}" for line in run_one)
    source = (
        _HEADER
        + "".join(f"{imp}\n" for imp in imports)
        + _NODES
        + "\n// ---- user code ----\n"
        + body
        + "\n// ---- end user code ----\n\n"
        + "public class Main {\n"
        + _RUNTIME
        + "\n    static double runOne(J input, StringBuilder res) {\n"
        + run_one_src
        + "\n    }\n}\n"
    )
    return {"Main.java": source}
