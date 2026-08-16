import { Component, inject } from '@angular/core';
import { ModalComponent } from '../modal/modal.component';
import { ConfirmService } from './confirm.service';

@Component({
  selector: 'app-confirm-host',
  standalone: true,
  imports: [ModalComponent],
  template: `
    <app-modal
      [open]="confirm.open()"
      [title]="confirm.title()"
      [maxWidth]="'420px'"
      (closed)="confirm.cancel()"
    >
      <div body class="text-sm">{{ confirm.message() }}</div>
      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="confirm.cancel()">Cancel</button>
        <button type="button" class="btn-danger text-xs" (click)="confirm.accept()">Delete</button>
      </div>
    </app-modal>
  `,
})
export class ConfirmHostComponent {
  readonly confirm = inject(ConfirmService);
}
