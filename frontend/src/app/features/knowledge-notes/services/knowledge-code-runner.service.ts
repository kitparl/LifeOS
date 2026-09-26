import { DestroyRef, Injectable, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CodeExecutionService } from '../../../shared/code-workspace/services/code-execution.service';
import { CodeExecutionResult } from '../../../shared/code-workspace/models/code-execution.model';
import { normalizeExecutableLanguage } from '../../../shared/code-workspace/utils/fenced-code-blocks';
import { CodeBlock } from '../models/knowledge-notes.models';

/**
 * Run state for one section (enable toggle, running block, last output).
 * Provided by the section editor so view and edit modes share it.
 */
@Injectable()
export class KnowledgeCodeRunnerService {
  private readonly execution = inject(CodeExecutionService);
  private readonly destroyRef = inject(DestroyRef);

  readonly enabled = signal(true);
  readonly runningBlockId = signal<string | null>(null);
  readonly lastResult = signal<CodeExecutionResult | null>(null);

  private readonly blockResults = new Map<string, CodeExecutionResult>();

  run(sectionId: string, block: CodeBlock): void {
    if (!this.enabled() || this.runningBlockId()) {
      return;
    }
    this.runningBlockId.set(block.id);
    this.execution
      .execute({
        language: normalizeExecutableLanguage(block.language),
        code: block.code,
        executionId: `${sectionId}_${block.id}`,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (result) => this.storeResult(block, result),
        error: (error) =>
          this.storeResult(block, {
            success: false,
            stdout: '',
            stderr: '',
            error: error?.message || 'Execution failed',
            exitCode: 1,
          }),
      });
  }

  setEnabled(enabled: boolean): void {
    this.enabled.set(enabled);
  }

  clear(): void {
    this.lastResult.set(null);
  }

  /** Called when a different section is loaded. */
  reset(): void {
    this.lastResult.set(null);
    this.runningBlockId.set(null);
    this.blockResults.clear();
  }

  private storeResult(block: CodeBlock, result: CodeExecutionResult): void {
    this.runningBlockId.set(null);
    this.lastResult.set(result);
    this.blockResults.set(block.id, result);
    block.executionResult = {
      output: result.stdout || result.stderr || '',
      error: result.success ? null : result.error || result.stderr || 'Execution failed',
      executionTime: result.executionTimeMs ?? 0,
      timestamp: new Date(),
    };
  }
}
