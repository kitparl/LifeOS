import { Component, ElementRef, EventEmitter, Input, Output, ViewChild, inject } from '@angular/core';
import { MarkdownImportResult, MarkdownImportService } from './markdown-import.service';

@Component({
  selector: 'app-markdown-import-button',
  standalone: true,
  template: `
    <button
      type="button"
      [class]="buttonClass || 'kn-plus'"
      [attr.aria-label]="tooltip"
      [title]="tooltip"
      data-testid="markdown-import-button"
      (click)="openPicker()"
    >
      +
    </button>
    <input
      #fileInput
      type="file"
      class="hidden"
      accept=".md,text/markdown,text/plain"
      data-testid="markdown-import-input"
      (change)="onFileSelected($event)"
    />
  `,
  styles: [
    `
      .hidden {
        display: none;
      }
    `,
  ],
})
export class MarkdownImportButtonComponent {
  private readonly importService = inject(MarkdownImportService);

  @ViewChild('fileInput') fileInput?: ElementRef<HTMLInputElement>;

  @Input() currentContent = '';
  @Input() currentTitle = '';
  @Input() buttonClass = '';
  @Input() tooltip = 'Import markdown';

  @Output() imported = new EventEmitter<MarkdownImportResult>();
  @Output() importError = new EventEmitter<string>();

  openPicker(): void {
    this.fileInput?.nativeElement.click();
  }

  async onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) {
      return;
    }

    try {
      const result = await this.importService.importFromFile(
        file,
        this.currentContent,
        this.currentTitle
      );
      if (result) {
        this.imported.emit(result);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Import failed.';
      this.importError.emit(message);
    }
  }
}
