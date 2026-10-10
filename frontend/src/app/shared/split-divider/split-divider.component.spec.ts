import { Component, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { SplitDividerComponent, ratioFromPointer } from './split-divider.component';

@Component({
  standalone: true,
  imports: [SplitDividerComponent],
  template: `<app-split-divider [value]="value()" [min]="0.2" [max]="0.8" [bounds]="bounds" (valueChange)="value.set($event)" />`,
})
class HostComponent {
  readonly value = signal(0.5);
  bounds = () => ({ start: 0, end: 400 });
}

describe('SplitDividerComponent', () => {
  let fixture: ComponentFixture<HostComponent>;
  let el: HTMLElement;

  beforeEach(() => {
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
    el = fixture.debugElement.query(By.directive(SplitDividerComponent)).nativeElement;
  });

  const key = (k: string) => {
    el.dispatchEvent(new KeyboardEvent('keydown', { key: k, cancelable: true }));
    fixture.detectChanges();
  };

  it('maps pointer position to a ratio of the span', () => {
    expect(ratioFromPointer(100, { start: 0, end: 400 })).toBe(0.25);
    expect(ratioFromPointer(5, { start: 0, end: 0 })).toBeNull();
  });

  it('moves in 5% steps with arrow keys and clamps to min/max', () => {
    key('ArrowRight');
    expect(fixture.componentInstance.value()).toBeCloseTo(0.55);
    fixture.componentInstance.value.set(0.8);
    fixture.detectChanges();
    key('ArrowRight');
    expect(fixture.componentInstance.value()).toBe(0.8);
  });

  it('resets to the default on Home and double-click', () => {
    fixture.componentInstance.value.set(0.7);
    fixture.detectChanges();
    key('Home');
    expect(fixture.componentInstance.value()).toBe(0.5);
    fixture.componentInstance.value.set(0.3);
    el.dispatchEvent(new MouseEvent('dblclick'));
    expect(fixture.componentInstance.value()).toBe(0.5);
  });

  it('exposes separator semantics', () => {
    expect(el.getAttribute('role')).toBe('separator');
    expect(el.getAttribute('aria-valuenow')).toBe('50');
  });
});
