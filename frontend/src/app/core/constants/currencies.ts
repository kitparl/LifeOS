/**
 * Currencies selectable in Settings. `locale` drives digit grouping, so INR
 * renders as ₹1,00,000 (Indian grouping) while USD renders as $100,000.
 */
export interface CurrencyOption {
  code: string;
  symbol: string;
  locale: string;
  label: string;
}

export const CURRENCIES: CurrencyOption[] = [
  { code: 'INR', symbol: '₹', locale: 'en-IN', label: 'Indian Rupee' },
  { code: 'USD', symbol: '$', locale: 'en-US', label: 'US Dollar' },
  { code: 'EUR', symbol: '€', locale: 'de-DE', label: 'Euro' },
  { code: 'GBP', symbol: '£', locale: 'en-GB', label: 'British Pound' },
  { code: 'AED', symbol: 'د.إ', locale: 'en-AE', label: 'UAE Dirham' },
  { code: 'SGD', symbol: 'S$', locale: 'en-SG', label: 'Singapore Dollar' },
  { code: 'AUD', symbol: 'A$', locale: 'en-AU', label: 'Australian Dollar' },
  { code: 'CAD', symbol: 'C$', locale: 'en-CA', label: 'Canadian Dollar' },
  { code: 'JPY', symbol: '¥', locale: 'ja-JP', label: 'Japanese Yen' },
];

export const DEFAULT_CURRENCY: CurrencyOption = CURRENCIES[0];

export function findCurrency(code: string | undefined | null): CurrencyOption {
  return CURRENCIES.find((c) => c.code === code) ?? DEFAULT_CURRENCY;
}
