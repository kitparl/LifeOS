import { Component, inject } from '@angular/core';
import { ModalComponent } from '../modal/modal.component';
import { MarkdownImportChoiceService } from './markdown-import-choice.service';

@Component({
  selector: 'app-markdown-import-choice-host',
  standalone: true,
  imports: [ModalComponent],
  template: `
    <app-modal
      [open]="choice.open()"
      title="Import markdown"
      [maxWidth]="'420px'"
      (closed)="choice.pick('cancel')"
    >
      <div body class="text-sm">{{ choice.message() }}</div>
      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="choice.pick('cancel')">
          Cancel
        </button>
        <button type="button" class="btn-secondary text-xs" (click)="choice.pick('append')">
          Append
        </button>
        <button type="button" class="btn-primary text-xs" (click)="choice.pick('replace')">
          Replace
        </button>
      </div>
    </app-modal>
  `,
})
export class MarkdownImportChoiceHostComponent {
  readonly choice = inject(MarkdownImportChoiceService);
}
