import { Injectable } from '@angular/core';
import TurndownService from 'turndown';
import { MarkdownService } from '../markdown.service';
import {
  ConversionOptions,
  ConversionResult,
  ValidationResult,
} from '../../models/migration.model';
import { prettyPrintMarkdown } from './markdown-pretty-printer';

const DEFAULT_OPTIONS: ConversionOptions = {
  preserveWhitespace: false,
  codeBlockLanguage: null,
  linkStyle: 'inline',
  bulletMarker: '-',
  headingStyle: 'atx',
};

const FORMATTING_TAGS = new Set(['STRONG', 'B', 'EM', 'I']);

/**
 * Converts TipTap HTML to Markdown with turndown.js and TipTap-specific rules.
 */
@Injectable({ providedIn: 'root' })
export class ContentConverterService {
  constructor(private markdownService: MarkdownService) {}

  async htmlToMarkdown(
    html: string,
    options?: Partial<ConversionOptions>
  ): Promise<ConversionResult> {
    const merged: ConversionOptions = { ...DEFAULT_OPTIONS, ...options };
    const originalLength = html?.length ?? 0;

    if (!html || !html.trim()) {
      return {
        markdown: '',
        success: true,
        warnings: [],
        metadata: {
          originalLength,
          markdownLength: 0,
          elementsConverted: 0,
        },
      };
    }

    try {
      const turndown = this.createTurndownService(merged);
      const markdown = this.prettyPrint(turndown.turndown(html));

      return {
        markdown,
        success: true,
        warnings: [],
        metadata: {
          originalLength,
          markdownLength: markdown.length,
          elementsConverted: this.countElements(html),
        },
      };
    } catch (error) {
      console.error('Conversion failed:', error);
      const fallbackMarkdown = `\`\`\`html\n${html}\n\`\`\``;
      return {
        markdown: fallbackMarkdown,
        success: false,
        warnings: ['Conversion failed, HTML preserved in code block'],
        metadata: {
          originalLength,
          markdownLength: fallbackMarkdown.length,
          elementsConverted: 0,
        },
      };
    }
  }

  /**
   * Round-trip validation: Markdown → HTML vs original HTML semantic structure.
   */
  validateConversion(html: string, markdown: string): ValidationResult {
    const differences: string[] = [];

    if (!html && !markdown) {
      return { valid: true, differences, semanticEquivalent: true };
    }

    const original = this.extractSemantic(html);
    const roundTripHtml = this.markdownService.parse(markdown);
    const roundTrip = this.extractSemantic(roundTripHtml);

    if (original.text && original.text !== roundTrip.text) {
      const originalTokens = this.tokens(original.text).join(' ');
      const roundTripTokens = this.tokens(roundTrip.text).join(' ');
      if (originalTokens !== roundTripTokens) {
        differences.push('Text content differs after round-trip conversion');
      }
    }

    this.compareLists(
      differences,
      'bold formatting',
      original.bold,
      roundTrip.bold
    );
    this.compareLists(
      differences,
      'italic formatting',
      original.italic,
      roundTrip.italic
    );
    this.compareHeadings(differences, original.headings, roundTrip.headings);
    this.compareListStructure(differences, original.lists, roundTrip.lists);
    this.compareLinks(differences, original.links, roundTrip.links);
    this.compareCodeBlocks(differences, original.codeBlocks, roundTrip.codeBlocks);

    const semanticEquivalent = differences.length === 0;
    return {
      valid: semanticEquivalent,
      differences,
      semanticEquivalent,
    };
  }

  prettyPrint(markdown: string): string {
    return prettyPrintMarkdown(markdown);
  }

  private createTurndownService(options: ConversionOptions): TurndownService {
    const turndown = new TurndownService({
      headingStyle: options.headingStyle,
      codeBlockStyle: 'fenced',
      fence: '```',
      bulletListMarker: options.bulletMarker,
      emDelimiter: '*',
      strongDelimiter: '**',
      linkStyle: options.linkStyle === 'reference' ? 'referenced' : 'inlined',
      hr: '---',
      preformattedCode: options.preserveWhitespace,
    });

    this.addCustomRules(turndown, options);
    return turndown;
  }

