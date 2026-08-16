import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LanguageSelectorComponent } from './language-selector.component';
import { EditorLanguage } from '../../models';

describe('LanguageSelectorComponent', () => {
  let fixture: ComponentFixture<LanguageSelectorComponent>;
  let component: LanguageSelectorComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LanguageSelectorComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(LanguageSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('lists languages and emits the selected language', () => {
    const emitted: EditorLanguage[] = [];
    component.languageChange.subscribe((l) => emitted.push(l));
    expect(fixture.nativeElement.querySelector('select[aria-label="Programming language"]')).toBeTruthy();
    component.selectedLanguageId = 'python';
    component.onLanguageChange();
    expect(emitted[0].id).toBe('python');
  });
});
