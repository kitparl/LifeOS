import { Component, computed, input } from '@angular/core';
import qrcode from 'qrcode-generator';

const QUIET_ZONE = 2;

export interface QrMatrix {
  /** Side length in modules, including the quiet zone. */
  size: number;
  /** SVG path covering every dark module. */
  path: string;
}

function encode(payload: string): ReturnType<typeof qrcode> {
  const qr = qrcode(0, 'M');
  qr.addData(payload);
  qr.make();
  return qr;
}

/** Encodes `payload` locally (no network) into an SVG path of dark modules. */
export function buildQrMatrix(payload: string): QrMatrix {
  const qr = encode(payload);
  const count = qr.getModuleCount();
  const parts: string[] = [];
  for (let row = 0; row < count; row++) {
    for (let col = 0; col < count; col++) {
      if (qr.isDark(row, col)) parts.push(`M${col + QUIET_ZONE} ${row + QUIET_ZONE}h1v1h-1z`);
    }
  }
  return { size: count + QUIET_ZONE * 2, path: parts.join('') };
}

/** The same QR as a PNG image (for sharing or saving), drawn on a canvas in the browser. */
export function qrPngBlob(payload: string, scale = 10): Promise<Blob> {
  const qr = encode(payload);
  const count = qr.getModuleCount();
  const size = (count + QUIET_ZONE * 2) * scale;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (!ctx) return Promise.reject(new Error('Canvas is not available'));
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, size, size);
  ctx.fillStyle = '#000';
  for (let row = 0; row < count; row++) {
    for (let col = 0; col < count; col++) {
      if (qr.isDark(row, col)) ctx.fillRect((col + QUIET_ZONE) * scale, (row + QUIET_ZONE) * scale, scale, scale);
    }
  }
  return new Promise((resolve, reject) =>
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('Could not draw the QR'))), 'image/png'),
  );
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
