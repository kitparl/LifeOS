import { findCurrency } from '../../../core/constants/currencies';

/**
 * Split amounts are always INR (UPI is INR-only), so they are formatted as rupees
 * regardless of the display-currency preference, which would misstate the amount.
 */
const INR = findCurrency('INR');

export function formatInr(paise: number): string {
  const rupees = paise / 100;
  return new Intl.NumberFormat(INR.locale, {
    style: 'currency',
    currency: INR.code,
    minimumFractionDigits: paise % 100 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(rupees);
}

/** Same rounding as the server: `round(rupees * 100)`. */
export function rupeesToPaise(rupees: number): number {
  return Math.round(rupees * 100);
}

const MAX_RUPEES = 10_000_000;
const RUPEES_TEXT = /^\d+(\.\d{1,2})?$/;

/** A bill amount as the server accepts it (> 0, ≤ ₹1 crore, ≤ 2 decimals), else null. */
export function parseRupees(text: string): number | null {
  const trimmed = text.trim();
  if (!RUPEES_TEXT.test(trimmed)) return null;
  const rupees = Number(trimmed);
  return rupees > 0 && rupees <= MAX_RUPEES ? rupees : null;
}
