import { Component, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { SPLIT_EXPIRY_OPTIONS, SplitExpiry, SplitGroupCreatePayload } from '../models/split.models';

/** Group name, your name and link expiry. Bills are added after create, inside the group. */
@Component({
  selector: 'app-split-create',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form class="grid gap-3 text-sm" [formGroup]="form" (ngSubmit)="submit()" data-testid="split-create-form">
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block" for="split-group-name">Group name</label>
          <input id="split-group-name" class="input-field" formControlName="name" maxlength="80" placeholder="Dinner" />
        </div>
        <div>
          <label class="mb-1 block" for="split-creator-name">Your name</label>
          <input id="split-creator-name" class="input-field" formControlName="creator_name" maxlength="40" />
        </div>
      </div>
      <div>
        <span class="mb-1 block">Link stays open for</span>
        <div class="flex flex-wrap gap-4 text-xs">
          @for (option of expiryOptions; track option.value) {
            <label class="flex items-center gap-2">
              <input type="radio" formControlName="expiry" [value]="option.value" data-testid="split-expiry-option" />
              {{ option.label }}
            </label>
          }
        </div>
      </div>
      <div class="flex justify-end">
        <button type="submit" class="btn-primary text-xs" data-testid="split-create" [disabled]="form.invalid || busy()">
          Create
        </button>
      </div>
    </form>
  `,
})
export class SplitCreateComponent {
  private readonly fb = inject(FormBuilder);

  readonly busy = input(false);
  readonly create = output<SplitGroupCreatePayload>();

  readonly expiryOptions = SPLIT_EXPIRY_OPTIONS;

  readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(80), Validators.pattern(/\S/)]],
    creator_name: ['', [Validators.required, Validators.maxLength(40), Validators.pattern(/\S/)]],
    expiry: ['24h' as SplitExpiry, Validators.required],
  });

  submit(): void {
    if (this.form.invalid) return;
    const { name, creator_name, expiry } = this.form.getRawValue();
    this.create.emit({ name: name.trim(), creator_name: creator_name.trim(), expiry });
  }
}
