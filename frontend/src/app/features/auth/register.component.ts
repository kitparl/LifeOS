import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="mx-auto mt-16 max-w-md">
      <div class="title-bar">Create your LifeOS account</div>
      <div class="panel">
        <form [formGroup]="form" (ngSubmit)="onSubmit()" class="flex flex-col gap-3">
          <label class="text-sm font-medium">
            Display name
            <input class="input-field mt-1" type="text" formControlName="display_name" autocomplete="name" />
          </label>
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
              autocomplete="new-password"
            />
          </label>
          @if (error()) {
            <p class="text-sm text-red-700">{{ error() }}</p>
          }
          <button class="btn-primary" type="submit" [disabled]="form.invalid || submitting()">
            Register
          </button>
        </form>
        <p class="mt-4 text-center text-sm">
          Already have an account?
          <a routerLink="/login" class="text-[var(--xp-blue)] underline">Log in</a>
        </p>
      </div>
    </div>
  `,
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    display_name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  onSubmit(): void {
    if (this.form.invalid) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.auth.register(this.form.getRawValue()).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: () => {
        this.error.set('Registration failed. Email may already be in use.');
        this.submitting.set(false);
      },
      complete: () => this.submitting.set(false),
    });
  }
}
