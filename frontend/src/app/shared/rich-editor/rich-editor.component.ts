import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  SimpleChanges,
  ViewChild,
  forwardRef,
  signal,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';

/**
 * RichEditorComponent — TipTap-based WYSIWYG editor
 *
 * Usage with reactive forms:
 *   <app-rich-editor formControlName="content" [placeholder]="'Write something…'" />
 *
 * The stored value is HTML. Plain-text legacy values are displayed as-is in readonly mode.
 */
@Component({
  selector: 'app-rich-editor',
  standalone: true,
  imports: [],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => RichEditorComponent),
      multi: true,
    },
  ],
  template: `
    <!-- Toolbar -->
    <div class="rich-editor__toolbar">
      <button type="button" class="rich-editor__tool" title="Bold (Ctrl+B)"
              (click)="execCmd('bold')" [class.active]="editor?.isActive('bold')">
        <strong>B</strong>
      </button>
      <button type="button" class="rich-editor__tool" title="Italic (Ctrl+I)"
              (click)="execCmd('italic')" [class.active]="editor?.isActive('italic')">
        <em>I</em>
      </button>
      <button type="button" class="rich-editor__tool" title="Heading 2"
              (click)="execCmd('heading')" [class.active]="editor?.isActive('heading', {level: 2})">
        H2
      </button>
      <button type="button" class="rich-editor__tool" title="Bullet list"
              (click)="execCmd('bulletList')" [class.active]="editor?.isActive('bulletList')">
        •—
      </button>
      <button type="button" class="rich-editor__tool" title="Ordered list"
              (click)="execCmd('orderedList')" [class.active]="editor?.isActive('orderedList')">
        1.
      </button>
      <button type="button" class="rich-editor__tool" title="Blockquote"
              (click)="execCmd('blockquote')" [class.active]="editor?.isActive('blockquote')">
        ❝
      </button>
      <button type="button" class="rich-editor__tool" title="Code block"
              (click)="execCmd('codeBlock')" [class.active]="editor?.isActive('codeBlock')">
        &#123;&#125;
      </button>
      <div class="rich-editor__sep"></div>
      <button type="button" class="rich-editor__tool" title="Focus mode"
              (click)="toggleFocus()" [class.active]="focusMode()">
        ⊡
      </button>
    </div>

    <!-- Editor surface -->
    <div
      #editorEl
      class="rich-editor__content"
      [class.rich-editor__content--focus]="focusMode()"
    ></div>
  `,
})
export class RichEditorComponent
  implements ControlValueAccessor, AfterViewInit, OnDestroy, OnChanges
{
  @ViewChild('editorEl') editorEl!: ElementRef<HTMLElement>;

  @Input() placeholder = 'Start writing…';
  @Input() minHeight = '200px';

  editor?: Editor;
  focusMode = signal(false);

  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};
  private pendingValue = '';
  private disabled = false;

  ngAfterViewInit(): void {
    this.editor = new Editor({
      element: this.editorEl.nativeElement,
      extensions: [StarterKit],
      content: this.pendingValue || '',
      editable: !this.disabled,
      onUpdate: ({ editor }) => {
        const html = editor.isEmpty ? '' : editor.getHTML();
        this.onChange(html);
        this.onTouched();
      },
    });

    // Apply pending value if written before view init
    if (this.pendingValue) {
      this.editor.commands.setContent(this.pendingValue, { emitUpdate: false });
    }

    // Style the host element's ProseMirror div
    this.applyEditorStyles();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['placeholder'] && this.editor) {
      this.applyEditorStyles();
    }
  }

  ngOnDestroy(): void {
    this.editor?.destroy();
  }

  // ControlValueAccessor
  writeValue(value: string): void {
    if (this.editor) {
      const current = this.editor.isEmpty ? '' : this.editor.getHTML();
      if (current !== value) {
        this.editor.commands.setContent(value || '', { emitUpdate: false });
      }
    } else {
      this.pendingValue = value || '';
    }
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    this.editor?.setEditable(!isDisabled);
  }

  execCmd(cmd: string): void {
    if (!this.editor) return;
    const c = this.editor.chain().focus();
    switch (cmd) {
      case 'bold':         c.toggleBold().run(); break;
      case 'italic':       c.toggleItalic().run(); break;
      case 'heading':      c.toggleHeading({ level: 2 }).run(); break;
      case 'bulletList':   c.toggleBulletList().run(); break;
      case 'orderedList':  c.toggleOrderedList().run(); break;
      case 'blockquote':   c.toggleBlockquote().run(); break;
      case 'codeBlock':    c.toggleCodeBlock().run(); break;
    }
  }

  toggleFocus(): void {
    this.focusMode.set(!this.focusMode());
    this.editor?.commands.focus();
  }

  private applyEditorStyles(): void {
    const el = this.editorEl?.nativeElement;
    if (!el) return;
    const pm = el.querySelector('.ProseMirror') as HTMLElement | null;
    if (pm) {
      pm.style.minHeight = this.minHeight;
      pm.style.outline = 'none';
      pm.style.padding = '0.875rem 1rem';
      pm.setAttribute('data-placeholder', this.placeholder);
    }
  }
}
