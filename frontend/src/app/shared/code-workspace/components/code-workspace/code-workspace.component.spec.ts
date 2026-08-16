import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of } from 'rxjs';
import { CodeWorkspaceComponent } from './code-workspace.component';
import { CodeExecutionService } from '../../services/code-execution.service';

describe('CodeWorkspaceComponent', () => {
  let fixture: ComponentFixture<CodeWorkspaceComponent>;
  let component: CodeWorkspaceComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CodeWorkspaceComponent],
      providers: [
        provideHttpClient(),
        {
          provide: BreakpointObserver,
          useValue: {
            observe: () => of({ breakpoints: {}, matches: true }),
          },
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(CodeWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('content', '# Hi');
    fixture.componentRef.setInput('showLanguageSelector', false);
    fixture.componentRef.setInput('showRunButton', false);
    fixture.detectChanges();
  });

  afterEach(() => fixture.destroy());

  it('exposes a labeled region and accepts configuration inputs', () => {
    expect(fixture.nativeElement.getAttribute('role')).toBe('region');
    expect(fixture.nativeElement.getAttribute('aria-label')).toBe('Code workspace');
    fixture.componentRef.setInput('mode', 'code');
    fixture.componentRef.setInput('showPreview', false);
    fixture.detectChanges();
    expect(component.mode).toBe('code');
    expect(component.showPreview).toBeFalse();
  });

  it('emits contentChange after debounce', fakeAsync(() => {
    const local = TestBed.createComponent(CodeWorkspaceComponent);
    const cmp = local.componentInstance;
    local.detectChanges();
    const values: string[] = [];
    cmp.contentChange.subscribe((v) => values.push(v));
    cmp.onContentChange('next');
    tick(299);
    expect(values.length).toBe(0);
    tick(1);
    expect(values).toEqual(['next']);
    local.destroy();
  }));

  it('emits save documents', () => {
    const saved: string[] = [];
    component.save.subscribe((d) => saved.push(d.content));
    component.onContentChange('saved');
    component.onSave();
    expect(saved).toContain('saved');
  });

  it('emits run and shows output for javascript', fakeAsync(() => {
    const execution = TestBed.inject(CodeExecutionService);
    spyOn(execution, 'isExecutionSupported').and.returnValue(true);
    spyOn(execution, 'execute').and.returnValue(
      of({ success: true, stdout: '1', stderr: '', exitCode: 0 })
    );
    const runs: string[] = [];
    component.run.subscribe((r) => runs.push(r.language));
    fixture.componentRef.setInput('showRunButton', true);
    fixture.componentRef.setInput('language', 'javascript');
    component.currentLanguage = 'javascript';
    component.currentContent = 'console.log(1)';
    component.onRunCode();
    tick();
    expect(runs).toContain('javascript');
    expect(component.executionResult?.stdout).toBe('1');
  }));
});
