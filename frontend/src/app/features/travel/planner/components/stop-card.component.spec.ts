import { TestBed } from '@angular/core/testing';
import { PlanStop } from '../../models/share.models';
import { newStop } from '../plan-ops';
import { PlannerStopCardComponent } from './stop-card.component';

describe('PlannerStopCardComponent', () => {
  function render(editable: boolean, first = false, extra: Partial<PlanStop> = {}) {
    TestBed.configureTestingModule({ imports: [PlannerStopCardComponent] });
    const fixture = TestBed.createComponent(PlannerStopCardComponent);
    fixture.componentRef.setInput('stop', newStop({ title: 'Hampta Pass', start_time: '09:30:00', place: { name: 'Hampta', lat: 32.2, lng: 77.3 }, ...extra }));
    fixture.componentRef.setInput('index', 1);
    fixture.componentRef.setInput('color', 'var(--tp-day-1)');
    fixture.componentRef.setInput('editable', editable);
    fixture.componentRef.setInput('first', first);
    fixture.detectChanges();
    return fixture;
  }

  it('moves with labelled up / down buttons and arrow keys on the handle', () => {
    const fixture = render(true);
    const moves: number[] = [];
    fixture.componentInstance.nudge.subscribe((d) => moves.push(d));
    const el = fixture.nativeElement as HTMLElement;
    const up = el.querySelector<HTMLButtonElement>('[data-testid="stop-up"]')!;
    expect(up.getAttribute('aria-label')).toBe('Move Hampta Pass up');
    up.click();
    el.querySelector<HTMLButtonElement>('[data-testid="stop-down"]')!.click();
    el.querySelector<HTMLButtonElement>('.handle')!.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    expect(moves).toEqual([-1, 1, 1]);
    expect(el.textContent).toContain('09:30');
    expect(el.querySelector<HTMLAnchorElement>('a.maps')!.href).toContain('google.com/maps');
  });

  it('cannot move above the very first stop', () => {
    const el = render(true, true).nativeElement as HTMLElement;
    expect(el.querySelector<HTMLButtonElement>('[data-testid="stop-up"]')!.disabled).toBeTrue();
  });

  it('shows no move controls when the plan is read-only', () => {
    const el = render(false).nativeElement as HTMLElement;
    expect(el.querySelector('[data-testid="stop-up"]')).toBeNull();
  });

  it('shows every detail a friend filled in: time range, getting there, stay, notes and links', () => {
    const el = render(false, false, {
      end_time: '17:00:00',
      transport: 'Shared taxi',
      stay: 'Camp Chika',
      notes: 'Carry water',
      links: ['https://www.himachaltourism.gov.in/hampta'],
    }).nativeElement as HTMLElement;
    expect(el.querySelector('[data-testid="stop-time"]')!.textContent).toContain('09:30 – 17:00');
    expect(el.textContent).toContain('Getting there: Shared taxi');
    expect(el.textContent).toContain('Stay: Camp Chika');
    expect(el.textContent).toContain('Carry water');
    const link = el.querySelector<HTMLAnchorElement>('[data-testid="stop-link"]')!;
    expect(link.textContent).toContain('himachaltourism.gov.in');
    expect(link.rel).toBe('noopener noreferrer');
  });
});
