/**
 * Default environment (production=true).
 * Local dev: `npm start` reads backend/.env ENV=dev and uses development config.
 * Production build: replaced by environment.production.ts
 */
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
};
