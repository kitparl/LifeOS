import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HomePreferencesService } from '../../core/services/home-preferences.service';

@Component({
  selector: 'app-settings-home-section',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="space-y-3">
      <p class="text-sm text-[var(--text-muted)]">
        Choose which module opens when you visit the home URL.
      </p>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar">Default home</div>
        <div class="p-3">
          <label class="mb-1 block text-sm" for="default-home-module">Module</label>
          <select
            id="default-home-module"
            class="input-field"
            [ngModel]="homePrefs.moduleId()"
            (ngModelChange)="homePrefs.setModuleId($event)"
          >
            @for (group of homePrefs.groupedOptions; track group.category) {
              <optgroup [label]="group.category">
                @for (item of group.items; track item.id) {
                  <option [value]="item.id">{{ item.label }}</option>
                }
              </optgroup>
            }
          </select>
        </div>
      </div>
    </div>
  `,
})
export class SettingsHomeSectionComponent {
  readonly homePrefs = inject(HomePreferencesService);
}
