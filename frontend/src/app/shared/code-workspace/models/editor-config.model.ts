export interface EditorConfig {
  language?: string;
  theme?: 'light' | 'dark';
  readOnly?: boolean;
  lineNumbers?: boolean;
  lineWrapping?: boolean;
  tabSize?: number;
  indentWithTabs?: boolean;
  placeholder?: string;
}
