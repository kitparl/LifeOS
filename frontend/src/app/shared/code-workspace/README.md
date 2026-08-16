# Code Workspace - Production-Ready Angular Editor

A comprehensive, reusable Markdown and multi-language code editor workspace for Angular applications with execution capabilities.

## Features

### ✅ Core Editor (Unit 1)
- CodeMirror 6 integration with lifecycle management
- Syntax highlighting for 18+ languages
- Line numbers, bracket matching, code folding
- Theme support (light/dark/system)
- Read-only mode

### ✅ Markdown Support (Unit 2)
- Live Markdown preview with debounced rendering (300ms)
- Dual sanitization (Angular DomSanitizer + DOMPurify)
- XSS protection
- Syntax highlighting for fenced code blocks
- Responsive images and tables

### ✅ Multi-Language Support (Unit 3)
- **18+ languages**: JavaScript, TypeScript, Python, Java, C, C++, C#, Go, Rust, PHP, SQL, HTML, CSS, JSON, YAML, XML, Bash, Markdown
- Language selector with filtering
- Dynamic language switching without component recreation
- Extensible language registry

### ✅ Code Execution (Unit 4)
- **JavaScript**: Web Worker sandboxed execution (never eval in main window)
- **Python**: Pyodide WebAssembly (lazy-loaded, cached)
- **SQL**: SQLite WASM with DDL/DML support
- **Backend**: Mock executor with API contract for Phase 2
- Console capture (log, info, warn, error)
- Timeout enforcement
- Execution results display

### ✅ UI Components (Unit 5)
- **EditorToolbar**: Formatting actions (Bold, Italic, Headings, Lists, Blocks, Inserts)
- **WorkspaceTabs**: Mobile navigation (Edit | Preview | Output)
- **CodeWorkspaceComponent**: Main container orchestrating all components
- Responsive layouts:
  - Desktop: Split view with resizable divider
  - Tablet: Adaptive (split or tabs)
  - Mobile: Tabs only
- Virtual keyboard handling

### ✅ Persistence & Autosave (Unit 6)
- Debounced autosave (2.5 seconds)
- IndexedDB storage via Dexie
- Draft recovery on reload
- Backend sync (queued when online)
- File import/export (.md, .txt, .js, .py, etc.)
- Copy to clipboard

## Installation

The workspace is already integrated into your Angular application. All dependencies are installed.

## Usage

### Basic Usage

```typescript
import { CodeWorkspaceComponent } from './shared/code-workspace';

@Component({
  selector: 'app-my-component',
  standalone: true,
  imports: [CodeWorkspaceComponent],
  template: `
    <app-code-workspace
      [content]="content"
      [mode]="'markdown'"
      [language]="'markdown'"
      [showPreview]="true"
      [showToolbar]="true"
      [showRunButton]="true"
      (contentChange)="onContentChange($event)"
      (run)="onRun($event)"
      (save)="onSave($event)"
    ></app-code-workspace>
  `
})
export class MyComponent {
  content = '# Hello World\n\nThis is **markdown**!';

  onContentChange(content: string) {
    console.log('Content changed:', content);
  }

  onRun(request: CodeExecutionRequest) {
    console.log('Run code:', request);
  }

  onSave(document: EditorDocument) {
    console.log('Save document:', document);
  }
}
```

### Configuration API

#### Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | `string` | `''` | Initial document content |
| `mode` | `'markdown' \| 'code' \| 'markdown-code'` | `'markdown'` | Editor mode |
| `language` | `string` | `'markdown'` | Programming language |
| `showPreview` | `boolean` | `true` | Show/hide preview panel |
| `showToolbar` | `boolean` | `true` | Show/hide toolbar |
| `showRunButton` | `boolean` | `true` | Show/hide run button |
| `showLanguageSelector` | `boolean` | `true` | Show/hide language selector |
| `showWordCount` | `boolean` | `true` | Show/hide word count |
| `showOutput` | `boolean` | `true` | Show/hide output panel |
| `enableAutosave` | `boolean` | `false` | Enable/disable autosave |
| `enableFileImport` | `boolean` | `false` | Enable/disable file import |
| `enableFileExport` | `boolean` | `false` | Enable/disable file export |
| `readOnly` | `boolean` | `false` | Read-only mode |
| `theme` | `'light' \| 'dark' \| 'system'` | `'system'` | Theme selection |

#### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `contentChange` | `EventEmitter<string>` | Emits when content changes (debounced) |
| `run` | `EventEmitter<CodeExecutionRequest>` | Emits when run button clicked |
| `save` | `EventEmitter<EditorDocument>` | Emits when save requested |

### Code Execution

#### JavaScript Example

```typescript
<app-code-workspace
  [content]="'console.log(\"Hello World\");'"
  [mode]="'code'"
  [language]="'javascript'"
  [showRunButton]="true"
  (run)="onRun($event)"
></app-code-workspace>
```

#### Python Example

```typescript
<app-code-workspace
  [content]="'print(\"Hello from Python!\")'"
  [mode]="'code'"
  [language]="'python'"
  [showRunButton]="true"
  (run)="onRun($event)"
></app-code-workspace>
```

#### SQL Example

```typescript
<app-code-workspace
  [content]="'CREATE TABLE users (id INT, name TEXT); SELECT * FROM users;'"
  [mode]="'code'"
  [language]="'sql'"
  [showRunButton]="true"
  (run)="onRun($event)"
></app-code-workspace>
```

### Autosave

```typescript
import { EditorPersistenceService } from './shared/code-workspace';

@Component({...})
export class MyComponent implements OnInit, OnDestroy {
  private contentSubject = new Subject<string>();

  constructor(private persistence: EditorPersistenceService) {}

  ngOnInit() {
    // Enable autosave
    this.persistence.enableAutosave('my-document-id', this.contentSubject);

    // Load draft
    this.loadDraft();
  }

  ngOnDestroy() {
    // Disable autosave
    this.persistence.disableAutosave('my-document-id');
  }

  async loadDraft() {
    const draft = await this.persistence.loadDraft('my-document-id');
    if (draft) {
      this.content = draft;
    }
  }

  onContentChange(content: string) {
    this.contentSubject.next(content);
  }
}
```

## Architecture

### Component Hierarchy

```
CodeWorkspaceComponent (Container)
├── EditorToolbarComponent
├── WorkspaceTabsComponent (Mobile Only)
├── MarkdownEditorComponent
│   └── CodeMirror 6 Integration
├── MarkdownPreviewComponent
├── CodeOutputComponent
└── LanguageSelectorComponent
```

### Service Layer

- **EditorService**: CodeMirror lifecycle management
- **MarkdownService**: Markdown parsing and sanitization
- **CodeExecutionService**: Execution orchestration
- **LanguageRegistryService**: Language configuration
- **EditorPersistenceService**: Autosave and draft management

### Executor Architecture

- **BaseExecutor**: Abstract interface
- **JavaScriptExecutor**: Web Worker sandboxed execution
- **PythonExecutor**: Pyodide WASM lazy-loading
- **SqlExecutor**: SQLite WASM
- **BackendExecutor**: API contract + mock

## Security

### XSS Protection (Multi-Layer)
1. **Input Validation**: Validate before processing
2. **Angular DomSanitizer**: Sanitize before binding
3. **DOMPurify**: Additional sanitization layer
4. **CSP Headers**: Content Security Policy

### Code Execution Security
- **JavaScript**: Web Worker isolation (never eval in main window)
- **Python**: WASM sandboxing
- **SQL**: Sandboxed SQLite WASM
- **Timeout enforcement**: Prevent infinite loops
- **Resource limits**: CPU and memory constraints

## Performance

- **Lazy loading**: Language packages and runtimes loaded on demand
- **Debouncing**: Autosave (2.5s), Preview updates (300ms)
- **OnPush change detection**: Efficient rendering
- **Virtual scrolling**: CodeMirror built-in viewport optimization

## Responsive Design

### Breakpoints
- **Mobile**: 0-767px (Tabs)
- **Tablet**: 768-1023px (Adaptive)
- **Desktop**: 1024px+ (Split view)

### Virtual Keyboard Handling
- Modern CSS viewport units (dvh)
- Cursor visibility when keyboard open
- Layout adjustments

