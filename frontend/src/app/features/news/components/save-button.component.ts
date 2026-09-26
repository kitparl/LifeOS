import { Component, OnDestroy, inject, input, linkedSignal, output, signal } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { GuestLockedControlComponent } from '../../../shared/guest-locked/guest-locked-control.component';
import { NewsArticle, newsErrorCode, newsErrorMessage, toSavedArticleCreate } from '../models/news.models';
import { NEWS_ACCESS_MODE } from '../news-access-mode';
import { NewsService } from '../services/news.service';
import { CollectionMenuComponent } from './collection-menu.component';

const FEEDBACK_MS = 2500;

/**
 * Star toggle that saves/unsaves a live article; after saving, offers "Add to collection?".
 * Guests see the star locked: it explains that saving needs an account and never calls the API.
 */
@Component({
  selector: 'app-news-save-button',
  standalone: true,
  imports: [LucideDynamicIcon, CollectionMenuComponent, GuestLockedControlComponent],
  host: { class: 'inline-flex items-center gap-1' },
  template: `
    @if (isGuest) {
      <app-guest-locked-control
        label="Save article (sign in required)"
        message="Sign in to save articles"
        detail="Saving and collections are part of your LifeOS account."
        testId="news-save-button-locked"
      >
        <svg class="h-4 w-4" lucideIcon="star" fill="none" aria-hidden="true"></svg>
      </app-guest-locked-control>
    } @else {
      @if (feedback()) {
        <span class="text-xs" style="color: var(--text-muted)" aria-hidden="true">{{ feedback() }}</span>
      }
      <span class="sr-only" aria-live="polite">{{ feedback() }}</span>
      @if (savedId(); as id) {
        <app-collection-menu
          [savedArticleId]="id"
          [collectionIds]="collectionIds()"
          [startOpen]="promptCollections()"
          (collectionIdsChange)="collectionIds.set($event)"
        />
      }
      <button
        type="button"
        class="btn-ghost !min-h-8 !px-2"
        [class.star-favorite]="!!savedId()"
        [attr.aria-label]="savedId() ? 'Remove saved article' : 'Save article'"
        [attr.aria-pressed]="!!savedId()"
        [disabled]="busy()"
        data-testid="news-save-button"
        (click)="toggle()"
      >
        <svg class="h-4 w-4" lucideIcon="star" [attr.fill]="savedId() ? 'currentColor' : 'none'" aria-hidden="true"></svg>
      </button>
    }
  `,
})
export class NewsSaveButtonComponent implements OnDestroy {
  private readonly news = inject(NewsService);
  readonly isGuest = inject(NEWS_ACCESS_MODE) === 'guest';
  private feedbackTimer: ReturnType<typeof setTimeout> | undefined;

  readonly article = input.required<NewsArticle>();
  readonly savedChange = output<string | null>();

  readonly savedId = linkedSignal(() => this.article().saved_article_id);
  readonly collectionIds = signal<string[]>([]);
  readonly promptCollections = signal(false);
  readonly busy = signal(false);
  readonly feedback = signal('');

  toggle(): void {
    const id = this.savedId();
    this.busy.set(true);
    if (id) {
      this.news.removeSaved(id).subscribe({
        next: () => this.done(null, 'Removed'),
        error: (err: unknown) => this.fail(err),
      });
      return;
    }
    this.news.save(toSavedArticleCreate(this.article())).subscribe({
      next: (saved) => {
        this.collectionIds.set(saved.collection_ids);
        this.promptCollections.set(!saved.already_saved);
        this.done(saved.id, saved.already_saved ? 'Already saved' : 'Saved');
      },
      error: (err: unknown) => this.fail(err),
    });
  }

  ngOnDestroy(): void {
    clearTimeout(this.feedbackTimer);
  }

  private done(savedId: string | null, message: string): void {
    this.busy.set(false);
    this.savedId.set(savedId);
    if (!savedId) this.promptCollections.set(false);
    // Cached feeds still carry the old saved state.
    this.news.invalidateNews();
    this.savedChange.emit(savedId);
    this.flash(message);
  }

  private fail(err: unknown): void {
    this.busy.set(false);
    this.flash(newsErrorMessage(newsErrorCode(err)));
  }

  private flash(message: string): void {
    clearTimeout(this.feedbackTimer);
    this.feedback.set(message);
    this.feedbackTimer = setTimeout(() => this.feedback.set(''), FEEDBACK_MS);
  }
}
