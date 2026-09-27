import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CURRENCIES } from '../../../core/constants/currencies';
import { CurrencyPreferencesService } from '../../../core/services/currency-preferences.service';
import { apiErrorMessage } from '../../../core/utils/http';
import { MapsSettings, PricingRow, USAGE_LEVEL_LABELS, UsageLevel, UsageSummary } from '../models/travel.models';
import { UsageApiService } from '../services/usage-api.service';
import { fromUsd, thresholdAlerts } from '../utils/usage';

interface SettingsForm {
  protection_enabled: boolean;
  budget_amount: number;
  warning_amount: number;
  budget_currency: string;
  stop_at_free_tier: boolean;
  rate: number | null;
}

/**
 * Travel Settings → Google Maps Usage (spec §27–§30). An application monitoring estimate built from
 * the usage recorded for every Google request; Google Cloud billing stays authoritative.
 */
@Component({
  selector: 'app-travel-maps-usage-page',
  standalone: true,
  imports: [FormsModule, RouterLink, DatePipe, DecimalPipe],
  template: `
    <div class="space-y-3 text-sm">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h2 class="text-base font-semibold">Google Maps Usage</h2>
        <input class="input-field !w-auto text-xs" type="month" aria-label="Month" [ngModel]="month()" (ngModelChange)="setMonth($event)" />
      </div>
      <p class="text-xs rounded p-2" style="background: var(--info-soft)">
        Application monitoring estimate. Google Cloud billing is the authoritative source for actual charges.
        Estimates are shown in {{ displayCode() }} (your currency in Settings).
      </p>

      @if (summary(); as s) {
        @for (alert of alerts(); track alert) {
          <p class="text-xs rounded p-2" style="background: var(--warning-soft)">⚠️ Google Maps usage is high. {{ alert }}</p>
        }
        @if (s.budget.non_essential_blocked) {
          <p class="text-xs rounded p-2" style="background: var(--danger-soft)">
            Maps cost protection activated. New non-essential Google Maps requests are temporarily restricted. Your saved travel data remains available.
          </p>
        }

        <div class="panel space-y-1">
          <p class="font-medium">Current month · {{ s.month }}</p>
          <p>
            Spent (estimate): <strong>{{ spentLabel() }}</strong> of {{ s.budget.budget_amount | number: '1.0-2' }} {{ s.budget.currency }}
            @if (s.budget.pct_of_budget !== null) { ({{ s.budget.pct_of_budget }}%) }
            · <span [style.color]="levelColor(s.budget.level)">{{ levelLabels[s.budget.level] }}</span>
          </p>
          <p class="text-xs" style="color: var(--text-muted)">Cost protection is {{ s.budget.protection_enabled ? 'ON' : 'OFF' }}.</p>
        </div>

        <div class="panel overflow-x-auto p-0">
          <table class="w-full text-left text-xs">
            <thead>
              <tr>
                <th class="p-2">API</th>
                <th class="p-2 text-right">Requests</th>
                <th class="p-2 text-right">Free allowance</th>
                <th class="p-2 text-right">% used</th>
                <th class="p-2">Status</th>
                <th class="p-2 text-right">Estimated exposure</th>
                <th class="p-2 text-right">Blocked</th>
              </tr>
            </thead>
            <tbody>
              @for (row of s.skus; track row.sku) {
                <tr style="border-top: 1px solid var(--border)">
                  <td class="p-2">{{ row.label }}</td>
                  <td class="p-2 text-right">{{ row.requests | number }}</td>
                  <td class="p-2 text-right">{{ row.free_units | number }}</td>
                  <td class="p-2 text-right">{{ row.pct_of_free | number: '1.0-1' }}%</td>
                  <td class="p-2" [style.color]="levelColor(row.level)">{{ levelLabels[row.level] }}</td>
                  <td class="p-2 text-right">{{ money(row.estimated_cost_usd) }}</td>
                  <td class="p-2 text-right">{{ row.blocked }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        <form class="panel space-y-2" (submit)="$event.preventDefault(); saveSettings()">
          <p class="font-medium">Maps cost protection</p>
          <label class="flex items-center gap-2 text-xs">
            <input type="checkbox" name="enabled" [(ngModel)]="form.protection_enabled" /> Protection on
          </label>
          <div class="flex flex-wrap items-end gap-2">
            <label class="text-xs">Currency
              <select class="input-field !w-auto" name="currency" [(ngModel)]="form.budget_currency" (ngModelChange)="currencyChanged($event)">
                @for (c of currencies; track c.code) {
                  <option [value]="c.code">{{ c.code }}</option>
                }
              </select>
            </label>
            <label class="text-xs">Monthly safety budget (stop non-essential)
              <input class="input-field !w-32" type="number" min="0" step="0.01" name="budget" [(ngModel)]="form.budget_amount" />
            </label>
            <label class="text-xs">Warning at
              <input class="input-field !w-32" type="number" min="0" step="0.01" name="warning" [(ngModel)]="form.warning_amount" />
            </label>
            @if (form.budget_currency !== 'USD') {
              <label class="text-xs">1 USD = ? {{ form.budget_currency }}
                <input class="input-field !w-28" type="number" min="0.0001" step="0.0001" name="rate" [(ngModel)]="form.rate" />
              </label>
            }
          </div>
          <label class="flex items-center gap-2 text-xs">
            <input type="checkbox" name="freeTier" [(ngModel)]="form.stop_at_free_tier" /> Also stop each API when its free allowance is used up
          </label>
          <p class="text-xs" style="color: var(--text-muted)">
            At the budget, search, routes and elevation pause; tapping the map keeps naming places only while that stays free.
            Saved places, trips, photos, journals, GPX and "Open in Google Maps" always work.
          </p>
          <button type="submit" class="btn-primary text-xs" [disabled]="busy()">Save protection settings</button>
        </form>

        <div class="panel space-y-2">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <p class="font-medium">Rates and free allowances</p>
            <p class="text-xs" style="color: var(--text-muted)">
              Last reviewed: {{ s.pricing_last_reviewed_at ? (s.pricing_last_reviewed_at | date: 'mediumDate') : 'never' }}
            </p>
          </div>
          @if (s.pricing_review_due) {
            <p class="text-xs rounded p-2" style="background: var(--warning-soft)">
              Review these against Google's pricing page (mapsplatform.google.com/pricing) — prices change, and a stale rate makes the estimates wrong.
            </p>
          }
          <table class="w-full text-left text-xs">
            <thead>
              <tr>
                <th class="p-1">API</th>
                <th class="p-1">USD per 1,000</th>
                <th class="p-1">Free per month</th>
                <th class="p-1">Counted</th>
              </tr>
            </thead>
            <tbody>
              @for (p of pricing(); track p.sku) {
                <tr>
                  <td class="p-1">{{ p.label }}</td>
                  <td class="p-1"><input class="input-field !w-24 text-xs" type="number" min="0" step="0.01" [name]="'price-' + p.sku" [(ngModel)]="p.unit_price_usd_per_1000" /></td>
                  <td class="p-1"><input class="input-field !w-28 text-xs" type="number" min="0" step="1" [name]="'free-' + p.sku" [(ngModel)]="p.free_monthly_units" /></td>
                  <td class="p-1"><input type="checkbox" [name]="'active-' + p.sku" [(ngModel)]="p.active" [attr.aria-label]="'Count ' + p.label" /></td>
                </tr>
              }
            </tbody>
          </table>
          <button type="button" class="btn-primary text-xs" [disabled]="busy()" (click)="savePricing()">Save rates (marks them reviewed)</button>
        </div>

        <details class="panel text-xs">
          <summary class="cursor-pointer font-medium">Google Cloud protection (required)</summary>
          <ul class="mt-2 list-disc space-y-1 pl-4" style="color: var(--text-muted)">
            <li>Billing budget with email alerts on the Google Cloud project.</li>
            <li>Per-API daily quotas for Geocoding, Places (New), Routes and Elevation.</li>
            <li>API key restricted to those four APIs, and to your server's IP address.</li>
            <li>This screen is an extra safety layer, not a replacement for Google Cloud billing controls.</li>
            <li>Manage the key in <a routerLink="/integrations" fragment="google-maps" class="underline">Integrations → Google Maps</a>.</li>
          </ul>
        </details>
      } @else {
        <p style="color: var(--text-muted)">Loading…</p>
      }
      @if (message(); as m) {
        <p class="text-xs" [style.color]="m.ok ? 'var(--success)' : 'var(--danger)'">{{ m.text }}</p>
      }
    </div>
  `,
})
export class MapsUsagePageComponent implements OnInit {
  private readonly api = inject(UsageApiService);
  private readonly currency = inject(CurrencyPreferencesService);

