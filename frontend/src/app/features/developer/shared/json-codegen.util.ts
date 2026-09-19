// Shared JSON -> typed-model schema inference + per-language emitters.
// Used by JSON → TypeScript/Python/Pydantic/Go/Kotlin/Dart (6 bookmarkable routes, 1 engine — see
// the Code Generators unit decision in the execution plan).

export type IRType =
  | { kind: 'string' }
  | { kind: 'integer' }
  | { kind: 'number' }
  | { kind: 'boolean' }
  | { kind: 'any' }
  | { kind: 'array'; of: IRType }
  | { kind: 'ref'; name: string };

export interface IRField {
  name: string;
  type: IRType;
  nullable: boolean;
}

export interface IRObjectType {
  name: string;
  fields: IRField[];
}

export interface IRResult {
  root: IRType;
  types: IRObjectType[];
}

export function toPascalCase(name: string): string {
  const cleaned = name.replace(/[^a-zA-Z0-9]+/g, ' ').trim();
  const parts = cleaned.split(' ').filter(Boolean);
  const pascal = parts.map((w) => w[0].toUpperCase() + w.slice(1)).join('');
  return pascal || 'Item';
}

export function toCamelCase(name: string): string {
  const pascal = toPascalCase(name);
  return pascal[0].toLowerCase() + pascal.slice(1);
}

export function toSnakeCase(name: string): string {
  return name
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .toLowerCase()
    .replace(/^_+|_+$/g, '');
}

function singularize(name: string): string {
  if (name.endsWith('ies')) return name.slice(0, -3) + 'y';
  if (name.endsWith('s') && !name.endsWith('ss')) return name.slice(0, -1);
  return name;
}

function build(name: string, value: unknown, types: IRObjectType[]): IRType {
  if (value === null || value === undefined) return { kind: 'any' };
  if (Array.isArray(value)) {
    if (value.length === 0) return { kind: 'array', of: { kind: 'any' } };
    return { kind: 'array', of: build(singularize(name), value[0], types) };
  }
  if (typeof value === 'object') {
    const typeName = toPascalCase(name);
    const fields: IRField[] = Object.entries(value as Record<string, unknown>).map(([k, v]) => ({
      name: k,
      type: build(k, v, types),
      nullable: v === null,
    }));
    types.push({ name: typeName, fields });
    return { kind: 'ref', name: typeName };
  }
  if (typeof value === 'string') return { kind: 'string' };
  if (typeof value === 'boolean') return { kind: 'boolean' };
  if (typeof value === 'number') return Number.isInteger(value) ? { kind: 'integer' } : { kind: 'number' };
  return { kind: 'any' };
}

export function buildIR(rootName: string, value: unknown): IRResult {
  const types: IRObjectType[] = [];
  const root = build(rootName, value, types);
  return { root, types };
}

export interface CodeGenOptions {
  optionalFields: boolean;
  nullableFields: boolean;
  useType: boolean; // TypeScript only: `type` alias instead of `interface`
}

// --- TypeScript ---
export function generateTypeScript(rootName: string, value: unknown, opts: CodeGenOptions): string {
  const { types } = buildIR(rootName, value);
  const blocks = types.map((t) => {
    const body = t.fields
      .map((f) => `  ${f.name}${opts.optionalFields ? '?' : ''}: ${tsType(f.type)}${f.nullable || opts.nullableFields ? ' | null' : ''};`)
      .join('\n');
    return opts.useType ? `type ${t.name} = {\n${body}\n};` : `interface ${t.name} {\n${body}\n}`;
  });
  return blocks.join('\n\n');
}
function tsType(t: IRType): string {
  switch (t.kind) {
    case 'string':
      return 'string';
    case 'integer':
    case 'number':
      return 'number';
    case 'boolean':
      return 'boolean';
    case 'any':
      return 'unknown';
    case 'array':
      return `${tsType(t.of)}[]`;
    case 'ref':
      return t.name;
  }
}

// --- Python dataclass ---
export function generatePython(rootName: string, value: unknown, opts: CodeGenOptions): string {
  const { types } = buildIR(rootName, value);
  const header = 'from dataclasses import dataclass\nfrom typing import Any, List, Optional\n\n';
  const blocks = types.map((t) => {
    const body =
      t.fields.map((f) => `    ${toSnakeCase(f.name)}: ${pyType(f.type, f.nullable || opts.optionalFields)}`).join('\n') || '    pass';
    return `@dataclass\nclass ${t.name}:\n${body}`;
  });
  return header + blocks.join('\n\n\n');
}

