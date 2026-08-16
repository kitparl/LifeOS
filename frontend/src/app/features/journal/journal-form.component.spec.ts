import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of } from 'rxjs';
import { JournalFormComponent } from './journal-form.component';
import { JournalService } from './services/journal.service';
import { JournalEntry } from './models/journal.models';

const entry = (content: string): JournalEntry => ({
  id: 'j1',
  entry_date: '2026-08-16',
  entry_type: 'morning',
  title: 'Hello',
  content,
  gratitude: null,
  wins: null,
  lessons: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
});

function routeSnapshot(urlPaths: string[], id: string | null) {
  return {
    snapshot: {
      paramMap: { get: () => id },
      url: urlPaths.map((path) => ({ path })),
    },
  };
}

const testProviders = [
  provideHttpClient(),
  provideRouter([]),
  {
    provide: JournalService,
    useValue: {
      get: () => of(entry('# Hello')),
      create: () => of(entry('md')),
      update: () => of(entry('md')),
    },
  },
  {
    provide: BreakpointObserver,
    useValue: { observe: () => of({ breakpoints: {}, matches: true }) },
  },
];

describe('JournalFormComponent', () => {
  describe('new entry', () => {
    let fixture: ComponentFixture<JournalFormComponent>;
    let component: JournalFormComponent;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [JournalFormComponent],
        providers: [
          ...testProviders,
          { provide: ActivatedRoute, useValue: routeSnapshot([], null) },
        ],
      }).compileComponents();
      fixture = TestBed.createComponent(JournalFormComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
      await fixture.whenStable();
      fixture.detectChanges();
    });

    it('uses Code Workspace instead of the old markdown CVA editor', () => {
      expect(component.editorReady).toBeTrue();
      expect(fixture.nativeElement.querySelector('app-code-workspace')).toBeTruthy();
      expect(
        fixture.nativeElement.querySelector('app-markdown-editor[formControlName="content"]')
      ).toBeFalsy();
      expect(fixture.nativeElement.querySelector('[formControlName="gratitude"]')).toBeTruthy();
    });

    it('writes workspace content into the form control', () => {
      component.onContentChange('# Hello');
      expect(component.form.controls.content.value).toBe('# Hello');
    });

    it('toggles page Read without hiding gratitude', () => {
      component.onContentChange('- item');
      expect(fixture.nativeElement.querySelector('app-code-workspace')).toBeTruthy();
      component.togglePageMode();
      fixture.detectChanges();
      expect(component.previewOnly).toBeTrue();
      expect(fixture.nativeElement.querySelector('app-code-workspace')).toBeFalsy();
      expect(fixture.nativeElement.querySelector('.markdown-body')).toBeTruthy();
      expect(fixture.nativeElement.textContent).toContain('item');
      expect(fixture.nativeElement.querySelector('[formControlName="gratitude"]')).toBeTruthy();
      component.togglePageMode();
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('app-code-workspace')).toBeTruthy();
    });
  });

  describe('edit entry', () => {
    let component: JournalFormComponent;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [JournalFormComponent],
        providers: [
          ...testProviders,
          { provide: ActivatedRoute, useValue: routeSnapshot(['journal', 'j1', 'edit'], 'j1') },
        ],
      }).compileComponents();
      const fixture = TestBed.createComponent(JournalFormComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
      await fixture.whenStable();
      fixture.detectChanges();
    });

    it('loads markdown content into the editor', () => {
      expect(component.editorReady).toBeTrue();
      expect(component.editorContent).toBe('# Hello');
      expect(component.form.controls.content.value).toBe('# Hello');
    });
  });
});
