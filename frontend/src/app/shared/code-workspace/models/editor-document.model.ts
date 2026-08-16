export interface EditorDocument {
  id?: string;
  title: string;
  content: string;
  format: 'markdown' | 'code';
  language?: string;
  createdAt?: string;
  updatedAt?: string;
}
