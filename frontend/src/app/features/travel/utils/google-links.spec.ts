import { directionsUrl, openInGoogleMapsUrl, routeLinks } from './google-links';

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

  describe('routeLinks', () => {
    const points = (n: number) => Array.from({ length: n }, (_, i) => ({ lat: 30 + i, lng: 77 }));

    it('starts from the first point and keeps every point in between', () => {
      const [link] = routeLinks(points(3));
      const url = new URL(link.url);
      expect(url.searchParams.get('origin')).toBe('30.000000,77.000000');
      expect(url.searchParams.get('destination')).toBe('32.000000,77.000000');
      expect(url.searchParams.get('waypoints')).toBe('31.000000,77.000000');
      expect(url.searchParams.get('travelmode')).toBe('driving');
      expect([link.first, link.last]).toEqual([1, 3]);
    });

    it('splits a long route into parts that share their joining point, dropping nothing', () => {
      const links = routeLinks(points(25));
      expect(links.map((l) => [l.first, l.last])).toEqual([[1, 11], [11, 21], [21, 25]]);
      const second = new URL(links[1].url);
      expect(second.searchParams.get('origin')).toBe('40.000000,77.000000');
      expect(second.searchParams.get('waypoints')!.split('|').length).toBe(9);
    });

    it('merges back-to-back repeats and needs two points', () => {
      expect(routeLinks([{ lat: 1, lng: 2 }, { lat: 1, lng: 2 }])).toEqual([]);
      expect(routeLinks([])).toEqual([]);
      expect(routeLinks([{ lat: 1, lng: 2 }, { lat: 1, lng: 2 }, { lat: 3, lng: 4 }]).length).toBe(1);
    });
  });
});
