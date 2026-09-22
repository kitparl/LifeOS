import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { DocumentViewerService } from '../../../shared/document-viewer/document-viewer.service';
import { FilesService } from '../../files/services/files.service';
import { KnowledgeChapterDocumentsGroup } from '../models/knowledge-notes.models';
import { KnowledgeChapterDocumentsComponent } from './knowledge-chapter-documents.component';

const groups: KnowledgeChapterDocumentsGroup[] = [
  {
    chapter_id: 'c1',
    chapter_title: 'Caching',
    documents: [
      {
        id: 'pdf1',
        filename: 'notes.pdf',
        content_type: 'application/pdf',
        size_bytes: 2048,
        storage_backend: 'local',
        url: '/api/v1/files/pdf1/content',
        module: 'knowledge_notes',
        entity_id: 's1',
        created_at: new Date().toISOString(),
        section_id: 's1',
        section_title: 'Invalidation',
        chapter_id: 'c1',
        chapter_title: 'Caching',
      },
    ],
  },
];

describe('KnowledgeChapterDocumentsComponent', () => {
  let fixture: ComponentFixture<KnowledgeChapterDocumentsComponent>;
  let component: KnowledgeChapterDocumentsComponent;
  let files: { delete: jasmine.Spy };
  let confirm: { confirm: jasmine.Spy };
  let viewer: { open: jasmine.Spy };

  beforeEach(async () => {
    files = { delete: jasmine.createSpy('delete').and.returnValue(of(void 0)) };
    confirm = { confirm: jasmine.createSpy('confirm').and.returnValue(Promise.resolve(true)) };
    viewer = { open: jasmine.createSpy('open') };

    await TestBed.configureTestingModule({
      imports: [KnowledgeChapterDocumentsComponent],
      providers: [
        { provide: FilesService, useValue: files },
        { provide: ConfirmService, useValue: confirm },
        { provide: DocumentViewerService, useValue: viewer },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(KnowledgeChapterDocumentsComponent);
    component = fixture.componentInstance;
    component.groups = groups;
    fixture.detectChanges();
  });

  it('lists documents with view and delete actions', () => {
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Caching');
    expect(text).toContain('notes.pdf');
    expect(text).toContain('Invalidation');
    expect(fixture.nativeElement.querySelector('[data-testid="kn-chapter-document-view"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="kn-chapter-document-delete"]')).toBeTruthy();
  });

  it('opens the document viewer', () => {
    (fixture.nativeElement.querySelector('[data-testid="kn-chapter-document-view"]') as HTMLButtonElement).click();
    expect(viewer.open).toHaveBeenCalledWith({
      documentId: 'pdf1',
      fileName: 'notes.pdf',
      mimeType: 'application/pdf',
    });
  });

  it('deletes a document after confirmation', async () => {
    const removed: string[] = [];
    component.removed.subscribe((doc) => removed.push(doc.id));
    (fixture.nativeElement.querySelector('[data-testid="kn-chapter-document-delete"]') as HTMLButtonElement).click();
    await fixture.whenStable();
    expect(confirm.confirm).toHaveBeenCalled();
    expect(files.delete).toHaveBeenCalledWith('pdf1');
    expect(removed).toEqual(['pdf1']);
  });

  it('does not delete when the confirm alert is cancelled', async () => {
    confirm.confirm.and.returnValue(Promise.resolve(false));
    (fixture.nativeElement.querySelector('[data-testid="kn-chapter-document-delete"]') as HTMLButtonElement).click();
    await fixture.whenStable();
    expect(files.delete).not.toHaveBeenCalled();
  });
});
