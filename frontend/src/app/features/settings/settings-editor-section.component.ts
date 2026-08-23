import { Component, inject } from '@angular/core';
import {
  EditorKeymap,
  EditorPreferencesService,
} from '../../core/services/editor-preferences.service';

@Component({
  selector: 'app-settings-editor-section',
  standalone: true,
  template: `
    <div class="space-y-3">
      <p class="text-sm text-[var(--text-muted)]">
        Applies to Knowledge Notes, Journal, Writing, and other editors.
      </p>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar">Keymap</div>
        <div class="flex flex-wrap gap-2 p-3">
          @for (option of options; track option.value) {
            <button
              type="button"
              class="text-xs"
              [class.btn-primary]="editorPrefs.keymap() === option.value"
              [class.btn-secondary]="editorPrefs.keymap() !== option.value"
              (click)="setKeymap(option.value)"
            >
              {{ option.label }}
            </button>
          }
        </div>
      </div>
    </div>
  `,
})
export class SettingsEditorSectionComponent {
  readonly editorPrefs = inject(EditorPreferencesService);

  readonly options: { value: EditorKeymap; label: string }[] = [
    { value: 'default', label: 'Default' },
    { value: 'vim', label: 'Vim' },
  ];

  setKeymap(keymap: EditorKeymap): void {
    this.editorPrefs.setKeymap(keymap);
  }
}
