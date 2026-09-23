import {
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
  signal,
} from '@angular/core';

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), Math.max(min, max));
}

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
          #modalEl
          class="modal"
          [class.modal--maximized]="maximized()"
          [class.modal--plain]="plain"
          [style.maxWidth]="maximized() ? '' : (resizable && width() ? 'none' : maxWidth)"
          [style.width.px]="resizable ? width() : null"
          [style.height.px]="resizable && !maximized() ? height() : null"
          [style.background]="background"
          role="dialog"
          aria-modal="true"
          [attr.aria-label]="title || 'Dialog'"
          (click)="$event.stopPropagation()"
        >
          <div class="modal-header">
            <ng-content select="[titleIcon]"></ng-content>
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

          @if (resizable && !maximized()) {
            <div class="modal-resize-handle modal-resize-handle--right" (pointerdown)="startResize($event, { width: true, height: false })"></div>
            <div class="modal-resize-handle modal-resize-handle--bottom" (pointerdown)="startResize($event, { width: false, height: true })"></div>
            <div class="modal-resize-handle modal-resize-handle--corner" (pointerdown)="startResize($event, { width: true, height: true })"></div>
          }
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
  /** Overrides the modal's background (e.g. to tint it with a note/item color). Null keeps the default surface color. */
  @Input() background: string | null = null;
  /** Removes the header/footer divider borders, for a seamless single-surface look (e.g. a Google Keep–style card). */
  @Input() plain = false;
  /** Enables drag-to-resize handles (bottom-right corner + right/bottom edges). Disabled by default. */
  @Input() resizable = false;
  /** localStorage key the last resized width/height is persisted under. Omit to skip persistence. */
  @Input() resizeStorageKey: string | null = null;
  @Input() resizeMinWidth = 320;
  @Input() resizeMinHeight = 200;
  @Input() resizeMaxWidth = 900;
  @Input() resizeMaxHeight = 800;

  @Output() closed = new EventEmitter<void>();

  @ViewChild('modalEl') modalEl?: ElementRef<HTMLDivElement>;

  readonly maximized = signal(false);
  /** Current resized width/height in px; null = use the default CSS sizing (not yet resized). */
  readonly width = signal<number | null>(null);
  readonly height = signal<number | null>(null);

  private resizing = false;
  private resizeAxis = { width: false, height: false };
  private resizeStartX = 0;
  private resizeStartY = 0;
  private resizeStartWidth = 0;
  private resizeStartHeight = 0;
  private readonly onResizeMove = (event: PointerEvent): void => this.handleResizeMove(event);
  private readonly onResizeEnd = (): void => this.handleResizeEnd();

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['open']) {
      this.lockScroll(this.open);
      if (this.open && this.resizable) this.loadPersistedSize();
    }
  }

  ngOnDestroy(): void {
    this.lockScroll(false);
    this.stopResizeListeners();
  }

  private viewportMaxWidth(): number {
    const vw = typeof window !== 'undefined' ? window.innerWidth : this.resizeMaxWidth;
    return Math.min(this.resizeMaxWidth, Math.max(this.resizeMinWidth, vw - 32));
  }

  private viewportMaxHeight(): number {
    const vh = typeof window !== 'undefined' ? window.innerHeight : this.resizeMaxHeight;
    return Math.min(this.resizeMaxHeight, Math.max(this.resizeMinHeight, vh - 32));
  }

  private loadPersistedSize(): void {
    if (!this.resizeStorageKey || typeof localStorage === 'undefined') return;
    try {
      const raw = localStorage.getItem(this.resizeStorageKey);
      if (!raw) return;
      const parsed = JSON.parse(raw) as { width?: number; height?: number };
      if (typeof parsed.width === 'number') {
        this.width.set(clamp(parsed.width, this.resizeMinWidth, this.viewportMaxWidth()));
      }
      if (typeof parsed.height === 'number') {
        this.height.set(clamp(parsed.height, this.resizeMinHeight, this.viewportMaxHeight()));
      }
    } catch {
      /* ignore malformed/unavailable storage */
    }
  }

  private persistSize(): void {
    if (!this.resizeStorageKey || typeof localStorage === 'undefined') return;
    try {
      localStorage.setItem(this.resizeStorageKey, JSON.stringify({ width: this.width(), height: this.height() }));
    } catch {
      /* ignore storage errors (private browsing, quota, etc.) */
    }
  }

  startResize(event: PointerEvent, axis: { width: boolean; height: boolean }): void {
    if (!this.resizable) return;
    event.preventDefault();
    event.stopPropagation();
    const rect = this.modalEl?.nativeElement.getBoundingClientRect();
    this.resizing = true;
    this.resizeAxis = axis;
    this.resizeStartX = event.clientX;
    this.resizeStartY = event.clientY;
    this.resizeStartWidth = rect?.width ?? this.resizeMinWidth;
    this.resizeStartHeight = rect?.height ?? this.resizeMinHeight;
    if (typeof document !== 'undefined') document.body.style.userSelect = 'none';
    document.addEventListener('pointermove', this.onResizeMove);
    document.addEventListener('pointerup', this.onResizeEnd);
  }

  private handleResizeMove(event: PointerEvent): void {
    if (!this.resizing) return;
    if (this.resizeAxis.width) {
      const w = this.resizeStartWidth + (event.clientX - this.resizeStartX);
      this.width.set(clamp(w, this.resizeMinWidth, this.viewportMaxWidth()));
    }
    if (this.resizeAxis.height) {
      const h = this.resizeStartHeight + (event.clientY - this.resizeStartY);
      this.height.set(clamp(h, this.resizeMinHeight, this.viewportMaxHeight()));
    }
  }

  private handleResizeEnd(): void {
    if (!this.resizing) return;
    this.resizing = false;
    if (typeof document !== 'undefined') document.body.style.userSelect = '';
    this.stopResizeListeners();
    this.persistSize();
  }

  private stopResizeListeners(): void {
    document.removeEventListener('pointermove', this.onResizeMove);
    document.removeEventListener('pointerup', this.onResizeEnd);
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
