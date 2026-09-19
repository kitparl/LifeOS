import { DecimalPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  Input,
  OnChanges,
  inject,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MarkdownPipe } from '../../../markdown/markdown.pipe';
import { DocumentPreviewApiService } from '../../services/document-preview-api.service';

const MAX_BYTES = 1024 * 1024; // ~1 MB, per spec

/** Minimal CSV line parser — handles quoted fields with escaped ("") quotes. */
function parseCsvLine(line: string): string[] {
  const fields: string[] = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"' && line[i + 1] === '"') {
        field += '"';
        i++;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ',') {
      fields.push(field);
      field = '';
    } else {
      field += ch;
    }
  }
  fields.push(field);
  return fields;
}

@Component({
  selector: 'app-text-renderer',
  standalone: true,
  imports: [MarkdownPipe, DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="text-renderer">
      @if (loading) {
        <p class="state-text">Loading…</p>
      } @else if (error) {
        <p class="state-text error">{{ error }}</p>
      } @else {
        @if (truncated) {
          <p class="truncated-notice">
            Showing the first {{ maxBytes / 1024 / 1024 | number: '1.0-1' }} MB — the rest was
            truncated. Download the file to see everything.
          </p>
        }
        @switch (previewType) {
          @case ('markdown') {
            <div class="markdown-body" [innerHTML]="content | markdown"></div>
          }
          @case ('csv') {
            <div class="csv-table-wrap">
              <table class="csv-table">
                @for (row of rows; track $index; let isHeader = $first) {
                  <tr>
                    @for (cell of row; track $index) {
                      @if (isHeader) {
                        <th>{{ cell }}</th>
                      } @else {
                        <td>{{ cell }}</td>
                      }
                    }
                  </tr>
                }
              </table>
            </div>
          }
          @default {
            <pre class="plain-text">{{ content }}</pre>
          }
        }
      }
    </div>
  `,
  styles: [
    `
      .text-renderer {
        height: 100%;
        overflow: auto;
        padding: 1rem;
      }
      .state-text {
        color: var(--text-muted, #666);
        font-size: 0.875rem;
      }
      .state-text.error {
        color: var(--danger, #c0392b);
      }
      .truncated-notice {
        font-size: 0.8rem;
        color: var(--text-muted, #666);
        margin-bottom: 0.75rem;
      }
      .plain-text {
        white-space: pre-wrap;
        word-break: break-word;
        font-family: ui-monospace, monospace;
        font-size: 0.85rem;
        margin: 0;
      }
      .csv-table-wrap {
        overflow-x: auto;
      }
      .csv-table {
        border-collapse: collapse;
        font-size: 0.85rem;
      }
      .csv-table th,
      .csv-table td {
        border: 1px solid var(--xp-border, #ccc);
        padding: 0.25rem 0.5rem;
        text-align: left;
        white-space: nowrap;
      }
      .csv-table th {
        background: var(--surface-2, #f2f2f2);
        font-weight: 600;
      }
    `,
  ],
})
export class TextRendererComponent implements OnChanges {
  @Input({ required: true }) documentId!: string;
  @Input({ required: true }) previewType!: 'text' | 'csv' | 'markdown';

  private readonly api = inject(DocumentPreviewApiService);
  private readonly destroyRef = inject(DestroyRef);

  readonly maxBytes = MAX_BYTES;
  loading = true;
  error: string | null = null;
  content = '';
  truncated = false;
  rows: string[][] = [];

  ngOnChanges(): void {
    this.load();
  }

  private load(): void {
    this.loading = true;
    this.error = null;
    this.api
      .fetchText(this.documentId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (text) => {
          this.truncated = text.length > MAX_BYTES;
          this.content = this.truncated ? text.slice(0, MAX_BYTES) : text;
          this.rows = this.previewType === 'csv' ? this.content.split(/\r?\n/).filter((l) => l.length > 0).map(parseCsvLine) : [];
          this.loading = false;
        },
        error: () => {
          this.error = 'Could not load this file.';
          this.loading = false;
        },
      });
  }
}
