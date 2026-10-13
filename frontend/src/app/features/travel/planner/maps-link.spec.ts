import { isShortMapsLink, looksLikeLink, parseMapsLink } from './maps-link';

describe('maps-link', () => {
  it('reads the place and exact pin from a shared Google Maps place link', () => {
    expect(parseMapsLink('https://www.google.com/maps/place/Hampta+Pass/@32.2667,77.3667,14z/data=!3d32.27!4d77.37')).toEqual({
      name: 'Hampta Pass',
      lat: 32.27,
      lng: 77.37,
      google_place_id: null,
    });
  });

  it('reads search links with coordinates and a place id', () => {
    expect(parseMapsLink('https://www.google.com/maps/search/?api=1&query=15.5,73.8&query_place_id=ChIJgoa')).toEqual({
      name: null,
      lat: 15.5,
      lng: 73.8,
      google_place_id: 'ChIJgoa',
    });
    expect(parseMapsLink('https://maps.google.co.in/maps?q=Baga+Beach')?.name).toBe('Baga Beach');
  });

  it('ignores links that are not Google Maps', () => {
    expect(parseMapsLink('https://evil.example.com/maps/@1,2,3z')).toBeNull();
    expect(parseMapsLink('not a link')).toBeNull();
  });

  it('spots short links from the Maps app and anything link-shaped', () => {
    expect(isShortMapsLink('https://maps.app.goo.gl/AbC123')).toBeTrue();
    expect(isShortMapsLink('https://goo.gl/maps/AbC123')).toBeTrue();
    expect(isShortMapsLink('http://maps.app.goo.gl/AbC123')).toBeFalse();
    expect(looksLikeLink(' https://x.example ')).toBeTrue();
    expect(looksLikeLink('Lunch at the lake')).toBeFalse();
  });
});
