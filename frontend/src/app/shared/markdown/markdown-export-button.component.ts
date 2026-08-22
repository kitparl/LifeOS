import { Component, EventEmitter, Input, Output } from '@angular/core';
import { downloadMarkdown } from './markdown-export';

@Component({
  selector: 'app-markdown-export-button',
  standalone: true,
  template: `
    <button
      type="button"
      [class]="buttonClass || 'kn-plus'"
      [attr.aria-label]="tooltip"
      [title]="tooltip"
      data-testid="markdown-export-button"
      (click)="exportMd()"
    >
      ↓
    </button>
  `,
})
export class MarkdownExportButtonComponent {
  @Input() content = '';
  @Input() filename = 'export';
  @Input() buttonClass = '';
  @Input() tooltip = 'Export markdown';

  @Output() exportError = new EventEmitter<string>();

  exportMd(): void {
    try {
      downloadMarkdown(this.content, this.filename);
    } catch {
      this.exportError.emit('Export failed.');
    }
  }
}