// --- Pydantic model ---
export function generatePydantic(rootName: string, value: unknown, opts: CodeGenOptions): string {
  const { types } = buildIR(rootName, value);
  const header = 'from typing import Any, List, Optional\nfrom pydantic import BaseModel\n\n';
  const blocks = types.map((t) => {
    const body =
      t.fields.map((f) => `    ${toSnakeCase(f.name)}: ${pyType(f.type, f.nullable || opts.optionalFields)}`).join('\n') || '    pass';
    return `class ${t.name}(BaseModel):\n${body}`;
  });
  return header + blocks.join('\n\n\n');
}
function pyType(t: IRType, nullable: boolean): string {
  const base = (() => {
    switch (t.kind) {
      case 'string':
        return 'str';
      case 'integer':
        return 'int';
      case 'number':
        return 'float';
      case 'boolean':
        return 'bool';
      case 'any':
        return 'Any';
      case 'array':
        return `List[${pyType(t.of, false)}]`;
      case 'ref':
        return t.name;
    }
  })();
  return nullable ? `Optional[${base}] = None` : base;
}

// --- Go struct ---
export function generateGo(rootName: string, value: unknown): string {
  const { types } = buildIR(rootName, value);
  const blocks = types.map((t) => {
    const body = t.fields.map((f) => `\t${toPascalCase(f.name)} ${goType(f.type)} \`json:"${f.name}"\``).join('\n');
    return `type ${t.name} struct {\n${body}\n}`;
  });
  return blocks.join('\n\n');
}
function goType(t: IRType): string {
  switch (t.kind) {
    case 'string':
      return 'string';
    case 'integer':
      return 'int';
    case 'number':
      return 'float64';
    case 'boolean':
      return 'bool';
    case 'any':
      return 'interface{}';
    case 'array':
      return `[]${goType(t.of)}`;
    case 'ref':
      return t.name;
  }
}

// --- Kotlin data class ---
export function generateKotlin(rootName: string, value: unknown, opts: CodeGenOptions): string {
  const { types } = buildIR(rootName, value);
  const blocks = types.map((t) => {
    const fields = t.fields
      .map((f) => `    val ${toCamelCase(f.name)}: ${ktType(f.type)}${f.nullable || opts.nullableFields ? '? = null' : ''}`)
      .join(',\n');
    return `data class ${t.name}(\n${fields}\n)`;
  });
  return blocks.join('\n\n');
}
function ktType(t: IRType): string {
  switch (t.kind) {
    case 'string':
      return 'String';
    case 'integer':
      return 'Int';
    case 'number':
      return 'Double';
    case 'boolean':
      return 'Boolean';
    case 'any':
      return 'Any';
    case 'array':
      return `List<${ktType(t.of)}>`;
    case 'ref':
      return t.name;
  }
}

// --- Dart model ---
export function generateDart(rootName: string, value: unknown): string {
  const { types } = buildIR(rootName, value);
  const blocks = types.map((t) => {
    const fields = t.fields.map((f) => `  final ${dartType(f.type)}${f.nullable ? '?' : ''} ${toCamelCase(f.name)};`).join('\n');
    const ctorParams = t.fields.map((f) => `this.${toCamelCase(f.name)}`).join(', ');
    const fromJson = t.fields.map((f) => `      ${toCamelCase(f.name)}: json['${f.name}'],`).join('\n');
    return `class ${t.name} {\n${fields}\n\n  ${t.name}({${ctorParams}});\n\n  factory ${t.name}.fromJson(Map<String, dynamic> json) => ${t.name}(\n${fromJson}\n  );\n}`;
  });
  return blocks.join('\n\n');
}
function dartType(t: IRType): string {
  switch (t.kind) {
    case 'string':
      return 'String';
    case 'integer':
      return 'int';
    case 'number':
      return 'double';
    case 'boolean':
      return 'bool';
    case 'any':
      return 'dynamic';
    case 'array':
      return `List<${dartType(t.of)}>`;
    case 'ref':
      return t.name;
  }
}
