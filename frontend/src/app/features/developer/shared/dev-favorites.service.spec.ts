import { TestBed } from '@angular/core/testing';
import { DevFavoritesService } from './dev-favorites.service';
import { DEV_TOOLS_STORAGE_SCOPE } from './dev-storage-scope';

describe('DevFavoritesService', () => {
  beforeEach(() => {
    localStorage.removeItem('lifeos-dev-tools-favorites');
    localStorage.removeItem('lifeos-dev-tools-favorites-guest');
  });

  it('toggles favorites and persists tool IDs (not content) to localStorage', () => {
    const service = TestBed.inject(DevFavoritesService);
    expect(service.isFavorite('json-formatter')).toBe(false);

    service.toggle('json-formatter');
    expect(service.isFavorite('json-formatter')).toBe(true);
    expect(JSON.parse(localStorage.getItem('lifeos-dev-tools-favorites')!)).toEqual(['json-formatter']);

    service.toggle('json-formatter');
    expect(service.isFavorite('json-formatter')).toBe(false);
  });

  it('uses a separate guest key in guest scope and never touches the user key', () => {
    TestBed.configureTestingModule({ providers: [{ provide: DEV_TOOLS_STORAGE_SCOPE, useValue: 'guest' }] });
    const service = TestBed.inject(DevFavoritesService);

    service.toggle('base64');
    expect(JSON.parse(localStorage.getItem('lifeos-dev-tools-favorites-guest')!)).toEqual(['base64']);
    expect(localStorage.getItem('lifeos-dev-tools-favorites')).toBeNull();
  });
});
