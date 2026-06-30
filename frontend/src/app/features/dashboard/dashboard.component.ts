import { Component, inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  template: `
    <div class="max-w-2xl">
      <div class="title-bar">Dashboard</div>
      <div class="panel">
        @if (auth.user(); as user) {
          <h1 class="text-lg font-semibold">Welcome, {{ user.display_name }}</h1>
          <p class="mt-2 text-sm text-gray-700">
            Your LifeOS workspace is ready. More modules will appear here as the product grows.
          </p>
        } @else {
          <p class="text-sm">Loading your profile…</p>
        }
      </div>
    </div>
  `,
})
export class DashboardComponent {
  readonly auth = inject(AuthService);
}
