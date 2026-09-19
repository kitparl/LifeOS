export function ipv4ToIpv6Mapped(ipv4: string): string {
  const parts = ipv4.trim().split('.');
  if (parts.length !== 4 || parts.some((p) => !/^\d{1,3}$/.test(p) || Number(p) > 255)) {
    throw new Error('Invalid IPv4 address, e.g. 192.168.1.1.');
  }
  const hex = parts.map((p) => Number(p).toString(16).padStart(2, '0'));
  return `::ffff:${hex[0]}${hex[1]}:${hex[2]}${hex[3]}`;
}

export function ipv6MappedToIpv4(ipv6: string): string {
  const trimmed = ipv6.trim().toLowerCase();
  const dotted = trimmed.match(/^::ffff:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$/);
  if (dotted) return dotted[1];
  const hexMatch = trimmed.match(/^::ffff:([0-9a-f]{1,4}):([0-9a-f]{1,4})$/);
  if (hexMatch) {
    const a = parseInt(hexMatch[1], 16);
    const b = parseInt(hexMatch[2], 16);
    return `${(a >> 8) & 255}.${a & 255}.${(b >> 8) & 255}.${b & 255}`;
  }
  throw new Error('Expected an IPv4-mapped IPv6 address, e.g. ::ffff:192.168.1.1');
}
