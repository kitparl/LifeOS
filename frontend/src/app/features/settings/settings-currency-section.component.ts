import { Component, inject } from '@angular/core';
import { CurrencyPreferencesService } from '../../core/services/currency-preferences.service';

@Component({
  selector: 'app-settings-currency-section',
  standalone: true,
  template: `
    <div class="space-y-3">
      <p class="text-sm text-[var(--text-muted)]">
        The currency amounts are shown in across Finance.
      </p>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar">Currency</div>
        <div class="flex flex-wrap gap-2 p-3">
          @for (option of currencyPrefs.options; track option.code) {
            <button
              type="button"
              class="text-xs"
              [class.btn-primary]="currencyPrefs.code() === option.code"
              [class.btn-secondary]="currencyPrefs.code() !== option.code"
              [title]="option.label"
              (click)="currencyPrefs.setCurrency(option.code)"
            >
              {{ option.symbol }} {{ option.code }}
            </button>
          }
        </div>
        <div class="border-t border-[var(--xp-border)] px-3 py-2 text-xs" style="color: var(--text-muted)">
          Preview: {{ currencyPrefs.format(100000) }} · {{ currencyPrefs.format(850) }}
        </div>
      </div>

      <p class="text-xs" style="color: var(--text-muted)">
        This changes how amounts are displayed, not what they are worth. Existing
        entries keep their recorded numbers — nothing is converted between currencies.
      </p>
    </div>
  `,
})
export class SettingsCurrencySectionComponent {
  readonly currencyPrefs = inject(CurrencyPreferencesService);
}
