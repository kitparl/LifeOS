import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ExportPageComponent } from '../export/export-page.component';
import { ProfileComponent } from '../profile/profile.component';
import { SettingsAppSectionComponent } from './settings-app-section.component';
import { SettingsIntegrationsSectionComponent } from './settings-integrations-section.component';
import { SettingsSidebarSectionComponent } from './settings-sidebar-section.component';
import { SettingsEditorSectionComponent } from './settings-editor-section.component';
import { SettingsCurrencySectionComponent } from './settings-currency-section.component';
import { SettingsChangePasswordComponent } from './settings-change-password.component';

@Component({
  selector: 'app-settings-hub',
  standalone: true,
  imports: [
    RouterLink,
    ProfileComponent,
    SettingsIntegrationsSectionComponent,
    ExportPageComponent,
    SettingsSidebarSectionComponent,
    SettingsEditorSectionComponent,
    SettingsCurrencySectionComponent,
    SettingsChangePasswordComponent,
    SettingsAppSectionComponent,
  ],
  template: `
    <div class="space-y-8">
      <nav class="flex flex-wrap gap-2 text-sm">
        @for (s of sections; track s.id) {
          <a class="rounded-lg border border-[var(--xp-border)] px-3 py-1.5 no-underline hover:bg-[var(--surface-3)]"
             routerLink="/settings" [fragment]="s.id">
            {{ s.label }}
          </a>
        }
      </nav>

      <section id="profile" class="scroll-mt-24 space-y-3">
        <h2 class="text-base font-semibold">Profile</h2>
        <app-profile />
      </section>

      <section id="password" class="scroll-mt-24 space-y-3">
        <h2 class="text-base font-semibold">Password</h2>
        <app-settings-change-password />
      </section>

      <section id="integrations" class="scroll-mt-24 space-y-3">
        <h2 class="text-base font-semibold">Integrations</h2>
        <p class="text-sm text-[var(--text-muted)]">
          Enable or disable delivery channels. Your notification inbox remains at
          <a routerLink="/notifications" class="link">Notifications</a>.
        </p>
        <app-settings-integrations-section />
      </section>

      <section id="export" class="scroll-mt-24 space-y-3">
        <h2 class="text-base font-semibold">Export</h2>
        <app-export-page />
      </section>

      <section id="sidebar" class="scroll-mt-24 space-y-3">
        <h2 class="text-base font-semibold">Sidebar</h2>
        <app-settings-sidebar-section />
      </section>

      <section id="editor" class="scroll-mt-24 space-y-3">
        <h2 class="text-base font-semibold">Editor</h2>
        <app-settings-editor-section />
      </section>

      <section id="currency" class="scroll-mt-24 space-y-3">
        <h2 class="text-base font-semibold">Currency</h2>
        <app-settings-currency-section />
      </section>

      <section id="app" class="scroll-mt-24 space-y-3">
        <h2 class="text-base font-semibold">App updates</h2>
        <app-settings-app-section />
      </section>
    </div>
  `,
})
export class SettingsHubComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  readonly sections = [
    { id: 'profile', label: 'Profile' },
    { id: 'password', label: 'Password' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'export', label: 'Export' },
    { id: 'sidebar', label: 'Sidebar' },
    { id: 'editor', label: 'Editor' },
    { id: 'currency', label: 'Currency' },
    { id: 'app', label: 'App updates' },
  ];

  ngOnInit(): void {
    this.route.fragment.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((fragment) => {
      if (!fragment) {
        return;
      }
      // Map legacy #notifications → #integrations
      const target = fragment === 'notifications' ? 'integrations' : fragment;
      requestAnimationFrame(() => {
        document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }
}
