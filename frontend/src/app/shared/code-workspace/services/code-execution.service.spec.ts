import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { of, throwError } from 'rxjs';
import { CodeExecutionService } from './code-execution.service';
import { JavaScriptExecutor } from '../executors/javascript.executor';
import { PythonExecutor } from '../executors/python.executor';
import { SqlExecutor } from '../executors/sql.executor';
import { CodeExecutionResult } from '../models/code-execution.model';

const ok = (overrides: Partial<CodeExecutionResult> = {}): CodeExecutionResult => ({
  success: true,
  stdout: 'ok',
  stderr: '',
  exitCode: 0,
  ...overrides,
});

describe('CodeExecutionService', () => {
  let service: CodeExecutionService;
  let js: jasmine.SpyObj<JavaScriptExecutor>;
  let py: jasmine.SpyObj<PythonExecutor>;
  let sql: jasmine.SpyObj<SqlExecutor>;

  beforeEach(() => {
    js = jasmine.createSpyObj('JavaScriptExecutor', ['execute', 'stop', 'isReady', 'destroy']);
    py = jasmine.createSpyObj('PythonExecutor', ['execute', 'stop', 'isReady', 'isLoading']);
    sql = jasmine.createSpyObj('SqlExecutor', ['execute', 'stop', 'isReady', 'isLoading', 'resetDatabase', 'destroy']);
    (js as any).executionType = 'browser';
    (py as any).executionType = 'wasm';
    (sql as any).executionType = 'wasm';
    js.execute.and.returnValue(of(ok({ stdout: 'js' })));
    py.execute.and.returnValue(of(ok({ stdout: 'py' })));
    sql.execute.and.returnValue(of(ok({ stdout: 'sql' })));
    js.isReady.and.resolveTo(true);
    py.isReady.and.resolveTo(true);
    sql.isReady.and.resolveTo(true);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        { provide: JavaScriptExecutor, useValue: js },
        { provide: PythonExecutor, useValue: py },
        { provide: SqlExecutor, useValue: sql },
      ],
    });
    service = TestBed.inject(CodeExecutionService);
  });

  it('routes javascript, python, and sql to the matching executor', () => {
    service.execute({ language: 'javascript', code: '1' }).subscribe((r) => expect(r.stdout).toBe('js'));
    service.execute({ language: 'python', code: '1' }).subscribe((r) => expect(r.stdout).toBe('py'));
    service.execute({ language: 'sql', code: '1' }).subscribe((r) => expect(r.stdout).toBe('sql'));
    expect(js.execute).toHaveBeenCalled();
    expect(py.execute).toHaveBeenCalled();
    expect(sql.execute).toHaveBeenCalled();
  });

  it('rejects unsupported languages', (done) => {
    service.execute({ language: 'brainfuck', code: '+' }).subscribe({
      next: () => fail('expected error'),
      error: (err) => {
        expect(err.error).toContain('not supported');
        done();
      },
    });
  });

  it('propagates executor errors', (done) => {
    js.execute.and.returnValue(throwError(() => ({ success: false, error: 'boom' })));
    service.execute({ language: 'javascript', code: 'throw 1' }).subscribe({
      next: () => fail('expected error'),
      error: (err) => {
        expect(err.error).toBe('boom');
        done();
      },
    });
  });

  it('reports execution support and type', () => {
    expect(service.isExecutionSupported('javascript')).toBeTrue();
    expect(service.isExecutionSupported('markdown')).toBeFalse();
    expect(service.getExecutionType('python')).toBe('wasm');
    expect(service.getSupportedLanguages()).toContain('javascript');
  });
});
