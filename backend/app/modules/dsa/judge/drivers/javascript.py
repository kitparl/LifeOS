"""JavaScript (Node.js) driver: ListNode/TreeNode + user code + a JS port of codec.invoke + test loop."""

from __future__ import annotations

import json

from app.modules.dsa.judge.drivers.common import ProgramFiles, Spec, mutate_hint, visible_params

_PRELUDE = """\
function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}
function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}
"""

# Mirrors codec.py (decode/encode/invoke); kept in one place per language.
_RUNTIME = r"""
const __dsa = (() => {
  const MAX_NODES = 200000;
  function listFrom(vals) {
    const dummy = new ListNode(0); let tail = dummy;
    for (const v of vals) { tail.next = new ListNode(v); tail = tail.next; }
    return dummy.next;
  }
  function listTo(head) {
    const out = [];
    while (head !== null && head !== undefined) {
      if (out.length >= MAX_NODES) throw new Error("linked list too long or has a cycle");
      out.push(head.val); head = head.next;
    }
    return out;
  }
  function treeFrom(vals) {
    if (vals.length === 0) return null;
    const nodes = vals.map((v) => (v === null ? null : new TreeNode(v)));
    let k = 1;
    for (const node of nodes) {
      if (node === null) continue;
      node.left = k < nodes.length ? nodes[k] : null; k++;
      node.right = k < nodes.length ? nodes[k] : null; k++;
    }
    return nodes[0];
  }
  function treeTo(root) {
    const out = []; const queue = [root]; let i = 0; let count = 0;
    while (i < queue.length) {
      const node = queue[i++];
      if (node === null || node === undefined) { out.push(null); continue; }
      if (++count > MAX_NODES) throw new Error("tree too large or has a cycle");
      out.push(node.val); queue.push(node.left); queue.push(node.right);
    }
    while (out.length && out[out.length - 1] === null) out.pop();
    return out;
  }
  function circularTo(head) {
    const out = []; let node = head;
    while (node !== null && node !== undefined) {
      if (out.length >= MAX_NODES) throw new Error("circular list too long");
      out.push(node.val); node = node.next;
      if (node === head) return out;
    }
    if (out.length) throw new Error("expected a circular list (the tail should point back to the head)");
    return out;
  }
  function nodesOf(head) {
    const out = [];
    while (head !== null && head !== undefined) { out.push(head); head = head.next; }
    return out;
  }
  function append(head, tail) {
    const nodes = nodesOf(head);
    if (!nodes.length) return tail;
    nodes[nodes.length - 1].next = tail;
    return head;
  }
  function applyLinks(links, args) {
    const hidden = new Set();
    for (const link of links || []) {
      if (link.kind === "cycle") {
        hidden.add(link.pos);
        const nodes = nodesOf(args[link.list]); const pos = args[link.pos];
        if (nodes.length && pos >= 0) nodes[nodes.length - 1].next = nodes[pos];
      } else if (link.kind === "circular") {
        const nodes = nodesOf(args[link.list]);
        if (nodes.length) nodes[nodes.length - 1].next = nodes[0];
      } else {
        hidden.add(link.shared);
        const shared = listFrom(args[link.shared]);
        args[link.a] = append(args[link.a], shared);
        args[link.b] = append(args[link.b], shared);
      }
    }
    return hidden;
  }
  function decode(t, v) {
    if (t === "ListNode") return listFrom(v);
    if (t === "ListNode[]") return v.map(listFrom);
    if (t === "TreeNode") return treeFrom(v);
    if (t.endsWith("[]")) { const inner = t.slice(0, -2); return v.map((x) => decode(inner, x)); }
    return v;
  }
  function encode(t, v, circular) {
    if (t === "void") return null;
    const toJson = circular ? circularTo : listTo;
    if (t === "ListNode") return toJson(v);
    if (t === "ListNode[]") return Array.from(v, toJson);
    if (t === "TreeNode") return treeTo(v);
    if (t.endsWith("[]")) {
      const inner = t.slice(0, -2);
      if (t === "char[]" && typeof v === "string") return v.split("");
      return Array.from(v, (x) => encode(inner, x));
    }
    if (t === "double") {
      if (typeof v !== "number" || !Number.isFinite(v)) throw new Error("result is not a finite number");
      return v;
    }
    return v === undefined ? null : v;
  }
  function invoke(spec, target, input) {
    if (spec.kind === "function") {
      const args = {};
      spec.params.forEach((p, i) => { args[p.name] = decode(p.type, input[i]); });
      const hidden = applyLinks(spec.links, args);
      const result = target(...spec.params.filter((p) => !hidden.has(p.name)).map((p) => args[p.name]));
      if (spec.mutates) {
        const type = spec.params.find((p) => p.name === spec.mutates).type;
        const mutated = encode(type, args[spec.mutates]);
        return spec.returns === "void" ? mutated : [encode(spec.returns, result), mutated];
      }
      return encode(spec.returns, result, spec.circular_output);
    }
    const methods = Object.fromEntries(spec.methods.map((m) => [m.name, m]));
    const ctorArgs = spec.constructor.map((p, i) => decode(p.type, input.args[0][i]));
    const obj = new target(...ctorArgs);
    const out = [null];
    for (let k = 1; k < input.ops.length; k++) {
      const m = methods[input.ops[k]];
      const args = m.params.map((p, i) => decode(p.type, input.args[k][i]));
      out.push(encode(m.returns, obj[input.ops[k]](...args)));
    }
    return out;
  }
  return { invoke };
})();
"""

