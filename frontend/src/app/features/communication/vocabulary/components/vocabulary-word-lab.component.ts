import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import {
  WordLabGameRound,
  WordLabGameType,
  WordLabLookupResponse,
  WordLabMode,
  WordLabSaveResponse,
  WordLabStatus,
} from '../models/vocabulary.models';
import { VocabularyService } from '../services/vocabulary.service';

type WordLabTool = WordLabMode | 'game';

const TOOLS: { id: WordLabTool; label: string; placeholder: string }[] = [
  { id: 'dictionary', label: 'Dictionary', placeholder: 'Look up a word' },
  { id: 'synonyms', label: 'Synonyms', placeholder: 'Find synonyms for…' },
  {
    id: 'explorer',
    label: 'Explorer',
    placeholder: 'Describe an idea, e.g. fear of heights',
  },
  { id: 'rhymes', label: 'Rhymes', placeholder: 'Find rhymes for…' },
  { id: 'game', label: 'Game', placeholder: '' },
];

const GAMES: { id: WordLabGameType; label: string }[] = [
  { id: 'guess_word', label: 'Guess the word' },
  { id: 'guess_meaning', label: 'Guess the meaning' },
  { id: 'scramble', label: 'Scramble' },
];

const ERROR_MESSAGES: Record<string, string> = {
  invalid_credential: 'Wordnik rejected the API key. Check it in Integrations.',
  rate_limit: 'Wordnik hourly limit reached. Try again later.',
  timeout: 'Wordnik took too long to answer. Try again.',
};

