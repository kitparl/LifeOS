export function uuidV4(): string {
  return crypto.randomUUID();
}

/** RFC 9562 UUIDv7: 48-bit millisecond timestamp + random bits. */
export function uuidV7(): string {
  const bytes = new Uint8Array(16);
  let ts = Date.now();
  for (let i = 5; i >= 0; i--) {
    bytes[i] = ts & 0xff;
    ts = Math.floor(ts / 256);
  }
  bytes.set(crypto.getRandomValues(new Uint8Array(10)), 6);
  bytes[6] = (bytes[6] & 0x0f) | 0x70; // version 7
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // variant 10
  const hex = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export interface RandomStringOptions {
  length: number;
  lowercase: boolean;
  uppercase: boolean;
  numbers: boolean;
  symbols: boolean;
}

const CHARSETS = {
  lowercase: 'abcdefghijklmnopqrstuvwxyz',
  uppercase: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  numbers: '0123456789',
  symbols: '!@#$%^&*()-_=+[]{};:,.<>?',
};

/** Uses crypto.getRandomValues (CSPRNG), never Math.random. */
export function generateRandomString(opts: RandomStringOptions): string {
  let charset = '';
  if (opts.lowercase) charset += CHARSETS.lowercase;
  if (opts.uppercase) charset += CHARSETS.uppercase;
  if (opts.numbers) charset += CHARSETS.numbers;
  if (opts.symbols) charset += CHARSETS.symbols;
  if (!charset) throw new Error('Select at least one character set.');
  const randomValues = crypto.getRandomValues(new Uint32Array(Math.max(1, opts.length)));
  return Array.from(randomValues)
    .map((v) => charset[v % charset.length])
    .join('');
}

export function passwordStrengthBits(opts: RandomStringOptions): number {
  let charsetSize = 0;
  if (opts.lowercase) charsetSize += 26;
  if (opts.uppercase) charsetSize += 26;
  if (opts.numbers) charsetSize += 10;
  if (opts.symbols) charsetSize += CHARSETS.symbols.length;
  if (charsetSize === 0) return 0;
  return Math.round(opts.length * Math.log2(charsetSize));
}

const LOREM_WORDS = [
  'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit', 'sed', 'do',
  'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore', 'magna', 'aliqua', 'enim',
  'ad', 'minim', 'veniam', 'quis', 'nostrud', 'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip',
  'ex', 'ea', 'commodo', 'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
  'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint', 'occaecat', 'cupidatat',
];

function randomFrom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function generateLoremIpsum(paragraphs: number, sentencesPerParagraph = 4): string {
  const out: string[] = [];
  for (let p = 0; p < Math.max(1, paragraphs); p++) {
    const sentences: string[] = [];
    for (let s = 0; s < sentencesPerParagraph; s++) {
      const wordCount = 8 + Math.floor(Math.random() * 8);
      const words = Array.from({ length: wordCount }, () => randomFrom(LOREM_WORDS));
      words[0] = words[0][0].toUpperCase() + words[0].slice(1);
      sentences.push(words.join(' ') + '.');
    }
    out.push(sentences.join(' '));
  }
  return out.join('\n\n');
}

const FIRST_NAMES = ['Ada', 'Alan', 'Grace', 'Linus', 'Margaret', 'Dennis', 'Barbara', 'Ken', 'Radia', 'Vint'];
const LAST_NAMES = ['Lovelace', 'Turing', 'Hopper', 'Torvalds', 'Hamilton', 'Ritchie', 'Liskov', 'Thompson', 'Perlman', 'Cerf'];
const CITIES = ['Austin', 'Berlin', 'Toronto', 'Lisbon', 'Nairobi', 'Osaka', 'Bengaluru', 'Warsaw'];

const FAKE_GENERATORS: Record<string, () => unknown> = {
  name: () => `${randomFrom(FIRST_NAMES)} ${randomFrom(LAST_NAMES)}`,
  firstName: () => randomFrom(FIRST_NAMES),
  lastName: () => randomFrom(LAST_NAMES),
  email: () => `${randomFrom(FIRST_NAMES).toLowerCase()}.${randomFrom(LAST_NAMES).toLowerCase()}@example.com`,
  uuid: () => uuidV4(),
  number: () => Math.floor(Math.random() * 1000),
  boolean: () => Math.random() < 0.5,
  date: () => new Date(Date.now() - Math.floor(Math.random() * 1e10)).toISOString(),
  word: () => randomFrom(LOREM_WORDS),
  city: () => randomFrom(CITIES),
};

export const FAKE_JSON_PLACEHOLDERS = Object.keys(FAKE_GENERATORS);

function fillTemplate(node: unknown): unknown {
  if (typeof node === 'string') {
    const match = node.match(/^\{\{(\w+)\}\}$/);
    if (match && FAKE_GENERATORS[match[1]]) return FAKE_GENERATORS[match[1]]();
    return node;
  }
  if (Array.isArray(node)) return node.map(fillTemplate);
  if (node !== null && typeof node === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(node)) out[k] = fillTemplate(v);
    return out;
  }
  return node;
}

export function generateFakeData(template: unknown, count: number): unknown {
  const one = () => fillTemplate(template);
  return count > 1 ? Array.from({ length: count }, one) : one();
}
