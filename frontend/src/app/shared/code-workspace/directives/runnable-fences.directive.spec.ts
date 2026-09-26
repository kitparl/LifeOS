import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RunnableFencesDirective } from './runnable-fences.directive';
import { ParsedCodeBlock, parseFencedCodeBlocks } from '../utils/fenced-code-blocks';

const MARKDOWN = '```py\nprint(1)\n```\n\n```js\nconsole.log(2)\n```';
const HTML =
  '<pre><code class="language-py">print(1)\n</code></pre>' +
  '<pre><code>plain\n</code></pre>' +
  '<pre><code class="language-js">console.log(2)\n</code></pre>';

@Component({
  standalone: true,
  imports: [RunnableFencesDirective],
  template: `
    <div
      [appRunnableFences]="blocks"
      [runningFenceId]="runningId"
      [fenceRunDisabled]="disabled"
      (fenceRun)="ran.push($event)"
      [innerHTML]="html"
    ></div>
  `,
})
class HostComponent {
  blocks: ParsedCodeBlock[] = parseFencedCodeBlocks(MARKDOWN);
  runningId: string | null = null;
  disabled = false;
  html = HTML;
  ran: ParsedCodeBlock[] = [];
}

describe('RunnableFencesDirective', () => {
  let fixture: ComponentFixture<HostComponent>;
  let host: HostComponent;

  const buttons = (): HTMLButtonElement[] =>
    Array.from(fixture.nativeElement.querySelectorAll('button.fence-run'));

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    host = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('adds a labelled Run button only to matched fences', () => {
    const [py, js] = buttons();
    expect(buttons().length).toBe(2);
    expect(py.textContent).toBe('Run python');
    expect(py.getAttribute('aria-label')).toBe('Run python block 1: print(1)');
    expect(js.getAttribute('aria-label')).toBe('Run javascript block 2: console.log(2)');
    const pres = fixture.nativeElement.querySelectorAll('pre');
    expect(pres[1].querySelector('button')).toBeNull();
  });

  it('emits the block for the clicked fence', () => {
    buttons()[1].click();
    expect(host.ran).toEqual([host.blocks[1]]);
  });

  it('shows Running… and disables every button while a block runs', () => {
    host.runningId = host.blocks[0].id;
    fixture.detectChanges();
    const [py, js] = buttons();
    expect(py.textContent).toBe('Running…');
    expect(py.disabled).toBeTrue();
    expect(js.disabled).toBeTrue();
  });

  it('disables buttons when run is disabled', () => {
    host.disabled = true;
    fixture.detectChanges();
    expect(buttons().every((button) => button.disabled)).toBeTrue();
  });

  it('adds nothing when no blocks are passed', () => {
    host.blocks = [];
    fixture.detectChanges();
    expect(buttons().length).toBe(0);
  });

  it('re-decorates after the rendered HTML is replaced', async () => {
    host.html = '<pre><code class="language-py">print(1)\n</code></pre>';
    fixture.detectChanges();
    await new Promise((resolve) => setTimeout(resolve));
    expect(buttons().length).toBe(1);
  });
});
