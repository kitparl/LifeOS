/// <reference lib="webworker" />

interface ExecutionMessage {
  type: 'execute';
  code: string;
  executionId: string;
  timeoutMs?: number;
}

interface ResultMessage {
  type: 'result' | 'error';
  executionId: string;
  stdout?: string;
  stderr?: string;
  error?: string;
  exitCode?: number;
  executionTimeMs?: number;
}

// Capture console output
const consoleOutput: string[] = [];
const consoleErrors: string[] = [];

// Override console methods to capture output
const originalConsole = {
  log: console.log,
  info: console.info,
  warn: console.warn,
  error: console.error,
};

console.log = (...args: any[]) => {
  consoleOutput.push(args.map(arg => String(arg)).join(' '));
  originalConsole.log(...args);
};

console.info = (...args: any[]) => {
  consoleOutput.push(args.map(arg => String(arg)).join(' '));
  originalConsole.info(...args);
};

console.warn = (...args: any[]) => {
  consoleErrors.push('[WARN] ' + args.map(arg => String(arg)).join(' '));
  originalConsole.warn(...args);
};

console.error = (...args: any[]) => {
  consoleErrors.push('[ERROR] ' + args.map(arg => String(arg)).join(' '));
  originalConsole.error(...args);
};

addEventListener('message', ({ data }: MessageEvent<ExecutionMessage>) => {
  if (data.type === 'execute') {
    const startTime = performance.now();
    
    // Clear previous output
    consoleOutput.length = 0;
    consoleErrors.length = 0;

    try {
      // Execute code using Function constructor (safer than eval)
      // The code runs in the worker's global scope, isolated from the main window
      const func = new Function(data.code);
      const result = func();

      // If the result is a promise, wait for it
      if (result instanceof Promise) {
        result
          .then(() => {
            const endTime = performance.now();
            postMessage({
              type: 'result',
              executionId: data.executionId,
              stdout: consoleOutput.join('\n'),
              stderr: consoleErrors.join('\n'),
              exitCode: 0,
              executionTimeMs: Math.round(endTime - startTime),
            } as ResultMessage);
          })
          .catch((error: Error) => {
            const endTime = performance.now();
            postMessage({
              type: 'error',
              executionId: data.executionId,
              stdout: consoleOutput.join('\n'),
              stderr: consoleErrors.join('\n') + '\n' + error.message,
              error: error.message,
              exitCode: 1,
              executionTimeMs: Math.round(endTime - startTime),
            } as ResultMessage);
          });
      } else {
        // Synchronous execution completed
        const endTime = performance.now();
        postMessage({
          type: 'result',
          executionId: data.executionId,
          stdout: consoleOutput.join('\n'),
          stderr: consoleErrors.join('\n'),
          exitCode: 0,
          executionTimeMs: Math.round(endTime - startTime),
        } as ResultMessage);
      }
    } catch (error: any) {
      const endTime = performance.now();
      postMessage({
        type: 'error',
        executionId: data.executionId,
        stdout: consoleOutput.join('\n'),
        stderr: consoleErrors.join('\n') + '\n' + error.message,
        error: error.message,
        exitCode: 1,
        executionTimeMs: Math.round(endTime - startTime),
      } as ResultMessage);
    }
  }
});

// Handle timeout by listening for termination
// The parent will terminate the worker if execution exceeds timeout
