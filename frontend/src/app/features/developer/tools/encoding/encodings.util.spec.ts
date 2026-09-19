import {
  base64Encode, base64Decode,
  base32Encode, base32Decode,
  base58Encode, base58Decode,
  textToHex, hexToText,
  textToBinary, binaryToText,
  textToAscii, asciiToText,
  textToUnicodeEscape, unicodeEscapeToText,
  htmlEncode, htmlDecode,
  urlEncode, urlDecode,
} from './encodings.util';

describe('encodings.util', () => {
  it('round-trips base64', () => {
    expect(base64Decode(base64Encode('Hello, world! 🎉'))).toBe('Hello, world! 🎉');
  });

  it('rejects invalid base64', () => {
    expect(() => base64Decode('not-valid-base64!!!')).toThrowError();
  });

  it('round-trips base32', () => {
    expect(base32Decode(base32Encode('Hello, World!'))).toBe('Hello, World!');
  });

  it('round-trips base58', () => {
    expect(base58Decode(base58Encode('Hello, World!'))).toBe('Hello, World!');
  });

  it('base58 rejects invalid characters (0, O, I, l)', () => {
    expect(() => base58Decode('0OIl')).toThrowError();
  });

  it('round-trips hex', () => {
    expect(hexToText(textToHex('abc'))).toBe('abc');
  });

  it('rejects odd-length hex', () => {
    expect(() => hexToText('abc')).toThrowError();
  });

  it('round-trips binary', () => {
    expect(binaryToText(textToBinary('Hi'))).toBe('Hi');
  });

  it('round-trips ascii codes', () => {
    expect(asciiToText(textToAscii('Hi!'))).toBe('Hi!');
  });

  it('round-trips unicode escapes', () => {
    expect(unicodeEscapeToText(textToUnicodeEscape('Hi'))).toBe('Hi');
  });

  it('encodes and decodes HTML entities', () => {
    expect(htmlEncode('<a href="x">&</a>')).toBe('&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;');
    expect(htmlDecode('&lt;b&gt;')).toBe('<b>');
  });

  it('encodes and decodes URL components', () => {
    expect(urlEncode('a b&c')).toBe('a%20b%26c');
    expect(urlDecode('a%20b%26c')).toBe('a b&c');
  });
});
