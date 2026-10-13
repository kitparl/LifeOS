import { TestBed } from '@angular/core/testing';
import { NAV_LUCIDE_ICON_PROVIDERS } from '../layout/nav-lucide';
import { ShareActionsComponent } from './share-actions.component';
import { ShareText } from './share-links';

const TEXT: ShareText = {
  heading: 'Share this link with friends',
  shareLabel: 'Share link',
  qrHint: 'Scan to open the plan.',
  filePrefix: 'trip',
  subject: (name) => `Help plan ${name}`,
  message: (name, url) => `Plan "${name}" with me: ${url}`,
};

describe('ShareActionsComponent', () => {
  function render(prefix: string) {
    TestBed.configureTestingModule({ imports: [ShareActionsComponent], providers: [...NAV_LUCIDE_ICON_PROVIDERS] });
    const fixture = TestBed.createComponent(ShareActionsComponent);
    fixture.componentRef.setInput('name', 'Goa 2027');
    fixture.componentRef.setInput('urlPath', '/t/k7mq2p3x');
    fixture.componentRef.setInput('text', TEXT);
    fixture.componentRef.setInput('testIdPrefix', prefix);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('uses the feature words and test ids for the link, WhatsApp and email', () => {
    const el = render('trip-share');
    const url = `${location.origin}/t/k7mq2p3x`;
    expect(el.textContent).toContain('Share this link with friends');
    expect(el.querySelector('[data-testid="trip-share-share-url"]')!.textContent).toContain(url);
    const whatsapp = el.querySelector<HTMLAnchorElement>('[data-testid="trip-share-whatsapp"]')!;
    expect(decodeURIComponent(whatsapp.href)).toContain(`Plan "Goa 2027" with me: ${url}`);
    const email = el.querySelector<HTMLAnchorElement>('[data-testid="trip-share-email"]')!;
    expect(email.href).toContain(`subject=${encodeURIComponent('Help plan Goa 2027')}`);
  });

  it('keeps the Split test ids when Split passes its prefix', () => {
    const el = render('split');
    expect(el.querySelector('[data-testid="split-copy"]')).not.toBeNull();
    expect(el.querySelector('[data-testid="split-qr-toggle"]')).not.toBeNull();
  });
});
