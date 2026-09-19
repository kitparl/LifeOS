export interface RegexPreset {
  id: string;
  label: string;
  pattern: string;
  flags: string;
  description: string;
}

export const REGEX_PRESETS: RegexPreset[] = [
  { id: 'email', label: 'Email address', pattern: '^[\\w.+-]+@[\\w-]+\\.[a-zA-Z]{2,}$', flags: '', description: 'Matches a simple email address.' },
  { id: 'url', label: 'URL', pattern: '^https?:\\/\\/[\\w.-]+(?:\\.[a-zA-Z]{2,})+(?:\\/[^\\s]*)?$', flags: '', description: 'Matches an http(s) URL.' },
  { id: 'ipv4', label: 'IPv4 address', pattern: '^(?:(?:25[0-5]|2[0-4]\\d|[01]?\\d?\\d)\\.){3}(?:25[0-5]|2[0-4]\\d|[01]?\\d?\\d)$', flags: '', description: 'Matches an IPv4 address (0-255 per octet).' },
  { id: 'uuid', label: 'UUID', pattern: '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', flags: 'i', description: 'Matches a UUID/GUID.' },
  { id: 'hex-color', label: 'Hex color', pattern: '^#(?:[0-9a-fA-F]{3}){1,2}$', flags: '', description: 'Matches a 3- or 6-digit hex color.' },
  { id: 'date-iso', label: 'Date (YYYY-MM-DD)', pattern: '^\\d{4}-\\d{2}-\\d{2}$', flags: '', description: 'Matches an ISO-style date (does not validate calendar correctness).' },
  { id: 'integer', label: 'Integer', pattern: '^-?\\d+$', flags: '', description: 'Matches a whole number, optionally negative.' },
  { id: 'decimal', label: 'Decimal number', pattern: '^-?\\d+(?:\\.\\d+)?$', flags: '', description: 'Matches an integer or decimal number.' },
  { id: 'slug', label: 'URL slug', pattern: '^[a-z0-9]+(?:-[a-z0-9]+)*$', flags: '', description: 'Matches a lowercase, hyphen-separated slug.' },
  { id: 'whitespace', label: 'Whitespace-only', pattern: '^\\s*$', flags: '', description: 'Matches empty or whitespace-only text.' },
];
