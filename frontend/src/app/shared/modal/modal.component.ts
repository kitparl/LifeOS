import {
  Component,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  signal,
} from '@angular/core';

/**
 * ModalComponent — reusable, accessible dialog with a complete lifecycle.
 *
 * Fixes the class of bugs where a "maximized" popup can no longer be closed:
 * the close control lives in the header and stays reachable in every state
 * (normal, maximized, mobile full-screen). Supports Escape, backdrop click,
 * body scroll-lock, and maximize/restore.
 *
 *   <app-modal [open]="isOpen()" title="Edit" [maximizable]="true" (closed)="isOpen.set(false)">
 *     <ng-container body>...</ng-container>
 *     <ng-container footer>...</ng-container>
 *   </app-modal>
 */
@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [],
  template: `
    @if (open) {
      <div
        class="modal-backdrop"
        (click)="onBackdrop()"
        role="presentation"
      >
        <div
          class="modal"
          [class.modal--maximized]="maximized()"
          [style.maxWidth]="maximized() ? '' : maxWidth"
          role="dialog"
          aria-modal="true"
          [attr.aria-label]="title || 'Dialog'"
          (click)="$event.stopPropagation()"
        >
          <div class="modal-header">
            <span class="modal-header__title">{{ title }}</span>
            <div class="modal-header__actions">
              <ng-content select="[headerActions]"></ng-content>
              @if (maximizable) {
                <button
                  type="button"
                  class="modal-header__btn"
                  [title]="maximized() ? 'Restore' : 'Maximize'"
                  [attr.aria-label]="maximized() ? 'Restore' : 'Maximize'"
                  (click)="toggleMaximize()"
                >{{ maximized() ? '❐' : '⛶' }}</button>
              }
              <button
                type="button"
                class="modal-header__btn"
                title="Close"
                aria-label="Close"
                (click)="close()"
              >✕</button>
            </div>
          </div>

          <div class="modal-body">
            <ng-content select="[body]"></ng-content>
            <ng-content></ng-content>
          </div>

          <div class="modal-footer" [hidden]="!hasFooter">
            <ng-content select="[footer]"></ng-content>
          </div>
        </div>
      </div>
    }
  `,
})
export class ModalComponent implements OnChanges, OnDestroy {
  @Input() open = false;
  @Input() title = '';
  @Input() maxWidth = '520px';
  @Input() closeOnBackdrop = true;
  @Input() maximizable = false;
  /** Set false to hide the footer region entirely. */
  @Input() hasFooter = true;

  @Output() closed = new EventEmitter<void>();

  readonly maximized = signal(false);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['open']) this.lockScroll(this.open);
  }

  ngOnDestroy(): void {
    this.lockScroll(false);
  }

  private lockScroll(locked: boolean): void {
    if (typeof document !== 'undefined') {
      document.body.style.overflow = locked ? 'hidden' : '';
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.open) this.close();
  }

  onBackdrop(): void {
    if (this.closeOnBackdrop) this.close();
  }

  toggleMaximize(): void {
    this.maximized.set(!this.maximized());
  }

  close(): void {
    this.maximized.set(false);
    this.closed.emit();
  }
}
