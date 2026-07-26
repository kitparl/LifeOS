import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="login-root">

      <!-- Left pane: brand + description -->
      <div class="login-brand">
        <div class="login-brand__inner">
          <div class="login-brand__logo">
            <span style="font-size: 2rem; font-weight: 700; color: var(--primary); letter-spacing: -1px">LifeOS</span>
            <span class="badge badge--default" style="margin-left: 0.5rem; vertical-align: middle">Beta</span>
          </div>
          <p class="login-brand__tagline">Your Personal AI Operating System</p>

          <ul class="login-features">
            <li class="login-feature">
              <span class="login-feature__dot"></span>
              <div>
                <strong>Unified Productivity Hub</strong>
                <p>Tasks, goals, habits, journal, calendar — all in one place.</p>
              </div>
            </li>
            <li class="login-feature">
              <span class="login-feature__dot"></span>
              <div>
                <strong>Knowledge Management</strong>
                <p>Vocabulary, Q&A, communication practice, documents, and memory.</p>
              </div>
            </li>
            <li class="login-feature">
              <span class="login-feature__dot"></span>
              <div>
                <strong>Health & Fitness</strong>
                <p>Running journal with events & competitions, habits tracking.</p>
              </div>
            </li>
            <li class="login-feature">
              <span class="login-feature__dot"></span>
              <div>
                <strong>Finance & Career</strong>
                <p>Income/expense tracking, career portfolio, job applications.</p>
              </div>
            </li>
            <li class="login-feature">
              <span class="login-feature__dot"></span>
              <div>
                <strong>AI Assistant</strong>
                <p>Context-aware AI powered by your own data. Works offline-first.</p>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- Right pane: login form -->
      <div class="login-form-pane">
        <div class="login-form-inner">
          <div class="login-form-header">
            <h1 style="font-size: 1.25rem; font-weight: 600; color: var(--text); margin: 0 0 0.25rem">Sign in</h1>
            <p style="font-size: 0.8125rem; color: var(--text-muted); margin: 0">Welcome back to LifeOS</p>
          </div>

          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="login-form" autocomplete="on">
            <div class="form-group">
              <label class="form-label" for="identifier">Email or username</label>
              <input
                id="identifier"
                class="input-field"
                type="text"
                formControlName="identifier"
                autocomplete="username"
                placeholder="you@example.com or johndoe"
              />
            </div>

            <div class="form-group">
              <label class="form-label" for="password">Password</label>
              <input
                id="password"
                class="input-field"
                type="password"
                formControlName="password"
                autocomplete="current-password"
                placeholder="Your password"
              />
            </div>

            @if (error()) {
              <div class="badge badge--danger" style="display: block; padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.8125rem; font-weight: 400; text-transform: none; letter-spacing: 0">
                {{ error() }}
              </div>
            }

            <button
              class="btn-primary w-full"
              type="submit"
              style="min-height: 40px; font-size: 0.9rem"
              [disabled]="form.invalid || submitting()"
            >
              {{ submitting() ? 'Signing in…' : 'Sign in' }}
            </button>
          </form>
        </div>

        <!-- Footer -->
        <footer class="login-footer">
          <div class="login-footer__links">
            <a href="https://scripted-mind.vercel.app/" target="_blank" rel="noopener noreferrer" class="login-footer__link">Blog</a>
            <span class="login-footer__sep">·</span>
            <a href="#" class="login-footer__link">Portfolio</a>
            <span class="login-footer__sep">·</span>
            <a href="https://wa.me/917522023037" target="_blank" rel="noopener noreferrer" class="login-footer__link">WhatsApp</a>
          </div>
          <p class="login-footer__copy">LifeOS — Personal productivity, privately yours.</p>
        </footer>
      </div>
    </div>

    <style>
      .login-root {
        display: flex;
        min-height: 100dvh;
        background: var(--page-bg);
      }

      /* Brand pane */
      .login-brand {
        display: none;
        flex: 1;
        background: var(--sidebar-bg);
        border-right: 1px solid var(--border);
        overflow-y: auto;
        padding: 3rem 2.5rem;
      }

      @media (min-width: 768px) {
        .login-brand { display: flex; align-items: flex-start; }
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

      /* Form pane */
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

      /* Footer */
      .login-footer {
        margin-top: 3rem;
        text-align: center;
      }

      .login-footer__links {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
      }

      .login-footer__link {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-decoration: none;
        transition: color 120ms ease;
      }

      .login-footer__link:hover {
        color: var(--primary);
      }

      .login-footer__sep {
        font-size: 0.75rem;
        color: var(--text-faint);
      }

      .login-footer__copy {
        font-size: 0.7rem;
        color: var(--text-faint);
        margin: 0;
      }
    </style>
  `,
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    identifier: ['', Validators.required],
    password: ['', Validators.required],
  });

  onSubmit(): void {
    if (this.form.invalid) return;
    this.submitting.set(true);
    this.error.set(null);
    this.auth.login(this.form.getRawValue()).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: () => {
        this.error.set('Invalid email, username, or password. Please try again.');
        this.submitting.set(false);
      },
      complete: () => this.submitting.set(false),
    });
  }
}
