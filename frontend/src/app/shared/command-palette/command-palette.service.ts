import { Injectable, signal } from '@angular/core';
import { CommandPaletteItem } from './command-palette.models';

@Injectable({ providedIn: 'root' })
export class CommandPaletteService {
  readonly isOpen = signal(false);
  readonly query = signal('');
  readonly items = signal<CommandPaletteItem[]>([]);
  readonly activeIndex = signal(0);

  private keydownHandler = (event: KeyboardEvent) => this.onKeydown(event);

  registerItems(items: CommandPaletteItem[]): void {
    this.items.set(items);
  }

  open(): void {
    this.query.set('');
    this.activeIndex.set(0);
    this.isOpen.set(true);
    document.addEventListener('keydown', this.keydownHandler);
  }

  close(): void {
    this.isOpen.set(false);
    document.removeEventListener('keydown', this.keydownHandler);
  }

  setQuery(value: string): void {
    this.query.set(value);
    this.activeIndex.set(0);
  }

  filteredItems(): CommandPaletteItem[] {
    const q = this.query().trim().toLowerCase();
    const all = this.items();
    if (!q) {
      return all;
    }
    return all.filter(
      (item) =>
        item.label.toLowerCase().includes(q) ||
        item.group.toLowerCase().includes(q) ||
        (item.hint?.toLowerCase().includes(q) ?? false),
    );
  }

  moveActive(delta: number): void {
    const list = this.filteredItems();
    if (list.length === 0) {
      return;
    }
    const next = (this.activeIndex() + delta + list.length) % list.length;
    this.activeIndex.set(next);
  }

  selectActive(): CommandPaletteItem | null {
    const list = this.filteredItems();
    const item = list[this.activeIndex()];
    if (!item || item.disabled) {
      return null;
    }
    return item;
  }

  private onKeydown(event: KeyboardEvent): void {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      if (this.isOpen()) {
        this.close();
      } else {
        this.open();
      }
      return;
    }

    if (!this.isOpen()) {
      return;
    }

    if (event.key === 'Escape') {
      event.preventDefault();
      this.close();
    }
  }
}
