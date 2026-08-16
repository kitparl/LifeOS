describe('markdown-body list styles', () => {
  afterEach(() => {
    document.querySelectorAll('.markdown-body-spec-host').forEach((el) => el.remove());
  });

  function mount(html: string): HTMLElement {
    const host = document.createElement('div');
    host.className = 'markdown-body markdown-body-spec-host';
    host.innerHTML = html;
    document.body.appendChild(host);
    return host;
  }

  it('shows disc markers on unordered lists', () => {
    const host = mount('<ul><li>item</li></ul>');
    const ul = host.querySelector('ul') as HTMLElement;
    expect(getComputedStyle(ul).listStyleType).toBe('disc');
  });

  it('shows decimal markers on ordered lists', () => {
    const host = mount('<ol><li>item</li></ol>');
    const ol = host.querySelector('ol') as HTMLElement;
    expect(getComputedStyle(ol).listStyleType).toBe('decimal');
  });

  it('applies the same list styles under .prose-content', () => {
    const host = document.createElement('div');
    host.className = 'prose-content markdown-body-spec-host';
    host.innerHTML = '<ul><li>item</li></ul>';
    document.body.appendChild(host);
    expect(getComputedStyle(host.querySelector('ul') as HTMLElement).listStyleType).toBe('disc');
  });
});
