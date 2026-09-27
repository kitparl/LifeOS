import { SkuUsage } from '../models/travel.models';
import { fromUsd, thresholdAlerts } from './usage';

function sku(label: string, pct: number, level: SkuUsage['level'], free = 10_000): SkuUsage {
  return { sku: label, label, requests: 0, blocked: 0, free_units: free, pct_of_free: pct, estimated_cost_usd: '0', level };
}

describe('usage utils', () => {
  it('converts USD estimates with the stored rates', () => {
    expect(fromUsd(2, 'USD', {})).toBe(2);
    expect(fromUsd(2, 'INR', { INR: 83 })).toBe(166);
    expect(fromUsd(2, 'EUR', { INR: 83 })).toBeNull();
  });

  it('lists warning-or-worse SKUs, highest first (spec §28 wording)', () => {
    const alerts = thresholdAlerts([
      sku('Routes', 20, 'ok'),
      sku('Place search', 89.2, 'high'),
      sku('Geocoding', 72, 'warning'),
      sku('Elevation', 60, 'info'),
      sku('Unpriced', 500, 'limit', 0),
    ]);
    expect(alerts).toEqual([
      'Place search: 89% of configured monthly allowance used.',
      'Geocoding: 72% of configured monthly allowance used.',
    ]);
  });
});
