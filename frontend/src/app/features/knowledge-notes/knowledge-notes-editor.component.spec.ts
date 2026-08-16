import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { KnowledgeNotesEditorComponent } from './knowledge-notes-editor.component';
import { KnowledgeNotesService } from './services/knowledge-notes.service';
import { CodeExecutionService } from '../../shared/code-workspace/services/code-execution.service';
import { FilesService } from '../files/services/files.service';
import { KnowledgeSection } from './models/knowledge-notes.models';

const section = (content: string): KnowledgeSection => ({
  id: 's1',
  chapter_id: 'c1',
  title: 'Note',
  content,
  order_index: 0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
});

class NotesStub {
  parseCodeBlocks(md: string) {
    const blocks = [];
    const re = /```(\w+)\n([\s\S]*?)```/g;
    let match: RegExpExecArray | null;
    while ((match = re.exec(md))) {
      blocks.push({
        id: match[1],
        language: match[1],
        code: match[2],
        lineStart: 1,
        lineEnd: 2,
      });
    }
    return blocks;
  }
  enrichSection(s: KnowledgeSection) {
    return { ...s, format: 'markdown' as const };
  }
  updateSection() {
    return of(section('saved'));
  }
}

describe('KnowledgeNotesEditorComponent', () => {
  let fixture: ComponentFixture<KnowledgeNotesEditorComponent>;
  let component: KnowledgeNotesEditorComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [KnowledgeNotesEditorComponent],
      providers: [
        provideHttpClient(),
        { provide: KnowledgeNotesService, useClass: NotesStub },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(KnowledgeNotesEditorComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('section', section('```javascript\nconsole.log(1)\n```'));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('shows a Run button for executable fences', () => {
    expect(component.executableBlocks.length).toBeGreaterThan(0);
    expect(fixture.nativeElement.textContent).toContain('Run javascript');
  });

  it('executes a block and keeps the result', fakeAsync(() => {
    const execution = TestBed.inject(CodeExecutionService);
    spyOn(execution, 'execute').and.returnValue(
      of({ success: true, stdout: '1', stderr: '', exitCode: 0 })
    );
    component.onRunCode(component.executableBlocks[0]);
    tick();
    expect(component.lastResult?.stdout).toBe('1');
  }));

  it('hides the output panel when cleared', () => {
    component.lastResult = { success: true, stdout: '1', stderr: '', exitCode: 0 };
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-code-output')).toBeTruthy();
    component.clearOutput();
    fixture.detectChanges();
    expect(component.lastResult).toBeNull();
    expect(fixture.nativeElement.querySelector('app-code-output')).toBeFalsy();
  });

  it('shows Python enabled status and can disable run', () => {
    expect(fixture.nativeElement.textContent).toContain('Python enabled');
    component.executionEnabled = false;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Python disabled');
    expect(fixture.nativeElement.textContent).toContain('Enable');
  });

  it('asks the parent to save instead of patching the section itself', () => {
    const notes = TestBed.inject(KnowledgeNotesService) as unknown as NotesStub;
    spyOn(notes, 'updateSection').and.callThrough();
    const requested = jasmine.createSpy('saveRequested');
    component.saveRequested.subscribe(requested);
    component.onSave({
      id: 's1',
      title: 'Note',
      content: 'edited',
      format: 'markdown',
      language: 'markdown',
    });
    expect(requested).toHaveBeenCalled();
    expect(notes.updateSection).not.toHaveBeenCalled();
  });

  it('loads blank content when switching to a new section', async () => {
    fixture.componentRef.setInput(
      'section',
      section('')
    );
    fixture.componentRef.setInput('section', {
      ...section(''),
      id: 's-new',
    });
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(component.editorContent).toBe('');
  });

  it('uploads pasted files against the section and inserts markdown', async () => {
    const files = TestBed.inject(FilesService);
    spyOn(files, 'upload').and.returnValue(
      of({
        id: 'f1',
        filename: 'shot.png',
        content_type: 'image/png',
        size_bytes: 4,
        storage_backend: 'local',
        url: '/api/v1/files/f1/content',
        module: 'knowledge_notes',
        entity_id: 's1',
        created_at: new Date().toISOString(),
      })
    );
    const insert = jasmine.createSpy('insertAtCursor');
    component.workspace = { insertAtCursor: insert } as never;
    await component.onFilesPasted([new File(['x'], 'shot.png', { type: 'image/png' })]);
    expect(files.upload).toHaveBeenCalledWith(jasmine.any(File), 'knowledge_notes', 's1');
    expect(insert).toHaveBeenCalledWith('![shot.png](/api/v1/files/f1/content)');
  });

  it('inserts a link for non-image pastes', async () => {
    const files = TestBed.inject(FilesService);
    spyOn(files, 'upload').and.returnValue(
      of({
        id: 'f2',
        filename: 'notes.pdf',
        content_type: 'application/pdf',
        size_bytes: 4,
        storage_backend: 'local',
        url: '/api/v1/files/f2/content',
        module: 'knowledge_notes',
        entity_id: 's1',
        created_at: new Date().toISOString(),
      })
    );
    const insert = jasmine.createSpy('insertAtCursor');
    component.workspace = { insertAtCursor: insert } as never;
    await component.onFilesPasted([new File(['x'], 'notes.pdf', { type: 'application/pdf' })]);
    expect(insert).toHaveBeenCalledWith('[notes.pdf](/api/v1/files/f2/content)');
  });
});
