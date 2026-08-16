import { Injectable } from '@angular/core';
import { EditorView, basicSetup } from 'codemirror';
import { EditorState, Compartment, Extension } from '@codemirror/state';
import { keymap } from '@codemirror/view';
import { defaultKeymap, history, historyKeymap, redo, undo } from '@codemirror/commands';
import { openSearchPanel, search, searchKeymap } from '@codemirror/search';
import { markdown } from '@codemirror/lang-markdown';
import { javascript } from '@codemirror/lang-javascript';
import { python } from '@codemirror/lang-python';
import { sql } from '@codemirror/lang-sql';
import { html } from '@codemirror/lang-html';
import { css } from '@codemirror/lang-css';
import { json } from '@codemirror/lang-json';
import { java } from '@codemirror/lang-java';
import { cpp } from '@codemirror/lang-cpp';
import { rust } from '@codemirror/lang-rust';
import { php } from '@codemirror/lang-php';
import { xml } from '@codemirror/lang-xml';
import { EditorConfig } from '../models';
import type { FormatAction } from '../components/editor-toolbar/editor-toolbar.component';
import { EditorTheme } from './theme/theme-integration.service';

@Injectable({
  providedIn: 'root'
})
export class EditorService {
  private languageCompartment = new Compartment();
  private themeCompartment = new Compartment();
  private readOnlyCompartment = new Compartment();

  createEditor(
    container: HTMLElement,
    config: EditorConfig = {},
    onChange?: (content: string) => void
  ): EditorView {
    const {
      language = 'markdown',
      theme = 'light',
      readOnly = false,
      lineNumbers = true,
      lineWrapping = true,
      tabSize = 2,
      placeholder = ''
    } = config;

    const state = EditorState.create({
      doc: '',
      extensions: [
        basicSetup,
        keymap.of([...defaultKeymap, ...historyKeymap, ...searchKeymap]),
        history(),
        search(),
        this.languageCompartment.of(this.getLanguageExtension(language)),
        this.themeCompartment.of(this.getThemeExtension(theme)),
        this.readOnlyCompartment.of(EditorState.readOnly.of(readOnly)),
        EditorView.lineWrapping,
        EditorState.tabSize.of(tabSize),
        ...(onChange
          ? [
              EditorView.updateListener.of((update) => {
                if (update.docChanged) {
                  onChange(update.state.doc.toString());
                }
              }),
            ]
          : []),
      ]
    });

    const view = new EditorView({
      state,
      parent: container
    });

    return view;
  }

  destroyEditor(view: EditorView): void {
    view.destroy();
  }

  setContent(view: EditorView, content: string): void {
    view.dispatch({
      changes: {
        from: 0,
        to: view.state.doc.length,
        insert: content
      }
    });
  }

  getContent(view: EditorView): string {
    return view.state.doc.toString();
  }

  setLanguage(view: EditorView, language: string): void {
    view.dispatch({
      effects: this.languageCompartment.reconfigure(
        this.getLanguageExtension(language)
      )
    });
  }

  setTheme(view: EditorView, theme: 'light' | 'dark'): void {
    view.dispatch({
      effects: this.themeCompartment.reconfigure(
        this.getThemeExtension(theme)
      )
    });
  }

  updateTheme(view: EditorView, theme: 'light' | 'dark' | EditorTheme): void {
    const name = typeof theme === 'string'
      ? theme
      : theme.name === 'dark' ? 'dark' : 'light';
    this.setTheme(view, name);
  }

  setReadOnly(view: EditorView, readOnly: boolean): void {
    view.dispatch({
      effects: this.readOnlyCompartment.reconfigure(
        EditorState.readOnly.of(readOnly)
      )
    });
  }

  insertText(view: EditorView, text: string, at: 'cursor' | 'selection' = 'cursor'): void {
    const selection = view.state.selection.main;
    view.dispatch({
      changes: {
        from: selection.from,
        to: selection.to,
        insert: text
      },
      selection: {
        anchor: selection.from + text.length
      }
    });
  }

