import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { SettingsEditorSectionComponent } from './settings-editor-section.component';
import { EditorPreferencesService } from '../../core/services/editor-preferences.service';

describe('SettingsEditorSectionComponent', () => {
  let fixture: ComponentFixture<SettingsEditorSectionComponent>;
  let editorPrefs: EditorPreferencesService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsEditorSectionComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsEditorSectionComponent);
    editorPrefs = TestBed.inject(EditorPreferencesService);
    fixture.detectChanges();
  });

  it('renders Default and Vim options', () => {
    const buttons = Array.from(fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>).map(
      (button) => button.textContent?.trim(),
    );
    expect(buttons).toContain('Default');
    expect(buttons).toContain('Vim');
  });

  it('updates preference when Vim is selected', () => {
    spyOn(editorPrefs, 'setKeymap').and.callThrough();

    const vimButton = Array.from(fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>).find(
      (button) => button.textContent?.trim() === 'Vim',
    );

    vimButton?.click();
    fixture.detectChanges();

    expect(editorPrefs.setKeymap).toHaveBeenCalledWith('vim');
    expect(editorPrefs.keymap()).toBe('vim');
  });
});
