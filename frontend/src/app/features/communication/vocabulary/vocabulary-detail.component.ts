import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { PersonalExample, VocabularyDetailResponse } from './models/vocabulary.models';
import { VocabularyService } from './services/vocabulary.service';

/** Full vocabulary detail (PRD §25): every field, bookmark toggle, unlimited personal
 * examples. Kept off the concise daily card per PRD §49. */
@Component({
  selector: 'app-vocabulary-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="space-y-3">
      <a class="text-xs underline" [routerLink]="['/communication']">← Back to Communication</a>

      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      }

      @if (data(); as d) {
        <div class="panel space-y-2 text-sm">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">{{ d.vocabulary.term }}</h2>
            <button type="button" class="btn-secondary !min-h-8 text-xs" [disabled]="busy()" (click)="toggleBookmark()">
              {{ d.is_bookmarked ? '♥ Bookmarked' : '♡ Bookmark' }}
            </button>
          </div>
          <p style="color: var(--text-muted)">
            {{ d.vocabulary.part_of_speech }} · {{ d.vocabulary.level }} · {{ d.vocabulary.type }}
            @if (d.vocabulary.pronunciation) {
              · {{ d.vocabulary.pronunciation }}
            }
          </p>

          <p><strong>Meaning:</strong> {{ d.vocabulary.simple_meaning }}</p>
          @if (d.vocabulary.meaning_in_context) {
            <p><strong>In context:</strong> {{ d.vocabulary.meaning_in_context }}</p>
          }
          <p><strong>Example:</strong> {{ d.vocabulary.example }}</p>
          @if (d.vocabulary.example_context) {
            <p style="color: var(--text-muted)">{{ d.vocabulary.example_context }}</p>
          }
          @if (d.vocabulary.usage_note) {
            <p><strong>Usage note:</strong> {{ d.vocabulary.usage_note }}</p>
          }
          @if (d.vocabulary.communication_intents.length) {
            <p><strong>Used for:</strong> {{ d.vocabulary.communication_intents.join(', ') }}</p>
          }
          @if (d.vocabulary.topics.length) {
            <p><strong>Topics:</strong> {{ d.vocabulary.topics.join(', ') }}</p>
          }
          @if (d.vocabulary.common_collocations.length) {
            <p><strong>Common collocations:</strong> {{ d.vocabulary.common_collocations.join(', ') }}</p>
          }
          @if (d.vocabulary.synonyms.length) {
            <p><strong>Synonyms:</strong> {{ d.vocabulary.synonyms.join(', ') }}</p>
          }
          @if (d.vocabulary.antonyms.length) {
            <p><strong>Antonyms:</strong> {{ d.vocabulary.antonyms.join(', ') }}</p>
          }
          <p style="color: var(--text-muted)">
            {{ d.vocabulary.commonness }} · {{ d.vocabulary.formality }} · priority: {{ d.vocabulary.learning_priority }}
          </p>
          @if (d.mastery_level > 0 || d.times_reviewed > 0) {
            <p style="color: var(--text-muted)">Mastery: {{ d.mastery_level }} / 5 · reviewed {{ d.times_reviewed }} times</p>
          }
        </div>

        <div class="panel space-y-2 text-sm">
          <h3 class="font-semibold">My examples ({{ examples().length }})</h3>
          @for (ex of examples(); track ex.id) {
            <div class="flex items-start justify-between gap-2 border-t pt-2" style="border-color: var(--border)">
              <div>
                <p>"{{ ex.sentence }}"</p>
                @if (ex.notes) {
                  <p class="text-xs" style="color: var(--text-muted)">{{ ex.notes }}</p>
                }
              </div>
              <button type="button" class="text-xs underline" (click)="deleteExample(ex.id)">Delete</button>
            </div>
          }

          <div class="flex flex-wrap gap-2 pt-2">
            <input
              type="text"
              class="input-field flex-1"
              placeholder="Add your own example sentence..."
              [value]="draftSentence()"
              (input)="draftSentence.set($any($event.target).value)"
            />
            <button type="button" class="btn-secondary !min-h-8 text-xs" [disabled]="!draftSentence().trim()" (click)="addExample()">
              Add example
            </button>
          </div>
        </div>
      }
    </div>
  `,
})
export class VocabularyDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly vocabularyService = inject(VocabularyService);

  readonly data = signal<VocabularyDetailResponse | null>(null);
  readonly examples = signal<PersonalExample[]>([]);
  readonly error = signal<string | null>(null);
  readonly busy = signal(false);
  readonly draftSentence = signal('');

  private get vocabularyId(): string {
    return this.route.snapshot.paramMap.get('id') ?? '';
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    const id = this.vocabularyId;
    this.vocabularyService.getDetail(id).subscribe({
      next: (res) => this.data.set(res),
      error: () => this.error.set('Could not load that vocabulary item.'),
    });
    this.vocabularyService.listExamples(id).subscribe({
      next: (res) => this.examples.set(res),
      error: () => {},
    });
  }

  toggleBookmark(): void {
    const d = this.data();
    if (!d) return;
    this.busy.set(true);
    const onDone = () => {
      this.busy.set(false);
      this.data.set({ ...d, is_bookmarked: !d.is_bookmarked });
    };
    const onError = () => {
      this.busy.set(false);
      this.error.set('Could not update the bookmark — please try again.');
    };
    if (d.is_bookmarked) {
      this.vocabularyService.removeBookmark(this.vocabularyId).subscribe({ next: onDone, error: onError });
    } else {
      this.vocabularyService.addBookmark(this.vocabularyId).subscribe({ next: onDone, error: onError });
    }
  }

  addExample(): void {
    const sentence = this.draftSentence().trim();
    if (!sentence) return;
    this.vocabularyService.addExample(this.vocabularyId, sentence).subscribe({
      next: (example) => {
        this.examples.set([example, ...this.examples()]);
        this.draftSentence.set('');
      },
      error: () => this.error.set('Could not save that example — please try again.'),
    });
  }

  deleteExample(exampleId: string): void {
    this.vocabularyService.deleteExample(exampleId).subscribe({
      next: () => this.examples.set(this.examples().filter((e) => e.id !== exampleId)),
      error: () => this.error.set('Could not delete that example — please try again.'),
    });
  }
}
