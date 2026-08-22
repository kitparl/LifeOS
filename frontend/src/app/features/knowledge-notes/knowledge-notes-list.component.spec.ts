import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { KnowledgeNotesListComponent } from './knowledge-notes-list.component';
import { KnowledgeNotesService } from './services/knowledge-notes.service';
import { KnowledgeSubjectListItem } from './models/knowledge-notes.models';

const subjects: KnowledgeSubjectListItem[] = [
  {
    id: 'sub1',
    title: 'AI Class',
    description: 'adfas',
    icon: '📘',
    order_index: 0,
    chapter_count: 1,
    section_count: 1,
    updated_at: new Date().toISOString(),
  },
];

describe('KnowledgeNotesListComponent', () => {
  let fixture: ComponentFixture<KnowledgeNotesListComponent>;
  let component: KnowledgeNotesListComponent;
  let notes: {
    listSubjects: jasmine.Spy;
    updateSubject: jasmine.Spy;
    search: jasmine.Spy;
    createSubject: jasmine.Spy;
  };

  beforeEach(async () => {
    notes = {
      listSubjects: jasmine.createSpy('listSubjects').and.returnValue(of(structuredClone(subjects))),
      updateSubject: jasmine.createSpy('updateSubject').and.returnValue(of({})),
      search: jasmine.createSpy('search').and.returnValue(of([])),
      createSubject: jasmine.createSpy('createSubject').and.returnValue(of({ id: 'new' })),
    };

    await TestBed.configureTestingModule({
      imports: [KnowledgeNotesListComponent],
      providers: [
        provideHttpClient(),
        provideRouter([]),
        { provide: KnowledgeNotesService, useValue: notes },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(KnowledgeNotesListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('renders subject cards with title and description', () => {
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('AI Class');
    expect(text).toContain('adfas');
  });

  it('saves inline title edits', () => {
    component.startEdit('title', 'sub1', new MouseEvent('dblclick', { bubbles: true }));
    fixture.detectChanges();
    const input = fixture.nativeElement.querySelector('[aria-label="Edit subject title"]') as HTMLInputElement;
    expect(input).toBeTruthy();
    input.value = 'AI Masterclass';
    input.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    expect(notes.updateSubject).toHaveBeenCalledWith('sub1', { title: 'AI Masterclass' });
  });

  it('saves inline description edits', () => {
    const desc = (Array.from(fixture.nativeElement.querySelectorAll('p')) as HTMLElement[]).find((el) =>
      el.textContent?.includes('adfas')
    );
    expect(desc).toBeTruthy();
    desc!.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    fixture.detectChanges();
    const textarea = fixture.nativeElement.querySelector(
      '[aria-label="Edit subject description"]'
    ) as HTMLTextAreaElement;
    textarea.value = 'AI Masterclass';
    textarea.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    expect(notes.updateSubject).toHaveBeenCalledWith('sub1', { description: 'AI Masterclass' });
  });
});
