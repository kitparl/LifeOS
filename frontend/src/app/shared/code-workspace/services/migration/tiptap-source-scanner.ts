import { TipTapUsageLocation, UsageContext } from '../../models/migration.model';

const TIPTAP_IMPORT = /from\s+['"](@tiptap\/(?:core|starter-kit|pm))['"]/g;
const RICH_EDITOR_IMPORT = /from\s+['"]([^'"]*rich-editor[^'"]*)['"]/g;
const TEMPLATE_TAG = /<app-rich-editor\b/g;
const EDITOR_CONSTRUCT = /\bnew\s+Editor\s*\(/g;
const CLASS_NAME = /export\s+class\s+(\w+)/;
const FORMS_IMPORT = /from\s+['"]@angular\/forms['"]/;

export interface SourceFile {
  filePath: string;
  content: string;
}

/**
 * Finds TipTap / RichEditor usage in a TypeScript or HTML source file.
 * Uses regex scanning (browser-safe). ts-morph is Node-only, so this is the
 * in-app equivalent of AST import/template analysis.
 */
export function scanTipTapSource(filePath: string, content: string): TipTapUsageLocation[] {
  if (/tiptap-source-scanner|tiptap-scan-results/.test(filePath)) {
    return [];
  }
  const componentName = extractComponentName(filePath, content);
  const dependencies = extractDependencies(content);
  const locations: TipTapUsageLocation[] = [];

  addMatches(locations, content, TIPTAP_IMPORT, componentName, filePath, 'import', dependencies);
  addMatches(locations, content, RICH_EDITOR_IMPORT, componentName, filePath, 'import', dependencies);
  addMatches(locations, content, TEMPLATE_TAG, componentName, filePath, 'template', dependencies);
  addMatches(locations, content, EDITOR_CONSTRUCT, componentName, filePath, editorContext(content), dependencies);

  return dedupe(locations);
}

function addMatches(
  locations: TipTapUsageLocation[],
  content: string,
  pattern: RegExp,
  componentName: string,
  filePath: string,
  usageContext: UsageContext,
  dependencies: string[]
): void {
  const regex = new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : `${pattern.flags}g`);
  let match: RegExpExecArray | null;
  while ((match = regex.exec(content))) {
    locations.push({
      componentName,
      filePath,
      lineNumber: lineNumberAt(content, match.index),
      usageContext,
      riskLevel: 'low',
      dependencies: [...dependencies],
    });
  }
}

function extractComponentName(filePath: string, content: string): string {
  const match = content.match(CLASS_NAME);
  if (match) {
    return match[1];
  }
  const base = filePath.split('/').pop() || filePath;
  return base.replace(/\.html$/, '').replace(/\.ts$/, '');
}

function extractDependencies(content: string): string[] {
  const deps = new Set<string>();
  let match: RegExpExecArray | null;

  const tiptap = new RegExp(TIPTAP_IMPORT.source, 'g');
  while ((match = tiptap.exec(content))) {
    deps.add(match[1]);
  }

  const rich = new RegExp(RICH_EDITOR_IMPORT.source, 'g');
  while ((match = rich.exec(content))) {
    deps.add('RichEditorComponent');
  }

  if (FORMS_IMPORT.test(content) || content.includes('NG_VALUE_ACCESSOR')) {
    deps.add('@angular/forms');
  }
  if (content.includes('ControlValueAccessor') || content.includes('NG_VALUE_ACCESSOR')) {
    deps.add('ControlValueAccessor');
  }

  return [...deps];
}

function editorContext(content: string): UsageContext {
  const construct = content.search(EDITOR_CONSTRUCT);
  if (construct < 0) {
    return 'method';
  }
  const before = content.slice(0, construct);
  const ctor = before.lastIndexOf('constructor');
  const method = Math.max(
    before.lastIndexOf('ngAfterViewInit'),
    before.lastIndexOf('ngOnInit'),
    before.lastIndexOf('\n  ')
  );
  if (ctor > method) {
    return 'constructor';
  }
  return 'method';
}

function lineNumberAt(content: string, index: number): number {
  return content.slice(0, index).split('\n').length;
}

function dedupe(locations: TipTapUsageLocation[]): TipTapUsageLocation[] {
  const seen = new Set<string>();
  return locations.filter((location) => {
    const key = `${location.filePath}:${location.lineNumber}:${location.usageContext}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}
