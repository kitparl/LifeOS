import {
  Component,
  ElementRef,
  HostListener,
  effect,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { WordOfTheDayService } from '../../features/communication/vocabulary/services/word-of-the-day.service';

/**
 * Header chip for the Word of the Day. Hidden unless the user's Wordnik key is connected
 * (the service only yields a word then). Hover/focus/tap opens a mini detail popover;
 * clicking the term opens the full vocabulary detail page.
 */
const CLOSE_DELAY_MS = 300;

@Component({
  selector: 'app-word-of-the-day-chip',
  standalone: true,
  host: {
    class: 'relative inline-flex min-w-0',
    '(pointerdown)': 'lastPointer = $event.pointerType',
    '(mouseenter)': 'onHover()',
    '(mouseleave)': 'onLeave()',
    '(focusout)': 'onFocusOut($event)',
  },
  template: `
    @if (word(); as w) {
      <button
        type="button"
        class="chip max-w-[10rem] sm:max-w-[16rem]"
        aria-controls="wotd-popover"
        [attr.aria-label]="'Word of the Day: ' + w.term"
        [attr.aria-expanded]="open()"
        (focus)="onFocus()"
        (click)="onChipClick()"
      >
        <span class="truncate">{{ w.term }}</span>
      </button>
      @if (open()) {
        <!-- pt-2 (not mt-*) keeps the popover inside the hover area: no gap to fall through. -->
        <div
          id="wotd-popover"
          role="dialog"
          aria-label="Word of the Day"
          class="absolute right-0 top-full pt-2"
          style="z-index: 60"
        >
          <div class="menu w-72 space-y-2 p-3 text-sm">
            <p>
              <span class="font-semibold">{{ w.term }}</span>
              <span class="text-xs" style="color: var(--text-muted)">
                · {{ w.part_of_speech }}</span
              >
            </p>
            <div>
              <p class="text-xs font-medium" style="color: var(--text-muted)">
                Meaning
              </p>
              <p>{{ w.simple_meaning }}</p>
            </div>
            <div>
              <p class="text-xs font-medium" style="color: var(--text-muted)">
                Example
              </p>
              <p>{{ w.example }}</p>
            </div>
            @if (w.synonyms.length) {
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">
                  Synonyms
                </p>
                <p>{{ w.synonyms.join(', ') }}</p>
              </div>
            }
            <button
              type="button"
              class="btn-primary text-xs"
              (click)="openDetail()"
            >
              View full details
            </button>
          </div>
        </div>
      }
    }
  `,
})
export class WordOfTheDayChipComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly elementRef = inject(ElementRef<HTMLElement>);
  private readonly wordOfTheDay = inject(WordOfTheDayService);

  readonly word = this.wordOfTheDay.word;
  readonly open = signal(false);
  // Esc returns focus to the chip; that focus must not reopen the popover.
  private suppressFocusOpen = false;
  // A tap also fires emulated mouseenter + focus; only the tap's click may toggle on touch.
  lastPointer = '';
  // Leaving the chip/popover closes after a short grace period, so small cursor slips don't.
  private closeTimer: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    effect(() => {
      const userId = this.auth.user()?.id;
      if (userId) this.wordOfTheDay.load(userId);
    });
  }

  show(): void {
    clearTimeout(this.closeTimer);
    this.open.set(true);
  }

  hide(): void {
    clearTimeout(this.closeTimer);
    this.open.set(false);
  }

  onHover(): void {
    if (this.lastPointer !== 'touch') this.show();
  }

  onLeave(): void {
    if (this.lastPointer === 'touch') return;
    clearTimeout(this.closeTimer);
    this.closeTimer = setTimeout(() => this.open.set(false), CLOSE_DELAY_MS);
  }

  /** Keyboard users tabbing into the popover keep it open; tabbing out of the whole chip closes it. */
  onFocusOut(event: FocusEvent): void {
    const next = event.relatedTarget as Node | null;
    if (next && this.elementRef.nativeElement.contains(next)) return;
    if (this.lastPointer !== 'touch') this.onLeave();
  }

  onFocus(): void {
    if (this.suppressFocusOpen || this.lastPointer === 'touch') {
      this.suppressFocusOpen = false;
      return;
    }
    this.show();
  }

  /** Touch has no hover: the first tap opens the popover, the next one navigates. */
  onChipClick(): void {
    if (this.lastPointer === 'touch' && !this.open()) {
      this.show();
      return;
    }
    this.openDetail();
  }

  openDetail(): void {
    const w = this.word();
    this.hide();
    if (w) this.router.navigate(['/communication/vocabulary', w.id]);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (
      this.open() &&
      !this.elementRef.nativeElement.contains(event.target as Node)
    )
      this.hide();
  }

  @HostListener('document:keydown', ['$event'])
  onDocumentKeydown(event: KeyboardEvent): void {
    if (event.key !== 'Escape' || !this.open()) return;
    this.hide();
    this.suppressFocusOpen = true;
    this.elementRef.nativeElement.querySelector('button')?.focus();
  }
}
