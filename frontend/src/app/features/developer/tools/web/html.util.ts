const VOID_ELEMENTS = new Set([
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr',
]);

// Parsed via an inert <template> — content is never attached to the live DOM, so scripts don't
// run and resources don't load. Used for formatting/minifying only (not the sandboxed preview tool).
function parseFragment(html: string): DocumentFragment {
  const template = document.createElement('template');
  template.innerHTML = html;
  return template.content;
}

function escapeAttr(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
}

function serializePretty(node: Node, depth: number, indentUnit: string): string {
  const pad = indentUnit.repeat(depth);
  let out = '';
  for (const child of Array.from(node.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) {
      const text = (child.textContent ?? '').trim();
      if (text) out += pad + text + '\n';
    } else if (child.nodeType === Node.COMMENT_NODE) {
      out += `${pad}<!--${child.textContent}-->\n`;
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      const el = child as Element;
      const tag = el.tagName.toLowerCase();
      const attrs = Array.from(el.attributes)
        .map((a) => ` ${a.name}="${escapeAttr(a.value)}"`)
        .join('');
      if (VOID_ELEMENTS.has(tag)) {
        out += `${pad}<${tag}${attrs}>\n`;
      } else if (el.childNodes.length === 0) {
        out += `${pad}<${tag}${attrs}></${tag}>\n`;
      } else {
        out += `${pad}<${tag}${attrs}>\n`;
        out += serializePretty(el, depth + 1, indentUnit);
        out += `${pad}</${tag}>\n`;
      }
    }
  }
  return out;
}

export function formatHtml(html: string, indentSize = 2): string {
  const fragment = parseFragment(html);
  return serializePretty(fragment, 0, ' '.repeat(indentSize)).trim() + '\n';
}

function serializeCompact(node: Node): string {
  let out = '';
  for (const child of Array.from(node.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) {
      out += (child.textContent ?? '').replace(/\s+/g, ' ');
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      const el = child as Element;
      const tag = el.tagName.toLowerCase();
      const attrs = Array.from(el.attributes)
        .map((a) => ` ${a.name}="${escapeAttr(a.value)}"`)
        .join('');
      if (VOID_ELEMENTS.has(tag)) {
        out += `<${tag}${attrs}>`;
      } else {
        out += `<${tag}${attrs}>${serializeCompact(el)}</${tag}>`;
      }
    }
  }
  return out;
}

export function minifyHtml(html: string): string {
  return serializeCompact(parseFragment(html)).trim();
}
