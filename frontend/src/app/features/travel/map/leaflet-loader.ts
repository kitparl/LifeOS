import type * as Leaflet from 'leaflet';
import { ensureStylesheet } from '../../../core/utils/stylesheet';

/**
 * Leaflet is loaded on demand so it (and its CSS) only ever reaches users who open Travel.
 * The stylesheet is copied to `/leaflet/leaflet.css` by angular.json (not added to global styles).
 */
let loading: Promise<typeof Leaflet> | null = null;

export function loadLeaflet(): Promise<typeof Leaflet> {
  if (!loading) {
    ensureStylesheet('leaflet-css', 'leaflet/leaflet.css');
    loading = import('leaflet').then((mod) => ((mod as { default?: typeof Leaflet }).default ?? mod) as typeof Leaflet);
  }
  return loading;
}
