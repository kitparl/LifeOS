import { Component, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { localIsoDate } from '../../core/utils/date';
import { DateInputComponent } from './date-input.component';
import { DateInputMode } from './date-input.utils';

@Component({
  standalone: true,
  imports: [DateInputComponent, ReactiveFormsModule, FormsModule],
  template: `
    <app-date-input [formControl]="control" [mode]="mode()" [min]="min()" testId="reactive" />
    <app-date-input [value]="plain()" (valueChange)="plain.set($event)" testId="plain" />
  `,
})
class HostComponent {
  readonly control = new FormControl<string | null>('2026-11-13');
  readonly mode = signal<DateInputMode>('date');
  readonly min = signal('');
  readonly plain = signal('');
}

describe('DateInputComponent', () => {
  let fixture: ComponentFixture<HostComponent>;
  let host: HostComponent;

  function field(testId: string): HTMLInputElement {
    return (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(`[data-testid="${testId}"]`)!;
  }

  function type(testId: string, text: string): void {
    const input = field(testId);
    input.focus();
    input.value = text;
    input.dispatchEvent(new FocusEvent('blur')); // flatpickr reads typed text when the field is left
    fixture.detectChanges();
  }

  function key(testId: string, name: string): void {
    field(testId).dispatchEvent(new KeyboardEvent('keydown', { key: name, bubbles: true, cancelable: true }));
    fixture.detectChanges();
  }

  beforeEach(() => {
    fixture = TestBed.createComponent(HostComponent);
    host = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => document.querySelectorAll('.flatpickr-calendar').forEach((el) => el.remove()));

  it('shows the form value readably and writes typed plain English back in the stored format', () => {
    expect(field('reactive').value).toBe('Fri, 13 Nov 2026');
    type('reactive', '25 dec 2026');
    expect(host.control.value).toBe('2026-12-25');
    expect(field('reactive').value).toBe('Fri, 25 Dec 2026');
  });

  it('keeps the old value when the text cannot be read', () => {
    type('reactive', 'not a date');
    expect(host.control.value).toBe('2026-11-13');
    expect(field('reactive').value).toBe('Fri, 13 Nov 2026');
  });

  it('nudges with + / - and PageUp, and clears to an empty string', () => {
    key('reactive', '+');
    expect(host.control.value).toBe('2026-11-14');
    key('reactive', '-');
    key('reactive', '-');
    expect(host.control.value).toBe('2026-11-12');
    key('reactive', 'PageUp');
    expect(host.control.value).toBe('2026-12-12');
    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.date-input__clear')!.click();
    fixture.detectChanges();
    expect(host.control.value).toBe('');
  });

  it('respects min and follows the form control being disabled', () => {
    host.min.set('2026-11-13');
    fixture.detectChanges();
    key('reactive', '-');
    expect(host.control.value).toBe('2026-11-13');
    host.control.disable();
    fixture.detectChanges();
    expect(field('reactive').disabled).toBeTrue();
  });

  it('keeps showing (and never clears) a saved value that is outside min', () => {
    host.min.set('2026-12-01');
    fixture.detectChanges();
    expect(field('reactive').value).toBe('Fri, 13 Nov 2026');
    type('reactive', field('reactive').value);
    expect(host.control.value).toBe('2026-11-13');
    type('reactive', '20 nov 2026'); // still before min: rejected, old value kept
    expect(host.control.value).toBe('2026-11-13');
    type('reactive', '5 dec 2026');
    expect(host.control.value).toBe('2026-12-05');
  });

  it('offers Today in the calendar footer, and works without forms', () => {
    const footers = Array.from(document.querySelectorAll('.date-input__footer'));
    const today = footers[footers.length - 1].querySelector<HTMLButtonElement>('.date-input__pick')!;
    expect(today.textContent).toBe('Today');
    today.click();
    fixture.detectChanges();
    expect(host.plain()).toBe(localIsoDate());
  });

  it('switches mode, e.g. to a time field', () => {
    host.control.setValue('08:30');
    host.mode.set('time');
    fixture.detectChanges();
    expect(field('reactive').value).toBe('8:30 am');
    type('reactive', '6pm');
    expect(host.control.value).toBe('18:00');
  });
});
