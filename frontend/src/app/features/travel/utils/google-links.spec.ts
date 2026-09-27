import { directionsUrl, openInGoogleMapsUrl } from './google-links';

describe('google-links', () => {
  it('opens a saved place by coordinates, with the Google place id when known', () => {
    const url = new URL(openInGoogleMapsUrl({ lat: 32.2667, lng: 77.3667, external_place_id: 'ChIJx' }));
    expect(url.origin + url.pathname).toBe('https://www.google.com/maps/search/');
    expect(url.searchParams.get('api')).toBe('1');
    expect(url.searchParams.get('query')).toBe('32.266700,77.366700');
    expect(url.searchParams.get('query_place_id')).toBe('ChIJx');
  });

  it('omits the place id for hand-picked spots', () => {
    const url = new URL(openInGoogleMapsUrl({ lat: 1, lng: 2 }));
    expect(url.searchParams.has('query_place_id')).toBeFalse();
  });

  it('builds directions to the last stop via the others', () => {
    const url = new URL(
      directionsUrl(
        [
          { lat: 1, lng: 1 },
          { lat: 2, lng: 2 },
          { lat: 3, lng: 3 },
        ],
        'cycling',
      )!,
    );
    expect(url.searchParams.get('destination')).toBe('3.000000,3.000000');
    expect(url.searchParams.get('waypoints')).toBe('1.000000,1.000000|2.000000,2.000000');
    expect(url.searchParams.get('travelmode')).toBe('bicycling');
  });

  it('keeps at most 9 waypoints and returns null without stops', () => {
    const stops = Array.from({ length: 15 }, (_, i) => ({ lat: i, lng: i }));
    const url = new URL(directionsUrl(stops)!);
    expect(url.searchParams.get('waypoints')!.split('|').length).toBe(9);
    expect(directionsUrl([])).toBeNull();
  });
});
