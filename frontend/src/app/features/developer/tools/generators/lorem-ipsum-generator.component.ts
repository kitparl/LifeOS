import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { generateLoremIpsum } from './generators.util';

@Component({
  selector: 'app-lorem-ipsum-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="lorem-ipsum-generator"
      title="Lorem Ipsum Generator"
      description="Generate placeholder text."
      icon="text"
    >
      <div class="flex flex-wrap items-end justify-between gap-4 pb-3">
        <div>
          <label class="form-label">Paragraphs</label>
          <input class="input-field w-24" type="number" min="1" max="50" [ngModel]="paragraphs()" (ngModelChange)="setParagraphs(+$event)" />
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="btn-primary" (click)="regenerate()">Generate</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>
      <textarea class="input-field h-64 resize-y text-sm" readonly [ngModel]="output()"></textarea>
    </app-dev-tool-shell>
  `,
})
export class LoremIpsumGeneratorToolComponent implements OnInit {
  readonly paragraphs = signal(3);
  readonly output = signal('');

  ngOnInit(): void {
    this.regenerate();
  }

  setParagraphs(v: number): void {
    this.paragraphs.set(Math.min(50, Math.max(1, v || 1)));
  }

  regenerate(): void {
    this.output.set(generateLoremIpsum(this.paragraphs()));
  }
}
