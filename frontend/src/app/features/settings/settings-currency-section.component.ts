import { Component, inject } from '@angular/core';
import { CurrencyPreferencesService } from '../../core/services/currency-preferences.service';

@Component({
  selector: 'app-settings-currency-section',
  standalone: true,
  template: `
    <div class="panel max-w-2xl space-y-3">
      <div>
        <p class="form-label">Display currency</p>
        <div class="flex flex-wrap gap-2">
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
      </div>
      <p class="text-sm">
        <span style="color: var(--text-muted)">Preview:</span>
        {{ currencyPrefs.format(100000) }} · {{ currencyPrefs.format(850) }}
      </p>
      <p class="border-t border-[var(--xp-border)] pt-3 text-xs" style="color: var(--text-muted)">
        This changes how amounts are displayed, not what they are worth. Existing
        entries keep their recorded numbers — nothing is converted between currencies.
      </p>
    </div>
  `,
})
export class SettingsCurrencySectionComponent {
  readonly currencyPrefs = inject(CurrencyPreferencesService);
}
