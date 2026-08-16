import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

export type FormatAction = 
  | 'bold' | 'italic' | 'strikethrough'
  | 'h1' | 'h2' | 'h3'
  | 'bullet-list' | 'numbered-list' | 'checklist'
  | 'quote' | 'inline-code' | 'code-block' | 'horizontal-rule'
  | 'link' | 'image' | 'table'
  | 'undo' | 'redo' | 'find' | 'replace';

export interface EditorStats {
  wordCount: number;
  charCount: number;
  lineCount: number;
}

/**
 * Editor toolbar component with formatting actions and document statistics.
 * 
 * Features:
 * - Text formatting (Bold, Italic, Strikethrough)
 * - Headings (H1, H2, H3)
 * - Lists (Bullet, Numbered, Checklist)
 * - Blocks (Quote, Code, Horizontal rule)
 * - Inserts (Link, Image, Table)
 * - Editing (Undo, Redo, Find, Replace)
 * - Statistics (Word, Character, Line count)
 * 
 * Uses CodeMirror transactions (no DOM manipulation)
 * Responsive: Horizontal scroll on narrow screens
 */
@Component({
  selector: 'app-editor-toolbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './editor-toolbar.component.html',
  styleUrls: ['./editor-toolbar.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditorToolbarComponent {
  /**
   * Whether the toolbar is visible
   */
  @Input() visible: boolean = true;

  /**
   * Whether to show word/char/line count
   */
  @Input() showStats: boolean = true;

  /**
   * Current editor statistics
   */
  @Input() stats: EditorStats = {
    wordCount: 0,
    charCount: 0,
    lineCount: 0,
  };

  /**
   * Whether the editor is in read-only mode
   */
  @Input() readOnly: boolean = false;

  @Input() theme: 'light' | 'dark' | 'system' = 'light';

  @Input() mode: 'markdown' | 'code' | 'markdown-code' = 'markdown';

  /**
   * Emits when a formatting action is requested
   */
  @Output() formatAction = new EventEmitter<FormatAction>();

  /**
   * Handle format button click
   */
  onFormat(action: FormatAction): void {
    if (this.readOnly) return;
    this.formatAction.emit(action);
  }

  /**
   * Check if a button should be disabled
   */
  isDisabled(action: FormatAction): boolean {
    if (this.readOnly) return true;
    
    // Disable markdown-specific actions in code mode
    if (this.mode === 'code') {
      const markdownActions: FormatAction[] = [
        'bold', 'italic', 'strikethrough',
        'h1', 'h2', 'h3',
        'bullet-list', 'numbered-list', 'checklist',
        'quote', 'horizontal-rule',
        'link', 'image', 'table'
      ];
      return markdownActions.includes(action);
    }

    return false;
  }

  /**
   * Get tooltip for action
   */
  getTooltip(action: FormatAction): string {
    const tooltips: Record<FormatAction, string> = {
      'bold': 'Bold (Ctrl+B)',
      'italic': 'Italic (Ctrl+I)',
      'strikethrough': 'Strikethrough',
      'h1': 'Heading 1',
      'h2': 'Heading 2',
      'h3': 'Heading 3',
      'bullet-list': 'Bullet List',
      'numbered-list': 'Numbered List',
      'checklist': 'Checklist',
      'quote': 'Quote',
      'inline-code': 'Inline Code',
      'code-block': 'Code Block',
      'horizontal-rule': 'Horizontal Rule',
      'link': 'Link',
      'image': 'Image',
      'table': 'Table',
      'undo': 'Undo (Ctrl+Z)',
      'redo': 'Redo (Ctrl+Y)',
      'find': 'Find (Ctrl+F)',
      'replace': 'Replace (Ctrl+H)',
    };
    return tooltips[action] || action;
  }

  /**
   * Format stats for display
   */
  formatStats(): string {
    const parts: string[] = [];
    
    if (this.stats.wordCount !== undefined) {
      parts.push(`${this.stats.wordCount} words`);
    }
    
    if (this.stats.charCount !== undefined) {
      parts.push(`${this.stats.charCount} chars`);
    }
    
    if (this.stats.lineCount !== undefined) {
      parts.push(`${this.stats.lineCount} lines`);
    }

    return parts.join(' • ');
  }
}
