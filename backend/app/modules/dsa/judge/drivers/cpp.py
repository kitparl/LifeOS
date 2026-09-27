"""C++17 driver: headers + ListNode/TreeNode + user code + a tiny JSON runtime + a generated test loop.

Argument decoding is generated per signature (C++ is statically typed); result encoding uses
overloads, so users may return any natural type (e.g. `vector<vector<int>>`).
"""

from __future__ import annotations

from app.modules.dsa.judge.drivers.common import (
    ProgramFiles,
    Spec,
    hidden_params,
    mutate_hint,
    scalar_and_depth,
    visible_params,
)

_HEADERS = """\
#include <algorithm>
#include <array>
#include <bitset>
#include <cassert>
#include <chrono>
#include <climits>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <list>
#include <map>
#include <memory>
#include <numeric>
#include <queue>
#include <random>
#include <set>
#include <sstream>
#include <stack>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
using namespace std;

struct ListNode {
    int val;
    ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode *next) : val(x), next(next) {}
};

struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
};
"""

_RUNTIME = r"""
namespace dsa {
struct J {
    enum Kind { NUL, BOOL, NUM, STR, ARR, OBJ } k = NUL;
    bool b = false;
    std::string raw, s;
    std::vector<J> a;
    std::vector<std::pair<std::string, J>> o;
    const J& at(const std::string& key) const {
        for (const auto& kv : o) if (kv.first == key) return kv.second;
        throw std::runtime_error("missing key " + key);
    }
};

struct Parser {
    const std::string& in;
    size_t p = 0;
    explicit Parser(const std::string& text) : in(text) {}
    void ws() { while (p < in.size() && std::isspace((unsigned char)in[p])) ++p; }
    static void utf8(std::string& out, unsigned cp) {
        if (cp < 0x80) out += (char)cp;
        else if (cp < 0x800) { out += (char)(0xC0 | (cp >> 6)); out += (char)(0x80 | (cp & 0x3F)); }
        else if (cp < 0x10000) { out += (char)(0xE0 | (cp >> 12)); out += (char)(0x80 | ((cp >> 6) & 0x3F)); out += (char)(0x80 | (cp & 0x3F)); }
        else { out += (char)(0xF0 | (cp >> 18)); out += (char)(0x80 | ((cp >> 12) & 0x3F)); out += (char)(0x80 | ((cp >> 6) & 0x3F)); out += (char)(0x80 | (cp & 0x3F)); }
    }
    std::string str() {
        ++p;
        std::string out;
        while (p < in.size() && in[p] != '"') {
            char c = in[p++];
            if (c != '\\') { out += c; continue; }
            char e = in[p++];
            switch (e) {
                case 'n': out += '\n'; break;
                case 't': out += '\t'; break;
                case 'r': out += '\r'; break;
                case 'b': out += '\b'; break;
                case 'f': out += '\f'; break;
                case 'u': {
                    unsigned cp = std::stoul(in.substr(p, 4), nullptr, 16);
                    p += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && in.compare(p, 2, "\\u") == 0) {
                        unsigned lo = std::stoul(in.substr(p + 2, 4), nullptr, 16);
                        p += 6;
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                    }
                    utf8(out, cp);
                    break;
                }
                default: out += e;
            }
        }
        ++p;
        return out;
    }
    J value() {
        ws();
        J j;
        if (p >= in.size()) throw std::runtime_error("bad json");
        char c = in[p];
        if (c == '[' || c == '{') {
            bool arr = c == '[';
            j.k = arr ? J::ARR : J::OBJ;
            ++p;
            ws();
            if (in[p] == (arr ? ']' : '}')) { ++p; return j; }
            while (true) {
                if (arr) j.a.push_back(value());
                else {
                    ws();
                    std::string key = str();
                    ws();
                    ++p;  // ':'
                    j.o.emplace_back(key, value());
                }
                ws();
                if (in[p] == ',') { ++p; continue; }
                ++p;  // ']' or '}'
                return j;
            }
        }
        if (c == '"') { j.k = J::STR; j.s = str(); return j; }
        if (in.compare(p, 4, "true") == 0) { p += 4; j.k = J::BOOL; j.b = true; return j; }
        if (in.compare(p, 5, "false") == 0) { p += 5; j.k = J::BOOL; return j; }
        if (in.compare(p, 4, "null") == 0) { p += 4; return j; }
        size_t start = p;
        while (p < in.size() && (std::isdigit((unsigned char)in[p]) || std::strchr("+-.eE", in[p]))) ++p;
        j.k = J::NUM;
        j.raw = in.substr(start, p - start);
        return j;
    }
};

inline int toInt(const J& j) { return (int)std::stoll(j.raw); }
inline long long toLong(const J& j) { return std::stoll(j.raw); }
inline double toDouble(const J& j) { return std::stod(j.raw); }
inline bool toBool(const J& j) { return j.b; }
inline std::string toStr(const J& j) { return j.s; }
inline char toChar(const J& j) { return j.s.empty() ? '\0' : j.s[0]; }
template <class F>
auto vec(const J& j, F f) -> std::vector<decltype(f(j))> {
    std::vector<decltype(f(j))> v;
    v.reserve(j.a.size());
    for (const auto& x : j.a) v.push_back(f(x));
    return v;
}
inline ListNode* toList(const J& j) {
    ListNode dummy;
    ListNode* tail = &dummy;
    for (const auto& x : j.a) { tail->next = new ListNode(toInt(x)); tail = tail->next; }
    return dummy.next;
}
inline TreeNode* toTree(const J& j) {
    if (j.a.empty()) return nullptr;
    std::vector<TreeNode*> nodes;
    for (const auto& x : j.a) nodes.push_back(x.k == J::NUL ? nullptr : new TreeNode(toInt(x)));
    size_t k = 1;
    for (TreeNode* n : nodes) {
        if (!n) continue;
        n->left = k < nodes.size() ? nodes[k] : nullptr; ++k;
        n->right = k < nodes.size() ? nodes[k] : nullptr; ++k;
    }
    return nodes[0];
}

const size_t MAX_NODES = 200000;
inline void quote(std::string& o, const std::string& s) {
    o += '"';
    for (unsigned char c : s) {
        if (c == '"') o += "\\\"";
        else if (c == '\\') o += "\\\\";
        else if (c < 0x20) { char buf[8]; std::snprintf(buf, sizeof buf, "\\u%04x", c); o += buf; }
        else o += (char)c;
    }
    o += '"';
}
inline void enc(std::string& o, bool v) { o += v ? "true" : "false"; }
inline void enc(std::string& o, char c) { quote(o, std::string(1, c)); }
template <class T, typename std::enable_if<std::is_integral<T>::value && !std::is_same<T, bool>::value && !std::is_same<T, char>::value, int>::type = 0>
void enc(std::string& o, T v) { o += std::to_string(v); }
template <class T, typename std::enable_if<std::is_floating_point<T>::value, int>::type = 0>
void enc(std::string& o, T v) {
    if (!std::isfinite((double)v)) throw std::runtime_error("result is not a finite number");
    char buf[64];
    std::snprintf(buf, sizeof buf, "%.17g", (double)v);
    o += buf;
}
inline void enc(std::string& o, const std::string& s) { quote(o, s); }
inline void enc(std::string& o, const char* s) { quote(o, s); }
inline void enc(std::string& o, ListNode* h) {
    o += '[';
    size_t n = 0;
    for (; h; h = h->next) {
        if (++n > MAX_NODES) throw std::runtime_error("linked list too long or has a cycle");
        if (n > 1) o += ',';
        o += std::to_string(h->val);
    }
    o += ']';
}
inline void enc(std::string& o, TreeNode* root) {
    std::vector<TreeNode*> q{root};
    std::vector<std::string> parts;
    for (size_t i = 0; i < q.size(); ++i) {
        if (!q[i]) { parts.push_back("null"); continue; }
        if (parts.size() > 2 * MAX_NODES) throw std::runtime_error("tree too large or has a cycle");
        parts.push_back(std::to_string(q[i]->val));
        q.push_back(q[i]->left);
        q.push_back(q[i]->right);
    }
    while (!parts.empty() && parts.back() == "null") parts.pop_back();
    o += '[';
    for (size_t i = 0; i < parts.size(); ++i) { if (i) o += ','; o += parts[i]; }
    o += ']';
}
template <class T>
void enc(std::string& o, const std::vector<T>& v) {
    o += '[';
    bool first = true;
    for (const auto& x : v) {
        if (!first) o += ',';
        first = false;
        enc(o, static_cast<T>(x));
    }
    o += ']';
}

// Link directives: build cycles, circular lists and shared tails before calling user code.
inline std::vector<ListNode*> nodesOf(ListNode* head) {
    std::vector<ListNode*> out;
    for (; head; head = head->next) out.push_back(head);
    return out;
}
inline void linkCycle(ListNode* head, int pos) {
    auto nodes = nodesOf(head);
    if (!nodes.empty() && pos >= 0) nodes.back()->next = nodes[pos];
}
inline void linkCircular(ListNode* head) {
    auto nodes = nodesOf(head);
    if (!nodes.empty()) nodes.back()->next = nodes.front();
}
inline ListNode* appendList(ListNode* head, ListNode* tail) {
    auto nodes = nodesOf(head);
    if (nodes.empty()) return tail;
    nodes.back()->next = tail;
    return head;
}
inline ListNode* fromValues(const std::vector<int>& values) {
    ListNode dummy;
    ListNode* tail = &dummy;
    for (int v : values) { tail->next = new ListNode(v); tail = tail->next; }
    return dummy.next;
}
inline void encCircular(std::string& o, ListNode* head) {
    o += '[';
    size_t n = 0;
    for (ListNode* node = head; node;) {
        if (++n > MAX_NODES) throw std::runtime_error("circular list too long");
        if (n > 1) o += ',';
        o += std::to_string(node->val);
        node = node->next;
        if (node == head) { o += ']'; return; }
    }
    if (n) throw std::runtime_error("expected a circular list (the tail should point back to the head)");
    o += ']';
}
inline void encCircular(std::string& o, const std::vector<ListNode*>& lists) {
    o += '[';
    for (size_t i = 0; i < lists.size(); ++i) { if (i) o += ','; encCircular(o, lists[i]); }
    o += ']';
}
}  // namespace dsa
"""

