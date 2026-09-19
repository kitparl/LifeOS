import { Component, OnInit, inject, signal } from '@angular/core';
import { buildMatchPairs, buildMcQuestions, MatchPair, McQuestion } from '../games/question-builder';
import { GameHistoryPage, GameSource, GameType, GameVocabularyItem } from '../models/vocabulary.models';
import { VocabularyService } from '../services/vocabulary.service';
import { GameMatchingBoardComponent } from './game-matching-board.component';
import { GameMcQuestionComponent } from './game-mc-question.component';

const MC_TYPES: GameType[] = ['meaning_quiz', 'synonym_quiz', 'antonym_quiz', 'fill_in_blank', 'example_completion'];
const QUESTION_COUNT = 8;

interface GameOption {
  id: GameType;
  label: string;
}

type Phase = 'setup' | 'playing' | 'done';

/** Games (PRD §28-30). One shared engine (multiple-choice + matching-pairs) drives all
 * 7 named game types via `games/question-builder.ts` — see the design doc rationale. */
@Component({
  selector: 'app-vocabulary-games',
  standalone: true,
  imports: [GameMcQuestionComponent, GameMatchingBoardComponent],
  template: `
    <div class="space-y-3">
      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      }

      @switch (phase()) {
        @case ('setup') {
          <div class="panel space-y-3 text-sm">
            <div>
              <p class="mb-1 font-semibold">Game</p>
              <div class="flex flex-wrap gap-2">
                @for (g of gameOptions; track g.id) {
                  <button
                    type="button"
                    class="btn-secondary !min-h-8 text-xs"
                    [class.!bg-[var(--primary)]]="gameType() === g.id"
                    (click)="gameType.set(g.id)"
                  >
                    {{ g.label }}
                  </button>
                }
              </div>
            </div>
            <div>
              <p class="mb-1 font-semibold">Source</p>
              <select class="input-field" [value]="source()" (change)="onSourceChange($event)">
                <option value="today">Today's Words</option>
                <option value="all_learned">All Learned</option>
                <option value="bookmarked">Bookmarked</option>
                <option value="needs_revision">Needs Revision</option>
                <option value="level">Specific Level</option>
              </select>
            </div>
            @if (source() === 'level') {
              <select class="input-field" [value]="level()" (change)="level.set($any($event.target).value)">
                @for (l of levels; track l) {
                  <option [value]="l">{{ l }}</option>
                }
              </select>
            }
            <button type="button" class="btn-primary" [disabled]="loading()" (click)="start()">
              {{ loading() ? 'Loading…' : 'Start Game' }}
            </button>
          </div>

          @if (history().length) {
            <div class="panel text-sm">
              <p class="mb-2 font-semibold">Recent games</p>
              @for (h of history(); track h.id) {
                <div class="flex items-center justify-between border-t py-1" style="border-color: var(--border)">
                  <span>{{ h.game_type }} · {{ h.source }}</span>
                  <span style="color: var(--text-muted)">{{ h.score }} / {{ h.total_questions }}</span>
                </div>
              }
            </div>
          }
        }
        @case ('playing') {
          @if (isMcGame()) {
            <p class="text-xs" style="color: var(--text-muted)">
              Question {{ currentIndex() + 1 }} / {{ mcQuestions().length }} · Score: {{ score() }}
            </p>
            @if (currentMcQuestion(); as q) {
              <app-game-mc-question [question]="q" (answer)="onMcAnswer(q.vocabularyId, $event)" />
              <button type="button" class="btn-secondary text-xs" (click)="nextMcQuestion()">Next</button>
            }
          } @else {
            <p class="text-xs" style="color: var(--text-muted)">Match each word to its pair · Score: {{ score() }}</p>
            <app-game-matching-board
              [pairs]="matchPairs()"
              (pairAnswered)="onMatchAnswer($event)"
              (allMatched)="finish()"
            />
          }
        }
        @case ('done') {
          <div class="panel text-sm">
            <p class="font-semibold">Game complete!</p>
            <p style="color: var(--text-muted)">Score: {{ score() }} / {{ totalQuestions() }}</p>
            <button type="button" class="btn-primary mt-2" (click)="reset()">Play again</button>
          </div>
        }
      }
    </div>
  `,
})
export class VocabularyGamesComponent implements OnInit {
  private readonly vocabularyService = inject(VocabularyService);

