// Pure, dependency-free encode/decode functions for the Encoding & Decoding category.
// Every decode function throws a human-readable Error on invalid input — never fails silently.

function bytesToBase64(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function base64ToBytes(b64: string): Uint8Array {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function decodeUtf8(bytes: Uint8Array, sourceLabel: string): string {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  } catch {
    throw new Error(`${sourceLabel} decodes to bytes that are not valid UTF-8 text.`);
  }
}

// --- Base64 ---
export function base64Encode(text: string): string {
  return bytesToBase64(new TextEncoder().encode(text));
}
export function base64Decode(text: string): string {
  try {
    return decodeUtf8(base64ToBytes(text.trim().replace(/\s+/g, '')), 'Base64');
  } catch (e) {
    if (e instanceof Error && e.message.includes('UTF-8')) throw e;
    throw new Error('Invalid Base64 input — could not decode.');
  }
}

// --- URL ---
export function urlEncode(text: string): string {
  return encodeURIComponent(text);
}
export function urlDecode(text: string): string {
  try {
    return decodeURIComponent(text);
  } catch {
    throw new Error('Invalid percent-encoding — could not decode as a URL component.');
  }
}

// --- HTML entities ---
const HTML_ENCODE_MAP: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export function htmlEncode(text: string): string {
  return text.replace(/[&<>"']/g, (ch) => HTML_ENCODE_MAP[ch]);
}
export function htmlDecode(text: string): string {
  const el = document.createElement('textarea');
  el.innerHTML = text;
  return el.value;
}

// --- Hex ---
export function textToHex(text: string): string {
  return Array.from(new TextEncoder().encode(text))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join(' ');
}
export function hexToText(hex: string): string {
  const clean = hex.trim().replace(/0x/gi, '').replace(/[\s,:-]+/g, '');
  if (!/^[0-9a-fA-F]*$/.test(clean) || clean.length % 2 !== 0) {
    throw new Error('Invalid hex input — expected an even number of hex digits.');
  }
  const bytes = new Uint8Array(clean.length / 2);
  for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(clean.substr(i * 2, 2), 16);
  return decodeUtf8(bytes, 'Hex');
}

// --- Binary ---
export function textToBinary(text: string): string {
  return Array.from(new TextEncoder().encode(text))
    .map((b) => b.toString(2).padStart(8, '0'))
    .join(' ');
}
export function binaryToText(bin: string): string {
  const clean = bin.trim().replace(/\s+/g, '');
  if (!/^[01]*$/.test(clean) || clean.length % 8 !== 0) {
    throw new Error('Invalid binary input — expected groups of 8 bits (0/1).');
  }
  const bytes = new Uint8Array(clean.length / 8);
  for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(clean.substr(i * 8, 8), 2);
  return decodeUtf8(bytes, 'Binary');
}

// --- ASCII (decimal code points) ---
export function textToAscii(text: string): string {
  return Array.from(text)
    .map((ch) => ch.codePointAt(0)!.toString())
    .join(' ');
}
export function asciiToText(codes: string): string {
  const parts = codes.trim().split(/[\s,]+/).filter(Boolean);
  if (parts.length === 0) return '';
  if (!parts.every((p) => /^\d+$/.test(p) && Number(p) <= 0x10ffff)) {
    throw new Error('Invalid ASCII input — expected space or comma separated character codes.');
  }
  try {
    return parts.map((p) => String.fromCodePoint(Number(p))).join('');
  } catch {
    throw new Error('One or more character codes are out of range.');
  }
}

// --- Unicode escape sequences (\uXXXX) ---
export function textToUnicodeEscape(text: string): string {
  return Array.from(text)
    .map((ch) => '\\u' + ch.charCodeAt(0).toString(16).padStart(4, '0'))
    .join('');
}
export function unicodeEscapeToText(escaped: string): string {
  const clean = escaped.trim();
  if (!/^(\\u[0-9a-fA-F]{4})+$/.test(clean)) {
    throw new Error('Invalid Unicode escape input — expected one or more \\uXXXX groups.');
  }
  return clean.replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
}

// --- Base32 (RFC 4648) ---
const BASE32_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
export function base32Encode(text: string): string {
  const bytes = new TextEncoder().encode(text);
  let bits = 0;
  let value = 0;
  let output = '';
  for (const byte of bytes) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      output += BASE32_ALPHABET[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) {
    output += BASE32_ALPHABET[(value << (5 - bits)) & 31];
  }
  while (output.length % 8 !== 0) output += '=';
  return output;
}
export function base32Decode(input: string): string {
  const clean = input.trim().toUpperCase().replace(/=+$/, '');
  if (clean !== '' && !/^[A-Z2-7]+$/.test(clean)) {
    throw new Error('Invalid Base32 input — unexpected character.');
  }
  let bits = 0;
  let value = 0;
  const bytes: number[] = [];
  for (const char of clean) {
    const idx = BASE32_ALPHABET.indexOf(char);
    value = (value << 5) | idx;
    bits += 5;
    if (bits >= 8) {
      bytes.push((value >>> (bits - 8)) & 0xff);
      bits -= 8;
    }
  }
  return decodeUtf8(new Uint8Array(bytes), 'Base32');
}

// --- Base58 (Bitcoin alphabet) ---
const BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
export function base58Encode(text: string): string {
  const bytes = new TextEncoder().encode(text);
  if (bytes.length === 0) return '';
  let num = 0n;
  for (const b of bytes) num = num * 256n + BigInt(b);
  let encoded = '';
  while (num > 0n) {
    const rem = Number(num % 58n);
    encoded = BASE58_ALPHABET[rem] + encoded;
    num = num / 58n;
  }
  let leadingZeros = 0;
  for (const b of bytes) {
    if (b === 0) leadingZeros++;
    else break;
  }
  return BASE58_ALPHABET[0].repeat(leadingZeros) + encoded;
}
export function base58Decode(input: string): string {
  const clean = input.trim();
  if (!clean) return '';
  if (!/^[1-9A-HJ-NP-Za-km-z]+$/.test(clean)) {
    throw new Error('Invalid Base58 input — unexpected character (0, O, I, and l are not used).');
  }
  let num = 0n;
  for (const ch of clean) {
    num = num * 58n + BigInt(BASE58_ALPHABET.indexOf(ch));
  }
  const byteValues: number[] = [];
  while (num > 0n) {
    byteValues.unshift(Number(num % 256n));
    num = num / 256n;
  }
  let leadingOnes = 0;
  for (const ch of clean) {
    if (ch === '1') leadingOnes++;
    else break;
  }
  const result = new Uint8Array(leadingOnes + byteValues.length);
  result.set(byteValues, leadingOnes);
  return decodeUtf8(result, 'Base58');
}
