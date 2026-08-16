import { TestBed } from '@angular/core/testing';
import { EditorService } from './editor.service';

describe('EditorService', () => {
  let service: EditorService;
  let host: HTMLElement;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(EditorService);
    host = document.createElement('div');
    document.body.appendChild(host);
  });

  afterEach(() => {
    host.remove();
  });

  it('creates, reads, and destroys an editor', () => {
    const view = service.createEditor(host, { language: 'markdown' });
    expect(view).toBeTruthy();
    service.setContent(view, '# Hello');
    expect(service.getContent(view)).toBe('# Hello');
    service.destroyEditor(view);
  });

  it('preserves content when switching language and theme', () => {
    const view = service.createEditor(host, { language: 'javascript', theme: 'light' });
    service.setContent(view, 'const x = 1;');
    service.setLanguage(view, 'python');
    service.updateTheme(view, 'dark');
    expect(service.getContent(view)).toBe('const x = 1;');
    service.destroyEditor(view);
  });

  it('applies format transactions for bold and lists', () => {
    const view = service.createEditor(host, { language: 'markdown' });
    service.setContent(view, 'hello');
    view.dispatch({ selection: { anchor: 0, head: 5 } });
    service.applyFormat(view, 'bold');
    expect(service.getContent(view)).toContain('**hello**');
    service.applyFormat(view, 'bullet-list');
    expect(service.getContent(view).startsWith('- ')).toBeTrue();
    service.destroyEditor(view);
  });

  it('notifies onChange when the document changes', () => {
    const changes: string[] = [];
    const view = service.createEditor(host, { language: 'markdown' }, (content) => changes.push(content));
    service.setContent(view, 'abc');
    expect(changes[changes.length - 1]).toBe('abc');
    service.destroyEditor(view);
  });
});
