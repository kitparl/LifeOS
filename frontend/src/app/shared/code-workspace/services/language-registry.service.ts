import { Injectable } from '@angular/core';
import { EditorLanguage, ExecutionType } from '../models';

@Injectable({
  providedIn: 'root'
})
export class LanguageRegistryService {
  private languages: EditorLanguage[] = [
    // Web Technologies
    {
      id: 'javascript',
      name: 'JavaScript',
      extension: '.js',
      mimeType: 'text/javascript',
      supportsExecution: true,
      executionType: 'browser'
    },
    {
      id: 'typescript',
      name: 'TypeScript',
      extension: '.ts',
      mimeType: 'text/typescript',
      supportsExecution: false,
      executionType: 'none'
    },
    {
      id: 'html',
      name: 'HTML',
      extension: '.html',
      mimeType: 'text/html',
      supportsExecution: false,
      executionType: 'none'
    },
    {
      id: 'css',
      name: 'CSS',
      extension: '.css',
      mimeType: 'text/css',
      supportsExecution: false,
      executionType: 'none'
    },
    {
      id: 'json',
      name: 'JSON',
      extension: '.json',
      mimeType: 'application/json',
      supportsExecution: false,
      executionType: 'none'
    },
    // Backend Languages
    {
      id: 'python',
      name: 'Python',
      extension: '.py',
      mimeType: 'text/x-python',
      supportsExecution: true,
      executionType: 'wasm'
    },
    {
      id: 'java',
      name: 'Java',
      extension: '.java',
      mimeType: 'text/x-java',
      supportsExecution: true,
      executionType: 'backend'
    },
    {
      id: 'c',
      name: 'C',
      extension: '.c',
      mimeType: 'text/x-c',
      supportsExecution: true,
      executionType: 'backend'
    },
    {
      id: 'cpp',
      name: 'C++',
      extension: '.cpp',
      mimeType: 'text/x-c++',
      supportsExecution: true,
      executionType: 'backend'
    },
    {
      id: 'csharp',
      name: 'C#',
      extension: '.cs',
      mimeType: 'text/x-csharp',
      supportsExecution: true,
      executionType: 'backend'
    },
    {
      id: 'go',
      name: 'Go',
      extension: '.go',
      mimeType: 'text/x-go',
      supportsExecution: true,
      executionType: 'backend'
    },
    {
      id: 'rust',
      name: 'Rust',
      extension: '.rs',
      mimeType: 'text/x-rust',
      supportsExecution: true,
      executionType: 'backend'
    },
    {
      id: 'php',
      name: 'PHP',
      extension: '.php',
      mimeType: 'text/x-php',
      supportsExecution: true,
      executionType: 'backend'
    },
    // Data & Query Languages
    {
      id: 'sql',
      name: 'SQL',
      extension: '.sql',
      mimeType: 'text/x-sql',
      supportsExecution: true,
      executionType: 'wasm'
    },
    {
      id: 'yaml',
      name: 'YAML',
      extension: '.yaml',
      mimeType: 'text/x-yaml',
      supportsExecution: false,
      executionType: 'none'
    },
    {
      id: 'xml',
      name: 'XML',
      extension: '.xml',
      mimeType: 'text/xml',
      supportsExecution: false,
      executionType: 'none'
    },
    // Scripting
    {
      id: 'bash',
      name: 'Bash',
      extension: '.sh',
      mimeType: 'text/x-sh',
      supportsExecution: true,
      executionType: 'backend'
    },
    // Markdown
    {
      id: 'markdown',
      name: 'Markdown',
      extension: '.md',
      mimeType: 'text/markdown',
      supportsExecution: false,
      executionType: 'none'
    }
  ];

  private languageMap = new Map<string, EditorLanguage>();
  private extensionMap = new Map<string, EditorLanguage>();

  constructor() {
    this.buildMaps();
  }

  getAllLanguages(): EditorLanguage[] {
    return [...this.languages];
  }

  getLanguage(id: string): EditorLanguage | undefined {
    return this.languageMap.get(id.toLowerCase());
  }

  getLanguageByExtension(extension: string): EditorLanguage | undefined {
    const normalizedExt = extension.startsWith('.') ? extension : `.${extension}`;
    return this.extensionMap.get(normalizedExt);
  }

  registerLanguage(language: EditorLanguage): void {
    // Check if language already exists
    const existing = this.languageMap.get(language.id);
    if (existing) {
      console.warn(`Language '${language.id}' already registered. Overwriting.`);
    }

    this.languages.push(language);
    this.languageMap.set(language.id.toLowerCase(), language);
    this.extensionMap.set(language.extension, language);
  }

  isExecutionSupported(languageId: string): boolean {
    const language = this.getLanguage(languageId);
    return language?.supportsExecution ?? false;
  }

  getExecutionType(languageId: string): ExecutionType {
    const language = this.getLanguage(languageId);
    return language?.executionType ?? 'none';
  }

  getExecutableLanguages(): EditorLanguage[] {
    return this.languages.filter(lang => lang.supportsExecution);
  }

  searchLanguages(query: string): EditorLanguage[] {
    const lowerQuery = query.toLowerCase();
    return this.languages.filter(lang =>
      lang.name.toLowerCase().includes(lowerQuery) ||
      lang.id.toLowerCase().includes(lowerQuery) ||
      lang.extension.toLowerCase().includes(lowerQuery)
    );
  }

  private buildMaps(): void {
    this.languages.forEach(language => {
      this.languageMap.set(language.id.toLowerCase(), language);
      this.extensionMap.set(language.extension, language);
    });
  }
}
