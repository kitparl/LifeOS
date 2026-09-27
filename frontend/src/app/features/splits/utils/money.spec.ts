import { equalSplit } from './equal-split';
import { formatInr, parseRupees, rupeesToPaise } from './money';

describe('Split money utils', () => {
  it('formats paise as rupees regardless of the display-currency preference', () => {
    expect(formatInr(30000)).toBe('₹300');
    expect(formatInr(3334)).toBe('₹33.34');
    expect(formatInr(10000000)).toBe('₹1,00,000');
  });

  it('parses amounts the server accepts and rejects the rest', () => {
    expect(parseRupees(' 450 ')).toBe(450);
    expect(parseRupees('99.99')).toBe(99.99);
    for (const bad of ['', '0', '0.00', '-5', '1.234', 'abc', '1e3', '10000000.01']) {
      expect(parseRupees(bad)).withContext(bad).toBeNull();
    }
    expect(rupeesToPaise(99.99)).toBe(9999);
    expect(rupeesToPaise(0.29)).toBe(29);
  });

  it('mirrors the server equal split: extra paise go to the first members in join order', () => {
    expect([...equalSplit(10000, ['a', 'b', 'c']).values()]).toEqual([3334, 3333, 3333]);
    expect([...equalSplit(10000, ['a', 'b', 'c', 'd', 'e', 'f', 'g']).values()]).toEqual([
      1429, 1429, 1429, 1429, 1428, 1428, 1428,
    ]);
    expect([...equalSplit(10000, ['payer']).values()]).toEqual([10000]);
    expect(equalSplit(100, []).size).toBe(0);
  });
});
