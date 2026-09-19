import { TestBed } from '@angular/core/testing';
import { DevFavoritesService } from './dev-favorites.service';

describe('DevFavoritesService', () => {
  beforeEach(() => localStorage.removeItem('lifeos-dev-tools-favorites'));

  it('toggles favorites and persists tool IDs (not content) to localStorage', () => {
    const service = TestBed.inject(DevFavoritesService);
    expect(service.isFavorite('json-formatter')).toBe(false);

    service.toggle('json-formatter');
    expect(service.isFavorite('json-formatter')).toBe(true);
    expect(JSON.parse(localStorage.getItem('lifeos-dev-tools-favorites')!)).toEqual(['json-formatter']);

    service.toggle('json-formatter');
    expect(service.isFavorite('json-formatter')).toBe(false);
  });
});
