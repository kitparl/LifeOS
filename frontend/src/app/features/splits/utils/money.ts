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
