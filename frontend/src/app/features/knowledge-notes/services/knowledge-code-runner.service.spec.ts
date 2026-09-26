import { TestBed } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { CodeExecutionService } from '../../../shared/code-workspace/services/code-execution.service';
import { CodeExecutionResult } from '../../../shared/code-workspace/models/code-execution.model';
import { CodeBlock } from '../models/knowledge-notes.models';
import { KnowledgeCodeRunnerService } from './knowledge-code-runner.service';

const block = (id: string, code: string, language = 'py'): CodeBlock => ({
  id,
  language,
  code,
  lineStart: 1,
  lineEnd: 3,
});

describe('KnowledgeCodeRunnerService', () => {
  let runner: KnowledgeCodeRunnerService;
  let execute: jasmine.Spy;

  beforeEach(() => {
    execute = jasmine.createSpy('execute');
    TestBed.configureTestingModule({
      providers: [
        KnowledgeCodeRunnerService,
        { provide: CodeExecutionService, useValue: { execute } },
      ],
    });
    runner = TestBed.inject(KnowledgeCodeRunnerService);
  });

  it('runs the block with a normalized language and section-scoped id', () => {
    execute.and.returnValue(of({ success: true, stdout: '1', stderr: '', exitCode: 0 }));
    const target = block('b1', 'print(1)');
    runner.run('s1', target);
    expect(execute).toHaveBeenCalledWith({
      language: 'python',
      code: 'print(1)',
      executionId: 's1_b1',
    });
    expect(runner.lastResult()?.stdout).toBe('1');
    expect(runner.runningBlockId()).toBeNull();
    expect(target.executionResult?.output).toBe('1');
  });

  it('ignores a second run while one is in flight', () => {
    const pending = new Subject<CodeExecutionResult>();
    execute.and.returnValue(pending);
    runner.run('s1', block('b1', 'a'));
    runner.run('s1', block('b2', 'b'));
    expect(execute).toHaveBeenCalledTimes(1);
    expect(runner.runningBlockId()).toBe('b1');
  });

  it('does nothing when run is disabled', () => {
    runner.setEnabled(false);
    runner.run('s1', block('b1', 'a'));
    expect(execute).not.toHaveBeenCalled();
  });

  it('stores a failed result when execution errors', () => {
    execute.and.returnValue(throwError(() => new Error('boom')));
    runner.run('s1', block('b1', 'a'));
    expect(runner.lastResult()).toEqual(
      jasmine.objectContaining({ success: false, error: 'boom' })
    );
    expect(runner.runningBlockId()).toBeNull();
  });
});
