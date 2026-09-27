import { absoluteShareUrl, mailtoHref, shareMessage, whatsappHref } from './share-links';

describe('Split share links', () => {
  const url = absoluteShareUrl('/s/k7mq2p', 'https://lifeos.example');
  const message = shareMessage('Dinner', url);

  it('builds the absolute short URL and the join message', () => {
    expect(url).toBe('https://lifeos.example/s/k7mq2p');
    expect(message).toBe('Join "Dinner" on LifeOS: https://lifeos.example/s/k7mq2p');
  });

  it('defaults to the current origin', () => {
    expect(absoluteShareUrl('/s/k7mq2p')).toBe(`${location.origin}/s/k7mq2p`);
  });

  it('WhatsApp href starts with wa.me and carries the encoded short URL', () => {
    const href = whatsappHref(message);
    expect(href.startsWith('https://wa.me/?text=')).toBeTrue();
    expect(href).toContain(encodeURIComponent(url));
  });

  it('Email href is a mailto with subject and the same URL in the body', () => {
    const href = mailtoHref('Dinner', message);
    expect(href.startsWith('mailto:')).toBeTrue();
    expect(href).toContain(`subject=${encodeURIComponent('Join Dinner')}`);
    expect(href).toContain(encodeURIComponent(url));
  });
});