  applyFormat(view: EditorView, action: FormatAction): void {
    switch (action) {
      case 'bold':
        this.wrapSelection(view, '**', '**', 'bold');
        return;
      case 'italic':
        this.wrapSelection(view, '*', '*', 'italic');
        return;
      case 'strikethrough':
        this.wrapSelection(view, '~~', '~~', 'text');
        return;
      case 'inline-code':
        this.wrapSelection(view, '`', '`', 'code');
        return;
      case 'h1':
        this.prefixLine(view, '# ');
        return;
      case 'h2':
        this.prefixLine(view, '## ');
        return;
      case 'h3':
        this.prefixLine(view, '### ');
        return;
      case 'bullet-list':
        this.prefixLine(view, '- ');
        return;
      case 'numbered-list':
        this.prefixLine(view, '1. ');
        return;
      case 'checklist':
        this.prefixLine(view, '- [ ] ');
        return;
      case 'quote':
        this.prefixLine(view, '> ');
        return;
      case 'code-block':
        this.wrapSelection(view, '```\n', '\n```', 'code');
        return;
      case 'horizontal-rule':
        this.insertText(view, '\n\n---\n\n');
        return;
      case 'link':
        this.wrapSelection(view, '[', '](url)', 'text');
        return;
      case 'image':
        this.wrapSelection(view, '![', '](url)', 'alt');
        return;
      case 'table':
        this.insertText(view, '\n\n| Column | Column |\n| --- | --- |\n|  |  |\n\n');
        return;
      case 'undo':
        undo(view);
        return;
      case 'redo':
        redo(view);
        return;
      case 'find':
      case 'replace':
        openSearchPanel(view);
        return;
    }
  }

  private wrapSelection(view: EditorView, before: string, after: string, placeholder: string): void {
    const selection = view.state.selection.main;
    const selected = view.state.doc.sliceString(selection.from, selection.to) || placeholder;
    const insert = `${before}${selected}${after}`;
    view.dispatch({
      changes: {
        from: selection.from,
        to: selection.to,
        insert,
      },
      selection: {
        anchor: selection.from + before.length,
        head: selection.from + before.length + selected.length,
      },
    });
  }

  private prefixLine(view: EditorView, prefix: string): void {
    const selection = view.state.selection.main;
    const line = view.state.doc.lineAt(selection.from);
    const already = line.text.startsWith(prefix.replace(/\s+$/, ''));
    if (already) {
      return;
    }
    view.dispatch({
      changes: {
        from: line.from,
        insert: prefix,
      },
    });
  }

  private getLanguageExtension(language: string) {
    switch (language.toLowerCase()) {
      case 'javascript':
      case 'js':
        return javascript();
      case 'typescript':
      case 'ts':
        return javascript({ typescript: true });
      case 'python':
      case 'py':
        return python();
      case 'sql':
        return sql();
      case 'html':
        return html();
      case 'css':
        return css();
      case 'json':
        return json();
      case 'java':
        return java();
      case 'cpp':
      case 'c++':
      case 'c':
        return cpp();
      case 'rust':
      case 'rs':
        return rust();
      case 'php':
        return php();
      case 'xml':
        return xml();
      case 'markdown':
      case 'md':
      default:
        return markdown();
    }
  }

  private getThemeExtension(theme: 'light' | 'dark'): Extension {
    return EditorView.theme({
      '&': {
        backgroundColor: 'var(--surface)',
        color: 'var(--text)',
        height: '100%',
        minHeight: '0',
      },
      '.cm-scroller': {
        overflow: 'auto',
      },
      '.cm-content': {
        caretColor: 'var(--text)',
      },
      '.cm-cursor, .cm-dropCursor': {
        borderLeftColor: 'var(--text)',
      },
      '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection': {
        backgroundColor: 'var(--primary-soft)',
      },
      '.cm-activeLine': {
        backgroundColor: 'var(--surface-2)',
      },
      '.cm-gutters': {
        backgroundColor: 'var(--surface)',
        color: 'var(--text-muted)',
        borderRight: '1px solid var(--border)',
      },
      '.cm-activeLineGutter': {
        backgroundColor: 'var(--surface-2)',
      },
    }, { dark: theme === 'dark' });
  }
}
