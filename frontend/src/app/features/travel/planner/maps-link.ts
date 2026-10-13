import { ResolvedLink } from '../models/share.models';

/**
 * Reading a pasted Google Maps link in the browser (full links carry the place in the URL).
 * Short links from the phone app (`maps.app.goo.gl/...`) are resolved by the backend instead.
 * Mirrors the backend parser `travel/maps_links.py`.
 */

const GOOGLE_HOST = /^(www\.|maps\.)?google\.[a-z]{2,3}(\.[a-z]{2})?$/;
const PRECISE = /!3d(-?\d{1,2}(?:\.\d+)?)!4d(-?\d{1,3}(?:\.\d+)?)/;
const VIEWPORT = /@(-?\d{1,2}(?:\.\d+)?),(-?\d{1,3}(?:\.\d+)?)/;
const LAT_LNG = /^\s*(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$/;

export function looksLikeLink(text: string): boolean {
  return /^https?:\/\/\S+$/i.test(text.trim());
}

export function isShortMapsLink(text: string): boolean {
  try {
    const url = new URL(text.trim());
    return url.protocol === 'https:' && (url.hostname === 'maps.app.goo.gl' || (url.hostname === 'goo.gl' && url.pathname.startsWith('/maps')));
  } catch {
    return false;
  }
}

function coords(lat: string, lng: string): [number, number] | null {
  const la = Number(lat);
  const ln = Number(lng);
  return Math.abs(la) <= 90 && Math.abs(ln) <= 180 ? [la, ln] : null;
}

export function parseMapsLink(text: string): ResolvedLink | null {
  let url: URL;
  try {
    url = new URL(text.trim());
  } catch {
    return null;
  }
  if (!/^https?:$/.test(url.protocol) || !GOOGLE_HOST.test(url.hostname)) return null;
  const decoded = decodeURIComponent(url.pathname.replace(/\+/g, ' ')) + '?' + url.search;

  let point: [number, number] | null = null;
  for (const pattern of [PRECISE, VIEWPORT]) {
    const match = pattern.exec(decoded);
    if (match && (point = coords(match[1], match[2]))) break;
  }
  let name: string | null = null;
  for (const key of ['q', 'query', 'destination', 'll']) {
    const value = url.searchParams.get(key)?.trim();
    if (!value) continue;
    const match = LAT_LNG.exec(value);
    if (match) point ??= coords(match[1], match[2]);
    else name ??= value.slice(0, 200);
  }
  const place = /\/place\/([^/@]+)/.exec(url.pathname);
  if (place) name = decodeURIComponent(place[1].replace(/\+/g, ' ')).trim().slice(0, 200) || name;
  const placeId = url.searchParams.get('query_place_id') ?? url.searchParams.get('place_id');
  const google_place_id = placeId && /^[A-Za-z0-9_\-:.]{1,255}$/.test(placeId) ? placeId : null;

  if (!point && !name && !google_place_id) return null;
  return { name, lat: point?.[0] ?? null, lng: point?.[1] ?? null, google_place_id };
}
