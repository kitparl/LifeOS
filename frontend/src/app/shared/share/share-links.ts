/**
 * Share links are built in the browser and open the person's own apps; LifeOS never
 * sends a message or picks a recipient. Used by Split Bills and shared trip plans.
 */

/** The words a feature puts around its short link (one constant per feature). */
export interface ShareText {
  heading: string;
  shareLabel: string;
  qrHint: string;
  /** Downloaded QR file name prefix, e.g. `split` gives `split-dinner-qr.png`. */
  filePrefix: string;
  subject(name: string): string;
  message(name: string, url: string): string;
}

export function absoluteShareUrl(urlPath: string, origin: string = location.origin): string {
  return `${origin}${urlPath}`;
}

export function whatsappHref(message: string): string {
  return `https://wa.me/?text=${encodeURIComponent(message)}`;
}

export function mailtoHref(subject: string, message: string): string {
  return `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(message)}`;
}
