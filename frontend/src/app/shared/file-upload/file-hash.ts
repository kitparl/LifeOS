/** SHA-256 hex digest of a File (for client-side duplicate checks). */
export async function sha256Hex(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function fileFingerprint(file: File): string {
  return `${file.name.toLowerCase()}|${file.size}|${file.lastModified}`;
}