_MAIN_HEAD = r"""
int main() {
    std::ifstream fin("tests.json");
    std::stringstream buffer;
    buffer << fin.rdbuf();
    const std::string text = buffer.str();
    dsa::Parser parser(text);
    const dsa::J tests = parser.value();
    std::ofstream out("result.jsonl");
    for (size_t i = 0; i < tests.a.size(); ++i) {
        const dsa::J& input = tests.a[i];
        std::string line = "{\"i\":" + std::to_string(i) + ",";
        try {
            std::string res;
            double ms = 0;
"""

_MAIN_TAIL = r"""
            char msbuf[32];
            std::snprintf(msbuf, sizeof msbuf, "%.3f", ms);
            line += "\"ok\":true,\"out\":" + res + ",\"ms\":" + msbuf + "}";
        } catch (const std::exception& e) {
            line += "\"ok\":false,\"err\":";
            dsa::quote(line, std::string("exception: ") + e.what());
            line += "}";
        } catch (...) {
            line += "\"ok\":false,\"err\":\"unknown exception\"}";
        }
        out << line << '\n';
        out.flush();
    }
    return 0;
}
"""

_SCALARS = {"int": "int", "long": "long long", "double": "double", "bool": "bool", "string": "string", "char": "char"}
_DECODERS = {
    "int": "dsa::toInt",
    "long": "dsa::toLong",
    "double": "dsa::toDouble",
    "bool": "dsa::toBool",
    "string": "dsa::toStr",
    "char": "dsa::toChar",
}


