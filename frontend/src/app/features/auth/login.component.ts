import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="mx-auto mt-16 max-w-md">
      <div class="title-bar">Sign in to LifeOS</div>
      <div class="panel">
        <form [formGroup]="form" (ngSubmit)="onSubmit()" class="flex flex-col gap-3">
          <label class="text-sm font-medium">
            Email
            <input class="input-field mt-1" type="email" formControlName="email" autocomplete="email" />
          </label>
          <label class="text-sm font-medium">
            Password
            <input
              class="input-field mt-1"
              type="password"
              formControlName="password"
              autocomplete="current-password"
            />
          </label>
          @if (error()) {
            <p class="text-sm text-red-700">{{ error() }}</p>
          }
          <button class="btn-primary" type="submit" [disabled]="form.invalid || submitting()">
            Log in
          </button>
        </form>
        <p class="mt-4 text-center text-sm">
          No account?
          <a routerLink="/register" class="text-[var(--xp-blue)] underline">Register</a>
        </p>
      </div>
    </div>
  `,
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  onSubmit(): void {
    if (this.form.invalid) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.auth.login(this.form.getRawValue()).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: () => {
        this.error.set('Invalid email or password.');
        this.submitting.set(false);
      },
      complete: () => this.submitting.set(false),
    });
  }
}