_MAIN = """
(() => {
  const fs = require("fs");
  const spec = JSON.parse(__DSA_SPEC);
  const tests = JSON.parse(fs.readFileSync("tests.json", "utf8"));
  const fd = fs.openSync("result.jsonl", "w");
  for (let i = 0; i < tests.length; i++) {
    let line;
    try {
      const target = __dsaTarget();
      const t0 = process.hrtime.bigint();
      const out = __dsa.invoke(spec, target, tests[i]);
      const ms = Number(process.hrtime.bigint() - t0) / 1e6;
      line = JSON.stringify({ i, ok: true, out: out === undefined ? null : out, ms: Math.round(ms * 1000) / 1000 });
    } catch (e) {
      const msg = e && e.name ? e.name + ": " + e.message : String(e);
      line = JSON.stringify({ i, ok: false, err: msg.slice(0, 500) });
    }
    fs.writeSync(fd, line + "\\n");
  }
  fs.closeSync(fd);
})();
"""

_TYPES = {
    "int": "number",
    "long": "number",
    "double": "number",
    "bool": "boolean",
    "string": "string",
    "char": "character",
    "ListNode": "ListNode",
    "ListNode[]": "ListNode[]",
    "TreeNode": "TreeNode",
    "void": "void",
}


def _js_type(type_: str) -> str:
    return _TYPES.get(type_) or f"{_js_type(type_[:-2])}[]"


def _jsdoc(params: list[dict], returns: str | None) -> list[str]:
    lines = ["/**"]
    lines += [f" * @param {{{_js_type(p['type'])}}} {p['name']}" for p in params]
    if returns is not None:
        lines.append(f" * @return {{{_js_type(returns)}}}")
    lines.append(" */")
    return lines


def starter(spec: Spec) -> str:
    if spec["kind"] == "function":
        params = visible_params(spec)
        names = ", ".join(p["name"] for p in params)
        doc = _jsdoc(params, spec["returns"])
        hint = mutate_hint(spec)
        if hint:
            doc[-1:] = [f" * {hint}", " */"]
        return "\n".join([*doc, f"var {spec['name']} = function({names}) {{", "", "};", ""])
    ctor = ", ".join(p["name"] for p in spec["constructor"])
    lines = [f"class {spec['name']} {{", *[f"  {x}" for x in _jsdoc(spec["constructor"], None)]]
    lines += [f"  constructor({ctor}) {{", "", "  }", ""]
    for m in spec["methods"]:
        margs = ", ".join(p["name"] for p in m["params"])
        lines += [f"  {x}" for x in _jsdoc(m["params"], m["returns"])]
        lines += [f"  {m['name']}({margs}) {{", "", "  }", ""]
    return "\n".join(lines).rstrip() + "\n}\n"


def program(spec: Spec, user_code: str) -> ProgramFiles:
    target = spec["name"]
    source = (
        f"{_PRELUDE}\n"
        "// ---- user code ----\n"
        f"{user_code}\n"
        "// ---- end user code ----\n"
        f"const __DSA_SPEC = {json.dumps(json.dumps(spec))};\n"
        f"function __dsaTarget() {{ return {target}; }}\n"
        f"{_RUNTIME}\n{_MAIN}"
    )
    return {"main.js": source}