def cpp_type(type_: str) -> str:
    if type_ == "void":
        return "void"
    if type_ == "ListNode":
        return "ListNode*"
    if type_ == "ListNode[]":
        return "vector<ListNode*>"
    if type_ == "TreeNode":
        return "TreeNode*"
    base, depth = scalar_and_depth(type_)
    out = _SCALARS[base]
    for _ in range(depth):
        out = f"vector<{out}>"
    return out


def _decoder(type_: str) -> str:
    """A callable expression `const dsa::J& -> value` for `type_`."""
    if type_ == "ListNode":
        return "dsa::toList"
    if type_ == "TreeNode":
        return "dsa::toTree"
    if type_ == "ListNode[]":
        return "[](const dsa::J& e) { return dsa::vec(e, dsa::toList); }"
    base, depth = scalar_and_depth(type_)
    fn = _DECODERS[base]
    for _ in range(depth):
        fn = f"[](const dsa::J& e) {{ return dsa::vec(e, {fn}); }}"
    return fn


def _decode(type_: str, source: str) -> str:
    return f"({_decoder(type_)})({source})"


def _param_decl(p: dict) -> str:
    t = cpp_type(p["type"])
    ref = "&" if t.startswith("vector") else ""
    return f"{t}{ref} {p['name']}"


def starter(spec: Spec) -> str:
    if spec["kind"] == "function":
        params = ", ".join(_param_decl(p) for p in visible_params(spec))
        hint = mutate_hint(spec)
        return (
            "class Solution {\n"
            "public:\n"
            f"    {cpp_type(spec['returns'])} {spec['name']}({params}) {{\n"
            f"        {'// ' + hint if hint else ''}\n"
            "    }\n"
            "};\n"
        )
    lines = [f"class {spec['name']} {{", "public:"]
    ctor = ", ".join(_param_decl(p) for p in spec["constructor"])
    lines += [f"    {spec['name']}({ctor}) {{", "        ", "    }", ""]
    for m in spec["methods"]:
        margs = ", ".join(_param_decl(p) for p in m["params"])
        lines += [f"    {cpp_type(m['returns'])} {m['name']}({margs}) {{", "        ", "    }", ""]
    return "\n".join(lines).rstrip() + "\n};\n"


