export const environment = {
  production: true,
  apiUrl: '/api/v1',
  /** Travel map tiles. OpenStreetMap by default; swap for a self-hosted or commercial tile server here. */
  travel: {
    tileUrl: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    tileAttribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
};
