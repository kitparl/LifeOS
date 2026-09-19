import { md5Hex, computeHash, computeHmac } from './hash.util';

describe('hash.util', () => {
  it('computes correct MD5 for known vectors', () => {
    expect(md5Hex(new TextEncoder().encode(''))).toBe('d41d8cd98f00b204e9800998ecf8427e');
    expect(md5Hex(new TextEncoder().encode('abc'))).toBe('900150983cd24fb0d6963f7d28e17f72');
  });

  it('computes SHA-256 via Web Crypto', async () => {
    const hash = await computeHash('SHA-256', 'abc');
    expect(hash).toBe('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  });

  it('computes HMAC-SHA256', async () => {
    const hmac = await computeHmac('SHA-256', 'key', 'The quick brown fox jumps over the lazy dog');
    expect(hmac).toBe('f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8');
  });
});
