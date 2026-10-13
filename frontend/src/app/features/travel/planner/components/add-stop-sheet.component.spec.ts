import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StopFields } from '../plan-ops';
import { PlannerStore } from '../planner-store';
import { PlannerAddStopComponent } from './add-stop-sheet.component';

describe('PlannerAddStopComponent (quick add)', () => {
  let fixture: ComponentFixture<PlannerAddStopComponent>;
  let saved: StopFields[];
  const q = <T extends HTMLElement>(sel: string) => document.querySelector<T>(sel)!;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [PlannerAddStopComponent],
      providers: [PlannerStore, provideHttpClient(), provideHttpClientTesting()],
    });
    fixture = TestBed.createComponent(PlannerAddStopComponent);
    fixture.componentRef.setInput('open', true);
    fixture.componentRef.setInput('dayLabel', 'Day 2 · Sat 13 Jun');
    saved = [];
    fixture.componentInstance.saved.subscribe((s) => saved.push(s));
    fixture.detectChanges();
  });

  afterEach(() => fixture.destroy());

  it('shows What, Where and the time up front; the rest opens from a clear More details button', () => {
    const visible = Array.from(document.querySelectorAll<HTMLInputElement>('form input')).map((i) => i.id || i.dataset['testid']);
    expect(visible).toEqual(['tp-what', 'tp-where', 'stop-start', 'stop-end']);
    const more = q<HTMLButtonElement>('[data-testid="more-details"]');
    expect(more.getAttribute('aria-expanded')).toBe('false');
    expect(more.textContent).toContain('How you get there, where you sleep, notes, links');
    more.click();
    fixture.detectChanges();
    expect(more.getAttribute('aria-expanded')).toBe('true');
    expect(q('[data-testid="stop-transport"]')).toBeTruthy();
    expect(q('[data-testid="stop-links"]')).toBeTruthy();
  });

  it('changing a stop shows every field it has, including the end time', () => {
    fixture.componentRef.setInput('open', false);
    fixture.detectChanges();
    fixture.componentRef.setInput('stop', {
      id: 's1', title: 'Hampta', kind: 'travel', place: null, start_time: '09:30:00', end_time: '17:00:00',
      transport: 'Taxi', stay: 'Camp', notes: 'Carry water', links: ['https://example.com/a'],
    });
    fixture.componentRef.setInput('open', true);
    fixture.detectChanges();
    expect(q<HTMLInputElement>('[data-testid="stop-end"]').value).toBe('17:00');
    expect(q<HTMLInputElement>('[data-testid="stop-transport"]').value).toBe('Taxi');
    expect(q<HTMLTextAreaElement>('[data-testid="stop-notes"]').value).toBe('Carry water');
    const end = q<HTMLInputElement>('[data-testid="stop-end"]');
    end.value = '18:15';
    end.dispatchEvent(new Event('input'));
    q<HTMLButtonElement>('[data-testid="stop-done"]').click();
    expect(saved[0]).toEqual(jasmine.objectContaining({ start_time: '09:30', end_time: '18:15', transport: 'Taxi', stay: 'Camp' }));
  });

  it('a chip picks the kind and fills an empty "What"', () => {
    const food = Array.from(document.querySelectorAll<HTMLButtonElement>('.chips button')).find((b) => b.textContent!.includes('Food'))!;
    food.click();
    fixture.detectChanges();
    expect(food.getAttribute('aria-pressed')).toBe('true');
    expect(q<HTMLInputElement>('[data-testid="stop-what"]').value).toBe('Eat');
    q<HTMLButtonElement>('[data-testid="stop-done"]').click();
    expect(saved[0]).toEqual(jasmine.objectContaining({ title: 'Eat', kind: 'food', place: null, links: [] }));
  });

  it('tapping the selected chip again unselects it and clears only the words it filled in', () => {
    const chip = (label: string) => Array.from(document.querySelectorAll<HTMLButtonElement>('.chips button')).find((b) => b.textContent!.includes(label))!;
    const what = q<HTMLInputElement>('[data-testid="stop-what"]');
    chip('Stay').click();
    fixture.detectChanges();
    chip('Food').click(); // switching replaces the suggestion
    fixture.detectChanges();
    expect(what.value).toBe('Eat');
    chip('Food').click();
    fixture.detectChanges();
    expect(chip('Food').getAttribute('aria-pressed')).toBe('false');
    expect(what.value).toBe('');
    expect(fixture.componentInstance.kind()).toBe('other');

    what.value = 'Dinner at Johnson Cafe';
    what.dispatchEvent(new Event('input'));
    chip('Food').click();
    chip('Food').click();
    fixture.detectChanges();
    expect(what.value).toBe('Dinner at Johnson Cafe'); // the friend's own words stay
  });

  it('asks for "What" instead of saving an empty stop', () => {
    q<HTMLButtonElement>('[data-testid="stop-done"]').click();
    fixture.detectChanges();
    expect(saved).toEqual([]);
    expect(document.body.textContent).toContain('Write what this stop is.');
  });

  it('keeps a pasted link it cannot read, so nothing is lost', async () => {
    const where = q<HTMLInputElement>('[data-testid="stop-where"]');
    where.value = 'https://example.com/some-blog-post';
    where.dispatchEvent(new Event('input'));
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.componentInstance.links()).toContain('https://example.com/some-blog-post');
    expect(document.body.textContent).toContain("We couldn't read that link");
  });
});
