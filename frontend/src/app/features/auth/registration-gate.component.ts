import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { RegistrationGateService } from '../../core/services/registration-gate.service';

@Component({
  selector: 'app-registration-gate',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="login-root">
      <div class="login-brand">
        <div class="login-brand__inner">
          <div class="login-brand__logo">
            <span style="font-size: 2rem; font-weight: 700; color: var(--primary); letter-spacing: -1px">LifeOS</span>
            <span class="badge badge--default" style="margin-left: 0.5rem; vertical-align: middle">Admin</span>
          </div>
          <p class="login-brand__tagline">Registration access gate</p>
          <ul class="login-features">
            <li class="login-feature">
              <span class="login-feature__dot"></span>
              <div>
                <strong>Restricted unlock</strong>
                <p>Only the allowed admin can unlock registration for this browser session.</p>
              </div>
            </li>
            <li class="login-feature">
              <span class="login-feature__dot"></span>
              <div>
                <strong>Session scoped</strong>
                <p>Closing the browser or locking registration revokes access again.</p>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <div class="login-form-pane">
        <div class="login-form-inner">
          <div class="login-form-header">
            <h1 style="font-size: 1.25rem; font-weight: 600; color: var(--text); margin: 0 0 0.25rem">
              Unlock registration
            </h1>
            <p style="font-size: 0.8125rem; color: var(--text-muted); margin: 0">
              Sign in as the registration admin
            </p>
          </div>

          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="login-form" autocomplete="on">
            <div class="form-group">
              <label class="form-label" for="gate-email">Email</label>
              <input
                id="gate-email"
                class="input-field"
                type="email"
                formControlName="email"
                autocomplete="username"
                placeholder="admin@example.com"
              />
            </div>

            <div class="form-group">
              <label class="form-label" for="gate-password">Password</label>
              <input
                id="gate-password"
                class="input-field"
                type="password"
                formControlName="password"
                autocomplete="current-password"
                placeholder="Your password"
              />
            </div>

            @if (error()) {
              <div
                class="badge badge--danger"
                style="display: block; padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.8125rem; font-weight: 400; text-transform: none; letter-spacing: 0"
              >
                {{ error() }}
              </div>
            }

            <button
              class="btn-primary w-full"
              type="submit"
              style="min-height: 40px; font-size: 0.9rem"
              [disabled]="form.invalid || submitting()"
            >
              {{ submitting() ? 'Unlocking…' : 'Unlock' }}
            </button>
          </form>
        </div>

        <footer class="login-footer">
          <p class="login-footer__copy">LifeOS — Registration is locked by default.</p>
        </footer>
      </div>
    </div>

    <style>
      .login-root {
        display: flex;
        min-height: 100dvh;
        background: var(--page-bg);
      }

      .login-brand {
        display: none;
        flex: 1;
        background: var(--sidebar-bg);
        border-right: 1px solid var(--border);
        overflow-y: auto;
        padding: 3rem 2.5rem;
      }

      @media (min-width: 768px) {
        .login-brand {
          display: flex;
          align-items: flex-start;
        }
      }

      .login-brand__inner {
        width: 100%;
        max-width: 380px;
        margin: auto 0;
        padding: 1rem 0;
      }

      .login-brand__logo {
        display: flex;
        align-items: baseline;
        margin-bottom: 0.5rem;
      }

      .login-brand__tagline {
        font-size: 0.9rem;
        color: var(--text-muted);
        margin: 0 0 2rem;
        font-weight: 400;
      }

      .login-features {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
      }

      .login-feature {
        display: flex;
        gap: 0.875rem;
        align-items: flex-start;
      }

      .login-feature__dot {
        display: block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--primary);
        margin-top: 5px;
        flex-shrink: 0;
      }

      .login-feature strong {
        display: block;
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 2px;
      }

      .login-feature p {
        margin: 0;
        font-size: 0.8rem;
        color: var(--text-muted);
        line-height: 1.5;
      }

      .login-form-pane {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        flex: 0 0 100%;
        padding: 2rem 1.5rem;
        overflow-y: auto;
      }

      @media (min-width: 768px) {
        .login-form-pane {
          flex: 0 0 400px;
          padding: 3rem 2.5rem;
        }
      }

      .login-form-inner {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        max-width: 340px;
        margin: auto auto;
        width: 100%;
      }

      .login-form-header {
        margin-bottom: 1.75rem;
      }

      .login-form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }

      .form-group {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }

      .form-label {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text);
      }

      .login-footer {
        margin-top: 3rem;
        text-align: center;
      }

      .login-footer__copy {
        font-size: 0.7rem;
        color: var(--text-faint);
        margin: 0;
      }
    </style>
  `,
})
export class RegistrationGateComponent {
  private readonly fb = inject(FormBuilder);
  private readonly gate = inject(RegistrationGateService);
  private readonly router = inject(Router);

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  onSubmit(): void {
    if (this.form.invalid) return;
    this.submitting.set(true);
    this.error.set(null);
    this.gate.login(this.form.getRawValue()).subscribe({
      next: () => this.router.navigate(['/add-new-user']),
      error: () => {
        this.error.set('Invalid credentials. Please try again.');
        this.submitting.set(false);
      },
      complete: () => this.submitting.set(false),
    });
  }
}