  readonly currencies = CURRENCIES;
  readonly levelLabels = USAGE_LEVEL_LABELS;
  readonly month = signal(new Date().toISOString().slice(0, 7));
  readonly summary = signal<UsageSummary | null>(null);
  readonly pricing = signal<PricingRow[]>([]);
  readonly busy = signal(false);
  readonly message = signal<{ ok: boolean; text: string } | null>(null);
  readonly displayCode = computed(() => {
    const s = this.summary();
    const code = this.currency.code();
    return s && fromUsd(1, code, s.fx_rates) === null ? 'USD' : code;
  });
  readonly alerts = computed(() => thresholdAlerts(this.summary()?.skus ?? []));
  readonly spentLabel = computed(() => {
    const b = this.summary()?.budget;
    if (!b) return '';
    return b.spent_in_budget_currency !== null ? `${Number(b.spent_in_budget_currency).toFixed(2)} ${b.currency}` : `$${Number(b.spent_usd).toFixed(2)}`;
  });
  form: SettingsForm = { protection_enabled: true, budget_amount: 500, warning_amount: 350, budget_currency: 'INR', stop_at_free_tier: false, rate: 83 };
  private fxRates: Record<string, number> = {};

  ngOnInit(): void {
    this.load();
    this.api.settings().subscribe({ next: (s) => this.applySettings(s) });
    this.api.pricing().subscribe({ next: (rows) => this.pricing.set(rows) });
  }

