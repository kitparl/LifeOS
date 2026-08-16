import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { EditorToolbarComponent } from './editor-toolbar.component';

describe('EditorToolbarComponent', () => {
  let fixture: ComponentFixture<EditorToolbarComponent>;
  let component: EditorToolbarComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EditorToolbarComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(EditorToolbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('emits format actions and disables them when read-only', () => {
    const emitted: string[] = [];
    component.formatAction.subscribe((a) => emitted.push(a));
    fixture.debugElement.query(By.css('[aria-label="Bold"]')).nativeElement.click();
    expect(emitted).toContain('bold');

    fixture.componentRef.setInput('readOnly', true);
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('[aria-label="Bold"]')).nativeElement.disabled).toBeTrue();
  });

  it('shows stats when enabled', () => {
    fixture.componentRef.setInput('showStats', true);
    fixture.componentRef.setInput('stats', { wordCount: 3, charCount: 11, lineCount: 1 });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('3');
  });

  it('pins Edit, Split, Preview and Fullscreen on the toolbar end', () => {
    fixture.componentRef.setInput('showViewModes', true);
    fixture.detectChanges();
    const end = fixture.nativeElement.querySelector('.toolbar-end') as HTMLElement;
    expect(end).toBeTruthy();
    expect(end.querySelector('[aria-label="Edit"]')).toBeTruthy();
    expect(end.querySelector('[aria-label="Split"]')).toBeTruthy();
    expect(end.querySelector('[aria-label="Preview"]')).toBeTruthy();
    expect(end.querySelector('[aria-label="Fullscreen"]')).toBeTruthy();
  });

  it('emits viewModeChange for Preview', () => {
    const modes: string[] = [];
    component.viewModeChange.subscribe((m) => modes.push(m));
    fixture.componentRef.setInput('showViewModes', true);
    fixture.componentRef.setInput('viewMode', 'write');
    fixture.detectChanges();

    const toggle = fixture.nativeElement.querySelector(
      '[aria-label="Preview"]'
    ) as HTMLButtonElement;
    expect(toggle).toBeTruthy();
    expect(toggle.getAttribute('aria-pressed')).toBe('false');
    toggle.click();
    expect(modes).toEqual(['preview']);
  });

  it('emits viewModeChange for Split', () => {
    const modes: string[] = [];
    component.viewModeChange.subscribe((m) => modes.push(m));
    fixture.componentRef.setInput('showViewModes', true);
    fixture.componentRef.setInput('viewMode', 'write');
    fixture.detectChanges();
    (fixture.nativeElement.querySelector('[aria-label="Split"]') as HTMLButtonElement).click();
    expect(modes).toEqual(['split']);
  });

  it('shows Vertical and Horizontal only after Split is on', () => {
    const orientations: string[] = [];
    component.splitOrientationChange.subscribe((o) => orientations.push(o));
    fixture.componentRef.setInput('showViewModes', true);
    fixture.componentRef.setInput('viewMode', 'write');
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[aria-label="Vertical preview"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('[aria-label="Horizontal preview"]')).toBeNull();

    fixture.componentRef.setInput('viewMode', 'split');
    fixture.componentRef.setInput('splitOrientation', 'horizontal');
    fixture.detectChanges();

    const vertical = fixture.nativeElement.querySelector(
      '[aria-label="Vertical preview"]'
    ) as HTMLButtonElement;
    const horizontal = fixture.nativeElement.querySelector(
      '[aria-label="Horizontal preview"]'
    ) as HTMLButtonElement;
    expect(horizontal.getAttribute('aria-pressed')).toBe('true');
    expect(vertical.getAttribute('aria-pressed')).toBe('false');
    vertical.click();
    expect(orientations).toEqual(['vertical']);
  });

  it('emits fullscreenToggle and labels Esc on the exit control', () => {
    const toggled = jasmine.createSpy('fullscreen');
    component.fullscreenToggle.subscribe(toggled);
    fixture.detectChanges();
    const enter = fixture.nativeElement.querySelector('[aria-label="Fullscreen"]') as HTMLButtonElement;
    expect(enter).toBeTruthy();
    enter.click();
    expect(toggled).toHaveBeenCalled();

    fixture.componentRef.setInput('fullscreen', true);
    fixture.detectChanges();
    const exit = fixture.nativeElement.querySelector(
      '[aria-label="Exit fullscreen (Esc)"]'
    ) as HTMLButtonElement;
    expect(exit).toBeTruthy();
    expect(exit.getAttribute('title')).toContain('Esc');
  });
});
