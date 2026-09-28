import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MapMarker, TravelMapComponent } from './travel-map.component';

const LABELS_KEY = 'lifeos-travel-map-labels';
const MARKERS: MapMarker[] = [
  { id: 'a', kind: 'place', lat: 32.24, lng: 77.19, label: '1. Kasol · Day 2 start', color: '#e95420' },
  { id: 'b', kind: 'place', lat: 32.0, lng: 77.3, label: '2. Tosh · Day 2 end', color: '#2980b9' },
];

/** Leaflet fades a closed tooltip out for 200 ms before removing its node. */
const afterFade = () => new Promise((r) => setTimeout(r, 250));

/** Leaflet is imported lazily, so the map appears some time after the first change detection. */
async function waitFor(condition: () => boolean): Promise<void> {
  for (let i = 0; i < 100 && !condition(); i++) await new Promise((r) => setTimeout(r, 20));
  expect(condition()).withContext('timed out waiting for the map').toBeTrue();
}

describe('TravelMapComponent labels', () => {
  let fixture: ComponentFixture<TravelMapComponent>;
  let host: HTMLElement;

  const openLabels = () => Array.from(host.querySelectorAll('.leaflet-tooltip')).map((t) => t.textContent);

  beforeEach(async () => {
    localStorage.removeItem(LABELS_KEY);
    TestBed.configureTestingModule({ imports: [TravelMapComponent] });
    fixture = TestBed.createComponent(TravelMapComponent);
    host = fixture.nativeElement as HTMLElement;
    host.style.height = '300px';
    document.body.appendChild(host);
    fixture.componentRef.setInput('markers', MARKERS);
    fixture.detectChanges();
    await waitFor(() => !!host.querySelector('.leaflet-container canvas'));
    fixture.detectChanges();
    await afterFade();
  });

  afterEach(() => {
    fixture.destroy();
    localStorage.removeItem(LABELS_KEY);
  });

  it('keeps every marker name open by default', () => {
    expect(openLabels()).toEqual(['1. Kasol · Day 2 start', '2. Tosh · Day 2 end']);
  });

  it('keeps names open after a re-render and the pointer passing over the pins', async () => {
    fixture.componentRef.setInput('markers', [...MARKERS]);
    fixture.detectChanges();
    const canvas = host.querySelector('canvas') as HTMLCanvasElement;
    const box = canvas.getBoundingClientRect();
    for (let x = box.left; x < box.right; x += 4) {
      for (let y = box.top; y < box.bottom; y += 20) {
        canvas.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: x, clientY: y }));
      }
    }
    canvas.dispatchEvent(new MouseEvent('mouseout', { bubbles: true, clientX: 0, clientY: 0 }));
    await afterFade();
    expect(openLabels()).toEqual(['1. Kasol · Day 2 start', '2. Tosh · Day 2 end']);
  });

  it('switches to hover-only from the Names toggle and remembers it', async () => {
    const toggle = host.querySelector('button.labels-toggle') as HTMLButtonElement;
    toggle.click();
    fixture.detectChanges();
    await afterFade();
    expect(openLabels()).toEqual([]);
    expect(localStorage.getItem(LABELS_KEY)).toBe('false');
  });
});
