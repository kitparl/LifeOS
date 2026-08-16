import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of } from 'rxjs';
import { KnowledgeSubjectComponent } from './knowledge-subject.component';
import { KnowledgeNotesService } from './services/knowledge-notes.service';
import { FilesService } from '../files/services/files.service';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import {
  KnowledgeChapter,
  KnowledgeSection,
  KnowledgeSubjectDetail,
} from './models/knowledge-notes.models';

const now = new Date().toISOString();
const subject: KnowledgeSubjectDetail = {
  id: 'sub1',
  title: 'System Design',
  description: null,
  icon: null,
  order_index: 0,
  created_at: now,
  updated_at: now,
  chapters: [
    {
      id: 'c1',
      subject_id: 'sub1',
      title: 'First',
      order_index: 0,
      sections: [
        {
          id: 's1',
          chapter_id: 'c1',
          title: 'Test',
          content: 'hello',
          order_index: 0,
          created_at: now,
          updated_at: now,
        },
      ],
    },
    {
      id: 'c2',
      subject_id: 'sub1',
      title: 'Second',
      order_index: 1,
      sections: [],
    },
  ],
};

describe('KnowledgeSubjectComponent', () => {
  let fixture: ComponentFixture<KnowledgeSubjectComponent>;
  let component: KnowledgeSubjectComponent;
  let notes: {
    getSubject: jasmine.Spy;
    parseCodeBlocks: jasmine.Spy;
    enrichSection: jasmine.Spy;
    updateSection: jasmine.Spy;
    updateChapter: jasmine.Spy;
    updateSubject: jasmine.Spy;
    createChapter: jasmine.Spy;
    createSection: jasmine.Spy;
    archiveSection: jasmine.Spy;
    restoreSection: jasmine.Spy;
    deleteSection: jasmine.Spy;
    deleteChapter: jasmine.Spy;
    deleteSubject: jasmine.Spy;
  };

  beforeEach(async () => {
    notes = {
      getSubject: jasmine.createSpy('getSubject').and.callFake(() => of(structuredClone(subject))),
      parseCodeBlocks: jasmine.createSpy('parseCodeBlocks').and.returnValue([]),
      enrichSection: jasmine.createSpy('enrichSection').and.callFake((s: unknown) => s),
      updateSection: jasmine
        .createSpy('updateSection')
        .and.returnValue(of(structuredClone(subject.chapters[0].sections[0]))),
      updateChapter: jasmine
        .createSpy('updateChapter')
        .and.returnValue(of(structuredClone(subject.chapters[0]))),
      updateSubject: jasmine.createSpy('updateSubject').and.returnValue(of(structuredClone(subject))),
      createChapter: jasmine.createSpy('createChapter').and.returnValue(
        of({
          id: 'c3',
          subject_id: 'sub1',
          title: 'Untitled',
          order_index: 2,
          sections: [],
        })
      ),
      createSection: jasmine.createSpy('createSection').and.returnValue(
        of({
          id: 's2',
          chapter_id: 'c1',
          title: 'Untitled',
          content: '',
          order_index: 1,
          created_at: now,
          updated_at: now,
        })
      ),
      archiveSection: jasmine.createSpy('archiveSection').and.callFake((id: string) =>
        of({
          ...structuredClone(subject.chapters[0].sections[0]),
          id,
          archived_at: now,
        })
      ),
      restoreSection: jasmine.createSpy('restoreSection').and.callFake((id: string) =>
        of({
          id,
          chapter_id: 'c1',
          title: 'Test',
          content: 'hello',
          order_index: 0,
          created_at: now,
          updated_at: now,
          archived_at: null,
        })
      ),
      deleteSection: jasmine.createSpy('deleteSection').and.returnValue(of(void 0)),
      deleteChapter: jasmine.createSpy('deleteChapter').and.returnValue(of(void 0)),
      deleteSubject: jasmine.createSpy('deleteSubject').and.returnValue(of(void 0)),
    };

    await TestBed.configureTestingModule({
      imports: [KnowledgeSubjectComponent],
      providers: [
        provideHttpClient(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => 'sub1' }, queryParamMap: { get: () => null } } },
        },
        { provide: KnowledgeNotesService, useValue: notes },
        {
          provide: ConfirmService,
          useValue: { confirm: () => Promise.resolve(true) },
        },
        {
          provide: FilesService,
          useValue: {
            list: () => of([]),
            upload: () => of({}),
            delete: () => of(void 0),
            tokenUrl: () => of(''),
          },
        },
        {
          provide: BreakpointObserver,
          useValue: { observe: () => of({ breakpoints: {}, matches: true }) },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(KnowledgeSubjectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('uses a breadcrumb and overflow menus instead of always-visible deletes', () => {
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Notes');
    expect(text).toContain('System Design');
    expect(text).toContain('Test');
    expect(text).toContain('Save');
    expect(fixture.nativeElement.querySelector('[aria-label="Subject actions"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[aria-label="Section actions"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[aria-label="Chapter actions"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('.btn-danger')).toBeFalsy();
  });

  it('opens subject rename and delete from the overflow menu', () => {
    (fixture.nativeElement.querySelector('[aria-label="Subject actions"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    const items = Array.from(fixture.nativeElement.querySelectorAll('.menu-item')) as HTMLButtonElement[];
    expect(items.map((el) => el.textContent?.trim())).toEqual(['Rename', 'Delete']);
  });

  it('keeps chapter rename/delete behind the chapter overflow', () => {
    component.toggleMenu('chapter:c1', new Event('click'));
    fixture.detectChanges();
    const items = Array.from(fixture.nativeElement.querySelectorAll('.menu-item')) as HTMLButtonElement[];
    expect(items.map((el) => el.textContent?.trim())).toEqual(['Rename', 'Delete']);
  });

  it('adds a chapter from the plus control and enters inline rename', () => {
    (fixture.nativeElement.querySelector('[aria-label="New chapter"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(notes.createChapter).toHaveBeenCalledWith('sub1', { title: 'Untitled' });
    expect(component.renaming()).toEqual({ kind: 'chapter', id: 'c3' });
    expect(fixture.nativeElement.querySelector('[aria-label="Rename chapter"]')).toBeTruthy();
  });

  it('adds a section from the chapter plus control', () => {
    (fixture.nativeElement.querySelector('[aria-label="New section"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(notes.createSection).toHaveBeenCalledWith('c1', { title: 'Untitled', content: '' });
    expect(component.selected()?.id).toBe('s2');
    expect(component.selected()?.content).toBe('');
    expect(component.form.controls.content.value).toBe('');
    expect(component.renaming()).toEqual({ kind: 'section', id: 's2' });
    expect(fixture.nativeElement.querySelector('[aria-label="Rename section"]')).toBeTruthy();
  });

  it('focuses the inline rename field after adding a section', async () => {
    (fixture.nativeElement.querySelector('[aria-label="New section"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    await fixture.whenStable();
    await new Promise((resolve) => setTimeout(resolve, 100));
    fixture.detectChanges();
    const input = fixture.nativeElement.querySelector('[aria-label="Rename section"]') as HTMLInputElement;
    expect(input).toBeTruthy();
    expect(document.activeElement).toBe(input);
  });

  it('numbers chapters and updates after reorder', () => {
    const chapters = Array.from(fixture.nativeElement.querySelectorAll('.kn-index--chapter')) as HTMLElement[];
    expect(chapters.map((el) => el.textContent?.trim())).toEqual(['1', '2']);
    expect(fixture.nativeElement.querySelector('.kn-index--section')).toBeFalsy();
    component.onChapterDrop({
      previousIndex: 0,
      currentIndex: 1,
      container: { data: component.subject()!.chapters, id: 'chapters' },
      previousContainer: { data: component.subject()!.chapters, id: 'chapters' },
    } as CdkDragDrop<KnowledgeChapter[]>);
    fixture.detectChanges();
    const reordered = Array.from(fixture.nativeElement.querySelectorAll('.kn-chapter__title')) as HTMLElement[];
    expect(reordered.map((el) => el.textContent?.trim())).toEqual(['Second', 'First']);
    expect(
      Array.from(
        fixture.nativeElement.querySelectorAll('.kn-index--chapter') as NodeListOf<HTMLElement>
      ).map((el) => el.textContent?.trim())
    ).toEqual(['1', '2']);
  });

  it('deletes a section from the list menu by archiving it', async () => {
    component.toggleMenu('section-row:s1', new Event('click'));
    fixture.detectChanges();
    const items = Array.from(fixture.nativeElement.querySelectorAll('.menu-item')) as HTMLButtonElement[];
    expect(items.map((el) => el.textContent?.trim())).toEqual(['Rename', 'Delete']);
    await component.deleteSection(component.subject()!.chapters[0].sections[0]);
    fixture.detectChanges();
    expect(notes.archiveSection).toHaveBeenCalledWith('s1');
    expect(notes.deleteSection).not.toHaveBeenCalled();
    expect(component.subject()!.chapters[0].sections.find((s) => s.id === 's1')).toBeUndefined();
    expect(component.archivedSections().some((s) => s.id === 's1')).toBeTrue();
    expect(fixture.nativeElement.textContent).toContain('Archived');
  });

  it('permanently deletes from the archived panel', async () => {
    await component.deleteSection(component.subject()!.chapters[0].sections[0]);
    fixture.detectChanges();
    notes.deleteSection.calls.reset();
    const archived = component.archivedSections()[0];
    await component.deletePermanently(archived);
    expect(notes.deleteSection).toHaveBeenCalledWith('s1');
  });

  it('renames a chapter on double-click commit', () => {
    const title = fixture.nativeElement.querySelector('.kn-chapter__title') as HTMLElement;
    title.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    fixture.detectChanges();
    const input = fixture.nativeElement.querySelector('[aria-label="Rename chapter"]') as HTMLInputElement;
    expect(input).toBeTruthy();
    input.value = 'Renamed';
    input.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    expect(notes.updateChapter).toHaveBeenCalledWith('c1', { title: 'Renamed' });
  });

  it('persists chapter reorder', () => {
    const chapters = component.subject()!.chapters;
    component.onChapterDrop({
      previousIndex: 0,
      currentIndex: 1,
      container: { data: chapters, id: 'chapters' },
      previousContainer: { data: chapters, id: 'chapters' },
    } as CdkDragDrop<KnowledgeChapter[]>);
    expect(component.subject()!.chapters.map((c) => c.id)).toEqual(['c2', 'c1']);
    expect(notes.updateChapter).toHaveBeenCalledWith('c2', { order_index: 0 });
    expect(notes.updateChapter).toHaveBeenCalledWith('c1', { order_index: 1 });
  });

  it('persists section reorder within a chapter', () => {
    const extra: KnowledgeSection = {
      id: 's9',
      chapter_id: 'c1',
      title: 'Other',
      content: '',
      order_index: 1,
      created_at: now,
      updated_at: now,
    };
    const list = component.subject()!.chapters[0].sections;
    list.push(extra);
    component.onSectionDrop({
      previousIndex: 0,
      currentIndex: 1,
      container: { data: list, id: 'kn-sec-c1' },
      previousContainer: { data: list, id: 'kn-sec-c1' },
    } as CdkDragDrop<KnowledgeSection[]>);
    expect(list.map((s) => s.id)).toEqual(['s9', 's1']);
    expect(notes.updateSection).toHaveBeenCalledWith('s9', { order_index: 0, chapter_id: 'c1' });
    expect(notes.updateSection).toHaveBeenCalledWith('s1', { order_index: 1, chapter_id: 'c1' });
  });

  it('shows a quiet sync state and skips Save when already synced', () => {
    expect(component.syncState()).toBe('synced');
    expect(fixture.nativeElement.textContent).toContain('Synced');
    const save = Array.from(fixture.nativeElement.querySelectorAll('button') as HTMLButtonElement[]).find(
      (el) => el.textContent?.trim() === 'Save'
    );
    expect(save?.disabled).toBeTrue();
    notes.updateSection.calls.reset();
    component.save();
    expect(notes.updateSection).not.toHaveBeenCalled();
  });

  it('saves only after the document is dirty', () => {
    notes.updateSection.calls.reset();
    component.form.controls.title.setValue('Changed title');
    fixture.detectChanges();
    expect(component.syncState()).toBe('unsaved');
    expect(fixture.nativeElement.textContent).toContain('Unsaved');
    component.save();
    expect(notes.updateSection).toHaveBeenCalledWith('s1', {
      title: 'Changed title',
      content: 'hello',
    });
    expect(component.syncState()).toBe('synced');
  });

  it('resizes the sidebar and clamps width', () => {
    component.sidebarWidth.set(256);
    component.onResizeKeydown(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
    expect(component.sidebarWidth()).toBe(272);
    component.sidebarWidth.set(180);
    component.onResizeKeydown(new KeyboardEvent('keydown', { key: 'ArrowLeft' }));
    expect(component.sidebarWidth()).toBe(180);
    component.resetSidebarWidth();
    expect(component.sidebarWidth()).toBe(256);
  });
});
