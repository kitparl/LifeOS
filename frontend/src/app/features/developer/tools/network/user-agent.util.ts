export interface ParsedUserAgent {
  browser: string;
  browserVersion: string;
  os: string;
  deviceType: string;
}

const BROWSER_PATTERNS: [RegExp, string][] = [
  [/Edg\/([\d.]+)/, 'Edge'],
  [/OPR\/([\d.]+)/, 'Opera'],
  [/CriOS\/([\d.]+)/, 'Chrome (iOS)'],
  [/Chrome\/([\d.]+)/, 'Chrome'],
  [/FxiOS\/([\d.]+)/, 'Firefox (iOS)'],
  [/Firefox\/([\d.]+)/, 'Firefox'],
  [/Version\/([\d.]+).*Safari/, 'Safari'],
];

function detectBrowser(ua: string): { browser: string; browserVersion: string } {
  for (const [re, name] of BROWSER_PATTERNS) {
    const m = ua.match(re);
    if (m) return { browser: name, browserVersion: m[1] };
  }
  return { browser: 'Unknown', browserVersion: '' };
}

function detectOs(ua: string): string {
  if (/Windows NT 10/.test(ua)) return 'Windows 10/11';
  if (/Windows NT/.test(ua)) return 'Windows';
  if (/Mac OS X/.test(ua)) return 'macOS';
  if (/Android/.test(ua)) return 'Android';
  if (/iPhone|iPad|iPod/.test(ua)) return 'iOS';
  if (/Linux/.test(ua)) return 'Linux';
  return 'Unknown';
}

/** Heuristic, regex-based parsing — not backed by an external user-agent database/service. */
export function parseUserAgent(ua: string): ParsedUserAgent {
  const { browser, browserVersion } = detectBrowser(ua);
  const os = detectOs(ua);
  const deviceType = /Tablet|iPad/i.test(ua) ? 'Tablet' : /Mobi|Android|iPhone/i.test(ua) ? 'Mobile' : 'Desktop';
  return { browser, browserVersion, os, deviceType };
}
