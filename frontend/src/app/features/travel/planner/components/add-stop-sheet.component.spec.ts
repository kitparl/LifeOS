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

  it('shows at most three fields up front; everything else waits under More details', () => {
    const visible = Array.from(document.querySelectorAll<HTMLInputElement>('form > div input')).map((i) => i.id);
    expect(visible).toEqual(['tp-what', 'tp-where', 'tp-time']);
    expect(q<HTMLDetailsElement>('details').open).toBeFalse();
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
