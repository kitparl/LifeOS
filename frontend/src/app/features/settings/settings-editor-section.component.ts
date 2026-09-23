import { Component, inject } from '@angular/core';
import {
  EditorKeymap,
  EditorPreferencesService,
} from '../../core/services/editor-preferences.service';

@Component({
  selector: 'app-settings-editor-section',
  standalone: true,
  template: `
    <div class="panel max-w-md space-y-2">
      <p class="form-label">Keymap</p>
      <div class="flex flex-wrap gap-2">
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
