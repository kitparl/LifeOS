import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { KnowledgeNotesEditorComponent } from './knowledge-notes-editor.component';
import { KnowledgeNotesService } from './services/knowledge-notes.service';
import { CodeExecutionService } from '../../shared/code-workspace/services/code-execution.service';
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
  async migrateToMarkdown(s: KnowledgeSection) {
    return { ...s, format: 'markdown' as const };
  }
  updateSection() {
    return of(section('saved'));
  }
  enrichSection(s: KnowledgeSection) {
    return s;
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
});
