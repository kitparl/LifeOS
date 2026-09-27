import { decodePolyline, haversineM, pathLengthM } from './geo';

describe('geo', () => {
  it('decodes Google encoded polylines (documented example)', () => {
    expect(decodePolyline('_p~iF~ps|U_ulLnnqC_mqNvxq`@')).toEqual([
      [38.5, -120.2],
      [40.7, -120.95],
      [43.252, -126.453],
    ]);
    expect(decodePolyline('')).toEqual([]);
  });

  it('measures distances like the backend', () => {
    expect(haversineM([0, 0], [0, 0])).toBe(0);
    // One degree of latitude is about 111.2 km.
    expect(haversineM([0, 0], [1, 0])).toBeCloseTo(111_195, -2);
    expect(pathLengthM([[0, 0], [1, 0], [2, 0]])).toBeCloseTo(2 * 111_195, -2);
  });
});
