import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import {
  CURRENCIES,
  CurrencyOption,
  DEFAULT_CURRENCY,
  findCurrency,
} from '../constants/currencies';
import {
  PreferencesApi,
  readJsonLocalStorage,
  writeJsonLocalStorage,
} from './preferences-sync';

export interface CurrencyPrefsValue {
  code: string;
}

const STORAGE_KEY = 'lifeos-currency-prefs';
const PREFS_KEY = 'currency';

function normalize(raw: unknown): CurrencyPrefsValue {
  if (raw && typeof raw === 'object' && 'code' in raw) {
    return { code: findCurrency((raw as CurrencyPrefsValue).code).code };
  }
  if (typeof raw === 'string') return { code: findCurrency(raw).code };
  return { code: DEFAULT_CURRENCY.code };
}

/**
 * The currency amounts are displayed in, stored as the `currency` user
 * preference. This is a *formatting* choice only — amounts are plain numbers
 * and are never converted between currencies.
 */
@Injectable({ providedIn: 'root' })
export class CurrencyPreferencesService {
  private readonly prefsApi = new PreferencesApi(inject(HttpClient));

  private readonly prefs = signal<CurrencyPrefsValue>({ code: DEFAULT_CURRENCY.code });

  readonly options = CURRENCIES;
  readonly currency = computed<CurrencyOption>(() => findCurrency(this.prefs().code));
  readonly code = computed(() => this.currency().code);
  readonly symbol = computed(() => this.currency().symbol);

  init(): void {
    this.prefs.set(this.readLocal());

    this.prefsApi.get<CurrencyPrefsValue>(PREFS_KEY).subscribe({
      next: (resp) => {
        if (resp.value) {
          const normalized = normalize(resp.value);
          this.prefs.set(normalized);
          this.cacheLocal(normalized);
        }
      },
      error: () => {
        // Offline / unauthenticated — keep the locally cached choice
      },
    });
  }

  setCurrency(code: string): void {
    const normalized = normalize({ code });
    this.prefs.set(normalized);
    this.cacheLocal(normalized);
    this.prefsApi.put(PREFS_KEY, normalized).subscribe({ error: () => undefined });
  }

  /** Format an amount in the selected currency, e.g. ₹1,00,000. */
  format(amount: number | null | undefined, options?: { compact?: boolean }): string {
    const { code, locale } = this.currency();
    const value = Number(amount ?? 0);
    try {
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: code,
        maximumFractionDigits: Number.isInteger(value) ? 0 : 2,
        notation: options?.compact ? 'compact' : 'standard',
      }).format(value);
    } catch {
      // Unknown locale/currency in an old browser — degrade to symbol + number
      return `${this.symbol()}${value.toLocaleString()}`;
    }
  }

  private cacheLocal(value: CurrencyPrefsValue): void {
    writeJsonLocalStorage(STORAGE_KEY, value);
  }

  private readLocal(): CurrencyPrefsValue {
    return normalize(readJsonLocalStorage<unknown>(STORAGE_KEY, { code: DEFAULT_CURRENCY.code }));
  }
}
