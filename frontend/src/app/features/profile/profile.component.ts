import { Component, effect, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="max-w-md">
      <div class="title-bar">Profile</div>
      <div class="panel">
        <form [formGroup]="form" (ngSubmit)="onSubmit()" class="flex flex-col gap-3">
          <label class="text-sm font-medium">
            Email
            <input class="input-field mt-1 bg-gray-100" type="email" [value]="email()" disabled />
          </label>
          <label class="text-sm font-medium">
            Display name
            <input class="input-field mt-1" type="text" formControlName="display_name" />
          </label>
          <label class="text-sm font-medium">
            Timezone
            <input class="input-field mt-1" type="text" formControlName="timezone" placeholder="UTC" />
          </label>
          @if (message()) {
            <p class="text-sm text-green-800">{{ message() }}</p>
          }
          @if (error()) {
            <p class="text-sm text-red-700">{{ error() }}</p>
          }
          <button class="btn-primary" type="submit" [disabled]="form.invalid || saving()">Save</button>
        </form>
      </div>
    </div>
  `,
})
export class ProfileComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);

  readonly email = signal('');
  readonly saving = signal(false);
  readonly message = signal<string | null>(null);
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    display_name: ['', Validators.required],
    timezone: ['', Validators.required],
  });

  constructor() {
    effect(() => {
      const user = this.auth.user();
      if (user) {
        this.email.set(user.email);
        this.form.patchValue({
          display_name: user.display_name,
          timezone: user.timezone,
        });
      }
    });
  }

  onSubmit(): void {
    if (this.form.invalid) {
      return;
    }
    this.saving.set(true);
    this.message.set(null);
    this.error.set(null);
    this.auth.updateProfile(this.form.getRawValue()).subscribe({
      next: () => {
        this.message.set('Profile updated.');
        this.saving.set(false);
      },
      error: () => {
        this.error.set('Could not update profile.');
        this.saving.set(false);
      },
    });
  }
}