  readonly gameOptions: GameOption[] = [
    { id: 'meaning_quiz', label: 'Meaning Quiz' },
    { id: 'synonym_quiz', label: 'Synonym Quiz' },
    { id: 'antonym_quiz', label: 'Antonym Quiz' },
    { id: 'fill_in_blank', label: 'Fill in the Blank' },
    { id: 'example_completion', label: 'Example Completion' },
    { id: 'word_matching', label: 'Word Matching' },
    { id: 'meaning_matching', label: 'Meaning Matching' },
  ];
  readonly levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  readonly gameType = signal<GameType>('meaning_quiz');
  readonly source = signal<GameSource>('all_learned');
  readonly level = signal('A2');
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly history = signal<GameHistoryPage['items']>([]);

  readonly phase = signal<Phase>('setup');
  readonly sessionId = signal<string | null>(null);
  readonly score = signal(0);
  readonly totalQuestions = signal(0);

  readonly mcQuestions = signal<McQuestion[]>([]);
  readonly currentIndex = signal(0);
  readonly matchPairs = signal<MatchPair[]>([]);

  ngOnInit(): void {
    this.loadHistory();
  }

  isMcGame(): boolean {
    return MC_TYPES.includes(this.gameType());
  }

  currentMcQuestion(): McQuestion | undefined {
    return this.mcQuestions()[this.currentIndex()];
  }

  onSourceChange(event: Event): void {
    this.source.set((event.target as HTMLSelectElement).value as GameSource);
  }

  loadHistory(): void {
    this.vocabularyService.getGameHistory(5, 0).subscribe({
      next: (res) => this.history.set(res.items),
      error: () => {},
    });
  }

  start(): void {
    this.loading.set(true);
    this.error.set(null);
    const level = this.source() === 'level' ? this.level() : undefined;
    this.vocabularyService.getGameVocabulary(this.source(), level, 30).subscribe({
      next: (page) => {
        this.loading.set(false);
        if (!page.items.length) {
          this.error.set('No vocabulary available for that source yet.');
          return;
        }
        this.buildRound(page.items);
        this.vocabularyService
          .createGameSession(this.gameType(), this.source(), this.totalQuestions(), level)
          .subscribe({
            next: (session) => {
              this.sessionId.set(session.id);
              this.phase.set('playing');
            },
            error: () => this.error.set('Could not start the game — please try again.'),
          });
      },
      error: () => {
        this.loading.set(false);
        this.error.set('Could not load vocabulary for this game.');
      },
    });
  }

  private buildRound(pool: GameVocabularyItem[]): void {
    this.score.set(0);
    this.currentIndex.set(0);
    if (this.isMcGame()) {
      const questions = buildMcQuestions(pool, this.gameType() as never, QUESTION_COUNT);
      this.mcQuestions.set(questions);
      this.totalQuestions.set(questions.length);
    } else {
      const pairs = buildMatchPairs(pool, this.gameType() as never, Math.min(QUESTION_COUNT, pool.length));
      this.matchPairs.set(pairs);
      this.totalQuestions.set(pairs.length);
    }
  }

  onMcAnswer(vocabularyId: string, isCorrect: boolean): void {
    if (isCorrect) this.score.update((s) => s + 1);
    const sid = this.sessionId();
    if (sid) {
      this.vocabularyService.submitGameAnswer(sid, vocabularyId, this.gameType(), isCorrect).subscribe({
        error: () => {},
      });
    }
  }

  nextMcQuestion(): void {
    if (this.currentIndex() + 1 >= this.mcQuestions().length) {
      this.finish();
    } else {
      this.currentIndex.update((i) => i + 1);
    }
  }

  onMatchAnswer(event: { vocabularyId: string; isCorrect: boolean }): void {
    if (event.isCorrect) this.score.update((s) => s + 1);
    const sid = this.sessionId();
    if (sid) {
      this.vocabularyService.submitGameAnswer(sid, event.vocabularyId, this.gameType(), event.isCorrect).subscribe({
        error: () => {},
      });
    }
  }

  finish(): void {
    const sid = this.sessionId();
    if (sid) {
      this.vocabularyService.completeGameSession(sid).subscribe({
        next: () => this.loadHistory(),
        error: () => {},
      });
    }
    this.phase.set('done');
  }

  reset(): void {
    this.phase.set('setup');
    this.sessionId.set(null);
  }
}
