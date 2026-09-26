import {
  AfterViewInit,
  Directive,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  Renderer2,
  SimpleChanges,
  inject,
} from '@angular/core';
import {
  ParsedCodeBlock,
  RenderedFence,
  codeBlockFirstLine,
  matchRenderedFences,
  normalizeExecutableLanguage,
} from '../utils/fenced-code-blocks';

interface FenceControl {
  block: ParsedCodeBlock;
  pre: HTMLElement;
  button: HTMLButtonElement;
  unlisten: () => void;
}

const LANGUAGE_CLASS = /(?:^|\s)language-(\S+)/;

/**
 * Adds an inline Run button to each rendered `pre > code` fence that matches
 * one of the given executable blocks. Buttons are attached after render
 * because the markdown sanitizer strips them from HTML. No blocks, no buttons.
 */
@Directive({
  selector: '[appRunnableFences]',
  standalone: true,
})
export class RunnableFencesDirective implements AfterViewInit, OnChanges, OnDestroy {
  private readonly el = inject(ElementRef<HTMLElement>);
  private readonly renderer = inject(Renderer2);

  @Input('appRunnableFences') blocks: ParsedCodeBlock[] = [];
  @Input() runningFenceId: string | null = null;
  @Input() fenceRunDisabled = false;

  @Output() readonly fenceRun = new EventEmitter<ParsedCodeBlock>();

  private controls: FenceControl[] = [];
  private observer?: MutationObserver;

  ngAfterViewInit(): void {
    this.decorate();
    this.observer = new MutationObserver(() => this.decorate());
    this.observer.observe(this.el.nativeElement, { childList: true });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.observer) return;
    if (changes['blocks']) {
      this.decorate();
    } else {
      this.updateControls();
    }
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
    this.removeControls();
  }

  private decorate(): void {
    this.removeControls();
    if (!this.blocks?.length) return;

    const codes = Array.from(
      (this.el.nativeElement as HTMLElement).querySelectorAll('pre > code')
    ) as HTMLElement[];
    const rendered: RenderedFence[] = codes.map((code) => ({
      language: code.className.match(LANGUAGE_CLASS)?.[1] ?? '',
      code: code.textContent ?? '',
    }));

    matchRenderedFences(rendered, this.blocks).forEach((block, index) => {
      const pre = codes[index].parentElement;
      if (block && pre) {
        this.controls.push(this.createControl(block, pre));
      }
    });
    this.updateControls();
  }

  private createControl(block: ParsedCodeBlock, pre: HTMLElement): FenceControl {
    const button = this.renderer.createElement('button') as HTMLButtonElement;
    this.renderer.setAttribute(button, 'type', 'button');
    this.renderer.addClass(button, 'btn-secondary');
    this.renderer.addClass(button, 'text-xs');
    this.renderer.addClass(button, 'fence-run');
    const language = normalizeExecutableLanguage(block.language);
    const number = this.blocks.indexOf(block) + 1;
    this.renderer.setAttribute(
      button,
      'aria-label',
      `Run ${language} block ${number}: ${codeBlockFirstLine(block.code)}`
    );
    this.renderer.addClass(pre, 'fence-runnable');
    this.renderer.appendChild(pre, button);
    const unlisten = this.renderer.listen(button, 'click', (event: Event) => {
      event.stopPropagation();
      this.fenceRun.emit(block);
    });
    return { block, pre, button, unlisten };
  }

  private updateControls(): void {
    const busy = this.runningFenceId !== null;
    for (const { block, button } of this.controls) {
      const running = this.runningFenceId === block.id;
      button.textContent = running
        ? 'Running…'
        : `Run ${normalizeExecutableLanguage(block.language)}`;
      button.disabled = this.fenceRunDisabled || busy;
    }
  }

  private removeControls(): void {
    for (const { pre, button, unlisten } of this.controls) {
      unlisten();
      if (button.parentNode === pre) {
        this.renderer.removeChild(pre, button);
      }
      this.renderer.removeClass(pre, 'fence-runnable');
    }
    this.controls = [];
  }
}
