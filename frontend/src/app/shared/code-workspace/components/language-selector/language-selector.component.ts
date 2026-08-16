import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LanguageRegistryService } from '../../services/language-registry.service';
import { EditorLanguage } from '../../models';

@Component({
  selector: 'app-language-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="language-selector">
      <label class="language-label">Language:</label>
      <div class="selector-container">
        <select
          [(ngModel)]="selectedLanguageId"
          (ngModelChange)="onLanguageChange()"
          class="language-dropdown"
          [disabled]="disabled"
          aria-label="Programming language"
        >
          <option *ngFor="let lang of filteredLanguages" [value]="lang.id">
            {{ lang.name }} ({{ lang.extension }})
          </option>
        </select>
      </div>
    </div>
  `,
  styles: [`
    .language-selector {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem;
    }

    .language-label {
      font-weight: 500;
      font-size: 0.875rem;
      white-space: nowrap;
    }

    .selector-container {
      flex: 1;
      min-width: 150px;
    }

    .language-dropdown {
      width: 100%;
      padding: 0.5rem;
      border: 1px solid #ccc;
      border-radius: 0.25rem;
      background-color: white;
      font-size: 0.875rem;
      cursor: pointer;
    }

    .language-dropdown:focus {
      outline: none;
      border-color: #0066cc;
      box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
    }

    @media (max-width: 768px) {
      .language-selector {
        flex-direction: column;
        align-items: stretch;
      }

      .selector-container {
        width: 100%;
      }
    }
  `]
})
export class LanguageSelectorComponent implements OnInit {
  @Input() selectedLanguage = 'javascript';
  @Input() filterExecutableOnly = false;
  @Input() disabled = false;
  
  @Output() languageChange = new EventEmitter<EditorLanguage>();

  selectedLanguageId = 'javascript';
  allLanguages: EditorLanguage[] = [];
  filteredLanguages: EditorLanguage[] = [];

  constructor(private languageRegistry: LanguageRegistryService) {}

  ngOnInit(): void {
    this.allLanguages = this.languageRegistry.getAllLanguages();
    this.applyFilter();
    this.selectedLanguageId = this.selectedLanguage;
  }

  onLanguageChange(): void {
    const language = this.languageRegistry.getLanguage(this.selectedLanguageId);
    if (language) {
      this.languageChange.emit(language);
    }
  }

  private applyFilter(): void {
    if (this.filterExecutableOnly) {
      this.filteredLanguages = this.languageRegistry.getExecutableLanguages();
    } else {
      this.filteredLanguages = this.allLanguages;
    }
  }
}