  setMonth(month: string): void {
    if (!month) return;
    this.month.set(month);
    this.load();
  }

  money(usd: string): string {
    const s = this.summary();
    const value = s ? fromUsd(Number(usd), this.displayCode(), s.fx_rates) : null;
    if (value === null || this.displayCode() === 'USD') return `$${Number(usd).toFixed(2)}`;
    return this.currency.format(value);
  }

  levelColor(level: UsageLevel): string {
    return { ok: 'var(--success)', info: 'var(--info)', warning: 'var(--warning)', high: 'var(--warning)', critical: 'var(--danger)', limit: 'var(--danger)' }[level];
  }

  currencyChanged(code: string): void {
    this.form.rate = code === 'USD' ? null : (this.fxRates[code] ?? null);
  }

  saveSettings(): void {
    const f = this.form;
    const fx = { ...this.fxRates };
    if (f.budget_currency !== 'USD' && f.rate) fx[f.budget_currency] = Number(f.rate);
    this.busy.set(true);
    this.api
      .saveSettings({
        protection_enabled: f.protection_enabled,
        budget_amount: String(f.budget_amount),
        warning_amount: String(f.warning_amount),
        budget_currency: f.budget_currency,
        stop_at_free_tier: f.stop_at_free_tier,
        fx_rates: fx,
      })
      .subscribe({
        next: (s) => {
          this.applySettings(s);
          this.done('Protection settings saved');
          this.load();
        },
        error: (err) => this.fail(err),
      });
  }

  savePricing(): void {
    this.busy.set(true);
    const rows = this.pricing().map(({ sku, unit_price_usd_per_1000, free_monthly_units, active }) => ({
      sku,
      unit_price_usd_per_1000: String(unit_price_usd_per_1000),
      free_monthly_units: Number(free_monthly_units),
      active,
    }));
    this.api.savePricing(rows).subscribe({
      next: (saved) => {
        this.pricing.set(saved);
        this.done('Rates saved and marked reviewed');
        this.load();
      },
      error: (err) => this.fail(err),
    });
  }

  private load(): void {
    this.api.summary(this.month()).subscribe({ next: (s) => this.summary.set(s), error: (err) => this.fail(err) });
  }

  private applySettings(s: MapsSettings): void {
    this.fxRates = s.fx_rates;
    this.form = {
      protection_enabled: s.protection_enabled,
      budget_amount: Number(s.budget_amount),
      warning_amount: Number(s.warning_amount),
      budget_currency: s.budget_currency,
      stop_at_free_tier: s.stop_at_free_tier,
      rate: s.budget_currency === 'USD' ? null : (s.fx_rates[s.budget_currency] ?? null),
    };
  }

  private done(text: string): void {
    this.busy.set(false);
    this.message.set({ ok: true, text });
  }

  private fail(err: unknown): void {
    this.busy.set(false);
    this.message.set({ ok: false, text: apiErrorMessage(err, 'Something went wrong') });
  }
}
