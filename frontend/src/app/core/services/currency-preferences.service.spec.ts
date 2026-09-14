import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { CurrencyPreferencesService } from './currency-preferences.service';

describe('CurrencyPreferencesService', () => {
  let service: CurrencyPreferencesService;

  beforeEach(() => {
    localStorage.removeItem('lifeos-currency-prefs');
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CurrencyPreferencesService);
  });

  it('defaults to INR', () => {
    expect(service.code()).toBe('INR');
    expect(service.symbol()).toBe('₹');
  });

  it('formats INR with Indian digit grouping', () => {
    // 1,00,000 rather than 100,000 — grouping follows the currency's locale.
    const formatted = service.format(100000);
    expect(formatted).toContain('1,00,000');
    expect(formatted).toContain('₹');
  });

  it('formats a non-INR currency with its own grouping', () => {
    service.setCurrency('USD');
    const formatted = service.format(100000);
    expect(service.code()).toBe('USD');
    expect(formatted).toContain('100,000');
    expect(formatted).not.toContain('1,00,000');
  });

  it('falls back to the default for an unknown currency code', () => {
    service.setCurrency('NOPE');
    expect(service.code()).toBe('INR');
  });

  it('keeps decimals only when the amount has them', () => {
    expect(service.format(850)).not.toContain('.');
    expect(service.format(850.5)).toContain('.5');
  });

  it('treats null and undefined as zero rather than throwing', () => {
    expect(service.format(null)).toContain('0');
    expect(service.format(undefined)).toContain('0');
  });
});
