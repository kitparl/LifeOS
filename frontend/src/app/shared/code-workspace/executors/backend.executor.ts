import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { BaseExecutor, ExecutionType } from './base.executor';
import { CodeExecutionRequest, CodeExecutionResult } from '../models/code-execution.model';

/**
 * Executor for languages that would need server-side execution
 * (Java, C, C++, C#, Go, Rust, PHP).
 *
 * The backend has no code-execution endpoint, so this returns a "not implemented yet"
 * message that echoes the user's code. Browser/WASM languages use their own executors.
 */
export class BackendExecutor implements BaseExecutor {
  readonly language: string;
  readonly executionType: ExecutionType = 'backend';

  constructor(language: string) {
    this.language = language;
  }

  execute(request: CodeExecutionRequest): Observable<CodeExecutionResult> {
    return this.mockExecute(request, request.executionId || this.generateExecutionId());
  }

  /** Nothing runs server-side, so there is nothing to cancel. */
  stop(_executionId: string): void {
    return;
  }

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

  static forLanguage(language: string): BackendExecutor {
    return new BackendExecutor(language);
  }
}
