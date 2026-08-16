export interface CodeExecutionRequest {
  language: string;
  code: string;
  stdin?: string;
  timeoutMs?: number;
  executionId?: string;
}

export interface CodeExecutionResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exitCode?: number;
  executionTimeMs?: number;
  error?: string;
  executionId?: string;
}
