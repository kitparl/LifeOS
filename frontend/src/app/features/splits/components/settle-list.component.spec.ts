import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SplitDebt, SplitSettlement } from '../models/split.models';
import { member } from '../testing/split-fixtures';
import { MarkPaidRequest, SplitSettleListComponent } from './settle-list.component';

const UPI = 'upi://pay?pa=asha@okbank&pn=Asha&am=300.00&cu=INR&tn=Dinner';

function debt(overrides: Partial<SplitDebt> = {}): SplitDebt {
  return {
    payer_member_id: 'm-b',
    payer_name: 'Bala',
    payee_member_id: 'm-a',
    payee_name: 'Asha',
    outstanding_paise: 30000,
    pending_paise: 0,
    amount_paise: 30000,
    amount_rupees: '300.00',
    upi_uri: UPI,
    ...overrides,
  };
}

describe('SplitSettleListComponent', () => {
  let fixture: ComponentFixture<SplitSettleListComponent>;
  let http: HttpTestingController;

  function render(debts: SplitDebt[], me: string | null = 'm-b', settlements: SplitSettlement[] = []): HTMLElement {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(SplitSettleListComponent);
    fixture.componentRef.setInput('debts', debts);
    fixture.componentRef.setInput('members', [member('m-a', 'Asha', 0, 'asha@okbank'), member('m-b', 'Bala', 1)]);
    fixture.componentRef.setInput('settlements', settlements);
    fixture.componentRef.setInput('myMemberId', me);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => http.verify());

  it('a debt whose payee has a VPA has a Pay link and a payment QR carrying the same upi:// intent', () => {
    const root = render([debt()]);
    const pay = root.querySelector<HTMLAnchorElement>('[data-testid="split-pay"]')!;
    expect(pay.getAttribute('href')).toBe(UPI);
    expect(pay.textContent).toContain('Pay ₹300');
    const qr = root.querySelector('[data-testid="split-payment-qr"] svg')!;
    expect(qr.getAttribute('data-payload')).toBe(UPI);
    expect(qr.getAttribute('data-payload')).not.toContain('/s/');
    expect(root.querySelector('[data-testid="split-mark-paid"]')!.textContent).toContain('Mark paid');
  });

  it('a debt with no VPA has no payment QR and is cash only', () => {
    const root = render([debt({ upi_uri: null })]);
    expect(root.querySelector('[data-testid="split-payment-qr"]')).toBeNull();
    expect(root.querySelector('[data-testid="split-pay"]')).toBeNull();
    expect(root.textContent).toContain('Add a UPI id to get a pay link and QR.');
    let emitted: MarkPaidRequest | undefined;
    fixture.componentInstance.markPaid.subscribe((v) => (emitted = v));
    root.querySelector<HTMLButtonElement>('[data-testid="split-mark-paid"]')!.click();
    expect(emitted?.method).toBe('cash');
  });

  it('only the payer can mark paid; pending amounts show as awaiting the payee', () => {
    const root = render([debt({ pending_paise: 10000, amount_paise: 20000 })], 'm-a');
    expect(root.querySelector('[data-testid="split-mark-paid"]')).toBeNull();
    expect(root.textContent).toContain('₹100 marked paid, awaiting Asha');
    expect(root.querySelector('[data-testid="split-pay"]')!.textContent).toContain('Pay ₹200');
  });

  it('asks once, after returning from the UPI app, whether to mark the price as paid', () => {
    const root = render([debt()]);
    let emitted: MarkPaidRequest | undefined;
    fixture.componentInstance.markPaid.subscribe((v) => (emitted = v));
    fixture.componentInstance.onPay(debt());
    fixture.componentInstance.onVisibilityChange();
    fixture.detectChanges();
    expect(root.querySelector('[data-testid="split-paid-prompt"]')!.textContent).toContain('Mark ₹300 to Asha as paid?');

    fixture.componentInstance.answerPrompt(true);
    fixture.componentInstance.onVisibilityChange();
    fixture.detectChanges();
    expect(emitted).toEqual({ debt: debt(), method: 'upi' });
    expect(root.querySelector('[data-testid="split-paid-prompt"]')).toBeNull();
  });

  it('the payee confirms pending payments made to them', () => {
    const pending: SplitSettlement = {
      id: 's-1',
      payer_member_id: 'm-b',
      payee_member_id: 'm-a',
      amount_paise: 30000,
      status: 'paid',
      method: 'upi',
      paid_at: '2026-09-27T10:00:00Z',
      confirmed_at: null,
    };
    let confirmed: string | undefined;
    const root = render([], 'm-a', [pending]);
    fixture.componentInstance.confirm.subscribe((id) => (confirmed = id));
    root.querySelector<HTMLButtonElement>('[data-testid="split-confirm"]')!.click();
    expect(confirmed).toBe('s-1');
  });

  it('lets a member set their UPI id and rejects a malformed one', () => {
    const root = render([]);
    const input = root.querySelector<HTMLInputElement>('[data-testid="split-my-upi"]')!;
    const save = root.querySelector<HTMLButtonElement>('[data-testid="split-upi-save"]')!;
    let saved: string | null | undefined;
    fixture.componentInstance.saveUpi.subscribe((v) => (saved = v));
    input.value = 'bala';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(save.disabled).toBeTrue();
    input.value = 'bala@okaxis';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    save.click();
    expect(saved).toBe('bala@okaxis');
  });
});
