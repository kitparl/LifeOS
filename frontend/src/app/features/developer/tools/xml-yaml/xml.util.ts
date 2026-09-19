import { formatXmlParseError } from '../../shared/dev-error.util';

export function parseXmlOrThrow(xml: string): XMLDocument {
  const doc = new DOMParser().parseFromString(xml, 'application/xml');
  const err = formatXmlParseError(doc);
  if (err) throw new Error(err);
  return doc;
}

function escapeXmlText(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function escapeXmlAttr(s: string): string {
  return escapeXmlText(s).replace(/"/g, '&quot;');
}

export function formatXml(xml: string, indent = 2): string {
  const doc = parseXmlOrThrow(xml);
  return serializeNode(doc.documentElement, 0, indent) + '\n';
}

function serializeNode(el: Element, depth: number, indent: number): string {
  const pad = ' '.repeat(depth * indent);
  const attrStr = Array.from(el.attributes)
    .map((a) => ` ${a.name}="${escapeXmlAttr(a.value)}"`)
    .join('');
  const childNodes = Array.from(el.childNodes).filter(
    (n) => n.nodeType === 1 || (n.nodeType === 3 && (n.textContent ?? '').trim() !== ''),
  );
  if (childNodes.length === 0) return `${pad}<${el.tagName}${attrStr}/>`;
  if (childNodes.length === 1 && childNodes[0].nodeType === 3) {
    return `${pad}<${el.tagName}${attrStr}>${escapeXmlText(childNodes[0].textContent!.trim())}</${el.tagName}>`;
  }
  const inner = childNodes
    .filter((n) => n.nodeType === 1)
    .map((n) => serializeNode(n as Element, depth + 1, indent))
    .join('\n');
  return `${pad}<${el.tagName}${attrStr}>\n${inner}\n${pad}</${el.tagName}>`;
}

// --- XML <-> JS object convention: @attr for attributes, #text for mixed text content ---

export function xmlToJsObject(xml: string): unknown {
  const doc = parseXmlOrThrow(xml);
  return { [doc.documentElement.tagName]: elementToObject(doc.documentElement) };
}

function elementToObject(el: Element): unknown {
  const obj: Record<string, unknown> = {};
  for (const attr of Array.from(el.attributes)) {
    obj['@' + attr.name] = attr.value;
  }
  const childElements = Array.from(el.children);
  if (childElements.length === 0) {
    const text = (el.textContent ?? '').trim();
    if (Object.keys(obj).length === 0) return text;
    if (text) obj['#text'] = text;
    return obj;
  }
  for (const child of childElements) {
    const childValue = elementToObject(child);
    const existing = obj[child.tagName];
    if (existing !== undefined) {
      obj[child.tagName] = Array.isArray(existing) ? [...existing, childValue] : [existing, childValue];
    } else {
      obj[child.tagName] = childValue;
    }
  }
  return obj;
}

export function jsObjectToXml(value: unknown, indent = 2): string {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Root JSON value must be an object with exactly one root element key, e.g. {"root": {...}}.');
  }
  const keys = Object.keys(value as object);
  if (keys.length !== 1) {
    throw new Error('Expected exactly one root element key, e.g. {"root": {...}}.');
  }
  const rootName = keys[0];
  return buildElement(rootName, (value as Record<string, unknown>)[rootName], 0, indent) + '\n';
}

function buildElement(name: string, value: unknown, depth: number, indent: number): string {
  const pad = ' '.repeat(depth * indent);
  if (value === null || value === undefined) return `${pad}<${name}/>`;
  if (typeof value !== 'object') return `${pad}<${name}>${escapeXmlText(String(value))}</${name}>`;
  if (Array.isArray(value)) {
    return value.map((v) => buildElement(name, v, depth, indent)).join('\n');
  }
  const record = value as Record<string, unknown>;
  const attrs: string[] = [];
  const children: string[] = [];
  let text = '';
  for (const [k, v] of Object.entries(record)) {
    if (k.startsWith('@')) attrs.push(`${k.slice(1)}="${escapeXmlAttr(String(v))}"`);
    else if (k === '#text') text = String(v);
    else if (Array.isArray(v)) children.push(v.map((item) => buildElement(k, item, depth + 1, indent)).join('\n'));
    else children.push(buildElement(k, v, depth + 1, indent));
  }
  const attrStr = attrs.length ? ' ' + attrs.join(' ') : '';
  if (children.length === 0 && !text) return `${pad}<${name}${attrStr}/>`;
  if (children.length === 0) return `${pad}<${name}${attrStr}>${escapeXmlText(text)}</${name}>`;
  return `${pad}<${name}${attrStr}>\n${children.join('\n')}\n${pad}</${name}>`;
}
