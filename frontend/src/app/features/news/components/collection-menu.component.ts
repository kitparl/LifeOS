import { HttpStatusCode } from '@angular/common/http';
import { Component, ElementRef, HostListener, OnInit, inject, input, linkedSignal, output, signal } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { Observable } from 'rxjs';
import { NewsCollection, newsErrorCode, newsErrorMessage } from '../models/news.models';
import { NewsService } from '../services/news.service';

/**
 * Popover to manage a saved article's collections.
 * - `toggle`: add/remove memberships (many-to-many), create a collection inline.
 * - `move`: move the article from `sourceCollectionId` to another collection.
 */
@Component({
  selector: 'app-collection-menu',
  standalone: true,
  imports: [LucideDynamicIcon],
  host: {
    class: 'relative inline-block',
    '[class.z-50]': 'open()',
  },
  template: `
    <button
      type="button"
      class="btn-ghost !min-h-8 !px-2 text-xs"
      [attr.aria-expanded]="open()"
      aria-haspopup="true"
      data-testid="collection-menu-trigger-button"
      (click)="toggleOpen()"
    >
      <svg class="h-3.5 w-3.5" lucideIcon="folder-plus" aria-hidden="true"></svg>
      {{ mode() === 'move' ? 'Move' : 'Collections' }}
    </button>

    @if (open()) {
      <div
        class="menu absolute right-0 bottom-full z-50 mb-1 w-64 max-w-[80vw] p-1"
        role="dialog"
        [attr.aria-label]="heading()"
        (keydown.escape)="close()"
      >
        <p class="px-3 pb-1 pt-2 text-xs font-semibold">{{ heading() }}</p>
        @if (collections() === null) {
          <p class="px-3 py-2 text-xs" style="color: var(--text-muted)" role="status">Loading…</p>
        } @else {
          @for (c of choices(); track c.id) {
            <button
              type="button"
              class="menu-item"
              [class.menu-item--active]="mode() === 'toggle' && memberIds().includes(c.id)"
              [attr.aria-pressed]="mode() === 'toggle' ? memberIds().includes(c.id) : null"
              [disabled]="busy()"
              [attr.data-testid]="'collection-menu-item-' + c.id"
              (click)="choose(c)"
            >
              <span class="flex-1 truncate">{{ c.name }}</span>
              @if (mode() === 'toggle' && memberIds().includes(c.id)) {
                <span aria-hidden="true">✓</span>
              }
            </button>
          } @empty {
            <p class="px-3 py-2 text-xs" style="color: var(--text-muted)">
              {{ mode() === 'move' ? 'No other collections yet.' : 'No collections yet.' }}
            </p>
          }
          @if (mode() === 'toggle') {
            <form class="flex gap-1 border-t p-2" style="border-color: var(--border)" (submit)="create($event)">
              <label class="sr-only" for="new-collection-{{ savedArticleId() }}">New collection name</label>
              <input
                id="new-collection-{{ savedArticleId() }}"
                class="input-field !min-h-8 flex-1 text-xs"
                maxlength="100"
                placeholder="New collection"
                data-testid="collection-menu-new-input"
                [value]="newName()"
                (input)="newName.set($any($event.target).value)"
              />
              <button
                type="submit"
                class="btn-secondary !min-h-8 !px-2 text-xs"
                [disabled]="busy() || !newName().trim()"
                data-testid="collection-menu-create-button"
              >
                Add
              </button>
            </form>
          }
        }
        @if (error()) {
          <p class="px-3 pb-2 text-xs" style="color: var(--danger)" role="alert">{{ error() }}</p>
        }
      </div>
    }
  `,
})
export class CollectionMenuComponent implements OnInit {
  private readonly news = inject(NewsService);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly savedArticleId = input.required<string>();
  readonly collectionIds = input<string[]>([]);
  readonly mode = input<'toggle' | 'move'>('toggle');
  readonly sourceCollectionId = input<string | null>(null);
  /** Open immediately (the "Add to collection?" prompt right after saving). */
  readonly startOpen = input(false);

  readonly collectionIdsChange = output<string[]>();
  readonly moved = output<string>();

  readonly open = signal(false);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly newName = signal('');
  readonly collections = signal<NewsCollection[] | null>(null);
  readonly memberIds = linkedSignal(() => this.collectionIds());

  ngOnInit(): void {
    if (this.startOpen()) this.show();
  }

  heading(): string {
    if (this.mode() === 'move') return 'Move to collection';
    return this.startOpen() ? 'Add to collection?' : 'Collections';
  }

  choices(): NewsCollection[] {
    const all = this.collections() ?? [];
    return this.mode() === 'move' ? all.filter((c) => c.id !== this.sourceCollectionId()) : all;
  }

  toggleOpen(): void {
    if (this.open()) this.close();
    else this.show();
  }

  close(): void {
    this.open.set(false);
    this.error.set(null);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (this.open() && !this.host.nativeElement.contains(event.target as Node)) this.close();
  }

  private show(): void {
    this.open.set(true);
    this.collections.set(null);
    this.news.listCollections().subscribe({
      next: (list) => this.collections.set(list),
      error: (err: unknown) => {
        this.collections.set([]);
        this.error.set(newsErrorMessage(newsErrorCode(err)));
      },
    });
  }

  choose(collection: NewsCollection): void {
    if (this.mode() === 'move') {
      this.run(
        this.news.moveToCollection(this.sourceCollectionId() ?? '', this.savedArticleId(), collection.id),
        () => {
          this.moved.emit(collection.id);
          this.close();
        },
      );
      return;
    }
    const isMember = this.memberIds().includes(collection.id);
    const request = isMember
      ? this.news.removeFromCollection(collection.id, this.savedArticleId())
      : this.news.addToCollection(collection.id, this.savedArticleId());
    this.run(request, () => {
      const next = isMember
        ? this.memberIds().filter((id) => id !== collection.id)
        : [...this.memberIds(), collection.id];
      this.memberIds.set(next);
      this.collectionIdsChange.emit(next);
    });
  }

  create(event: Event): void {
    event.preventDefault();
    const name = this.newName().trim();
    if (!name) return;
    this.busy.set(true);
    this.error.set(null);
    this.news.createCollection(name).subscribe({
      next: (created) => {
        this.newName.set('');
        this.collections.update((list) => [...(list ?? []), created]);
        this.busy.set(false);
        this.choose(created);
      },
      error: (err: unknown) => {
        this.busy.set(false);
        this.error.set(
          (err as { status?: number })?.status === HttpStatusCode.Conflict
            ? 'A collection with this name already exists.'
            : newsErrorMessage(newsErrorCode(err)),
        );
      },
    });
  }

  private run(request: Observable<unknown>, done: () => void): void {
    this.busy.set(true);
    this.error.set(null);
    request.subscribe({
      next: () => {
        this.busy.set(false);
        done();
      },
      error: (err: unknown) => {
        this.busy.set(false);
        this.error.set(newsErrorMessage(newsErrorCode(err)));
      },
    });
  }
}
