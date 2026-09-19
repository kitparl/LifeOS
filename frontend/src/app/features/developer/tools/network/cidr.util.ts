export interface CidrInfo {
  network: string;
  broadcast: string;
  netmask: string;
  wildcard: string;
  firstHost: string;
  lastHost: string;
  totalAddresses: number;
  usableHosts: number;
  prefixLength: number;
}

function ipToInt(ip: string): number {
  const parts = ip.split('.');
  if (parts.length !== 4) throw new Error('Invalid IPv4 address.');
  let n = 0;
  for (const p of parts) {
    const v = Number(p);
    if (!Number.isInteger(v) || v < 0 || v > 255) throw new Error(`Invalid IPv4 octet "${p}".`);
    n = (n << 8) | v;
  }
  return n >>> 0;
}

function intToIp(n: number): string {
  return [(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255].join('.');
}

export function calculateCidr(cidr: string): CidrInfo {
  const match = cidr.trim().match(/^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\/(\d{1,2})$/);
  if (!match) throw new Error('Expected format IPv4/prefix, e.g. 192.168.1.0/24.');
  const [, ipStr, prefixStr] = match;
  const prefix = Number(prefixStr);
  if (prefix < 0 || prefix > 32) throw new Error('Prefix length must be between 0 and 32.');
  const ip = ipToInt(ipStr);
  const maskBits = prefix === 0 ? 0 : (0xffffffff << (32 - prefix)) >>> 0;
  const network = (ip & maskBits) >>> 0;
  const broadcast = (network | (~maskBits >>> 0)) >>> 0;
  const total = 2 ** (32 - prefix);
  const usable = prefix >= 31 ? 0 : total - 2;
  return {
    network: intToIp(network),
    broadcast: intToIp(broadcast),
    netmask: intToIp(maskBits),
    wildcard: intToIp(~maskBits >>> 0),
    firstHost: usable > 0 ? intToIp(network + 1) : intToIp(network),
    lastHost: usable > 0 ? intToIp(broadcast - 1) : intToIp(broadcast),
    totalAddresses: total,
    usableHosts: usable,
    prefixLength: prefix,
  };
}
