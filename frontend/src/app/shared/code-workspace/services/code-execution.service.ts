import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { BaseExecutor } from '../executors/base.executor';
import { JavaScriptExecutor } from '../executors/javascript.executor';
import { PythonExecutor } from '../executors/python.executor';
import { SqlExecutor } from '../executors/sql.executor';
import { BackendExecutor } from '../executors/backend.executor';
import { CodeExecutionRequest, CodeExecutionResult } from '../models/code-execution.model';

/**
 * Code execution orchestration service.
 * 
 * Responsibilities:
 * - Maintain registry of language executors
 * - Route execution requests to appropriate executor
 * - Manage execution lifecycle (start, stop, timeout)
 * - Provide execution capabilities information
 * 
 * Supported Execution Types:
 * - Browser (Web Worker): JavaScript, TypeScript
 * - WASM: Python, SQL
 * - Backend (API): Java, C, C++, C#, Go, Rust, PHP
 */
@Injectable({
  providedIn: 'root'
})
export class CodeExecutionService implements OnDestroy {
  private executors = new Map<string, BaseExecutor>();

  constructor(
    private jsExecutor: JavaScriptExecutor,
    private pyExecutor: PythonExecutor,
    private sqlExecutor: SqlExecutor,
    private http: HttpClient
  ) {
    this.registerExecutors();
  }

  /**
   * Register all available executors
   */
  private registerExecutors(): void {
    // Browser executors (Web Worker)
    this.executors.set('javascript', this.jsExecutor);
    this.executors.set('typescript', this.jsExecutor); // TypeScript runs as JavaScript

    // WASM executors
    this.executors.set('python', this.pyExecutor);
    this.executors.set('sql', this.sqlExecutor);

    // Backend executors (lazy creation)
    const backendLanguages = ['java', 'c', 'cpp', 'csharp', 'go', 'rust', 'php'];
    for (const lang of backendLanguages) {
      // Create backend executors on demand
      const executor = BackendExecutor.forLanguage(this.http, lang);
      this.executors.set(lang, executor);
    }
  }

  /**
   * Execute code in the appropriate executor
   * 
   * @param request - Execution request containing language and code
   * @returns Observable stream of execution results
   */
  execute(request: CodeExecutionRequest): Observable<CodeExecutionResult> {
    const language = request.language.toLowerCase();
    const executor = this.getExecutor(language);

    if (!executor) {
      return throwError(() => ({
        success: false,
        stdout: '',
        stderr: '',
        error: `Execution not supported for language: ${request.language}`,
        exitCode: 1,
      }));
    }

    return executor.execute(request);
  }

  /**
   * Stop a running execution
   * 
   * @param executionId - The ID of the execution to stop
   * @param language - The language of the execution
   */
  stop(executionId: string, language: string): void {
    const executor = this.getExecutor(language.toLowerCase());
    if (executor) {
      executor.stop(executionId);
    }
  }

  /**
   * Get executor for a specific language
   * 
   * @param language - Programming language
   * @returns Executor instance or undefined if not supported
   */
  getExecutor(language: string): BaseExecutor | undefined {
    return this.executors.get(language.toLowerCase());
  }

  /**
   * Check if execution is supported for a language
   * 
   * @param language - Programming language
   * @returns true if execution is supported
   */
  isExecutionSupported(language: string): boolean {
    return this.executors.has(language.toLowerCase());
  }

  /**
   * Check if an executor is ready (runtime loaded)
   * 
   * @param language - Programming language
   * @returns Promise that resolves to true if ready
   */
  async isExecutorReady(language: string): Promise<boolean> {
    const executor = this.getExecutor(language.toLowerCase());
    if (!executor) {
      return false;
    }
    return executor.isReady();
  }

  /**
   * Get execution type for a language
   * 
   * @param language - Programming language
   * @returns Execution type ('browser', 'wasm', 'backend', 'none')
   */
  getExecutionType(language: string): string {
    const executor = this.getExecutor(language.toLowerCase());
    return executor?.executionType || 'none';
  }

  /**
   * Get all supported languages for execution
   * 
   * @returns Array of supported language names
   */
  getSupportedLanguages(): string[] {
    return Array.from(this.executors.keys());
  }

  /**
   * Check if Python runtime is loading
   */
  isPythonLoading(): boolean {
    return this.pyExecutor.isLoading();
  }

  /**
   * Check if SQL runtime is loading
   */
  isSqlLoading(): boolean {
    return this.sqlExecutor.isLoading();
  }

  /**
   * Reset SQL database (clear all data)
   */
  resetSqlDatabase(): void {
    this.sqlExecutor.resetDatabase();
  }

  /**
   * Clean up resources on service destroy
   */
  ngOnDestroy(): void {
    // Clean up JavaScript executor workers
    this.jsExecutor.destroy();
    
    // Clean up SQL executor database
    this.sqlExecutor.destroy();
  }
}
