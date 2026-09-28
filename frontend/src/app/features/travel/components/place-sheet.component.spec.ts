import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PlaceSheetComponent, PlaceSheetSubmit } from './place-sheet.component';

describe('PlaceSheetComponent', () => {
  let fixture: ComponentFixture<PlaceSheetComponent>;
  let component: PlaceSheetComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [PlaceSheetComponent] });
    fixture = TestBed.createComponent(PlaceSheetComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('open', true);
    fixture.componentRef.setInput('point', { lat: 32.2667, lng: 77.3667 });
  });

  it('falls back to coordinates only and needs a typed name', () => {
    fixture.componentRef.setInput('lookup', { result: null, fallback_reason: 'missing_credential' });
    fixture.detectChanges();
    const text = document.body.textContent ?? '';
    expect(text).toContain('no Google Maps key');
    expect(component.canSubmit()).toBeFalse();

    const emitted: PlaceSheetSubmit[] = [];
    component.submitted.subscribe((e) => emitted.push(e));
    component.name = '  Secret lake  ';
    component.submit('wishlist');
    expect(emitted).toEqual([
      {
        intent: 'wishlist',
        place: jasmine.objectContaining({
          name: 'Secret lake',
          lat: 32.2667,
          lng: 77.3667,
          external_place_id: null,
          status: 'wishlist',
        }),
      },
    ]);
  });

  it('pre-fills a geocoded result and keeps its Google id', () => {
    fixture.componentRef.setInput('lookup', {
      result: {
        name: 'Hampta Pass',
        address: 'Himachal Pradesh, India',
        country: 'India',
        region: 'Himachal Pradesh',
        city: null,
        lat: 32.2667,
        lng: 77.3667,
        external_place_id: 'ChIJhampta',
      },
      fallback_reason: null,
    });
    fixture.detectChanges();
    expect(component.name).toBe('Hampta Pass');
    const emitted: PlaceSheetSubmit[] = [];
    component.submitted.subscribe((e) => emitted.push(e));
    component.submit('save');
    expect(emitted[0].place.external_place_id).toBe('ChIJhampta');
    expect(emitted[0].place.region).toBe('Himachal Pradesh');
  });

  it('offers only "Add to trip" when opened from a trip', () => {
    fixture.componentRef.setInput('tripOnly', true);
    fixture.componentRef.setInput('lookup', { result: null, fallback_reason: null });
    fixture.detectChanges();
    const labels = Array.from(document.querySelectorAll('button')).map((b) => b.textContent?.trim() ?? '');
    expect(labels).toContain('🧳 Add to trip');
    expect(labels).not.toContain('Save Place');
    expect(labels).not.toContain('❤️ Add to Travel Wishlist');
  });

  it('does not submit while the lookup is still running', () => {
    fixture.componentRef.setInput('loading', true);
    component.name = 'Anything';
    fixture.detectChanges();
    expect(component.canSubmit()).toBeFalse();
  });

  it('starts every new point with default category and status (no carry-over)', () => {
    fixture.componentRef.setInput('lookup', { result: null, fallback_reason: 'missing_credential' });
    fixture.detectChanges();
    component.category = 'trek';
    component.status = 'visited';
    fixture.componentRef.setInput('point', { lat: 1, lng: 2 });
    fixture.componentRef.setInput('lookup', { result: null, fallback_reason: 'missing_credential' });
    fixture.detectChanges();
    expect(component.category).toBe('other');
    expect(component.status).toBe('wishlist');
  });
});
