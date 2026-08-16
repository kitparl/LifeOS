import { Injectable } from '@angular/core';
import { Observable, Subject, timer } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { BaseExecutor, ExecutionType } from './base.executor';
import { CodeExecutionRequest, CodeExecutionResult } from '../models/code-execution.model';

/**
 * JavaScript executor using Web Workers for isolated execution.
 * 
 * Security:
 * - Never uses eval() in the main window
 * - All code executes in an isolated Web Worker
 * - Workers have no access to DOM or main window variables
 * - Timeout enforcement prevents infinite loops
 */
@Injectable({
  providedIn: 'root'
})
export class JavaScriptExecutor implements BaseExecutor {
  readonly language = 'javascript';
  readonly executionType: ExecutionType = 'browser';

  private workers = new Map<string, Worker>();
  private readonly DEFAULT_TIMEOUT_MS = 10000; // 10 seconds

  /**
   * Execute JavaScript code in an isolated Web Worker
   */
  execute(request: CodeExecutionRequest): Observable<CodeExecutionResult> {
    return new Observable(observer => {
      const executionId = request.executionId || this.generateExecutionId();
      const timeoutMs = request.timeoutMs || this.DEFAULT_TIMEOUT_MS;

      // Create a new worker for this execution
      const worker = new Worker(
        new URL('../workers/javascript.worker', import.meta.url),
        { type: 'module' }
      );

      this.workers.set(executionId, worker);

      // Set up timeout
      const timeout$ = timer(timeoutMs);
      const cancel$ = new Subject<void>();

      timeout$
        .pipe(takeUntil(cancel$))
        .subscribe(() => {
          // Timeout exceeded - terminate worker
          this.stop(executionId);
          observer.next({
            success: false,
            stdout: '',
            stderr: '',
            error: `Execution timeout exceeded (${timeoutMs}ms)`,
            exitCode: 124, // Standard timeout exit code
            executionId,
          });
          observer.complete();
        });

      // Listen for results from worker
      worker.onmessage = ({ data }) => {
        cancel$.next();
        cancel$.complete();

        if (data.type === 'result') {
          observer.next({
            success: true,
            stdout: data.stdout || '',
            stderr: data.stderr || '',
            exitCode: data.exitCode || 0,
            executionTimeMs: data.executionTimeMs,
            executionId,
          });
        } else if (data.type === 'error') {
          observer.next({
            success: false,
            stdout: data.stdout || '',
            stderr: data.stderr || '',
            error: data.error,
            exitCode: data.exitCode || 1,
            executionTimeMs: data.executionTimeMs,
            executionId,
          });
        }

        // Clean up
        this.stop(executionId);
        observer.complete();
      };

      // Handle worker errors
      worker.onerror = (error) => {
        cancel$.next();
        cancel$.complete();

        observer.next({
          success: false,
          stdout: '',
          stderr: '',
          error: `Worker error: ${error.message}`,
          exitCode: 1,
          executionId,
        });

        this.stop(executionId);
        observer.complete();
      };

      // Send code to worker for execution
      worker.postMessage({
        type: 'execute',
        code: request.code,
        executionId,
        timeoutMs,
      });
    });
  }

  /**
   * Stop a running execution by terminating its worker
   */
  stop(executionId: string): void {
    const worker = this.workers.get(executionId);
    if (worker) {
      worker.terminate();
      this.workers.delete(executionId);
    }
  }

  /**
   * JavaScript executor is always ready (no runtime to load)
   */
  async isReady(): Promise<boolean> {
    return true;
  }

  /**
   * Generate a unique execution ID
   */
  private generateExecutionId(): string {
    return `js_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Clean up all workers (call on service destroy)
   */
  destroy(): void {
    this.workers.forEach(worker => worker.terminate());
    this.workers.clear();
  }
}
