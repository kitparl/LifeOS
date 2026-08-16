import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CodeExecutionResult } from '../../models/code-execution.model';

/**
 * Component for displaying code execution results.
 * 
 * Features:
 * - Display stdout (standard output)
 * - Display stderr (error output) with error styling
 * - Show execution time
 * - Show exit code
 * - Clear output action
 * - Copy output action
 * - Expandable/collapsible
 */
@Component({
  selector: 'app-code-output',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './code-output.component.html',
  styleUrls: ['./code-output.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CodeOutputComponent {
  /**
   * Execution result to display
   */
  @Input() result: CodeExecutionResult | null = null;
  @Input() theme: 'light' | 'dark' | 'system' = 'light';

  /**
   * Whether output is expanded
   */
  @Input() expanded: boolean = true;

  /**
   * Maximum height for output container (in pixels)
   */
  @Input() maxHeight: number = 400;

  /**
   * Toggle expanded/collapsed state
   */
  toggleExpanded(): void {
    this.expanded = !this.expanded;
  }

  /**
   * Copy output to clipboard
   */
  async copyOutput(): Promise<void> {
    if (!this.result) return;

    const output = this.getFullOutput();
    
    try {
      await navigator.clipboard.writeText(output);
      // TODO: Show toast notification "Copied to clipboard"
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      // Fallback for older browsers
      this.fallbackCopy(output);
    }
  }

  /**
   * Clear output (emit event to parent)
   */
  clearOutput(): void {
    // This would typically emit an event to parent
    // For now, we'll just set result to null (parent should handle this)
    console.log('Clear output requested');
  }

  /**
   * Get full output text (stdout + stderr)
   */
  private getFullOutput(): string {
    if (!this.result) return '';

    let output = '';

    if (this.result.stdout) {
      output += '=== Output ===\n';
      output += this.result.stdout + '\n\n';
    }

    if (this.result.stderr) {
      output += '=== Errors ===\n';
      output += this.result.stderr + '\n\n';
    }

    if (this.result.error) {
      output += '=== Error ===\n';
      output += this.result.error + '\n\n';
    }

    if (this.result.executionTimeMs !== undefined) {
      output += `\nExecution time: ${this.result.executionTimeMs}ms\n`;
    }

    if (this.result.exitCode !== undefined) {
      output += `Exit code: ${this.result.exitCode}\n`;
    }

    return output;
  }

  /**
   * Fallback copy method for older browsers
   */
  private fallbackCopy(text: string): void {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
      document.execCommand('copy');
      // TODO: Show toast notification "Copied to clipboard"
    } catch (error) {
      console.error('Fallback copy failed:', error);
    }
    
    document.body.removeChild(textArea);
  }

  /**
   * Format execution time for display
   */
  formatExecutionTime(): string {
    if (!this.result?.executionTimeMs) return '';

    const ms = this.result.executionTimeMs;
    if (ms < 1000) {
      return `${ms}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  }

  /**
   * Get status text
   */
  getStatusText(): string {
    if (!this.result) return '';

    if (this.result.success) {
      return 'Completed successfully';
    }

    if (this.result.error) {
      return `Error: ${this.result.error}`;
    }

    if (this.result.exitCode !== 0) {
      return `Exited with code ${this.result.exitCode}`;
    }

    return 'Completed with errors';
  }

  /**
   * Get status CSS class
   */
  getStatusClass(): string {
    if (!this.result) return '';

    return this.result.success ? 'success' : 'error';
  }

  /**
   * Check if has output
   */
  hasOutput(): boolean {
    if (!this.result) return false;
    return !!(this.result.stdout || this.result.stderr || this.result.error);
  }
}
