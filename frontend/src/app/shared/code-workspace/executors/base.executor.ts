import { Observable } from 'rxjs';
import { CodeExecutionRequest, CodeExecutionResult } from '../models/code-execution.model';

export type { ExecutionType } from '../models/editor-language.model';
import { ExecutionType } from '../models/editor-language.model';

/**
 * Base interface for code executors.
 * All language-specific executors must implement this interface.
 */
export interface BaseExecutor {
  /**
   * The language this executor handles
   */
  readonly language: string;

  /**
   * The execution environment type
   */
  readonly executionType: ExecutionType;

  /**
   * Execute code and return results as an Observable stream.
   * This allows for streaming output if the executor supports it.
   *
   * @param request - Execution request containing code and parameters
   * @returns Observable stream of execution results
   */
  execute(request: CodeExecutionRequest): Observable<CodeExecutionResult>;

  /**
   * Stop a running execution by its ID
   *
   * @param executionId - The ID of the execution to stop
   */
  stop(executionId: string): void;

  /**
   * Check if the executor is ready to execute code.
   * For WASM executors, this may involve loading the runtime.
   *
   * @returns Promise that resolves to true if ready, false otherwise
   */
  isReady(): Promise<boolean>;
}
