export type ExecutionType = 'browser' | 'wasm' | 'backend' | 'none';

export interface EditorLanguage {
  id: string;
  name: string;
  extension: string;
  mimeType?: string;
  supportsExecution: boolean;
  executionType: ExecutionType;
  icon?: string;
}
