import { AfterViewInit, Component, ElementRef, NgZone, ViewChild, effect, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { HttpErrorResponse, HttpStatusCode } from '@angular/common/http';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
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
                <p>Tasks, habits, journal, calendar — all in one place.</p>
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
                <strong>Finance</strong>
                <p>Income/expense tracking and loans.</p>
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

          @if (googleState() !== 'off') {
            <div class="login-divider"><span>or</span></div>
            <div #googleSlot class="login-google">
              @if (googleState() === 'loading') {
                <div class="skeleton login-google__placeholder"></div>
              }
              <div #googleButton class="login-google__button"></div>
            </div>
          }

          <div class="login-explore">
            <a routerLink="/explore" class="btn-secondary w-full" style="min-height: 40px" data-testid="login-explore-tools-link">
              Explore free tools
            </a>
            <p class="login-explore__hint">No sign-in needed</p>
          </div>
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

      .login-divider {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 1.25rem 0;
        font-size: 0.75rem;
        color: var(--text-faint);
      }

      .login-divider::before,
      .login-divider::after {
        content: '';
        flex: 1;
        border-top: 1px solid var(--border);
      }

      .login-explore {
        margin-top: 1.25rem;
        padding-top: 1.25rem;
        border-top: 1px solid var(--border);
        text-align: center;
      }

      .login-explore__hint {
        margin: 0.375rem 0 0;
        font-size: 0.75rem;
        color: var(--text-faint);
      }

      .login-google {
        display: flex;
        justify-content: center;
        min-height: 40px;
        /* Google's button is a light-scheme iframe; matching it avoids the browser
           painting an opaque white backdrop behind it when the page is dark. */
        color-scheme: light;
        position: relative;
      }

      /* Holds the button's space while Google's iframe loads (no layout shift). */
      .login-google__placeholder {
        position: absolute;
        inset: 0;
      }

      .login-google__button {
        position: relative;
        width: 100%;
        display: flex;
        justify-content: center;
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
export class LoginComponent implements AfterViewInit {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly zone = inject(NgZone);
  private readonly theme = inject(ThemeService);
  private googleInitialized = false;

  @ViewChild('googleSlot') private googleSlot?: ElementRef<HTMLElement>;
  @ViewChild('googleButton') private googleButton?: ElementRef<HTMLElement>;

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  /** loading = placeholder shown; ready = Google's button painted; off = hidden. */
  readonly googleState = signal<'loading' | 'ready' | 'off'>('loading');

  // Start the config fetch and the Google script download together, as soon as
  // the page is created, instead of one after the other.
  private readonly googleSetup = Promise.all([
    firstValueFrom(this.auth.getGoogleClientId()),
    loadGoogleScript(),
  ]);

  constructor() {
    // Re-render Google's button so it follows light/dark theme switches.
    effect(() => {
      const mode = this.theme.resolved();
      if (this.googleInitialized) this.drawGoogleButton(mode);
    });
  }

  readonly form = this.fb.nonNullable.group({
    identifier: ['', Validators.required],
    password: ['', Validators.required],
  });

  ngAfterViewInit(): void {
    this.googleSetup
      .then(([clientId]) => {
        if (!clientId) {
          this.zone.run(() => this.googleState.set('off'));
          return;
        }
        this.renderGoogleButton(clientId);
      })
      .catch(() => {
        // Config/script failed (offline, blocked): keep password login, hide Google.
        this.zone.run(() => this.googleState.set('off'));
      });
  }

  private renderGoogleButton(clientId: string): void {
    google.accounts.id.initialize({
      client_id: clientId,
      callback: (res: { credential?: string }) =>
        this.zone.run(() => this.onGoogleCredential(res.credential)),
    });
    this.googleInitialized = true;
    this.drawGoogleButton(this.theme.resolved());
  }

  private drawGoogleButton(mode: 'light' | 'dark'): void {
    const el = this.googleButton?.nativeElement;
    if (!el) return;
    el.replaceChildren();
    const width = this.googleSlot?.nativeElement.clientWidth || 340;
    google.accounts.id.renderButton(el, {
      type: 'standard',
      theme: mode === 'dark' ? 'filled_black' : 'outline',
      size: 'large',
      text: 'continue_with',
      shape: 'rectangular',
      logo_alignment: 'left',
      // Match the form width (Google caps the button at 400px).
      width: Math.min(400, width),
    });
    // Drop the placeholder once Google's iframe has painted the button.
    const markReady = () => this.zone.run(() => this.googleState.set('ready'));
    const iframe = el.querySelector('iframe');
    if (iframe) iframe.addEventListener('load', markReady, { once: true });
    else markReady();
  }

  private onGoogleCredential(credential: string | undefined): void {
    if (!credential) {
      this.error.set('Google sign-in was cancelled or failed. Please try again.');
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.auth.googleLogin(credential).subscribe({
      next: () => this.router.navigateByUrl('/'),
      error: (err: unknown) => {
        const detail = err instanceof HttpErrorResponse && err.status === HttpStatusCode.Unauthorized ? err.error?.detail : null;
        this.error.set(
          typeof detail === 'string' ? detail : 'Something went wrong signing in with Google. Please try again.',
        );
        this.submitting.set(false);
      },
      complete: () => this.submitting.set(false),
    });
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    this.submitting.set(true);
    this.error.set(null);
    this.auth.login(this.form.getRawValue()).subscribe({
      next: () => this.router.navigateByUrl('/'),
      error: () => {
        this.error.set('Invalid email, username, or password. Please try again.');
        this.submitting.set(false);
      },
      complete: () => this.submitting.set(false),
    });
  }
}

/** Minimal typing for the Google Identity Services global we use. */
declare const google: {
  accounts: {
    id: {
      initialize(config: { client_id: string; callback: (res: { credential?: string }) => void }): void;
      renderButton(parent: HTMLElement, options: Record<string, unknown>): void;
    };
  };
};

const GOOGLE_GSI_SRC = 'https://accounts.google.com/gsi/client';
let googleScriptPromise: Promise<void> | null = null;

/** Load the Google Identity Services script once per page. */
function loadGoogleScript(): Promise<void> {
  if (!googleScriptPromise) {
    googleScriptPromise = new Promise<void>((resolve, reject) => {
      const script = document.createElement('script');
      script.src = GOOGLE_GSI_SRC;
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => {
        googleScriptPromise = null;
        reject(new Error('Failed to load Google Identity Services'));
      };
      document.head.appendChild(script);
    });
  }
  return googleScriptPromise;
}
