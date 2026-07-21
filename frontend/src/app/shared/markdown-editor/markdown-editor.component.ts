import {
  Component,
  ElementRef,
  HostListener,
  Input,
  ViewChild,
  computed,
  forwardRef,
  inject,
  signal,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { MarkdownService } from '../markdown/markdown.service';

type ViewMode = 'write' | 'split' | 'preview';

/**
 * MarkdownEditorComponent — reusable, framework-agnostic Markdown editor.
 *
 * Stores raw Markdown text (ControlValueAccessor), offers a formatting toolbar,
 * live write/split/preview modes, auto-resize, a distraction-free fullscreen
 * mode (with a reachable exit control + Escape), and is mobile + keyboard
 * friendly. Reuse anywhere: Journal, Knowledge Notes, docs, notes, etc.
 *
 *   <app-markdown-editor formControlName="content" [minHeight]="'320px'" />
 */
@Component({
  selector: 'app-markdown-editor',
  standalone: true,
  imports: [],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => MarkdownEditorComponent),
      multi: true,
    },
  ],
  template: `
    <div
      class="md-editor"
      [class.md-editor--fullscreen]="fullscreen()"
      [attr.data-mode]="mode()"
    >
      <div class="md-editor__toolbar">
        <div class="md-editor__tools">
          <button type="button" class="md-editor__tool" title="Bold (Ctrl+B)"
                  (click)="wrap('**', '**')"><strong>B</strong></button>
          <button type="button" class="md-editor__tool" title="Italic (Ctrl+I)"
                  (click)="wrap('*', '*')"><em>I</em></button>
          <button type="button" class="md-editor__tool" title="Heading"
                  (click)="prefixLine('## ')">H</button>
          <button type="button" class="md-editor__tool" title="Quote"
                  (click)="prefixLine('> ')">❝</button>
          <button type="button" class="md-editor__tool" title="Bullet list"
                  (click)="prefixLine('- ')">•—</button>
          <button type="button" class="md-editor__tool" title="Numbered list"
                  (click)="prefixLine('1. ')">1.</button>
          <button type="button" class="md-editor__tool" title="Checklist"
                  (click)="prefixLine('- [ ] ')">☑</button>
          <button type="button" class="md-editor__tool" title="Inline code"
                  (click)="wrap('\`', '\`')">&#123;&#125;</button>
          <button type="button" class="md-editor__tool" title="Code block"
                  (click)="wrap('\\n\`\`\`\\n', '\\n\`\`\`\\n')">&lt;/&gt;</button>
          <button type="button" class="md-editor__tool" title="Link (Ctrl+K)"
                  (click)="insertLink()">🔗</button>
          <button type="button" class="md-editor__tool" title="Image"
                  (click)="insertImage()">🖼</button>
        </div>

        <div class="md-editor__spacer"></div>

        <div class="md-editor__modes" role="tablist" aria-label="Editor view">
          <button type="button" class="md-editor__mode" [class.active]="mode() === 'write'"
                  (click)="setMode('write')">Write</button>
          <button type="button" class="md-editor__mode md-editor__mode--split"
                  [class.active]="mode() === 'split'" (click)="setMode('split')">Split</button>
          <button type="button" class="md-editor__mode" [class.active]="mode() === 'preview'"
                  (click)="setMode('preview')">Preview</button>
          <button type="button" class="md-editor__tool md-editor__fs-toggle"
                  [title]="fullscreen() ? 'Exit fullscreen (Esc)' : 'Fullscreen'"
                  (click)="toggleFullscreen()">{{ fullscreen() ? '✕' : '⛶' }}</button>
        </div>
      </div>

      <div class="md-editor__panes">
        @if (mode() !== 'preview') {
          <textarea
            #ta
            class="md-editor__input"
            [style.minHeight]="minHeight"
            [attr.placeholder]="placeholder"
            [disabled]="disabled()"
            [value]="value()"
            (input)="onInput($event)"
            (blur)="onTouched()"
            (keydown)="onKeydown($event)"
          ></textarea>
        }
        @if (mode() !== 'write') {
          <div class="md-editor__preview markdown-body" [innerHTML]="preview()"></div>
        }
      </div>
    </div>
  `,
})
export class MarkdownEditorComponent implements ControlValueAccessor {
  @ViewChild('ta') textarea?: ElementRef<HTMLTextAreaElement>;

