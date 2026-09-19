// MD5 has no Web Crypto implementation, so it's hand-rolled here (RFC 1321). Everything else
// (SHA-1/256/512, HMAC) uses the browser's native Web Crypto — nothing is sent to a server.

function rotl(x: number, c: number): number {
  return (x << c) | (x >>> (32 - c));
}

const MD5_SHIFTS = [
  7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 4, 11, 16, 23, 4,
  11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
];
const MD5_K = new Int32Array(64);
for (let i = 0; i < 64; i++) MD5_K[i] = Math.floor(Math.abs(Math.sin(i + 1)) * 2 ** 32);

function toHexLE(n: number): string {
  const buf = new ArrayBuffer(4);
  new DataView(buf).setInt32(0, n, true);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function md5Hex(bytes: Uint8Array): string {
  let a0 = 0x67452301;
  let b0 = 0xefcdab89;
  let c0 = 0x98badcfe;
  let d0 = 0x10325476;

  const bitLen = bytes.length * 8;
  let paddedLen = bytes.length + 1;
  while (paddedLen % 64 !== 56) paddedLen++;
  paddedLen += 8;
  const padded = new Uint8Array(paddedLen);
  padded.set(bytes);
  padded[bytes.length] = 0x80;
  const dv = new DataView(padded.buffer);
  dv.setUint32(paddedLen - 8, bitLen >>> 0, true);
  dv.setUint32(paddedLen - 4, Math.floor(bitLen / 2 ** 32), true);

  for (let chunkStart = 0; chunkStart < paddedLen; chunkStart += 64) {
    const M = new Int32Array(16);
    for (let j = 0; j < 16; j++) M[j] = dv.getInt32(chunkStart + j * 4, true);

    let A = a0;
    let B = b0;
    let C = c0;
    let D = d0;
    for (let i = 0; i < 64; i++) {
      let F: number;
      let g: number;
      if (i < 16) {
        F = (B & C) | (~B & D);
        g = i;
      } else if (i < 32) {
        F = (D & B) | (~D & C);
        g = (5 * i + 1) % 16;
      } else if (i < 48) {
        F = B ^ C ^ D;
        g = (3 * i + 5) % 16;
      } else {
        F = C ^ (B | ~D);
        g = (7 * i) % 16;
      }
      F = (F + A + MD5_K[i] + M[g]) | 0;
      A = D;
      D = C;
      C = B;
      B = (B + rotl(F, MD5_SHIFTS[i])) | 0;
    }
    a0 = (a0 + A) | 0;
    b0 = (b0 + B) | 0;
    c0 = (c0 + C) | 0;
    d0 = (d0 + D) | 0;
  }

  return toHexLE(a0) + toHexLE(b0) + toHexLE(c0) + toHexLE(d0);
}

function bufToHex(buf: ArrayBuffer): string {
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

async function digestHex(algo: 'SHA-1' | 'SHA-256' | 'SHA-384' | 'SHA-512', bytes: Uint8Array): Promise<string> {
  const buf = await crypto.subtle.digest(algo, bytes);
  return bufToHex(buf);
}

export type HashAlgo = 'MD5' | 'SHA-1' | 'SHA-256' | 'SHA-512';
export const OUTDATED_HASH_ALGOS: HashAlgo[] = ['MD5', 'SHA-1'];

export async function computeHash(algo: HashAlgo, text: string): Promise<string> {
  const bytes = new TextEncoder().encode(text);
  if (algo === 'MD5') return md5Hex(bytes);
  return digestHex(algo, bytes);
}

export type HmacAlgo = 'SHA-1' | 'SHA-256' | 'SHA-512';

export async function computeHmac(algo: HmacAlgo, key: string, text: string): Promise<string> {
  const keyBytes = new TextEncoder().encode(key);
  const cryptoKey = await crypto.subtle.importKey('raw', keyBytes, { name: 'HMAC', hash: algo }, false, ['sign']);
  const signature = await crypto.subtle.sign('HMAC', cryptoKey, new TextEncoder().encode(text));
  return bufToHex(signature);
}
