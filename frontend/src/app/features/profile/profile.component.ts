import { Component, effect, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { UsernameService } from '../../core/services/username.service';
import { ModalComponent } from '../../shared/modal/modal.component';
import {
  usernameAvailableValidator,
  usernameErrorMessage,
  usernameFormatValidator,
} from '../../core/validators/username.validator';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [ReactiveFormsModule, ModalComponent],
  template: `
    <div class="max-w-md space-y-6">
      <div>
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

      <div>
        <div class="title-bar">Username</div>
        <div class="panel">
          <form [formGroup]="usernameForm" (ngSubmit)="openConfirm()" class="flex flex-col gap-3">
            <p class="text-sm text-[var(--text-muted)]">
              Current username:
              <strong>{{ '@' + (currentUsername() || '—') }}</strong>
            </p>
            <label class="text-sm font-medium">
              New username
              <input
                class="input-field mt-1"
                type="text"
                formControlName="username"
                autocomplete="username"
                placeholder="john_smith"
              />
            </label>
            @if (usernameStatus()) {
              <p
                class="text-sm"
                [class.text-green-800]="usernameStatus() === 'available'"
                [class.text-red-700]="usernameStatus() === 'error'"
                [class.text-gray-600]="usernameStatus() === 'checking'"
              >
                {{ usernameStatusMessage() }}
              </p>
            }
            <label class="text-sm font-medium">
              Reason <span class="font-normal text-[var(--text-muted)]">(optional)</span>
              <input class="input-field mt-1" type="text" formControlName="reason" maxlength="500" />
            </label>
            @if (usernameMessage()) {
              <p class="text-sm text-green-800">{{ usernameMessage() }}</p>
            }
            @if (usernameError()) {
              <p class="text-sm text-red-700">{{ usernameError() }}</p>
            }
            <button
              class="btn-primary"
              type="submit"
              [disabled]="usernameForm.invalid || usernameForm.pending || usernameSaving()"
            >
              Change username
            </button>
          </form>
        </div>
      </div>
    </div>

    <app-modal
      [open]="confirmOpen()"
      title="Confirm username change"
      (closed)="confirmOpen.set(false)"
    >
      <div body class="text-sm space-y-2">
        <p>Change your username to:</p>
        <p class="font-medium">{{ '@' + pendingUsername() }}</p>
        <p class="text-[var(--text-muted)]">This updates immediately across the app.</p>
      </div>
      <div footer class="flex gap-2 justify-end">
        <button type="button" class="btn-secondary" (click)="confirmOpen.set(false)">Cancel</button>
        <button
          type="button"
          class="btn-primary"
          [disabled]="usernameSaving()"
          (click)="confirmChange()"
        >
          Confirm
        </button>
      </div>
    </app-modal>
  `,
})
export class ProfileComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly usernameService = inject(UsernameService);

  readonly email = signal('');
  readonly currentUsername = signal('');
  readonly saving = signal(false);
  readonly message = signal<string | null>(null);
  readonly error = signal<string | null>(null);

  readonly usernameSaving = signal(false);
  readonly usernameMessage = signal<string | null>(null);
  readonly usernameError = signal<string | null>(null);
  readonly confirmOpen = signal(false);
  readonly pendingUsername = signal('');

  readonly form = this.fb.nonNullable.group({
    display_name: ['', Validators.required],
    timezone: ['', Validators.required],
  });

  readonly usernameForm = this.fb.nonNullable.group({
    username: [
      '',
      {
        validators: [Validators.required, usernameFormatValidator()],
        asyncValidators: [
          usernameAvailableValidator(this.usernameService, {
            currentUsername: () => this.currentUsername(),
          }),
        ],
      },
    ],
    reason: [''],
  });

  constructor() {
    effect(() => {
      const user = this.auth.user();
      if (user) {
        this.email.set(user.email);
        this.currentUsername.set(user.username);
        this.form.patchValue({
          display_name: user.display_name,
          timezone: user.timezone,
        });
        if (!this.usernameForm.controls.username.value) {
          this.usernameForm.patchValue({ username: user.username }, { emitEvent: false });
        }
      }
    });
  }

  usernameStatus(): 'checking' | 'available' | 'error' | null {
    const ctrl = this.usernameForm.controls.username;
    if (!ctrl.value || ctrl.pristine) return null;
    const current = this.currentUsername().toLowerCase();
    if (String(ctrl.value).trim().toLowerCase() === current && ctrl.valid) return null;
    if (ctrl.pending) return 'checking';
    if (ctrl.errors) return 'error';
    if (ctrl.valid) return 'available';
    return null;
  }

  usernameStatusMessage(): string {
    const ctrl = this.usernameForm.controls.username;
    if (ctrl.pending) return 'Checking…';
    const err = usernameErrorMessage(ctrl);
    if (err) return `✗ ${err}`;
    if (ctrl.valid) return '✓ Username available';
    return '';
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

  openConfirm(): void {
    if (this.usernameForm.invalid || this.usernameForm.pending) {
      return;
    }
    const next = String(this.usernameForm.controls.username.value).trim().toLowerCase();
    if (next === this.currentUsername().toLowerCase()) {
      this.usernameMessage.set('That is already your username.');
      return;
    }
    this.pendingUsername.set(next);
    this.usernameMessage.set(null);
    this.usernameError.set(null);
    this.confirmOpen.set(true);
  }

  confirmChange(): void {
    const username = this.pendingUsername();
    const reason = this.usernameForm.controls.reason.value?.trim() || null;
    this.usernameSaving.set(true);
    this.usernameService.changeUsername({ username, reason }).subscribe({
      next: (user) => {
        this.auth.user.set(user);
        this.currentUsername.set(user.username);
        this.usernameMessage.set('Username updated successfully.');
        this.usernameError.set(null);
        this.confirmOpen.set(false);
        this.usernameSaving.set(false);
        this.usernameForm.markAsPristine();
      },
      error: (err) => {
        const detail = err?.error?.detail;
        this.usernameError.set(typeof detail === 'string' ? detail : 'Could not change username.');
        this.confirmOpen.set(false);
        this.usernameSaving.set(false);
      },
    });
  }
}
