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
});
