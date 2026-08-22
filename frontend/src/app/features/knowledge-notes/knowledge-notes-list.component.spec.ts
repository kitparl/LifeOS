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

  it('opens edit modal from card edit icon and saves changes', () => {
    const editBtn = fixture.nativeElement.querySelector('[aria-label="Edit subject"]') as HTMLButtonElement;
    expect(editBtn).toBeTruthy();
    editBtn.click();
    fixture.detectChanges();

    const titleInput = fixture.nativeElement.querySelector('input[formcontrolname="title"]') as HTMLInputElement;
    const iconInput = fixture.nativeElement.querySelector('input[formcontrolname="icon"]') as HTMLInputElement;
    const descInput = fixture.nativeElement.querySelector('textarea[formcontrolname="description"]') as HTMLTextAreaElement;
    expect(titleInput.value).toBe('AI Class');
    expect(iconInput.value).toBe('📘');
    expect(descInput.value).toBe('adfas');

    titleInput.value = 'AI Masterclass';
    titleInput.dispatchEvent(new Event('input'));
    iconInput.value = '🧠';
    iconInput.dispatchEvent(new Event('input'));
    descInput.value = 'Updated description';
    descInput.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    component.submitForm();
    fixture.detectChanges();

    expect(notes.updateSubject).toHaveBeenCalledWith('sub1', {
      title: 'AI Masterclass',
      icon: '🧠',
      description: 'Updated description',
    });
  });
});
