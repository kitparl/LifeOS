export interface DecodedJwt {
  header: unknown;
  payload: unknown;
  signature: string;
  isExpired: boolean | null;
  expiresAt: string | null;
  issuedAt: string | null;
}

function base64UrlDecode(segment: string, label: string): string {
  const padded = segment.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(segment.length / 4) * 4, '=');
  let binary: string;
  try {
    binary = atob(padded);
  } catch {
    throw new Error(`Malformed JWT ${label} — could not Base64URL-decode.`);
  }
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  } catch {
    throw new Error(`Malformed JWT ${label} — decoded bytes are not valid UTF-8.`);
  }
}

function parseJsonPart(json: string, label: string): unknown {
  try {
    return JSON.parse(json);
  } catch {
    throw new Error(`JWT ${label} is not valid JSON.`);
  }
}

/** Decodes and inspects a JWT. Never verifies the signature (no secret is available client-side). */
export function decodeJwt(token: string): DecodedJwt {
  const parts = token.trim().split('.');
  if (parts.length !== 3) {
    throw new Error('Invalid JWT — expected 3 dot-separated parts (header.payload.signature).');
  }
  const [headerPart, payloadPart, signature] = parts;
  const header = parseJsonPart(base64UrlDecode(headerPart, 'header'), 'header');
  const payload = parseJsonPart(base64UrlDecode(payloadPart, 'payload'), 'payload');

  const claims = typeof payload === 'object' && payload !== null ? (payload as Record<string, unknown>) : {};
  const exp = typeof claims['exp'] === 'number' ? (claims['exp'] as number) : null;
  const iat = typeof claims['iat'] === 'number' ? (claims['iat'] as number) : null;

  return {
    header,
    payload,
    signature,
    isExpired: exp !== null ? Date.now() > exp * 1000 : null,
    expiresAt: exp !== null ? new Date(exp * 1000).toLocaleString() : null,
    issuedAt: iat !== null ? new Date(iat * 1000).toLocaleString() : null,
  };
}
