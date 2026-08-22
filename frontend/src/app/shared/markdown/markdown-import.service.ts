import { Injectable, inject } from '@angular/core';
import { ConfirmService } from '../confirm/confirm.service';
import { MarkdownImportChoiceService } from './markdown-import-choice.service';
import {
  hasMarkdownContent,
  mergeMarkdownContent,
  readMarkdownFile,
  suggestTitleFromImport,
  validateMarkdownFile,
} from './markdown-import';

export interface MarkdownImportResult {
  content: string;
  title?: string;
}

@Injectable({ providedIn: 'root' })
export class MarkdownImportService {
  private readonly choice = inject(MarkdownImportChoiceService);
  private readonly confirm = inject(ConfirmService);

  async importFromFile(
    file: File,
    currentContent: string,
    currentTitle = ''
  ): Promise<MarkdownImportResult | null> {
    const validationError = validateMarkdownFile(file);
    if (validationError) {
      throw new Error(validationError);
    }

    let imported: string;
    try {
      imported = await readMarkdownFile(file);
    } catch {
      throw new Error('Could not read the selected file.');
    }

    if (!imported.trim()) {
      throw new Error('The selected file is empty.');
    }

    let action: 'replace' | 'append' = 'replace';
    if (hasMarkdownContent(currentContent)) {
      const choice = await this.choice.choose(
        'This field already has content. Replace it with the imported markdown, or append the import at the end?'
      );
      if (choice === 'cancel') {
        return null;
      }
      action = choice;
    }

    const content = mergeMarkdownContent(currentContent, imported, action);
    const suggestedTitle = suggestTitleFromImport(file.name, imported, currentTitle);
    let title: string | undefined;

    if (suggestedTitle) {
      const ok = await this.confirm.confirm(
        `Use "${suggestedTitle}" as the title?`,
        'Suggest title'
      );
      if (ok) {
        title = suggestedTitle;
      }
    }

    return { content, title };
  }
}
