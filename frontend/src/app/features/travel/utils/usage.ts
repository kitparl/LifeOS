import { SkuUsage, UsageLevel } from '../models/travel.models';

/** USD estimate in `code`, using the rates stored with the pricing configuration; null when unknown. */
export function fromUsd(usd: number, code: string, fxRates: Record<string, number>): number | null {
  if (code === 'USD') return usd;
  const rate = fxRates[code];
  return rate && rate > 0 ? usd * rate : null;
}

const ALERT_LEVELS: readonly UsageLevel[] = ['warning', 'high', 'critical', 'limit'];

/** Spec §28 alert lines, e.g. "Place search: 89% of configured monthly allowance used." */
export function thresholdAlerts(skus: readonly SkuUsage[]): string[] {
  return skus
    .filter((s) => s.free_units > 0 && ALERT_LEVELS.includes(s.level))
    .sort((a, b) => b.pct_of_free - a.pct_of_free)
    .map((s) => `${s.label}: ${Math.round(s.pct_of_free)}% of configured monthly allowance used.`);
}