  private addCustomRules(turndown: TurndownService, options: ConversionOptions): void {
    const wrap = (value: string): string =>
      options.preserveWhitespace ? value : value.trim();

    turndown.addRule('tiptapBold', {
      filter: ['strong', 'b'],
      replacement: (content, node) => {
        if (this.isNestedFormatting(node)) {
          return content;
        }
        const inner = wrap(content);
        return inner ? `**${inner}**` : '';
      },
    });

    turndown.addRule('tiptapItalic', {
      filter: ['em', 'i'],
      replacement: (content, node) => {
        if (this.isNestedFormatting(node)) {
          return content;
        }
        const inner = wrap(content);
        return inner ? `*${inner}*` : '';
      },
    });

    turndown.addRule('tiptapNestedFormatting', {
      filter: (node) => this.isFormattingNode(node) && this.isNestedFormatting(node),
      replacement: (content, node) => {
        const inner = wrap(content);
        if (!inner) {
          return '';
        }
        if (this.isBoldNode(node)) {
          return `**${inner}**`;
        }
        return `*${inner}*`;
      },
    });

    turndown.addRule('tiptapParagraph', {
      filter: 'p',
      replacement: (content, node) => {
        const inner = options.preserveWhitespace ? content : content.trim();
        if (!inner || this.isEmptyParagraph(node)) {
          return '\n\n';
        }
        return `\n\n${inner}\n\n`;
      },
    });

    turndown.addRule('tiptapTable', {
      filter: 'table',
      replacement: (_content, node) => {
        const rows = Array.from(node.querySelectorAll('tr'));
        if (!rows.length) {
          return '';
        }
        const cellsOf = (row: Element): string[] =>
          Array.from(row.querySelectorAll('th,td')).map((cell) =>
            (cell.textContent || '').trim()
          );
        const header = cellsOf(rows[0]);
        const body = rows.slice(1).map(cellsOf);
        const headerLine = `| ${header.join(' | ')} |`;
        const separator = `| ${header.map(() => '---').join(' | ')} |`;
        const bodyLines = body.map((cells) => `| ${cells.join(' | ')} |`);
        return `\n\n${[headerLine, separator, ...bodyLines].join('\n')}\n\n`;
      },
    });
  }

  private isFormattingNode(node: HTMLElement): boolean {
    return FORMATTING_TAGS.has(node.nodeName);
  }

  private isBoldNode(node: HTMLElement): boolean {
    return node.nodeName === 'STRONG' || node.nodeName === 'B';
  }

  private isNestedFormatting(node: HTMLElement): boolean {
    if (!this.isFormattingNode(node)) {
      return false;
    }
    return this.hasFormattingAncestor(node) || this.hasFormattingDescendant(node);
  }

  private hasFormattingAncestor(node: HTMLElement): boolean {
    let parent = node.parentElement;
    while (parent) {
      if (FORMATTING_TAGS.has(parent.nodeName)) {
        return true;
      }
      parent = parent.parentElement;
    }
    return false;
  }

  private hasFormattingDescendant(node: HTMLElement): boolean {
    return Array.from(node.children).some(
      (child) =>
        FORMATTING_TAGS.has(child.nodeName) ||
        this.hasFormattingDescendant(child as HTMLElement)
    );
  }

  private isEmptyParagraph(node: HTMLElement): boolean {
    const text = (node.textContent || '').replace(/\u00a0/g, ' ').trim();
    if (text) {
      return false;
    }
    const children = Array.from(node.childNodes);
    return children.length === 0 || children.every((child) => {
      if (child.nodeType === 3) {
        return !(child.textContent || '').trim();
      }
      return child.nodeName === 'BR';
    });
  }

  private countElements(html: string): number {
    return (html.match(/<\/?[a-zA-Z][^>]*>/g) || []).length;
  }

  private extractSemantic(markup: string): SemanticSnapshot {
    const root = this.parseHtml(markup);
    const empty: SemanticSnapshot = {
      text: this.normalizeText(root.textContent || ''),
      headings: [],
      bold: [],
      italic: [],
      links: [],
      lists: [],
      codeBlocks: [],
    };

    if (typeof root.querySelectorAll !== 'function') {
      return empty;
    }

    const headings = Array.from(root.querySelectorAll('h1,h2,h3,h4,h5,h6')).map((el) => ({
      level: Number(el.tagName.charAt(1)),
      text: this.normalizeText(el.textContent || ''),
    }));
    const lists = Array.from(root.querySelectorAll('ul,ol'))
      .filter((list) => !list.parentElement?.closest('ul, ol'))
      .map((list) => ({
        ordered: list.tagName === 'OL',
        items: Array.from(list.children)
          .filter((child) => child.tagName === 'LI')
          .map((item) => this.normalizeText(item.textContent || '')),
      }));
    const codeBlocks = Array.from(root.querySelectorAll('pre')).map((pre) => {
      const codeEl = pre.querySelector('code') ?? pre;
      return {
        language: this.languageFromClass(codeEl.getAttribute('class') || ''),
        code: codeEl.textContent || '',
      };
    });

    return {
      text: this.normalizeText(root.textContent || ''),
      headings,
      bold: this.collectFormattedText(root, 'strong,b'),
      italic: this.collectFormattedText(root, 'em,i'),
      links: Array.from(root.querySelectorAll('a[href]')).map((el) => ({
        text: this.normalizeText(el.textContent || ''),
        href: el.getAttribute('href') || '',
      })),
      lists,
      codeBlocks,
    };
  }

