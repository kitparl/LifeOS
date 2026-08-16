import { Injectable } from '@angular/core';
import { Observable, from, of } from 'rxjs';
import { map, catchError, timeout } from 'rxjs/operators';
import { BaseExecutor, ExecutionType } from './base.executor';
import { CodeExecutionRequest, CodeExecutionResult } from '../models/code-execution.model';

declare const loadPyodide: any;

/**
 * Python executor using Pyodide WebAssembly runtime.
 * 
 * Features:
 * - Lazy loading: Pyodide is only loaded when first needed
 * - Runtime caching: After first load, execution is instant
 * - Standard library: Full Python standard library available
 * - stdin/stdout: Supports input/output streams
 */
@Injectable({
  providedIn: 'root'
})
export class PythonExecutor implements BaseExecutor {
  readonly language = 'python';
  readonly executionType: ExecutionType = 'wasm';

  private pyodide: any | null = null;
  private loading: boolean = false;
  private loadingPromise: Promise<void> | null = null;
  private readonly DEFAULT_TIMEOUT_MS = 30000; // 30 seconds (Pyodide can be slow)

  /**
   * Execute Python code using Pyodide
   */
  execute(request: CodeExecutionRequest): Observable<CodeExecutionResult> {
    const executionId = request.executionId || this.generateExecutionId();
    const timeoutMs = request.timeoutMs || this.DEFAULT_TIMEOUT_MS;
    const startTime = performance.now();

    return from(this.ensurePyodideLoaded()).pipe(
      map(() => {
        if (!this.pyodide) {
          throw new Error('Pyodide failed to load');
        }

        // Capture stdout/stderr
        let stdout = '';
        let stderr = '';

        try {
          // Set up stdout/stderr capture
          this.pyodide.runPython(`
import sys
from io import StringIO

sys.stdout = StringIO()
sys.stderr = StringIO()
`);

          // Run user code
          this.pyodide.runPython(request.code);

          // Get captured output
          stdout = this.pyodide.runPython('sys.stdout.getvalue()');
          stderr = this.pyodide.runPython('sys.stderr.getvalue()');

          // Reset stdout/stderr
          this.pyodide.runPython(`
sys.stdout = StringIO()
sys.stderr = StringIO()
`);

          const endTime = performance.now();

          return {
            success: true,
            stdout: stdout || '',
            stderr: stderr || '',
            exitCode: 0,
            executionTimeMs: Math.round(endTime - startTime),
            executionId,
          };
        } catch (error: any) {
          // Try to get stderr if available
          try {
            stderr = this.pyodide.runPython('sys.stderr.getvalue()');
          } catch (e) {
            // Ignore
          }

          const endTime = performance.now();

          return {
            success: false,
            stdout: stdout || '',
            stderr: stderr || error.message || '',
            error: error.message,
            exitCode: 1,
            executionTimeMs: Math.round(endTime - startTime),
            executionId,
          };
        }
      }),
      timeout(timeoutMs),
      catchError(error => {
        const endTime = performance.now();
        if (error?.name === 'TimeoutError') {
          return of({
            success: false,
            stdout: '',
            stderr: '',
            error: `Execution timeout exceeded (${timeoutMs}ms)`,
            exitCode: 124,
            executionTimeMs: Math.round(endTime - startTime),
            executionId,
          });
        }
        return from([{
          success: false,
          stdout: '',
          stderr: '',
          error: `Failed to load Pyodide: ${error.message}`,
          exitCode: 1,
          executionTimeMs: Math.round(endTime - startTime),
          executionId,
        }]);
      })
    );
  }

  /**
   * Stop execution (Pyodide doesn't support this directly)
   */
  stop(executionId: string): void {
    // Pyodide doesn't provide a way to interrupt execution
    // This would require running Pyodide in a Web Worker
    console.warn('Python execution cannot be stopped once started');
  }

  /**
   * Check if Pyodide is ready
   */
  async isReady(): Promise<boolean> {
    if (this.pyodide) {
      return true;
    }
    if (this.loading) {
      return false;
    }
    return false;
  }

  /**
   * Load Pyodide runtime if not already loaded
   */
  private async ensurePyodideLoaded(): Promise<void> {
    if (this.pyodide) {
      return;
    }

    if (this.loadingPromise) {
      return this.loadingPromise;
    }

    this.loading = true;
    this.loadingPromise = this.loadPyodide();

    try {
      await this.loadingPromise;
    } finally {
      this.loading = false;
    }
  }

  /**
   * Load Pyodide from CDN
   */
  private async loadPyodide(): Promise<void> {
    try {
      // Load Pyodide from CDN
      if (typeof loadPyodide === 'undefined') {
        // Load Pyodide script dynamically
        await this.loadPyodideScript();
      }

      this.pyodide = await loadPyodide({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/',
      });

      console.log('Pyodide loaded successfully');
    } catch (error) {
      console.error('Failed to load Pyodide:', error);
      throw error;
    }
  }

  /**
   * Dynamically load Pyodide script
   */
  private loadPyodideScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js';
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Pyodide script'));
      document.head.appendChild(script);
    });
  }

  /**
   * Generate a unique execution ID
   */
  private generateExecutionId(): string {
    return `py_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get loading status for UI
   */
  isLoading(): boolean {
    return this.loading;
  }
}
