import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { map } from 'rxjs';
import { ChipOption, ChipRowComponent } from '../../../shared/chip-row/chip-row.component';
import { DifficultyBadgeComponent } from '../components/difficulty-badge.component';
import { DsaStateComponent } from '../components/dsa-state.component';
import { DsaNoteEditorComponent } from '../components/dsa-note-editor.component';
import { ProgressIconComponent } from '../components/progress-icon.component';
import { PatternDetail, ProblemRow } from '../models/dsa.models';
import { DsaService } from '../services/dsa.service';

const DIFFICULTY_FILTERS: ChipOption[] = [
  { id: '', label: 'All' },
  { id: 'easy', label: 'Easy' },
  { id: 'medium', label: 'Medium' },
  { id: 'hard', label: 'Hard' },
];
const STATUS_FILTERS: ChipOption[] = [
  { id: '', label: 'All' },
  { id: 'not_started', label: 'Not started' },
  { id: 'attempted', label: 'Attempted' },
  { id: 'solved', label: 'Solved' },
];

@Component({
  selector: 'app-dsa-pattern-problems-page',
  standalone: true,
  imports: [
    RouterLink,
    LucideDynamicIcon,
    ChipRowComponent,
    DifficultyBadgeComponent,
    DsaStateComponent,
    DsaNoteEditorComponent,
    ProgressIconComponent,
  ],
  template: `
    <div class="mx-auto max-w-4xl space-y-4">
      <a class="btn-ghost !min-h-8 !px-2 text-xs" routerLink="../.." data-testid="dsa-problems-back-link">
        <svg class="h-3.5 w-3.5" lucideIcon="chevron-left" aria-hidden="true"></svg>
        Patterns
      </a>

      @if (loading()) {
        <div class="panel skeleton h-64"></div>
      } @else if (notFound()) {
        <app-dsa-state title="Pattern not found" />
      } @else if (error()) {
        <app-dsa-state title="We couldn't load this pattern." [retryable]="true" (retry)="load()" />
      } @else if (pattern()) {
        @let p = pattern()!;
        <header class="space-y-1">
          <div class="flex items-start justify-between gap-3">
            <h1 class="text-xl font-semibold">{{ p.number }}. {{ p.name }}</h1>
            <button type="button" class="btn-secondary !min-h-8 shrink-0 !px-3 text-xs" data-testid="dsa-pattern-note-button"
              [class.active]="noteOpen()" [attr.aria-expanded]="noteOpen()" aria-controls="dsa-pattern-note"
              (click)="noteOpen.set(!noteOpen())">
              <svg class="h-3.5 w-3.5" lucideIcon="notebook-pen" aria-hidden="true"></svg>
              Note
            </button>
          </div>
          <p class="text-sm" style="color: var(--text-muted)">{{ p.description }}</p>
          <p class="text-xs" style="color: var(--text-muted)">{{ p.solved }}/{{ p.total }} solved</p>
        </header>

        @if (noteOpen()) {
          <section id="dsa-pattern-note" class="panel space-y-2" aria-label="Pattern note">
            <h2 class="section-heading">Your note on {{ p.name }}</h2>
            <app-dsa-note-editor scope="patterns" [slug]="p.slug" />
          </section>
        }

        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
          <app-chip-row
            label="Difficulty"
            testIdPrefix="dsa-difficulty"
            [options]="difficultyFilters"
            [selected]="difficulty()"
            (selectedChange)="setFilter('difficulty', $event)"
          />
          <app-chip-row
            label="Status"
            testIdPrefix="dsa-status"
            [options]="statusFilters"
            [selected]="status()"
            (selectedChange)="setFilter('status', $event)"
          />
        </div>

        @if (visible().length === 0) {
          <app-dsa-state title="No problems match these filters" />
        } @else {
          <div class="panel !p-0 overflow-hidden">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs" style="color: var(--text-muted); border-bottom: 1px solid var(--border)">
                  <th class="w-10 px-3 py-2" scope="col"><span class="sr-only">Status</span></th>
                  <th class="px-3 py-2" scope="col">Problem</th>
                  <th class="w-24 px-3 py-2" scope="col">Difficulty</th>
                </tr>
              </thead>
              <tbody>
                @for (row of visible(); track row.slug) {
                  <tr style="border-bottom: 1px solid var(--border)" [attr.data-testid]="'dsa-problem-row-' + row.slug">
                    <td class="px-3 py-2"><app-dsa-progress-icon [status]="row.progress" /></td>
                    <td class="px-3 py-2">
                      <div class="flex flex-wrap items-center gap-1.5">
                        @if (row.status === 'published') {
                          <a class="link" [routerLink]="['../../problems', row.slug]" [attr.data-testid]="'dsa-problem-link-' + row.slug">
                            {{ row.title }}
                          </a>
                        } @else {
                          <span style="color: var(--text-muted)">{{ row.title }}</span>
                          <span class="chip !py-0 text-[0.6875rem]">Coming soon</span>
                        }
                        @if (row.tags.includes('blind75')) {
                          <span class="chip !py-0 text-[0.6875rem]" title="Blind 75">B75</span>
                        }
                        @if (row.is_variant) {
                          <span class="chip !py-0 text-[0.6875rem]" title="Our own definition of a course-specific title">Variant</span>
                        }
                      </div>
                    </td>
                    <td class="px-3 py-2"><app-dsa-difficulty-badge [difficulty]="row.difficulty" /></td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      }
    </div>
  `,
})
export class PatternProblemsPageComponent implements OnInit {
  private readonly dsa = inject(DsaService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly difficultyFilters = DIFFICULTY_FILTERS;
  readonly statusFilters = STATUS_FILTERS;
  readonly pattern = signal<PatternDetail | null>(null);
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly notFound = signal(false);
  readonly noteOpen = signal(false);

  private readonly query = toSignal(this.route.queryParamMap, { requireSync: true });
  readonly difficulty = computed(() => this.query().get('difficulty') ?? '');
  readonly status = computed(() => this.query().get('status') ?? '');

  readonly visible = computed<ProblemRow[]>(() => {
    const p = this.pattern();
    if (!p) return [];
    const difficulty = this.difficulty();
    const status = this.status();
    return p.problems.filter(
      (row) => (!difficulty || row.difficulty === difficulty) && (!status || row.progress === status),
    );
  });

  private readonly slug = toSignal(this.route.paramMap.pipe(map((params) => params.get('slug') ?? '')), {
    initialValue: '',
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(false);
    this.notFound.set(false);
    this.dsa.pattern(this.slug()).subscribe({
      next: (p) => {
        this.pattern.set(p);
        this.loading.set(false);
      },
      error: (err: { status?: number }) => {
        if (err.status === 404) this.notFound.set(true);
        else this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  setFilter(key: 'difficulty' | 'status', value: string): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { [key]: value || null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }
}