/** Wordnik-backed word tools: one search box, tool chips, one results region (Word Lab tab). */
@Component({
  selector: 'app-vocabulary-word-lab',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="panel space-y-3 text-sm">
      @if (!status()) {
        <p style="color: var(--text-muted)">Loading Word Lab…</p>
      } @else if (!status()!.connected) {
        <div class="space-y-2" data-testid="word-lab-locked">
          <p class="font-semibold">Connect Wordnik to use Word Lab</p>
          <p style="color: var(--text-muted)">
            Word Lab looks words up with your own Wordnik API key. Add it in
            Integrations, then come back here.
          </p>
          <a
            class="btn-primary inline-flex text-xs"
            routerLink="/integrations"
            fragment="wordnik"
            >Connect in Integrations</a
          >
        </div>
      } @else {
        <div class="flex flex-wrap items-center justify-between gap-2">
          <p
            class="text-xs"
            style="color: var(--text-muted)"
            data-testid="word-lab-usage"
          >
            Usage remaining: {{ usageLabel() }}
          </p>
          @if (tool() !== 'game') {
            <form
              class="flex flex-1 justify-end gap-2"
              style="min-width: 14rem"
              (submit)="$event.preventDefault(); search()"
            >
              <input
                type="text"
                class="input-field w-full sm:max-w-xs"
                maxlength="200"
                aria-label="Word Lab search"
                [placeholder]="placeholder()"
                [value]="query()"
                (input)="query.set($any($event.target).value)"
              />
              <button
                type="submit"
                class="btn-primary text-xs"
                [disabled]="busy() || !query().trim()"
              >
                Go
              </button>
            </form>
          }
        </div>

        <div
          class="flex flex-wrap gap-2"
          role="group"
          aria-label="Word Lab tool"
        >
          @for (t of tools; track t.id) {
            <button
              type="button"
              class="btn-secondary !min-h-8 text-xs"
              [class.!bg-[var(--primary)]]="tool() === t.id"
              [attr.aria-pressed]="tool() === t.id"
              (click)="selectTool(t.id)"
            >
              {{ t.label }}
            </button>
          }
        </div>

        @if (error()) {
          <p style="color: var(--danger)">{{ error() }}</p>
        }
        @if (busy()) {
          <p style="color: var(--text-muted)">Loading…</p>
        }

        @if (tool() === 'game') {
          <div class="space-y-3">
            <div
              class="flex flex-wrap gap-2"
              role="group"
              aria-label="Game type"
            >
              @for (g of games; track g.id) {
                <button
                  type="button"
                  class="btn-secondary !min-h-8 text-xs"
                  [class.!bg-[var(--primary)]]="gameType() === g.id"
                  [attr.aria-pressed]="gameType() === g.id"
                  (click)="selectGame(g.id)"
                >
                  {{ g.label }}
                </button>
              }
            </div>
            @if (round(); as r) {
              <div class="space-y-2">
                @if (r.type === 'scramble') {
                  <p class="text-xs" style="color: var(--text-muted)">
                    Unscramble the word
                  </p>
                  <p class="text-lg font-semibold tracking-widest">
                    {{ r.prompt }}
                  </p>
                  <p><span class="font-medium">Meaning:</span> {{ r.hint }}</p>
                  <form
                    class="flex gap-2"
                    (submit)="$event.preventDefault(); checkScramble()"
                  >
                    <input
                      type="text"
                      class="input-field"
                      aria-label="Your answer"
                      [value]="guess()"
                      [disabled]="revealed()"
                      (input)="guess.set($any($event.target).value)"
                    />
                    <button
                      type="submit"
                      class="btn-primary text-xs"
                      [disabled]="revealed() || !guess().trim()"
                    >
                      Check
                    </button>
                  </form>
                } @else {
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{
                      r.type === 'guess_word'
                        ? 'Which word has this meaning?'
                        : 'What does this word mean?'
                    }}
                  </p>
                  <p class="font-semibold">{{ r.prompt }}</p>
                  <div class="grid gap-2 sm:grid-cols-2">
                    @for (option of r.options; track $index) {
                      <button
                        type="button"
                        class="btn-secondary text-left text-xs"
                        [disabled]="revealed()"
                        [style.border-color]="optionColor($index)"
                        (click)="pick($index)"
                      >
                        {{ option }}
                      </button>
                    }
                  </div>
                }
                @if (feedback()) {
                  <p
                    [style.color]="
                      correct() ? 'var(--success)' : 'var(--danger)'
                    "
                  >
                    {{ feedback() }}
                  </p>
                }
                <div class="flex gap-2">
                  @if (r.type === 'scramble' && !revealed()) {
                    <button
                      type="button"
                      class="btn-ghost text-xs"
                      (click)="reveal()"
                    >
                      Reveal
                    </button>
                  }
                  <button
                    type="button"
                    class="btn-primary text-xs"
                    [disabled]="busy()"
                    (click)="loadRound()"
                  >
                    Next
                  </button>
                </div>
              </div>
            }
          </div>
        } @else {
          @if (result(); as res) {
            @if (res.mode === 'dictionary') {
              @if (res.definitions.length) {
                <div class="space-y-2">
                  <p class="text-base font-semibold">{{ res.query }}</p>
                  <div>
                    <p class="font-medium">Meaning</p>
                    <ul class="list-disc pl-5 space-y-1">
                      @for (d of res.definitions; track $index) {
                        <li>
                          @if (d.part_of_speech) {
                            <span
                              class="text-xs"
                              style="color: var(--text-muted)"
                              >{{ d.part_of_speech }} ·
                            </span>
                          }
                          {{ d.text }}
                        </li>
                      }
                    </ul>
                  </div>
                  @if (res.example) {
                    <div>
                      <p class="font-medium">Example</p>
                      <p>{{ res.example }}</p>
                    </div>
                  }
                  <div class="flex flex-wrap items-center gap-2">
                    @if (!saved()) {
                      <button
                        type="button"
                        class="btn-primary text-xs"
                        [disabled]="busy()"
                        (click)="save()"
                      >
                        Save as vocabulary
                      </button>
                    } @else {
                      <span class="text-xs" style="color: var(--success)">
                        {{
                          saved()!.created
                            ? 'Saved to vocabulary'
                            : 'Already in vocabulary'
                        }}
                      </span>
                      <a
                        class="text-xs underline"
                        [routerLink]="[
                          '/communication/vocabulary',
                          saved()!.id,
                        ]"
                        >Open detail</a
                      >
                    }
                  </div>
                </div>
              } @else {
                <p style="color: var(--text-muted)">
                  No definitions found for "{{ res.query }}".
                </p>
              }
            } @else {
              @if (res.words.length) {
                <div class="flex flex-wrap gap-2">
                  @for (w of res.words; track w.word) {
                    <button
                      type="button"
                      class="chip"
                      [title]="w.hint ?? 'Look up ' + w.word"
                      (click)="define(w.word)"
                    >
                      {{ w.word }}
                    </button>
                  }
                </div>
                <p class="text-xs" style="color: var(--text-muted)">
                  Select a word to see its meaning.
                </p>
              } @else {
                <p style="color: var(--text-muted)">
                  No results for "{{ res.query }}".
                </p>
              }
            }
          }
        }
      }
    </div>
  `,
})
export class VocabularyWordLabComponent implements OnInit {
  private readonly vocabulary = inject(VocabularyService);

  readonly tools = TOOLS;
  readonly games = GAMES;

  readonly status = signal<WordLabStatus | null>(null);
  readonly tool = signal<WordLabTool>('dictionary');
  readonly query = signal('');
  readonly result = signal<WordLabLookupResponse | null>(null);
  readonly saved = signal<WordLabSaveResponse | null>(null);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);

  readonly gameType = signal<WordLabGameType>('guess_word');
  readonly round = signal<WordLabGameRound | null>(null);
  readonly picked = signal<number | null>(null);
  readonly guess = signal('');
  readonly revealed = signal(false);
  readonly correct = signal(false);
  readonly feedback = signal<string | null>(null);

  readonly placeholder = computed(
    () => TOOLS.find((t) => t.id === this.tool())?.placeholder ?? '',
  );
  readonly usageLabel = computed(() => {
    const pct = this.status()?.usage_remaining_pct;
    return pct === null || pct === undefined ? 'Unknown' : `${pct}%`;
  });

  ngOnInit(): void {
    this.vocabulary.wordLabStatus().subscribe({
      next: (s) => this.status.set(s),
      error: () =>
        this.status.set({ connected: false, usage_remaining_pct: null }),
    });
  }

  selectTool(tool: WordLabTool): void {
    if (tool === this.tool()) return;
    this.tool.set(tool);
    this.error.set(null);
    if (tool === 'game') {
      this.loadRound();
    } else if (this.query().trim()) {
      this.search();
    } else {
      this.result.set(null);
    }
  }

  define(word: string): void {
    this.tool.set('dictionary');
    this.query.set(word);
    this.search();
  }

  search(): void {
    const q = this.query().trim();
    const mode = this.tool();
    if (!q || mode === 'game') return;
    this.begin();
    this.saved.set(null);
    this.vocabulary.wordLabLookup(q, mode).subscribe({
      next: (res) => {
        this.result.set(res);
        this.setUsage(res.usage_remaining_pct);
        this.busy.set(false);
      },
      error: (err) => this.fail(err),
    });
  }

  save(): void {
    const res = this.result();
    const first = res?.definitions[0];
    if (!res || !first) return;
    this.begin();
    this.vocabulary
      .wordLabSave({
        term: res.query,
        definition: first.text,
        part_of_speech: first.part_of_speech,
        example: res.example,
      })
      .subscribe({
        next: (saved) => {
          this.saved.set(saved);
          this.busy.set(false);
        },
        error: (err) => this.fail(err),
      });
  }

  selectGame(type: WordLabGameType): void {
    if (type === this.gameType() && this.round()) return;
    this.gameType.set(type);
    this.loadRound();
  }

  loadRound(): void {
    this.begin();
    this.round.set(null);
    this.picked.set(null);
    this.guess.set('');
    this.revealed.set(false);
    this.feedback.set(null);
    this.vocabulary.wordLabGame(this.gameType()).subscribe({
      next: (round) => {
        this.round.set(round);
        this.setUsage(round.usage_remaining_pct);
        this.busy.set(false);
      },
      error: (err) => this.fail(err),
    });
  }

  pick(index: number): void {
    const r = this.round();
    if (!r || this.revealed()) return;
    this.picked.set(index);
    this.revealed.set(true);
    const isCorrect = index === r.answer_index;
    this.correct.set(isCorrect);
    this.feedback.set(
      isCorrect
        ? 'Correct!'
        : `Not quite — the answer is "${r.options[r.answer_index ?? 0]}".`,
    );
  }

  checkScramble(): void {
    const r = this.round();
    if (!r?.answer) return;
    const isCorrect = this.guess().trim().toLowerCase() === r.answer;
    this.correct.set(isCorrect);
    if (isCorrect) {
      this.revealed.set(true);
      this.feedback.set('Correct!');
    } else {
      this.feedback.set('Not quite — try again or reveal the answer.');
    }
  }

  reveal(): void {
    const r = this.round();
    if (!r?.answer) return;
    this.revealed.set(true);
    this.correct.set(false);
    this.feedback.set(`The word was "${r.answer}".`);
  }

  optionColor(index: number): string | null {
    if (!this.revealed()) return null;
    if (index === this.round()?.answer_index) return 'var(--success)';
    return index === this.picked() ? 'var(--danger)' : null;
  }

  private begin(): void {
    this.busy.set(true);
    this.error.set(null);
  }

  private setUsage(pct: number | null): void {
    const s = this.status();
    if (s) this.status.set({ ...s, usage_remaining_pct: pct });
  }

  private fail(err: HttpErrorResponse): void {
    this.busy.set(false);
    const detail = err?.error?.detail;
    const code: string | undefined =
      typeof detail === 'object' && detail ? detail.code : undefined;
    if (code === 'missing_credential') {
      this.status.set({ connected: false, usage_remaining_pct: null });
      return;
    }
    if (code === 'rate_limit') this.setUsage(0);
    const message =
      typeof detail === 'string'
        ? detail
        : typeof detail === 'object'
          ? detail?.message
          : null;
    this.error.set(
      (code && ERROR_MESSAGES[code]) ||
        message ||
        'Word Lab request failed. Try again.',
    );
  }
}
