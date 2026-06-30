export interface CommandPaletteItem {
  id: string;
  label: string;
  group: string;
  route?: string;
  action?: () => void;
  disabled?: boolean;
  hint?: string;
}
