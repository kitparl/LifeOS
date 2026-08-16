import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { of } from 'rxjs';
import { JavaScriptExecutor } from './javascript.executor';
import { PythonExecutor } from './python.executor';
import { SqlExecutor } from './sql.executor';

describe('Executors', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({});
  });
  describe('JavaScriptExecutor', () => {
    let executor: JavaScriptExecutor;

    beforeEach(() => {
      executor = TestBed.inject(JavaScriptExecutor);
    });

    afterEach(() => {
      executor.destroy();
    });

    it('times out isolated worker execution and never uses eval', fakeAsync(() => {
      expect((executor.execute.toString() + JavaScriptExecutor.toString()).includes('eval(')).toBeFalse();

      (window as unknown as { Worker: typeof Worker }).Worker = class MockWorker {
        onmessage: ((ev: MessageEvent) => void) | null = null;
        onerror: ((ev: ErrorEvent) => void) | null = null;
        constructor(_url?: string | URL, _opts?: WorkerOptions) {}
        postMessage(): void {}
        terminate(): void {}
        addEventListener(): void {}
        removeEventListener(): void {}
        dispatchEvent(): boolean { return false; }
      } as unknown as typeof Worker;

      let result: { error?: string; exitCode?: number } | undefined;
      executor.execute({ language: 'javascript', code: 'while(true){}', timeoutMs: 30 }).subscribe((r) => {
        result = r;
      });
      tick(30);
      expect(result?.exitCode).toBe(124);
      expect(result?.error).toContain('timeout');
    }));
  });

  describe('PythonExecutor', () => {
    it('enforces a 30s default timeout when the runtime never becomes ready', fakeAsync(() => {
      const executor = TestBed.inject(PythonExecutor);
      spyOn(executor as unknown as { ensurePyodideLoaded: () => Promise<void> }, 'ensurePyodideLoaded')
        .and.returnValue(new Promise(() => undefined));
      let result: { exitCode?: number } | undefined;
      executor.execute({ language: 'python', code: 'print(1)', timeoutMs: 40 }).subscribe((r) => {
        result = r;
      });
      tick(40);
      expect(result?.exitCode).toBe(124);
    }));
  });

  describe('SqlExecutor', () => {
    it('enforces a 10s-class timeout when SQLite never initializes', fakeAsync(() => {
      const executor = TestBed.inject(SqlExecutor);
      spyOn(executor as unknown as { ensureSqlInitialized: () => Promise<void> }, 'ensureSqlInitialized')
        .and.returnValue(new Promise(() => undefined));
      let result: { exitCode?: number } | undefined;
      executor.execute({ language: 'sql', code: 'SELECT 1', timeoutMs: 40 }).subscribe((r) => {
        result = r;
      });
      tick(40);
      expect(result?.exitCode).toBe(124);
    }));
  });
});
