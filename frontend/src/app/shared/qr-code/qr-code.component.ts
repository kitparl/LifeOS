import { Component, computed, input } from '@angular/core';
import qrcode from 'qrcode-generator';

const QUIET_ZONE = 2;

export interface QrMatrix {
  /** Side length in modules, including the quiet zone. */
  size: number;
  /** SVG path covering every dark module. */
  path: string;
}

/** Encodes `payload` locally (no network) into an SVG path of dark modules. */
export function buildQrMatrix(payload: string): QrMatrix {
  const qr = qrcode(0, 'M');
  qr.addData(payload);
  qr.make();
  const count = qr.getModuleCount();
  const parts: string[] = [];
  for (let row = 0; row < count; row++) {
    for (let col = 0; col < count; col++) {
      if (qr.isDark(row, col)) parts.push(`M${col + QUIET_ZONE} ${row + QUIET_ZONE}h1v1h-1z`);
    }
  }
  return { size: count + QUIET_ZONE * 2, path: parts.join('') };
}

/** A QR code drawn in the browser. `data-payload` exposes the encoded text for tests. */
@Component({
  selector: 'app-qr-code',
  standalone: true,
  template: `
    <svg
      role="img"
      [attr.aria-label]="label()"
      [attr.data-payload]="payload()"
      [attr.width]="size()"
      [attr.height]="size()"
      [attr.viewBox]="'0 0 ' + matrix().size + ' ' + matrix().size"
      shape-rendering="crispEdges"
    >
      <rect width="100%" height="100%" fill="#fff" />
      <path [attr.d]="matrix().path" fill="#000" />
    </svg>
  `,
})
export class QrCodeComponent {
  readonly payload = input.required<string>();
  readonly label = input('QR code');
  readonly size = input(168);

  protected readonly matrix = computed(() => buildQrMatrix(this.payload()));
}