def _link_lines(spec: Spec, index: dict[str, int]) -> list[str]:
    lines = []
    for link in spec.get("links") or []:
        if link["kind"] == "cycle":
            lines.append(f"dsa::linkCycle(a{index[link['list']]}, a{index[link['pos']]});")
        elif link["kind"] == "circular":
            lines.append(f"dsa::linkCircular(a{index[link['list']]});")
        else:
            a, b, shared = index[link["a"]], index[link["b"]], index[link["shared"]]
            lines += [
                "{",
                f"    ListNode* shared = dsa::fromValues(a{shared});",
                f"    a{a} = dsa::appendList(a{a}, shared);",
                f"    a{b} = dsa::appendList(a{b}, shared);",
                "}",
            ]
    return lines


def _function_body(spec: Spec) -> list[str]:
    index = {p["name"]: i for i, p in enumerate(spec["params"])}
    lines = [f"auto a{i} = {_decode(p['type'], f'input.a[{i}]')};" for i, p in enumerate(spec["params"])]
    lines += _link_lines(spec, index)
    hidden = hidden_params(spec)
    call = f"sol.{spec['name']}({', '.join(f'a{index[p]}' for p in index if p not in hidden)})"
    lines += ["Solution sol;", "auto t0 = std::chrono::steady_clock::now();"]
    mutates, returns = spec.get("mutates"), spec["returns"]
    if mutates and returns == "void":
        lines += [f"{call};", "auto t1 = std::chrono::steady_clock::now();", f"dsa::enc(res, a{index[mutates]});"]
    elif mutates:
        lines += [
            f"auto r = {call};",
            "auto t1 = std::chrono::steady_clock::now();",
            "res += '[';",
            "dsa::enc(res, r);",
            "res += ',';",
            f"dsa::enc(res, a{index[mutates]});",
            "res += ']';",
        ]
    else:
        encoder = "dsa::encCircular" if spec.get("circular_output") else "dsa::enc"
        lines += [f"auto r = {call};", "auto t1 = std::chrono::steady_clock::now();", f"{encoder}(res, r);"]
    lines.append("ms = std::chrono::duration<double, std::milli>(t1 - t0).count();")
    return lines


def _class_body(spec: Spec) -> list[str]:
    name = spec["name"]
    lines = [
        'const dsa::J& ops = input.at("ops");',
        'const dsa::J& args = input.at("args");',
        'res = "[null";',
        "auto t0 = std::chrono::steady_clock::now();",
    ]
    ctor_args = []
    for i, p in enumerate(spec["constructor"]):
        lines.append(f"auto c{i} = {_decode(p['type'], f'args.a[0].a[{i}]')};")
        ctor_args.append(f"c{i}")
    lines.append(f"{name}* obj = new {name}({', '.join(ctor_args)});")
    lines += [
        "for (size_t k = 1; k < ops.a.size(); ++k) {",
        "    const std::string& op = ops.a[k].s;",
        "    const dsa::J& m = args.a[k];",
        "    res += ',';",
    ]
    for n, method in enumerate(spec["methods"]):
        keyword = "if" if n == 0 else "} else if"
        lines.append(f'    {keyword} (op == "{method["name"]}") {{')
        margs = []
        for i, p in enumerate(method["params"]):
            lines.append(f"        auto p{i} = {_decode(p['type'], f'm.a[{i}]')};")
            margs.append(f"p{i}")
        call = f"obj->{method['name']}({', '.join(margs)})"
        if method["returns"] == "void":
            lines += [f"        {call};", '        res += "null";']
        else:
            lines.append(f"        dsa::enc(res, {call});")
    lines += [
        "    } else {",
        '        throw std::runtime_error("unknown op: " + op);',
        "    }",
        "}",
        "auto t1 = std::chrono::steady_clock::now();",
        "res += ']';",
        "ms = std::chrono::duration<double, std::milli>(t1 - t0).count();",
    ]
    return lines


def program(spec: Spec, user_code: str) -> ProgramFiles:
    body = _function_body(spec) if spec["kind"] == "function" else _class_body(spec)
    indented = "\n".join(f"            {line}" for line in body)
    source = (
        f"{_HEADERS}\n"
        "// ---- user code ----\n"
        f"{user_code}\n"
        "// ---- end user code ----\n"
        f"{_RUNTIME}{_MAIN_HEAD}{indented}\n{_MAIN_TAIL}"
    )
    return {"main.cpp": source}
