import { ChangeDetectionStrategy, Component, HostListener, input, output, signal } from '@angular/core';

export interface SplitBounds {
  start: number;
  end: number;
}

/**
 * Draggable/keyboard-accessible separator between two panes. It only emits the first pane's share
 * (0–1, clamped to min/max); the parent owns the ratio and the layout, and styles the host element.
 */
@Component({
  selector: 'app-split-divider',
  standalone: true,
  template: '',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    role: 'separator',
    tabindex: '0',
    '[attr.aria-orientation]': 'orientation() === "horizontal" ? "vertical" : "horizontal"',
    '[attr.aria-valuenow]': 'percent()',
    '[attr.aria-valuemin]': 'min() * 100',
    '[attr.aria-valuemax]': 'max() * 100',
    '[attr.aria-label]': 'label()',
    '[attr.data-resizing]': 'dragging() ? "true" : null',
    title: 'Drag to resize. Double-click to reset.',
    style: 'touch-action: none',
  },
})
export class SplitDividerComponent {
  /** Direction panes are laid out in: `horizontal` = side by side (column divider). */
  readonly orientation = input<'horizontal' | 'vertical'>('horizontal');
  /** First pane's share, 0–1. */
  readonly value = input(0.5);
  readonly min = input(0.2);
  readonly max = input(0.8);
  readonly defaultValue = input(0.5);
  readonly label = input('Resize panes');
  /** Pixel extent (along the split axis) of the two panes, read when a drag moves. */
  readonly bounds = input.required<() => SplitBounds | null>();

  readonly valueChange = output<number>();
  readonly draggingChange = output<boolean>();

  readonly dragging = signal(false);

  percent(): number {
    return Math.round(this.value() * 100);
  }

  @HostListener('pointerdown', ['$event'])
  onPointerDown(event: PointerEvent): void {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    event.preventDefault();
    this.setDragging(true);
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  @HostListener('pointermove', ['$event'])
  onPointerMove(event: PointerEvent): void {
    if (!this.dragging()) return;
    const bounds = this.bounds()();
    if (!bounds) return;
    const pos = this.orientation() === 'horizontal' ? event.clientX : event.clientY;
    const ratio = ratioFromPointer(pos, bounds);
    if (ratio !== null) this.emit(ratio);
  }

  @HostListener('pointerup', ['$event'])
  @HostListener('pointercancel', ['$event'])
  onPointerUp(event: PointerEvent): void {
    if (!this.dragging()) return;
    this.setDragging(false);
    const target = event.currentTarget as HTMLElement;
    if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId);
  }

  @HostListener('dblclick')
  reset(): void {
    this.setDragging(false);
    this.valueChange.emit(this.defaultValue());
  }

  @HostListener('keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Home') {
      event.preventDefault();
      this.reset();
      return;
    }
    const shrink = event.key === 'ArrowLeft' || event.key === 'ArrowUp';
    const grow = event.key === 'ArrowRight' || event.key === 'ArrowDown';
    if (!shrink && !grow) return;
    event.preventDefault();
    this.emit(this.value() + (grow ? KEY_STEP : -KEY_STEP));
  }

  private emit(ratio: number): void {
    this.valueChange.emit(Math.min(this.max(), Math.max(this.min(), ratio)));
  }

  private setDragging(dragging: boolean): void {
    this.dragging.set(dragging);
    this.draggingChange.emit(dragging);
  }
}

const KEY_STEP = 0.05;

/** Pointer position as a 0–1 share of the span, or null when the span is empty. */
export function ratioFromPointer(pos: number, { start, end }: SplitBounds): number | null {
  const total = end - start;
  return total > 0 ? (pos - start) / total : null;
}
