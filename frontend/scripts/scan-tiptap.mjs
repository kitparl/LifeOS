#!/usr/bin/env node
/**
 * Walks frontend/src for TipTap / RichEditor usage and writes scan results JSON.
 * Usage: node scripts/scan-tiptap.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const TIPTAP_IMPORT = /from\s+['"](@tiptap\/(?:core|starter-kit|pm))['"]/g;
const RICH_EDITOR_IMPORT = /from\s+['"]([^'"]*rich-editor[^'"]*)['"]/g;
const TEMPLATE_TAG = /<app-rich-editor\b/g;
const EDITOR_CONSTRUCT = /\bnew\s+Editor\s*\(/g;
const CLASS_NAME = /export\s+class\s+(\w+)/;
const FORMS_IMPORT = /from\s+['"]@angular\/forms['"]/;

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const srcRoot = path.resolve(scriptDir, '../src');
const outFile = path.resolve(
  scriptDir,
  '../src/app/shared/code-workspace/services/migration/tiptap-scan-results.json'
);

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === 'dist') continue;
      files.push(...walk(full));
    } else if (/\.(ts|html)$/.test(entry.name) && !entry.name.endsWith('.spec.ts')) {
      if (/tiptap-source-scanner|tiptap-scan-results/.test(entry.name)) continue;
      files.push(full);
    }
  }
  return files;
}

function lineNumberAt(content, index) {
  return content.slice(0, index).split('\n').length;
}

function componentName(filePath, content) {
  const match = content.match(CLASS_NAME);
  if (match) return match[1];
  return path.basename(filePath).replace(/\.html$/, '').replace(/\.ts$/, '');
}

function extractDependencies(content) {
  const deps = new Set();
  let match;
  const tiptap = new RegExp(TIPTAP_IMPORT.source, 'g');
  while ((match = tiptap.exec(content))) deps.add(match[1]);
  const rich = new RegExp(RICH_EDITOR_IMPORT.source, 'g');
  while ((match = rich.exec(content))) deps.add('RichEditorComponent');
  if (FORMS_IMPORT.test(content) || content.includes('NG_VALUE_ACCESSOR')) {
    deps.add('@angular/forms');
  }
  if (content.includes('ControlValueAccessor') || content.includes('NG_VALUE_ACCESSOR')) {
    deps.add('ControlValueAccessor');
  }
  return [...deps];
}

function editorContext(content) {
  const construct = content.search(EDITOR_CONSTRUCT);
  if (construct < 0) return 'method';
  const before = content.slice(0, construct);
  const ctor = before.lastIndexOf('constructor');
  const method = Math.max(
    before.lastIndexOf('ngAfterViewInit'),
    before.lastIndexOf('ngOnInit')
  );
  return ctor > method ? 'constructor' : 'method';
}

function addMatches(locations, content, pattern, name, filePath, usageContext, dependencies) {
  const regex = new RegExp(pattern.source, 'g');
  let match;
  while ((match = regex.exec(content))) {
    locations.push({
      componentName: name,
      filePath,
      lineNumber: lineNumberAt(content, match.index),
      usageContext,
      dependencies: [...dependencies],
    });
  }
}

const locations = [];
for (const file of walk(srcRoot)) {
  const content = fs.readFileSync(file, 'utf8');
  if (
    !content.includes('@tiptap') &&
    !content.includes('app-rich-editor') &&
    !content.includes('rich-editor')
  ) {
    continue;
  }
  const rel = path.relative(path.resolve(scriptDir, '../..'), file).split(path.sep).join('/');
  const name = componentName(rel, content);
  const dependencies = extractDependencies(content);
  addMatches(locations, content, TIPTAP_IMPORT, name, rel, 'import', dependencies);
  addMatches(locations, content, RICH_EDITOR_IMPORT, name, rel, 'import', dependencies);
  addMatches(locations, content, TEMPLATE_TAG, name, rel, 'template', dependencies);
  addMatches(locations, content, EDITOR_CONSTRUCT, name, rel, editorContext(content), dependencies);
}

const seen = new Set();
const deduped = locations.filter((loc) => {
  const key = `${loc.filePath}:${loc.lineNumber}:${loc.usageContext}`;
  if (seen.has(key)) return false;
  seen.add(key);
  return true;
});

const payload = {
  scannedAt: new Date().toISOString(),
  totalLocations: deduped.length,
  locations: deduped,
};

fs.mkdirSync(path.dirname(outFile), { recursive: true });
fs.writeFileSync(outFile, `${JSON.stringify(payload, null, 2)}\n`);
console.log(`Wrote ${deduped.length} locations to ${path.relative(process.cwd(), outFile)}`);