  private parseHtml(markup: string): HTMLElement {
    if (typeof document === 'undefined') {
      const fallback = { textContent: markup.replace(/<[^>]+>/g, ' ') } as HTMLElement;
      return fallback;
    }
    const container = document.createElement('div');
    container.innerHTML = markup;
    return container;
  }

  private collectFormattedText(root: HTMLElement, selector: string): string[] {
    if (typeof root.querySelectorAll !== 'function') {
      return [];
    }
    return Array.from(root.querySelectorAll(selector))
      .map((el) => this.normalizeText(el.textContent || ''))
      .filter(Boolean)
      .sort();
  }

  private languageFromClass(className: string): string {
    const match = className.match(/language-([\w+-]+)/);
    return match ? match[1] : '';
  }

  private compareLists(
    differences: string[],
    label: string,
    original: string[],
    roundTrip: string[]
  ): void {
    if (original.join('|') !== roundTrip.join('|')) {
      if (original.length > 0 && roundTrip.length === 0) {
        differences.push(`${label} was not preserved`);
      } else if (original.length !== roundTrip.length) {
        differences.push(`${label} count differs after round-trip`);
      } else if (original.some((value, index) => value !== roundTrip[index])) {
        differences.push(`${label} text differs after round-trip`);
      }
    }
  }

  private compareHeadings(
    differences: string[],
    original: SemanticHeading[],
    roundTrip: SemanticHeading[]
  ): void {
    if (original.length === 0) {
      return;
    }
    if (original.length !== roundTrip.length) {
      differences.push('heading structure differs after round-trip');
      return;
    }
    const levelMismatch = original.some(
      (heading, index) =>
        heading.level !== roundTrip[index].level || heading.text !== roundTrip[index].text
    );
    if (levelMismatch) {
      differences.push('heading levels were not preserved');
    }
  }

  private compareListStructure(
    differences: string[],
    original: SemanticList[],
    roundTrip: SemanticList[]
  ): void {
    if (original.length === 0) {
      return;
    }
    if (original.length !== roundTrip.length) {
      differences.push('list structure differs after round-trip');
      return;
    }
    const mismatch = original.some((list, index) => {
      const other = roundTrip[index];
      return list.ordered !== other.ordered || list.items.join('|') !== other.items.join('|');
    });
    if (mismatch) {
      differences.push('list structure was not preserved');
    }
  }

  private compareLinks(
    differences: string[],
    original: SemanticLink[],
    roundTrip: SemanticLink[]
  ): void {
    if (original.length === 0) {
      return;
    }
    const key = (link: SemanticLink) => `${link.text}|${link.href}`;
    const originalKeys = original.map(key).sort().join('\n');
    const roundTripKeys = roundTrip.map(key).sort().join('\n');
    if (originalKeys !== roundTripKeys) {
      differences.push('link URLs or text were not preserved');
    }
  }

  private compareCodeBlocks(
    differences: string[],
    original: SemanticCodeBlock[],
    roundTrip: SemanticCodeBlock[]
  ): void {
    if (original.length === 0) {
      return;
    }
    if (original.length !== roundTrip.length) {
      differences.push('code block count differs after round-trip');
      return;
    }
    const whitespaceChanged = original.some(
      (block, index) => block.code !== roundTrip[index].code
    );
    if (whitespaceChanged) {
      differences.push('code block content changed (whitespace must be preserved)');
    }
  }

  private tokens(value: string): string[] {
    return value.split(' ').filter(Boolean);
  }

  private normalizeText(value: string): string {
    return value.replace(/\s+/g, ' ').trim();
  }
}

interface SemanticHeading {
  level: number;
  text: string;
}

interface SemanticLink {
  text: string;
  href: string;
}

interface SemanticList {
  ordered: boolean;
  items: string[];
}

interface SemanticCodeBlock {
  language: string;
  code: string;
}

interface SemanticSnapshot {
  text: string;
  headings: SemanticHeading[];
  bold: string[];
  italic: string[];
  links: SemanticLink[];
  lists: SemanticList[];
  codeBlocks: SemanticCodeBlock[];
}
