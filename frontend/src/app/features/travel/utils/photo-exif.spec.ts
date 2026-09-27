import { normalizeExif, readPhotoExif } from './photo-exif';

describe('photo-exif', () => {
  it('keeps a valid GPS position and capture time', () => {
    const taken = new Date('2027-06-17T06:20:00Z');
    expect(normalizeExif({ latitude: 32.2667123, longitude: 77.3667456 }, { DateTimeOriginal: taken })).toEqual({
      lat: 32.266712,
      lng: 77.366746,
      takenAt: '2027-06-17T06:20:00.000Z',
    });
  });

  it('never trusts missing, broken or null-island positions', () => {
    for (const gps of [null, {}, { latitude: 'x', longitude: 1 }, { latitude: 91, longitude: 1 }, { latitude: 0, longitude: 0 }]) {
      const out = normalizeExif(gps as never, { DateTimeOriginal: 'not a date' });
      expect(out).toEqual({ lat: null, lng: null, takenAt: null });
    }
  });

  it('resolves to nothing found for a file without EXIF', async () => {
    const out = await readPhotoExif(new Blob(['plain text'], { type: 'text/plain' }));
    expect(out).toEqual({ lat: null, lng: null, takenAt: null });
  });
});
