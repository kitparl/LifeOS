import { Component, ElementRef, computed, effect, inject, viewChild } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ExportPageComponent } from '../export/export-page.component';
import { ProfileComponent } from '../profile/profile.component';
import { SettingsAppSectionComponent } from './settings-app-section.component';
import { SettingsIntegrationsSectionComponent } from './settings-integrations-section.component';
import { SettingsSidebarSectionComponent } from './settings-sidebar-section.component';
import { SettingsHomeSectionComponent } from './settings-home-section.component';
import { SettingsEditorSectionComponent } from './settings-editor-section.component';
import { SettingsCurrencySectionComponent } from './settings-currency-section.component';
import { SettingsChangePasswordComponent } from './settings-change-password.component';
import { groupSettingsSections, resolveSettingsSection } from './settings-sections';

/** Settings shell: registry-driven nav (see settings-sections.ts) + one section at a time. */
@Component({
  selector: 'app-settings-hub',
  standalone: true,
  imports: [
    RouterLink,
    ProfileComponent,
    SettingsIntegrationsSectionComponent,
    ExportPageComponent,
    SettingsSidebarSectionComponent,
    SettingsHomeSectionComponent,
    SettingsEditorSectionComponent,
    SettingsCurrencySectionComponent,
    SettingsChangePasswordComponent,
    SettingsAppSectionComponent,
  ],
  template: `
    <div class="mx-auto max-w-5xl space-y-4">
      <header>
        <h2 class="text-lg font-semibold">Settings</h2>
        <p class="text-sm text-[var(--text-muted)]">Manage your account, connections, and how LifeOS behaves.</p>
      </header>

      <!-- Mobile: sticky section picker -->
      <div class="settings-picker md:hidden">
        <label class="sr-only" for="settings-section-picker">Settings section</label>
        <select
          id="settings-section-picker"
          class="input-field"
          (change)="select($any($event.target).value)"
        >
          @for (group of groups; track group.category) {
            <optgroup [label]="group.category">
              @for (s of group.sections; track s.id) {
                <option [value]="s.id" [selected]="s.id === active().id">{{ s.label }}</option>
              }
            </optgroup>
          }
        </select>
      </div>

      <div class="md:grid md:grid-cols-[11rem_minmax(0,1fr)] md:gap-6 lg:grid-cols-[13rem_minmax(0,1fr)]">
        <!-- Desktop: sticky grouped nav -->
        <nav class="settings-nav hidden md:block" aria-label="Settings sections">
          @for (group of groups; track group.category) {
            <p class="section-heading">{{ group.category }}</p>
            <ul class="mb-3">
              @for (s of group.sections; track s.id) {
                <li>
                  <a
                    class="settings-nav__item"
                    [class.settings-nav__item--active]="s.id === active().id"
                    [attr.aria-current]="s.id === active().id ? 'page' : null"
                    routerLink="/settings"
                    [fragment]="s.id"
                  >
                    {{ s.label }}
                  </a>
                </li>
              }
            </ul>
          }
        </nav>

        <section #sectionEl [id]="active().id" class="min-w-0 max-w-3xl scroll-mt-16 space-y-4 md:scroll-mt-4">
          <div>
            <p class="text-xs text-[var(--text-muted)]">{{ active().category }}</p>
            <h3 class="text-base font-semibold">{{ active().label }}</h3>
            @if (active().description) {
              <p class="mt-0.5 text-sm text-[var(--text-muted)]">{{ active().description }}</p>
            }
          </div>

          @switch (active().id) {
            @case ('profile') { <app-profile /> }
            @case ('password') { <app-settings-change-password /> }
            @case ('integrations') { <app-settings-integrations-section /> }
            @case ('export') { <app-export-page /> }
            @case ('sidebar') { <app-settings-sidebar-section /> }
            @case ('home') { <app-settings-home-section /> }
            @case ('editor') { <app-settings-editor-section /> }
            @case ('currency') { <app-settings-currency-section /> }
            @case ('app') { <app-settings-app-section /> }
          }
        </section>
      </div>
    </div>

    <style>
      .settings-picker {
        position: sticky;
        top: 0;
        z-index: 10;
        margin: 0 -0.25rem;
        padding: 0.375rem 0.25rem;
        background: var(--page-bg);
        border-bottom: 1px solid var(--border);
      }
      .settings-nav {
        position: sticky;
        top: 0.75rem;
        align-self: start;
      }
      .settings-nav__item {
        display: block;
        padding: 0.4rem 0.625rem;
        border-radius: 4px;
        font-size: 0.8125rem;
        color: var(--text);
        text-decoration: none;
        border-left: 2px solid transparent;
      }
      .settings-nav__item:hover {
        background: var(--surface-3);
      }
      .settings-nav__item--active,
      .settings-nav__item--active:hover {
        background: var(--sidebar-active-bg);
        color: var(--sidebar-active-text);
        border-left-color: var(--primary);
        font-weight: 500;
      }
    </style>
  `,
})
export class SettingsHubComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly sectionEl = viewChild<ElementRef<HTMLElement>>('sectionEl');

  readonly groups = groupSettingsSections();

  private readonly fragment = toSignal(this.route.fragment, { initialValue: this.route.snapshot.fragment });
  readonly active = computed(() => resolveSettingsSection(this.fragment()));

  constructor() {
    // When switching sections after scrolling down, bring the new section's heading back into view.
    effect(() => {
      this.active();
      const el = this.sectionEl()?.nativeElement;
      if (!el) return;
      requestAnimationFrame(() => {
        if (el.getBoundingClientRect().top < 64) {
          el.scrollIntoView({ block: 'start' });
        }
      });
    });
  }

  select(id: string): void {
    void this.router.navigate(['/settings'], { fragment: id });
  }
}
