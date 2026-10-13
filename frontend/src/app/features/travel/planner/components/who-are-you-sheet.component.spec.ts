import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GoogleButtonStubComponent } from '../testing/google-button.stub';
import { PlannerGoogleButtonComponent } from './google-button.component';
import { PlannerWhoComponent } from './who-are-you-sheet.component';

describe('PlannerWhoComponent ("Who are you?")', () => {
  let fixture: ComponentFixture<PlannerWhoComponent>;
  const q = (id: string) => document.querySelector<HTMLElement>(`[data-testid="${id}"]`);

  function render(inputs: Record<string, unknown>, inApp = false): void {
    TestBed.configureTestingModule({ imports: [PlannerWhoComponent] });
    TestBed.overrideComponent(PlannerWhoComponent, {
      remove: { imports: [PlannerGoogleButtonComponent] },
      add: { imports: [GoogleButtonStubComponent] },
    });
    fixture = TestBed.createComponent(PlannerWhoComponent);
    fixture.componentRef.setInput('open', true);
    fixture.componentRef.setInput('ownerName', 'Priya');
    for (const [key, value] of Object.entries(inputs)) fixture.componentRef.setInput(key, value);
    fixture.componentInstance.inApp.set(inApp);
    fixture.detectChanges();
  }

  afterEach(() => fixture.destroy());

  it('offers Google and "Just use my name" equally, with the privacy line', () => {
    render({});
    const google = jasmine.createSpy('google');
    fixture.componentInstance.google.subscribe(google);
    expect(document.body.textContent).toContain('Priya will see your name and Gmail.');
    q('google-stub')!.click();
    expect(google).toHaveBeenCalledWith('google-id-token');

    const named = jasmine.createSpy('named');
    fixture.componentInstance.named.subscribe(named);
    const input = q('who-name') as HTMLInputElement;
    expect((q('who-continue') as HTMLButtonElement).disabled).toBeTrue();
    input.value = '  Asha ';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    q('who-continue')!.click();
    expect(named).toHaveBeenCalledWith('Asha');
  });

  it('never leaves a dead end inside WhatsApp / Instagram: a hint, copy link, and the name path', () => {
    render({}, true);
    expect(q('who-inapp')!.textContent).toContain('Open the link in Chrome or Safari');
    expect(q('who-name')).not.toBeNull();
  });

  it('when Google fails to load, falls back to the name path', () => {
    render({});
    fixture.componentInstance.googleFailed.set(true);
    fixture.detectChanges();
    expect(q('google-stub')).toBeNull();
    expect(q('who-inapp')!.textContent).toContain('just use your name');
  });

  it('hides the name path when the owner requires Google', () => {
    render({ namesAllowed: false });
    expect(q('who-name')).toBeNull();
    expect(document.body.textContent).toContain('Priya asked everyone to continue with Google.');
  });
});
