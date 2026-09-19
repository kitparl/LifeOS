import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import DOMPurify from 'dompurify';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';

@Component({
  selector: 'app-html-preview-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="html-preview"
      title="HTML Preview"
      description="Preview HTML in a sandboxed, script-blocked frame. Nothing here can affect the rest of the app or load external resources."
      icon="square-code"
    >
      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">HTML</label>
          <textarea
            class="input-field h-80 resize-y font-mono text-sm"
            placeholder="<h1>Hello</h1>"
            [ngModel]="input()"
            (ngModelChange)="onChange($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">Preview</label>
          <iframe class="input-field h-80 w-full" style="background: #fff" sandbox="" [srcdoc]="sanitized()" title="HTML preview"></iframe>
        </div>
      </div>
    </app-dev-tool-shell>
  `,
})
export class HtmlPreviewToolComponent {
  readonly input = signal('<h1>Hello, world!</h1>\n<p>Edit the HTML on the left.</p>');
  readonly sanitized = computed(() => DOMPurify.sanitize(this.input(), { WHOLE_DOCUMENT: true }));

  onChange(value: string): void {
    this.input.set(value);
  }
}