  @Input() placeholder = 'Start writing…';
  @Input() minHeight = '240px';

  private readonly markdown = inject(MarkdownService);
  private readonly sanitizer = inject(DomSanitizer);

  readonly value = signal('');
  readonly mode = signal<ViewMode>('write');
  readonly fullscreen = signal(false);
  readonly disabled = signal(false);

  readonly preview = computed<SafeHtml>(() =>
    this.sanitizer.bypassSecurityTrustHtml(this.markdown.render(this.value())),
  );

  private onChange: (value: string) => void = () => {};
  onTouched: () => void = () => {};

  writeValue(value: string): void {
    this.value.set(value || '');
    queueMicrotask(() => this.autoGrow());
  }
  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }
  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
  setDisabledState(isDisabled: boolean): void {
    this.disabled.set(isDisabled);
  }

  setMode(mode: ViewMode): void {
    this.mode.set(mode);
    if (mode !== 'preview') queueMicrotask(() => this.autoGrow());
  }

  toggleFullscreen(): void {
    this.fullscreen.set(!this.fullscreen());
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.fullscreen()) this.fullscreen.set(false);
  }

  onInput(event: Event): void {
    const el = event.target as HTMLTextAreaElement;
    this.value.set(el.value);
    this.onChange(el.value);
    this.autoGrow();
  }

  onKeydown(event: KeyboardEvent): void {
    const mod = event.ctrlKey || event.metaKey;
    if (!mod) return;
    const key = event.key.toLowerCase();
    if (key === 'b') {
      event.preventDefault();
      this.wrap('**', '**');
    } else if (key === 'i') {
      event.preventDefault();
      this.wrap('*', '*');
    } else if (key === 'k') {
      event.preventDefault();
      this.insertLink();
    }
  }

  private autoGrow(): void {
    const el = this.textarea?.nativeElement;
    if (!el || this.fullscreen()) return;
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight}px`;
  }

  /** Wrap current selection (or caret) with before/after tokens. */
  wrap(before: string, after: string): void {
    const el = this.textarea?.nativeElement;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const text = el.value;
    const selected = text.slice(start, end);
    const next = text.slice(0, start) + before + selected + after + text.slice(end);
    this.commit(next);
    const caret = start + before.length + selected.length;
    queueMicrotask(() => {
      el.focus();
      el.setSelectionRange(selected ? caret : start + before.length, selected ? caret : start + before.length);
    });
  }

  /** Prefix the start of each selected line (lists, headings, quotes). */
  prefixLine(prefix: string): void {
    const el = this.textarea?.nativeElement;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const text = el.value;
    const lineStart = text.lastIndexOf('\n', start - 1) + 1;
    const block = text.slice(lineStart, end);
    const prefixed = block
      .split('\n')
      .map((line) => (line.startsWith(prefix) ? line : prefix + line))
      .join('\n');
    const next = text.slice(0, lineStart) + prefixed + text.slice(end);
    this.commit(next);
    queueMicrotask(() => el.focus());
  }

  insertLink(): void {
    const el = this.textarea?.nativeElement;
    if (!el) return;
    const selected = el.value.slice(el.selectionStart, el.selectionEnd) || 'text';
    this.wrapWith(`[${selected}](https://)`);
  }

  insertImage(): void {
    this.wrapWith('![alt](https://)');
  }

  private wrapWith(snippet: string): void {
    const el = this.textarea?.nativeElement;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const next = el.value.slice(0, start) + snippet + el.value.slice(end);
    this.commit(next);
    queueMicrotask(() => el.focus());
  }

  private commit(next: string): void {
    this.value.set(next);
    this.onChange(next);
    this.autoGrow();
  }
}
