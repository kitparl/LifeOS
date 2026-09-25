import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { NewsSkeletonComponent } from '../components/news-skeleton.component';
import { NewsStateComponent } from '../components/news-state.component';
import { NewsCollection, NewsErrorCode, newsErrorCode, newsErrorMessage } from '../models/news.models';
import { NewsService } from '../services/news.service';

@Component({
  selector: 'app-news-collections-tab',
  standalone: true,
  imports: [RouterLink, NewsSkeletonComponent, NewsStateComponent],
  template: `
    <section class="space-y-3" aria-labelledby="news-collections-heading">
      <h2 id="news-collections-heading" class="section-heading">Collections</h2>

      <form class="flex gap-2" (submit)="create($event)">
        <label class="sr-only" for="news-new-collection">New collection name</label>
        <input
          id="news-new-collection"
          class="input-field flex-1"
          maxlength="100"
          placeholder="New collection, e.g. AI Research"
          data-testid="news-collections-new-input"
          [value]="newName()"
          (input)="newName.set($any($event.target).value)"
        />
        <button type="submit" class="btn-primary" [disabled]="!newName().trim()" data-testid="news-collections-create-button">
          Create
        </button>
      </form>
      @if (actionError()) {
        <p class="text-xs" style="color: var(--danger)" role="alert">{{ actionError() }}</p>
      }

      @if (loading()) {
        <app-news-skeleton layout="rows" [count]="3" />
      } @else if (error()) {
        <app-news-state title="We couldn't load your collections." [message]="message(error()!)" [retryable]="true" (retry)="load()" />
      } @else if (collections().length === 0) {
        <app-news-state title="No collections yet" message="Create one to group saved articles, like AI Research or Read Later." />
      } @else {
        <ul class="space-y-2">
          @for (c of collections(); track c.id) {
            <li class="panel--flat flex flex-wrap items-center gap-2 !p-3">
              @if (editingId() === c.id) {
                <form class="flex flex-1 gap-2" (submit)="rename($event, c)">
                  <label class="sr-only" [for]="'rename-' + c.id">Collection name</label>
                  <input
                    [id]="'rename-' + c.id"
                    class="input-field flex-1"
                    maxlength="100"
                    [value]="editName()"
                    (input)="editName.set($any($event.target).value)"
                    (keydown.escape)="editingId.set(null)"
                  />
                  <button type="submit" class="btn-primary !min-h-8" [disabled]="!editName().trim()">Save</button>
                  <button type="button" class="btn-ghost !min-h-8" (click)="editingId.set(null)">Cancel</button>
                </form>
              } @else {
                <a class="link flex-1 font-medium" [routerLink]="['/news/collections', c.id]" data-testid="news-collections-open-link">
                  {{ c.name }}
                </a>
                <span class="text-xs" style="color: var(--text-muted)">
                  {{ c.article_count }} saved {{ c.article_count === 1 ? 'article' : 'articles' }}
                </span>
                <button type="button" class="btn-ghost !min-h-8 !px-2 text-xs" [attr.aria-label]="'Rename ' + c.name" (click)="startRename(c)">
                  Rename
                </button>
                <button type="button" class="btn-ghost !min-h-8 !px-2 text-xs" [attr.aria-label]="'Delete ' + c.name" (click)="remove(c)">
                  Delete
                </button>
              }
            </li>
          }
        </ul>
      }
    </section>
  `,
})
export class NewsCollectionsTabComponent implements OnInit {
  private readonly news = inject(NewsService);
  private readonly confirm = inject(ConfirmService);

  readonly collections = signal<NewsCollection[]>([]);
  readonly loading = signal(true);
  readonly error = signal<NewsErrorCode | null>(null);
  readonly actionError = signal<string | null>(null);
  readonly newName = signal('');
  readonly editingId = signal<string | null>(null);
  readonly editName = signal('');
  readonly message = newsErrorMessage;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.news.listCollections().subscribe({
      next: (list) => {
        this.collections.set(list);
        this.loading.set(false);
      },
      error: (err: unknown) => {
        this.error.set(newsErrorCode(err));
        this.loading.set(false);
      },
    });
  }

  create(event: Event): void {
    event.preventDefault();
    const name = this.newName().trim();
    if (!name) return;
    this.actionError.set(null);
    this.news.createCollection(name).subscribe({
      next: () => {
        this.newName.set('');
        this.load();
      },
      error: (err: unknown) => this.actionError.set(collectionError(err)),
    });
  }

  startRename(c: NewsCollection): void {
    this.editName.set(c.name);
    this.editingId.set(c.id);
  }

  rename(event: Event, c: NewsCollection): void {
    event.preventDefault();
    const name = this.editName().trim();
    if (!name) return;
    this.actionError.set(null);
    this.news.renameCollection(c.id, name).subscribe({
      next: (updated) => {
        this.editingId.set(null);
        this.collections.update((list) => list.map((x) => (x.id === updated.id ? updated : x)));
      },
      error: (err: unknown) => this.actionError.set(collectionError(err)),
    });
  }

  async remove(c: NewsCollection): Promise<void> {
    const ok = await this.confirm.confirm(
      `Delete the collection "${c.name}"? Its saved articles are kept.`,
      'Delete collection',
    );
    if (!ok) return;
    this.actionError.set(null);
    this.news.deleteCollection(c.id).subscribe({
      next: () => this.collections.update((list) => list.filter((x) => x.id !== c.id)),
      error: (err: unknown) => this.actionError.set(collectionError(err)),
    });
  }
}

function collectionError(err: unknown): string {
  return (err as { status?: number })?.status === 409
    ? 'A collection with this name already exists.'
    : newsErrorMessage(newsErrorCode(err));
}
