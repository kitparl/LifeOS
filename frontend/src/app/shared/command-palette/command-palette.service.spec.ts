import { TestBed } from '@angular/core/testing';
import { CommandPaletteService } from './command-palette.service';

describe('CommandPaletteService', () => {
  let service: CommandPaletteService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CommandPaletteService);
  });

  it('should open and close', () => {
    expect(service.isOpen()).toBeFalse();
    service.open();
    expect(service.isOpen()).toBeTrue();
    service.close();
    expect(service.isOpen()).toBeFalse();
  });

  it('should filter items by query', () => {
    service.registerItems([
      { id: 'a', label: 'Dashboard', group: 'Nav' },
      { id: 'b', label: 'Profile', group: 'Nav' },
    ]);
    service.setQuery('dash');
    expect(service.filteredItems().length).toBe(1);
    expect(service.filteredItems()[0].label).toBe('Dashboard');
  });
});
