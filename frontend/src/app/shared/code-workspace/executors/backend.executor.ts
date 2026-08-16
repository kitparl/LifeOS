import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { delay, catchError } from 'rxjs/operators';
import { BaseExecutor, ExecutionType } from './base.executor';
import { CodeExecutionRequest, CodeExecutionResult } from '../models/code-execution.model';

/**
 * Backend executor for server-side code execution.
 * 
 * Phase 1: Mock implementation that returns appropriate messages
 * Phase 2: Will integrate with real backend API
 * 
 * API Contract:
 * POST /api/code/execute
 * Request: { language, code, stdin?, timeoutMs? }
 * Response: { success, stdout, stderr, exitCode?, executionTimeMs?, error? }
 * 
 * Supported languages (backend execution):
 * - Java
 * - C
 * - C++
 * - C#
 * - Go
 * - Rust
 * - PHP
 */
export class BackendExecutor implements BaseExecutor {
  readonly language: string;
  readonly executionType: ExecutionType = 'backend';

  private readonly API_ENDPOINT = '/api/code/execute';
  private readonly MOCK_MODE = true; // Set to false when backend is ready

  constructor(
    private http: HttpClient,
    language: string
  ) {
    this.language = language;
  }

  /**
   * Execute code via backend API (or mock for Phase 1)
   */
  execute(request: CodeExecutionRequest): Observable<CodeExecutionResult> {
    const executionId = request.executionId || this.generateExecutionId();

    if (this.MOCK_MODE) {
      return this.mockExecute(request, executionId);
    }

    // Real backend execution (Phase 2)
    return this.http.post<CodeExecutionResult>(this.API_ENDPOINT, {
      language: request.language,
      code: request.code,
      stdin: request.stdin,
      timeoutMs: request.timeoutMs || 30000,
    }).pipe(
      catchError(error => {
        return of({
          success: false,
          stdout: '',
          stderr: '',
          error: `Backend execution failed: ${error.message}`,
          exitCode: 1,
          executionId,
        });
      })
    );
  }

  /**
   * Stop execution (send cancel request to backend)
   */
  stop(executionId: string): void {
    if (this.MOCK_MODE) {
      console.log(`Mock: Stopping execution ${executionId}`);
      return;
    }

    // Send cancel request to backend (Phase 2)
    this.http.post(`${this.API_ENDPOINT}/cancel`, { executionId }).subscribe({
      next: () => console.log(`Execution ${executionId} cancelled`),
      error: (error) => console.error(`Failed to cancel execution: ${error.message}`),
    });
  }

  /**
   * Backend is always ready (mock mode)
   */
  async isReady(): Promise<boolean> {
    return true;
  }

  /**
   * Mock execution for Phase 1
   * Returns appropriate messages indicating backend execution is not yet implemented
   */
  private mockExecute(request: CodeExecutionRequest, executionId: string): Observable<CodeExecutionResult> {
    const mockMessages: Record<string, string> = {
      java: `Mock Java Execution (Phase 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend execution for Java is not yet implemented.

Your code:
${this.truncateCode(request.code)}

Next Steps:
• Phase 2 will add containerized Java execution
• JDK 11+ with security restrictions
• CPU and memory limits enforced
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,

      c: `Mock C Execution (Phase 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend execution for C is not yet implemented.

Your code:
${this.truncateCode(request.code)}

Next Steps:
• Phase 2 will add GCC compilation and execution
• Sandboxed environment with security restrictions
• Resource limits enforced
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,

      cpp: `Mock C++ Execution (Phase 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend execution for C++ is not yet implemented.

Your code:
${this.truncateCode(request.code)}

Next Steps:
• Phase 2 will add G++ compilation and execution
• Sandboxed environment with security restrictions
• Resource limits enforced
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,

      csharp: `Mock C# Execution (Phase 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend execution for C# is not yet implemented.

Your code:
${this.truncateCode(request.code)}

Next Steps:
• Phase 2 will add .NET runtime execution
• Sandboxed environment with security restrictions
• Resource limits enforced
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,

      go: `Mock Go Execution (Phase 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend execution for Go is not yet implemented.

Your code:
${this.truncateCode(request.code)}

Next Steps:
• Phase 2 will add Go runtime execution
• Sandboxed environment with security restrictions
• Resource limits enforced
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,

      rust: `Mock Rust Execution (Phase 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend execution for Rust is not yet implemented.

Your code:
${this.truncateCode(request.code)}

Next Steps:
• Phase 2 will add Rust compilation and execution
• Sandboxed environment with security restrictions
• Resource limits enforced
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,

      php: `Mock PHP Execution (Phase 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend execution for PHP is not yet implemented.

Your code:
${this.truncateCode(request.code)}

Next Steps:
• Phase 2 will add PHP runtime execution
• Sandboxed environment with security restrictions
• Resource limits enforced
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
    };

    const message = mockMessages[request.language.toLowerCase()] || 
      `Backend execution for ${request.language} is not yet implemented.`;

    // Simulate network delay
    return of({
      success: false,
      stdout: message,
      stderr: '',
      error: 'Backend execution not implemented (Phase 1 - Mock)',
      exitCode: 0,
      executionTimeMs: 100,
      executionId,
    }).pipe(delay(500)); // 500ms delay to simulate network
  }

  /**
   * Truncate code for display in mock messages
   */
  private truncateCode(code: string, maxLines: number = 10): string {
    const lines = code.split('\n');
    if (lines.length <= maxLines) {
      return code;
    }
    return lines.slice(0, maxLines).join('\n') + `\n... (${lines.length - maxLines} more lines)`;
  }

  /**
   * Generate a unique execution ID
   */
  private generateExecutionId(): string {
    return `backend_${this.language}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Create backend executor for a specific language
   */
  static forLanguage(http: HttpClient, language: string): BackendExecutor {
    return new BackendExecutor(http, language);
  }
}
