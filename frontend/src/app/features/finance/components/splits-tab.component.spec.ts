import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { SplitHistoryItem } from '../../splits/models/split.models';
import { SplitsTabComponent } from './splits-tab.component';

function item(overrides: Partial<SplitHistoryItem>): SplitHistoryItem {
  return {
    code: 'k7mq2p',
    name: 'Dinner',
    url_path: '/s/k7mq2p',
    expires_at: '2026-09-28T10:00:00Z',
    ended_at: null,
    is_open: true,
    my_net_paise: 0,
    kept_at: '2026-09-27T10:00:00Z',
    ...overrides,
  };
}

describe('SplitsTabComponent (Finance → Splits)', () => {
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter([])] }));

  it('lists kept groups with links to /s/{code}, including expired ones as read-only', () => {
    const fixture = TestBed.createComponent(SplitsTabComponent);
    fixture.componentInstance.history = [
      item({ my_net_paise: 25000 }),
      item({ code: 'abcdef', name: 'Goa', url_path: '/s/abcdef', is_open: false, my_net_paise: -3333 }),
    ];
    fixture.detectChanges();
    const root = fixture.nativeElement as HTMLElement;
    const rows = Array.from(root.querySelectorAll('[data-testid="finance-split-row"]'));
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain('You get ₹250');
    expect(rows[1].textContent).toContain('Link closed · read-only');
    expect(rows[1].textContent).toContain('You owe ₹33.33');
    expect(rows.map((r) => r.querySelector('a')!.getAttribute('href'))).toEqual(['/s/k7mq2p', '/s/abcdef']);
  });

  it('explains how groups get here when the history is empty', () => {
    const fixture = TestBed.createComponent(SplitsTabComponent);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('No split groups yet.');
  });
});
