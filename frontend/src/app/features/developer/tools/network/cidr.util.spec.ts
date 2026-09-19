import { calculateCidr } from './cidr.util';

describe('cidr.util', () => {
  it('calculates a /24 network', () => {
    const info = calculateCidr('192.168.1.10/24');
    expect(info.network).toBe('192.168.1.0');
    expect(info.broadcast).toBe('192.168.1.255');
    expect(info.netmask).toBe('255.255.255.0');
    expect(info.firstHost).toBe('192.168.1.1');
    expect(info.lastHost).toBe('192.168.1.254');
    expect(info.usableHosts).toBe(254);
    expect(info.totalAddresses).toBe(256);
  });

  it('calculates a /30 network (2 usable hosts)', () => {
    const info = calculateCidr('10.0.0.0/30');
    expect(info.usableHosts).toBe(2);
    expect(info.firstHost).toBe('10.0.0.1');
    expect(info.lastHost).toBe('10.0.0.2');
  });

  it('handles /31 and /32 with zero usable hosts', () => {
    expect(calculateCidr('10.0.0.0/31').usableHosts).toBe(0);
    expect(calculateCidr('10.0.0.0/32').usableHosts).toBe(0);
  });

  it('rejects malformed input', () => {
    expect(() => calculateCidr('not-a-cidr')).toThrowError();
    expect(() => calculateCidr('999.1.1.1/24')).toThrowError();
    expect(() => calculateCidr('10.0.0.0/33')).toThrowError();
  });
});
