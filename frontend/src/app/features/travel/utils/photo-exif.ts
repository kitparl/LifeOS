/**
 * Read a photo's GPS position and capture time in the browser, before upload (requirements D-08).
 * The result is only a suggestion: the user confirms or edits it. Missing or broken EXIF is normal
 * (spec §17 — never assume it is present), so every failure resolves to "nothing found".
 */
export interface PhotoExif {
  lat: number | null;
  lng: number | null;
  takenAt: string | null;
}

const NONE: PhotoExif = { lat: null, lng: null, takenAt: null };

export async function readPhotoExif(file: Blob): Promise<PhotoExif> {
  try {
    // Loaded on demand (lite build) so it only reaches users who add travel photos.
    const exifr = (await import('exifr/dist/lite.esm.mjs')).default;
    const [gps, tags] = await Promise.all([
      exifr.gps(file).catch(() => null),
      exifr.parse(file, ['DateTimeOriginal']).catch(() => null),
    ]);
    return normalizeExif(gps, tags);
  } catch {
    return NONE;
  }
}

/** Validate what the parser returned; exported for tests. */
export function normalizeExif(
  gps: { latitude?: unknown; longitude?: unknown } | null | undefined,
  tags: { DateTimeOriginal?: unknown } | null | undefined,
): PhotoExif {
  const lat = typeof gps?.latitude === 'number' ? gps.latitude : NaN;
  const lng = typeof gps?.longitude === 'number' ? gps.longitude : NaN;
  const validPosition =
    Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 && !(lat === 0 && lng === 0);
  const taken = tags?.DateTimeOriginal instanceof Date && !isNaN(tags.DateTimeOriginal.getTime()) ? tags.DateTimeOriginal : null;
  return {
    lat: validPosition ? Math.round(lat * 1e6) / 1e6 : null,
    lng: validPosition ? Math.round(lng * 1e6) / 1e6 : null,
    takenAt: taken ? taken.toISOString() : null,
  };
}
