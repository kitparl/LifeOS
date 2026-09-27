import { TestBed } from '@angular/core/testing';
import { QrCodeComponent, buildQrMatrix } from './qr-code.component';

describe('QrCodeComponent', () => {
  it('builds a deterministic, non-empty module matrix with a quiet zone', () => {
    const a = buildQrMatrix('https://lifeos.example/s/k7mq2p');
    expect(a).toEqual(buildQrMatrix('https://lifeos.example/s/k7mq2p'));
    expect(a.size).toBeGreaterThanOrEqual(21 + 4);
    expect(a.path.length).toBeGreaterThan(0);
    expect(buildQrMatrix('upi://pay?pa=a@b&am=1.00').path).not.toBe(a.path);
  });

  it('renders an SVG exposing its payload', () => {
    const fixture = TestBed.createComponent(QrCodeComponent);
    fixture.componentRef.setInput('payload', 'https://lifeos.example/s/k7mq2p');
    fixture.detectChanges();
    const svg = (fixture.nativeElement as HTMLElement).querySelector('svg')!;
    expect(svg.getAttribute('data-payload')).toBe('https://lifeos.example/s/k7mq2p');
    expect(svg.querySelector('path')!.getAttribute('d')).toMatch(/^M\d+ \d+h1v1h-1z/);
  });
});
