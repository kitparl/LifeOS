/**
 * Default environment (production=false).
 * Local dev: `npm start` reads backend/.env ENV=dev and uses development config.
 * Production build: replaced by environment.production.ts
 */
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  /** Travel map tiles. OpenStreetMap by default; swap for a self-hosted or commercial tile server here. */
  travel: {
    tileUrl: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    tileAttribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
};