## Supported Languages

| Language | Execution | Type |
|----------|-----------|------|
| JavaScript | ✅ | Browser (Web Worker) |
| TypeScript | ✅ | Browser (runs as JS) |
| Python | ✅ | WASM (Pyodide) |
| SQL | ✅ | WASM (SQLite) |
| Java | 🔜 | Backend (Phase 2) |
| C | 🔜 | Backend (Phase 2) |
| C++ | 🔜 | Backend (Phase 2) |
| C# | 🔜 | Backend (Phase 2) |
| Go | 🔜 | Backend (Phase 2) |
| Rust | 🔜 | Backend (Phase 2) |
| PHP | 🔜 | Backend (Phase 2) |
| HTML | ❌ | Syntax only |
| CSS | ❌ | Syntax only |
| JSON | ❌ | Syntax only |
| YAML | ❌ | Syntax only |
| XML | ❌ | Syntax only |
| Bash | ❌ | Syntax only |
| Markdown | ❌ | Syntax + Preview |

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (iOS and macOS, latest)
- Edge (latest)

## Accessibility

- Full keyboard navigation
- Screen reader support (ARIA labels)
- High contrast mode compatibility
- Focus indicators
- Keyboard shortcuts (Ctrl/Cmd+S, Z, F, etc.)

## Testing

### Unit Tests
- All services (EditorService, CodeExecutionService, MarkdownService, etc.)
- All executors
- Utility functions

### Component Tests
- All 7 components
- Input/output behavior
- State management

### Integration Tests
- Component interactions
- Executor selection
- Theme switching

### E2E Tests
- Create/edit/preview workflow
- Code execution workflow
- Save/load workflow
- Responsive switching

### Security Tests
- XSS prevention (Markdown sanitization)
- Worker isolation verification
- No main window access

## Future Enhancements (Phase 2)

- Backend execution for compiled languages (Java, C, C++, C#, Go, Rust, PHP)
- Real-time collaboration
- Version history
- AI-powered code completion
- Snippet library
- Export to PDF/Word
- Custom themes
- Plugin system

### Theme integration

```typescript
import { ThemeIntegrationService } from './shared/code-workspace';

constructor(private themes: ThemeIntegrationService) {
  this.themes.subscribeToTheme((theme) => {
    // CodeWorkspaceComponent already does this internally.
    // Use this only if you host CodeMirror yourself.
    this.editorTheme = theme;
  });
}
```

`ThemeIntegrationService.getEditorTheme('dark')` maps to existing `--surface`, `--text`, `--border`, and `--primary-soft` tokens. Auto theme follows `ThemeService` time-of-day resolution.

### Troubleshooting

| Issue | What to check |
|---|---|
| Editor has no height | Wrap `<app-code-workspace>` in a parent with an explicit height (`min-height: 240px; height: 280px`). The workspace is `height: 100%`. |
| `[content]` did not apply | `content` is read in `ngOnInit`. Bind markdown, then create the editor (`*ngIf="editorReady"`). |
| Run does nothing in markdown mode | Put the snippet in a fenced block (` ```javascript `) or set `mode="code"` with an executable `language`. |
| Pyodide / SQL.js not loading | Those runtimes lazy-load from the CDN. Check the network tab. Timeouts: JS 10s, Python 30s, SQL 10s. |
| Theme did not update | Confirm `ThemeService.init()` ran at app bootstrap. The workspace subscribes to `resolvedTheme$`. |
| Tests | `cd frontend && npx ng test --no-watch --browsers=ChromeHeadless` |

Editor workflows (create/preview/save, run code, theme, autosave, mobile tabs) are covered by Karma specs under `src/app/shared/code-workspace/` rather than a separate Cypress project.

## License

This component is part of the LifeOS application.

## Contributors

- Implementation based on AI-DLC workflow
- CodeMirror 6: https://codemirror.net/
- Pyodide: https://pyodide.org/
- SQL.js: https://github.com/sql-js/sql.js/
- DOMPurify: https://github.com/cure53/DOMPurify
- marked: https://github.com/markedjs/marked

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2026-08-16
