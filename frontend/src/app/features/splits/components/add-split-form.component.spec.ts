import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SplitMember } from '../models/split.models';
import { member } from '../testing/split-fixtures';
import { AddSplitSubmit, SplitAddFormComponent } from './add-split-form.component';

describe('SplitAddFormComponent', () => {
  let fixture: ComponentFixture<SplitAddFormComponent>;
  let component: SplitAddFormComponent;

  function render(members: SplitMember[], me = 'm-a'): HTMLElement {
    fixture = TestBed.createComponent(SplitAddFormComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('members', members);
    fixture.componentRef.setInput('myMemberId', me);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  function type(root: HTMLElement, testId: string, value: string): void {
    const input = root.querySelector<HTMLInputElement>(`[data-testid="${testId}"]`)!;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  }

  function saveButton(root: HTMLElement): HTMLButtonElement {
    return root.querySelector<HTMLButtonElement>('[data-testid="split-add-save"]')!;
  }

  const three = [member('m-a', 'Asha', 0), member('m-b', 'Bala', 1), member('m-c', 'Chen', 2)];

  it('defaults to me paying and everyone included, and shows live shares that sum to the amount', () => {
    const root = render(three);
    expect(component.paidBy()).toBe('m-a');
    expect([...component.included()]).toEqual(['m-a', 'm-b', 'm-c']);
    expect(saveButton(root).disabled).toBeTrue();

    type(root, 'split-amount', '100');
    type(root, 'split-title', 'Dinner');
    const shares = Array.from(root.querySelectorAll('[data-testid="split-live-share"]')).map((e) => e.textContent!.trim());
    expect(shares).toEqual(['₹33.34', '₹33.33', '₹33.33']);
    expect(saveButton(root).disabled).toBeFalse();
  });

  it('recomputes shares for however many are selected and lets the payer be left off (paying for others)', () => {
    const root = render(three);
    type(root, 'split-amount', '90');
    type(root, 'split-title', 'Cab');
    component.toggle('m-c');
    fixture.detectChanges();
    expect([...component.shares().values()]).toEqual([4500, 4500]);
    component.toggle('m-a');
    fixture.detectChanges();
    expect([...component.shares()]).toEqual([['m-b', 9000]]);
    expect(saveButton(root).disabled).toBeFalse();
    component.toggle('m-b');
    fixture.detectChanges();
    expect(saveButton(root).disabled).toBeTrue();
    expect(root.textContent).toContain('Pick at least one person to split with.');
  });

  it('splits unequally: prefilled from the equal split, and saves only when the amounts add up', () => {
    let emitted: AddSplitSubmit | undefined;
    const root = render(three);
    component.save.subscribe((value) => (emitted = value));
    type(root, 'split-amount', '100');
    type(root, 'split-title', 'Groceries');
    (root.querySelector('[data-testid="split-mode-exact"]') as HTMLButtonElement).click();
    fixture.detectChanges();

    const inputs = () => Array.from(root.querySelectorAll<HTMLInputElement>('[data-testid="split-exact-input"]'));
    expect(inputs().map((i) => i.value)).toEqual(['33.34', '33.33', '33.33']);

    const setAt = (index: number, value: string) => {
      inputs()[index].value = value;
      inputs()[index].dispatchEvent(new Event('input'));
      fixture.detectChanges();
    };
    setAt(0, '50');
    expect(root.querySelector('[data-testid="split-remaining"]')!.textContent).toContain('₹16.66 over');
    expect(saveButton(root).disabled).toBeTrue();
    setAt(1, '25');
    setAt(2, '');
    expect(root.querySelector('[data-testid="split-remaining"]')!.textContent).toContain('₹25 left');
    setAt(2, 'abc');
    expect(root.textContent).toContain('Enter amounts like 120 or 120.50.');
    setAt(2, '25');
    expect(root.querySelector('[data-testid="split-remaining"]')!.textContent).toContain('All assigned');

    saveButton(root).click();
    expect(emitted?.expense).toEqual({
      title: 'Groceries',
      amount_rupees: 100,
      paid_by: 'm-a',
      shares: [
        { member_id: 'm-a', amount_rupees: 50 },
        { member_id: 'm-b', amount_rupees: 25 },
        { member_id: 'm-c', amount_rupees: 25 },
      ],
    });
  });

  it('asks for my UPI id only when I paid and my seat has none, and emits it with the bill', () => {
    let emitted: AddSplitSubmit | undefined;
    const root = render([member('m-a', 'Asha', 0), member('m-b', 'Bala', 1, 'bala@okbank')]);
    component.save.subscribe((value) => (emitted = value));
    expect(root.querySelector('[data-testid="split-upi-input"]')).not.toBeNull();

    type(root, 'split-amount', '10.50');
    type(root, 'split-title', 'Tea');
    type(root, 'split-upi-input', 'not-a-vpa');
    expect(saveButton(root).disabled).toBeTrue();
    type(root, 'split-upi-input', 'asha@okbank');
    saveButton(root).click();
    expect(emitted).toEqual({
      expense: { title: 'Tea', amount_rupees: 10.5, paid_by: 'm-a', member_ids: ['m-a', 'm-b'] },
      upiVpa: 'asha@okbank',
    });

    component.setPayer('m-b');
    fixture.detectChanges();
    expect(root.querySelector('[data-testid="split-upi-input"]')).toBeNull();
  });
});
