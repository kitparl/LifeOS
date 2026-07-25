import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { SecretInputComponent } from '../../shared/secret-input/secret-input.component';

@Component({
  selector: 'app-settings-change-password',
  standalone: true,
  imports: [ReactiveFormsModule, SecretInputComponent],
  template: `
    <div class="panel !p-0 overflow-hidden max-w-md">
      <div class="title-bar">Change Password</div>
      <div style="padding: 1rem;">
        <form [formGroup]="form" (ngSubmit)="onSubmit()" class="flex flex-col gap-3">
          <div class="flex flex-col gap-1">
            <label class="form-label" for="cp-current">Current password</label>
            <app-secret-input
              inputId="cp-current"
              formControlName="current_password"
              autocomplete="current-password"
              placeholder="Enter current password"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="form-label" for="cp-new">New password</label>
            <app-secret-input
              inputId="cp-new"
              formControlName="new_password"
              autocomplete="new-password"
              placeholder="At least 8 characters"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="form-label" for="cp-confirm">Confirm new password</label>
            <app-secret-input
              inputId="cp-confirm"
              formControlName="confirm_password"
              autocomplete="new-password"
              placeholder="Repeat new password"
            />
            @if (form.errors?.['mismatch'] && form.get('confirm_password')?.touched) {
              <p class="text-xs" style="color: var(--danger)">Passwords do not match.</p>
            }
          </div>

          @if (success()) {
            <p class="text-sm" style="color: var(--success)">Password changed successfully.</p>
          }
          @if (error()) {
            <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
          }

          <button
            class="btn-primary"
            type="submit"
            [disabled]="form.invalid || saving()"
          >
            {{ saving() ? 'Saving…' : 'Update password' }}
          </button>
        </form>
      </div>
    </div>
  `,
})
export class SettingsChangePasswordComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);

  readonly saving = signal(false);
  readonly success = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group(
    {
      current_password: ['', Validators.required],
      new_password: ['', [Validators.required, Validators.minLength(8)]],
      confirm_password: ['', Validators.required],
    },
    { validators: (g) => (g.get('new_password')!.value === g.get('confirm_password')!.value ? null : { mismatch: true }) },
  );

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { current_password, new_password } = this.form.getRawValue();
    this.saving.set(true);
    this.success.set(false);
    this.error.set(null);

    this.auth.changePassword(current_password, new_password).subscribe({
      next: () => {
        this.success.set(true);
        this.saving.set(false);
        this.form.reset();
      },
      error: (err) => {
        const msg = err?.error?.detail ?? 'Could not change password. Please try again.';
        this.error.set(msg);
        this.saving.set(false);
      },
    });
  }
}
