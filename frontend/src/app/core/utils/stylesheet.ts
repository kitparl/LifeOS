/**
 * Adds a `<link rel="stylesheet">` once per `id`. Used for third-party CSS that angular.json copies
 * as an asset instead of bundling globally, so it only loads for screens that need it.
 */
export function ensureStylesheet(id: string, href: string): void {
  if (document.getElementById(id)) return;
  const link = document.createElement('link');
  link.id = id;
  link.rel = 'stylesheet';
  link.href = href;
  document.head.appendChild(link);
}
