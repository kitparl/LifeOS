import { Component, Input, inject } from '@angular/core';
import {
  codeBlockFirstLine,
  normalizeExecutableLanguage,
} from '../../../shared/code-workspace/utils/fenced-code-blocks';
import { CodeBlock } from '../models/knowledge-notes.models';
import { KnowledgeCodeRunnerService } from '../services/knowledge-code-runner.service';

/** Run status + Enable/Disable, with an optional compact block picker for write mode. */
@Component({
  selector: 'app-knowledge-run-bar',
  standalone: true,
  template: `
    @if (blocks.length > 0) {
      <div class="kn-python">
        @if (runner.enabled()) {
          <span class="kn-python__status">Run enabled · {{ countLabel }}</span>
          @if (showPicker) {
            <select
              class="input-field !w-auto max-w-xs text-xs"
              aria-label="Code block to run"
              (change)="onSelect($event)"
            >
              @for (block of blocks; track block.id; let i = $index) {
                <option [value]="i" [selected]="block === selectedBlock">{{ describe(block, i) }}</option>
              }
            </select>
            <button
              type="button"
              class="btn-secondary text-xs"
              [disabled]="runner.runningBlockId() !== null"
              (click)="runSelected()"
            >
              {{ runner.runningBlockId() === selectedBlock?.id ? 'Running…' : 'Run' }}
            </button>
          }
          <button type="button" class="btn-ghost text-xs" (click)="runner.setEnabled(false)">
            Disable run
          </button>
        } @else {
          <span class="kn-python__status kn-python__status--off">Run disabled · {{ countLabel }}</span>
          <button type="button" class="btn-ghost text-xs" (click)="runner.setEnabled(true)">
            Enable
          </button>
        }
      </div>
    }
  `,
})
export class KnowledgeRunBarComponent {
  readonly runner = inject(KnowledgeCodeRunnerService);

  @Input({ required: true }) blocks: CodeBlock[] = [];
  @Input({ required: true }) sectionId = '';
  @Input() showPicker = false;

  /** By position: block ids embed character offsets and change while typing. */
  private selectedIndex = 0;

  get countLabel(): string {
    return this.blocks.length === 1 ? '1 runnable block' : `${this.blocks.length} runnable blocks`;
  }

  get selectedBlock(): CodeBlock | undefined {
    return this.blocks[this.selectedIndex] ?? this.blocks[0];
  }

  describe(block: CodeBlock, index: number): string {
    const language = normalizeExecutableLanguage(block.language);
    return `#${index + 1} · ${language} · L${block.lineStart}: ${codeBlockFirstLine(block.code)}`;
  }

  onSelect(event: Event): void {
    this.selectedIndex = Number((event.target as HTMLSelectElement).value);
  }

  runSelected(): void {
    const block = this.selectedBlock;
    if (block) {
      this.runner.run(this.sectionId, block);
    }
  }
}
