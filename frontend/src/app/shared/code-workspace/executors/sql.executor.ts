import { Injectable } from '@angular/core';
import { Observable, from, of } from 'rxjs';
import { map, catchError, timeout } from 'rxjs/operators';
import { BaseExecutor, ExecutionType } from './base.executor';
import { CodeExecutionRequest, CodeExecutionResult } from '../models/code-execution.model';

declare const initSqlJs: any;

/**
 * SQL executor using SQLite WebAssembly.
 * 
 * Features:
 * - Full SQLite support in the browser
 * - DDL operations (CREATE, DROP, ALTER)
 * - DML operations (SELECT, INSERT, UPDATE, DELETE)
 * - Transaction support
 * - Result formatting as tables
 */
@Injectable({
  providedIn: 'root'
})
export class SqlExecutor implements BaseExecutor {
  readonly language = 'sql';
  readonly executionType: ExecutionType = 'wasm';

  private SQL: any = null;
  private db: any = null;
  private loading: boolean = false;
  private loadingPromise: Promise<void> | null = null;
  private readonly DEFAULT_TIMEOUT_MS = 10000;

  /**
   * Execute SQL code
   */
  execute(request: CodeExecutionRequest): Observable<CodeExecutionResult> {
    const executionId = request.executionId || this.generateExecutionId();
    const startTime = performance.now();

    const timeoutMs = request.timeoutMs || this.DEFAULT_TIMEOUT_MS;

    return from(this.ensureSqlInitialized()).pipe(
      map(() => {
        if (!this.db) {
          throw new Error('SQLite database not initialized');
        }

        let stdout = '';
        let stderr = '';
        let success = true;

        try {
          // Split multiple SQL statements
          const statements = this.splitSqlStatements(request.code);

          for (const statement of statements) {
            const trimmed = statement.trim();
            if (!trimmed) continue;

            try {
              // Execute the statement
              const results = this.db.exec(trimmed);

              // Format results
              if (results && results.length > 0) {
                stdout += this.formatResults(results) + '\n\n';
              } else {
                // For non-SELECT statements (INSERT, UPDATE, DELETE, etc.)
                const changes = this.db.getRowsModified();
                if (changes > 0) {
                  stdout += `Query OK, ${changes} row(s) affected\n\n`;
                } else {
                  stdout += `Query OK\n\n`;
                }
              }
            } catch (error: any) {
              stderr += `Error in statement: ${trimmed}\n${error.message}\n\n`;
              success = false;
            }
          }

          const endTime = performance.now();

          return {
            success,
            stdout: stdout.trim(),
            stderr: stderr.trim(),
            exitCode: success ? 0 : 1,
            executionTimeMs: Math.round(endTime - startTime),
            executionId,
          };
        } catch (error: any) {
          const endTime = performance.now();

          return {
            success: false,
            stdout: stdout.trim(),
            stderr: error.message,
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
          error: `Failed to initialize SQLite: ${error.message}`,
          exitCode: 1,
          executionTimeMs: Math.round(endTime - startTime),
          executionId,
        }]);
      })
    );
  }

  /**
   * Stop execution (not supported for SQL)
   */
  stop(executionId: string): void {
    console.warn('SQL execution cannot be stopped once started');
  }

  /**
   * Check if SQL.js is ready
   */
  async isReady(): Promise<boolean> {
    if (this.db) {
      return true;
    }
    if (this.loading) {
      return false;
    }
    return false;
  }

  /**
   * Ensure SQL.js is initialized
   */
  private async ensureSqlInitialized(): Promise<void> {
    if (this.db) {
      return;
    }

    if (this.loadingPromise) {
      return this.loadingPromise;
    }

    this.loading = true;
    this.loadingPromise = this.initializeSql();

    try {
      await this.loadingPromise;
    } finally {
      this.loading = false;
    }
  }

  /**
   * Initialize SQL.js
   */
  private async initializeSql(): Promise<void> {
    try {
      // Load SQL.js from CDN if not already loaded
      if (typeof initSqlJs === 'undefined') {
        await this.loadSqlJsScript();
      }

      // Initialize SQL.js
      this.SQL = await initSqlJs({
        locateFile: (file: string) => `https://cdn.jsdelivr.net/npm/sql.js@1.8.0/dist/${file}`
      });

      // Create a new database
      this.db = new this.SQL.Database();

      console.log('SQL.js initialized successfully');
    } catch (error) {
      console.error('Failed to initialize SQL.js:', error);
      throw error;
    }
  }

  /**
   * Dynamically load SQL.js script
   */
  private loadSqlJsScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/sql.js@1.8.0/dist/sql-wasm.js';
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load SQL.js script'));
      document.head.appendChild(script);
    });
  }

  /**
   * Split SQL code into individual statements
   */
  private splitSqlStatements(sql: string): string[] {
    // Simple statement splitting on semicolons
    // This doesn't handle strings with semicolons, but it's good enough for now
    return sql.split(';').map(s => s.trim()).filter(s => s.length > 0);
  }

  /**
   * Format SQL query results as a table
   */
  private formatResults(results: any[]): string {
    let output = '';

    for (const result of results) {
      const { columns, values } = result;

      if (values.length === 0) {
        output += 'Empty set\n';
        continue;
      }

      // Calculate column widths
      const columnWidths = columns.map((col: string, i: number) => {
        const maxValueLength = Math.max(
          ...values.map((row: any[]) => String(row[i] ?? 'NULL').length)
        );
        return Math.max(col.length, maxValueLength);
      });

      // Create header
      const header = columns
        .map((col: string, i: number) => col.padEnd(columnWidths[i]))
        .join(' | ');
      const separator = columnWidths
        .map((width: number) => '-'.repeat(width))
        .join('-+-');

      output += header + '\n';
      output += separator + '\n';

      // Create rows
      for (const row of values) {
        const rowStr = row
          .map((val: any, i: number) => String(val ?? 'NULL').padEnd(columnWidths[i]))
          .join(' | ');
        output += rowStr + '\n';
      }

      output += `\n${values.length} row(s) returned\n`;
    }

    return output;
  }

  /**
   * Generate a unique execution ID
   */
  private generateExecutionId(): string {
    return `sql_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get loading status for UI
   */
  isLoading(): boolean {
    return this.loading;
  }

  /**
   * Reset database (clear all data)
   */
  resetDatabase(): void {
    if (this.db) {
      this.db.close();
      this.db = new this.SQL.Database();
    }
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }
}
