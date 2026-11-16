import { Component, DestroyRef, HostListener, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { catchError, debounceTime, map, of, switchMap, tap } from 'rxjs';
import { localIsoDate } from '../../core/utils/date';
import { TimelinePreferencesService } from '../../core/services/timeline-preferences.service';
import {
  TIMELINE_SOURCE_STYLE,
  TIMELINE_ZOOMS,
  TimelineItem,
  TimelineSource,
  TimelineSourceKey,
  TimelineZoom,
} from './models/timeline.models';
import { TimelineService } from './services/timeline.service';

interface DateRange {
  start: Date;
  end: Date;
}

interface TimelineDay {
  key: string;
  date: Date;
  items: TimelineItem[];
  isToday: boolean;
  isPast: boolean;
}

interface TimelineMonth {
  key: string;
  label: string;
  days: TimelineDay[];
}

interface RibbonSegment {
  source: TimelineSourceKey;
  share: number;
}

interface RibbonDay {
  key: string;
  label: string;
  count: number;
  segments: RibbonSegment[];
  isToday: boolean;
  isWeekend: boolean;
  monthStart: string | null;
}

const MS_PER_DAY = 86_400_000;

function addDays(date: Date, days: number): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

function fromDayKey(key: string): Date {
  return new Date(`${key}T00:00:00`);
}

function dayDiff(from: Date, to: Date): number {
  return Math.round((fromDayKey(localIsoDate(to)).getTime() - fromDayKey(localIsoDate(from)).getTime()) / MS_PER_DAY);
}

function rangeFor(anchor: Date, zoom: TimelineZoom): DateRange {
  const y = anchor.getFullYear();
  const m = anchor.getMonth();
  if (zoom === 'week') {
    const start = addDays(anchor, -((anchor.getDay() + 6) % 7));
    return { start, end: addDays(start, 6) };
  }
  if (zoom === 'month') {
    return { start: new Date(y, m, 1), end: new Date(y, m + 1, 0) };
  }
  return { start: new Date(y, m - 1, 1), end: new Date(y, m + 2, 0) };
}

function shiftAnchor(anchor: Date, zoom: TimelineZoom, direction: 1 | -1): Date {
  if (zoom === 'week') return addDays(anchor, 7 * direction);
  const months = zoom === 'month' ? 1 : 3;
  return new Date(anchor.getFullYear(), anchor.getMonth() + months * direction, 1);
}

function itemDayKey(item: TimelineItem): string {
  return localIsoDate(new Date(item.starts_at));
}

@Component({
  selector: 'app-timeline-page',
  standalone: true,
  imports: [LucideDynamicIcon],
  template: `
    <div class="space-y-3">
      <!-- ====== Toolbar ====== -->
      <div class="panel space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-1.5">
            <button type="button" class="btn-ghost !px-2" (click)="shift(-1)" aria-label="Previous range">
              <svg class="h-4 w-4" lucideIcon="chevron-left" aria-hidden="true"></svg>
            </button>
            <h2 class="min-w-[10rem] text-center text-sm font-semibold" style="color: var(--text)">{{ rangeLabel() }}</h2>
            <button type="button" class="btn-ghost !px-2" (click)="shift(1)" aria-label="Next range">
              <svg class="h-4 w-4" lucideIcon="chevron-right" aria-hidden="true"></svg>
            </button>
            <button type="button" class="btn-secondary text-xs" (click)="goToday()">Today</button>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <div class="tl-segmented" role="group" aria-label="Zoom">
              @for (z of zooms; track z.value) {
                <button
                  type="button"
                  [class.tl-segmented__on]="zoom() === z.value"
                  [attr.aria-pressed]="zoom() === z.value"
                  (click)="setZoom(z.value)"
                >
                  {{ z.label }}
                </button>
              }
            </div>
            <div class="relative">
              <svg
                class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2"
                style="color: var(--text-faint)"
                lucideIcon="search"
                aria-hidden="true"
              ></svg>
              <input
                type="search"
                class="input-field !pl-8 text-sm w-44"
                placeholder="Filter timeline…"
                aria-label="Filter timeline"
                [value]="query()"
                (input)="onQuery($event)"
              />
            </div>
          </div>
        </div>

        <!-- Source toggles (persisted per user) -->
        <div class="flex flex-wrap gap-1.5" role="group" aria-label="Sources">
          @for (s of sources(); track s.key) {
            <button
              type="button"
              class="tl-chip"
              [class.tl-chip--off]="!isEnabled(s)"
              [style.--tl-color]="style(s.key).color"
              [attr.aria-pressed]="isEnabled(s)"
              (click)="toggleSource(s)"
            >
              <svg class="h-3.5 w-3.5" [lucideIcon]="style(s.key).icon" aria-hidden="true"></svg>
              {{ s.label }}
              @if (isEnabled(s)) {
                <span class="tl-chip__count">{{ sourceCounts()[s.key] ?? 0 }}</span>
              }
            </button>
          }
        </div>

        <!-- Density ribbon: one bar per day, click to jump -->
        <div class="tl-ribbon" [class.tl-ribbon--dense]="ribbon().length > 40" aria-label="Activity per day">
          @for (d of ribbon(); track d.key) {
            <button
              type="button"
              class="tl-ribbon__day"
              [class.tl-ribbon__day--today]="d.isToday"
              [class.tl-ribbon__day--weekend]="d.isWeekend"
              [class.tl-ribbon__day--focus]="focusedDay() === d.key"
              [title]="d.label + ' · ' + d.count + (d.count === 1 ? ' item' : ' items')"
              [disabled]="d.count === 0 && !d.isToday"
              (click)="jumpTo(d.key)"
            >
              <span class="tl-ribbon__bar" [style.height.%]="barHeight(d.count)">
                @for (seg of d.segments; track seg.source) {
                  <span [style.flex-grow]="seg.share" [style.background]="style(seg.source).color"></span>
                }
              </span>
              @if (d.monthStart) {
                <span class="tl-ribbon__month">{{ d.monthStart }}</span>
              }
            </button>
          }
        </div>

        <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs" style="color: var(--text-muted)">
          <span><strong style="color: var(--text)">{{ filtered().length }}</strong> items</span>
          <span>{{ pastCount() }} done / past</span>
          <span>{{ filtered().length - pastCount() }} upcoming</span>
          @if (nextUp(); as next) {
            <button type="button" class="tl-next" (click)="openFromNext(next)">
              Next up: <strong>{{ next.title }}</strong> · {{ relative(next) }}
            </button>
          }
          <span class="hidden sm:inline ml-auto" style="color: var(--text-faint)">
            <kbd>←</kbd>/<kbd>→</kbd> move · <kbd>t</kbd> today
          </span>
        </div>
      </div>

      <!-- ====== Timeline ====== -->
      @if (error()) {
        <div class="panel empty-state">
          <div class="empty-state__title">Couldn't load the timeline</div>
          <div class="empty-state__desc">{{ error() }}</div>
          <button type="button" class="btn-secondary text-xs" (click)="reload()">Retry</button>
        </div>
      } @else if (loading() && items().length === 0) {
        <div class="panel empty-state"><div class="empty-state__desc">Loading timeline…</div></div>
      } @else if (months().length === 0) {
        <div class="panel empty-state">
          <svg class="h-8 w-8" style="opacity: 0.4" lucideIcon="chart-gantt" aria-hidden="true"></svg>
          <div class="empty-state__title">Nothing in this range</div>
          <div class="empty-state__desc">Try another range, clear the filter, or turn on more sources.</div>
        </div>
      } @else {
        <div class="tl" [class.tl--loading]="loading()">
          @for (month of months(); track month.key) {
            <div class="tl-month">{{ month.label }}</div>
            @for (day of month.days; track day.key; let i = $index) {
              <section
                class="tl-day"
                [id]="'tl-day-' + day.key"
                [class.tl-day--right]="i % 2 === 1"
                [class.tl-day--past]="day.isPast"
                [class.tl-day--focus]="focusedDay() === day.key"
              >
                <div class="tl-node" [class.tl-node--today]="day.isToday">
                  <span class="tl-node__dow">{{ day.isToday ? 'Today' : weekday(day.date) }}</span>
                  <span class="tl-node__num">{{ day.date.getDate() }}</span>
                </div>
                <div class="tl-cards">
                  @for (item of day.items; track item.id) {
                    <article
                      class="tl-card"
                      [class.tl-card--open]="expandedId() === item.id"
                      [style.--tl-color]="style(item.source).color"
                      tabindex="0"
                      role="button"
                      [attr.aria-expanded]="expandedId() === item.id"
                      (click)="toggleExpanded(item.id)"
                      (keydown.enter)="toggleExpanded(item.id)"
                    >
                      <div class="flex items-start gap-2.5">
                        <span class="tl-card__icon">
                          <svg class="h-4 w-4" [lucideIcon]="style(item.source).icon" aria-hidden="true"></svg>
                        </span>
                        <div class="min-w-0 flex-1">
                          <div class="flex items-center gap-2 text-[11px]" style="color: var(--text-muted)">
                            <span>{{ timeLabel(item) }}</span>
                            @if (spanLabel(item); as span) {
                              <span class="tl-pill">{{ span }}</span>
                            }
                            @if (item.status) {
                              <span class="tl-pill ml-auto">{{ item.status }}</span>
                            }
                          </div>
                          <div class="tl-card__title">{{ item.title }}</div>
                          @if (item.subtitle) {
                            <div class="tl-card__sub" [class.tl-card__sub--full]="expandedId() === item.id">
                              {{ item.subtitle }}
                            </div>
                          }
                        </div>
                      </div>
                      @if (expandedId() === item.id) {
                        <div class="tl-card__detail">
                          <span>{{ sourceLabel(item.source) }} · {{ fullDate(item) }} · {{ relative(item) }}</span>
                          @if (item.route) {
                            <button type="button" class="btn-primary text-xs" (click)="open(item, $event)">
                              Open
                              <svg class="h-3.5 w-3.5" lucideIcon="external-link" aria-hidden="true"></svg>
                            </button>
                          }
                        </div>
                      }
                    </article>
                  } @empty {
                    <div class="tl-card tl-card--empty">Nothing scheduled today</div>
                  }
                </div>
              </section>
            }
          }
        </div>
      }
    </div>
  `,
  styles: [
    `
      .tl-segmented {
        display: inline-flex;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        overflow: hidden;
      }
      .tl-segmented button {
        padding: 0.3rem 0.7rem;
        font-size: 0.75rem;
        color: var(--text-muted);
        background: var(--surface);
      }
      .tl-segmented button + button {
        border-left: 1px solid var(--border);
      }
      .tl-segmented .tl-segmented__on {
        background: var(--primary);
        color: var(--primary-contrast);
      }

      .tl-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
        border: 1px solid var(--tl-color);
        color: var(--text);
        background: color-mix(in srgb, var(--tl-color) 12%, transparent);
      }
      .tl-chip svg {
        color: var(--tl-color);
      }
      .tl-chip--off {
        background: transparent;
        border-color: var(--border);
        color: var(--text-faint);
      }
      .tl-chip--off svg {
        color: var(--text-faint);
      }
      .tl-chip__count {
        min-width: 1.25rem;
        padding: 0 0.3rem;
        border-radius: 999px;
        font-size: 0.6875rem;
        text-align: center;
        background: var(--tl-color);
        color: #fff;
      }

      .tl-ribbon {
        display: flex;
        align-items: flex-end;
        gap: 3px;
        height: 52px;
        padding-bottom: 12px;
        position: relative;
        border-bottom: 1px solid var(--border);
      }
      .tl-ribbon--dense {
        gap: 1px;
      }
      .tl-ribbon__day {
        position: relative;
        flex: 1 1 0;
        min-width: 3px;
        height: 100%;
        display: flex;
        align-items: flex-end;
        border-radius: var(--radius-xs) var(--radius-xs) 0 0;
      }
      .tl-ribbon__day:not(:disabled):hover {
        background: var(--surface-3);
      }
      .tl-ribbon__day--weekend {
        background: var(--surface-2);
      }
      .tl-ribbon__day--today {
        box-shadow: inset 0 -2px 0 var(--primary);
        background: var(--primary-soft);
      }
      .tl-ribbon__day--focus {
        outline: 1px solid var(--primary);
      }
      .tl-ribbon__bar {
        width: 100%;
        display: flex;
        flex-direction: column-reverse;
        border-radius: 2px 2px 0 0;
        overflow: hidden;
      }
      .tl-ribbon__bar span {
        flex-basis: 0;
        min-height: 2px;
      }
      .tl-ribbon__month {
        position: absolute;
        left: 0;
        bottom: -14px;
        font-size: 0.625rem;
        white-space: nowrap;
        color: var(--text-faint);
      }

      .tl-next {
        color: var(--text-muted);
        text-align: left;
      }
      .tl-next:hover strong {
        color: var(--primary);
      }

      /* ---- Spine ---- */
      .tl {
        position: relative;
        padding: 0.25rem 0 1rem;
        transition: opacity 0.15s;
      }
      .tl--loading {
        opacity: 0.6;
      }
      .tl::before {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        left: 27px;
        width: 2px;
        background: var(--border);
      }
      .tl-month {
        position: sticky;
        top: 0;
        z-index: 2;
        margin: 0.75rem 0 0.5rem;
        padding: 0.25rem 0.75rem;
        width: fit-content;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--text-muted);
        background: var(--page-bg);
        border: 1px solid var(--border);
        border-radius: 999px;
      }
      .tl-day {
        position: relative;
        display: grid;
        grid-template-columns: 56px 1fr;
        gap: 0.75rem;
        padding: 0.4rem 0;
        scroll-margin-top: 3rem;
      }
      .tl-node {
        grid-column: 1;
        grid-row: 1;
        z-index: 1;
        justify-self: center;
        align-self: start;
        width: 48px;
        height: 48px;
        border-radius: 999px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        line-height: 1.05;
        background: var(--surface);
        border: 2px solid var(--border-strong);
        color: var(--text);
      }
      .tl-node__dow {
        font-size: 0.5625rem;
        text-transform: uppercase;
        color: var(--text-muted);
      }
      .tl-node__num {
        font-size: 1rem;
        font-weight: 700;
      }
      .tl-node--today {
        background: var(--primary);
        border-color: var(--primary);
        color: var(--primary-contrast);
        box-shadow: 0 0 0 4px var(--ring);
      }
      .tl-node--today .tl-node__dow {
        color: var(--primary-contrast);
      }
      .tl-day--past .tl-node {
        border-color: var(--border);
        color: var(--text-muted);
      }
      .tl-day--focus .tl-node {
        box-shadow: 0 0 0 4px var(--ring);
      }
      .tl-cards {
        grid-column: 2;
        grid-row: 1;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        min-width: 0;
      }

      .tl-card {
        position: relative;
        padding: 0.6rem 0.75rem;
        border-radius: var(--radius-lg);
        border: 1px solid var(--border);
        border-left: 3px solid var(--tl-color);
        background: var(--surface);
        box-shadow: var(--shadow-sm);
        cursor: pointer;
        transition: border-color 0.15s, transform 0.15s;
        animation: tl-in 0.2s ease-out both;
      }
      .tl-card:hover,
      .tl-card:focus-visible {
        border-color: var(--tl-color);
        transform: translateY(-1px);
        outline: none;
      }
      .tl-card--open {
        border-color: var(--tl-color);
        background: color-mix(in srgb, var(--tl-color) 6%, var(--surface));
      }
      .tl-card--empty {
        cursor: default;
        border-left-color: var(--primary);
        border-style: dashed;
        color: var(--text-muted);
        font-size: 0.8125rem;
        box-shadow: none;
      }
      .tl-day--past .tl-card:not(.tl-card--open) {
        opacity: 0.72;
      }
      .tl-card__icon {
        flex: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: var(--radius-md);
        color: var(--tl-color);
        background: color-mix(in srgb, var(--tl-color) 14%, transparent);
      }
      .tl-card__title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text);
        overflow-wrap: anywhere;
      }
      .tl-card__sub {
        font-size: 0.75rem;
        color: var(--text-muted);
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      .tl-card__sub--full {
        display: block;
      }
      .tl-card__detail {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        margin-top: 0.6rem;
        padding-top: 0.5rem;
        border-top: 1px dashed var(--border);
        font-size: 0.75rem;
        color: var(--text-muted);
      }
      .tl-card__detail .btn-primary {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
      }
      .tl-pill {
        padding: 0 0.4rem;
        border-radius: 999px;
        background: var(--surface-3);
        text-transform: capitalize;
        white-space: nowrap;
      }

      /* Alternating sides around a centered spine on wide screens */
      @media (min-width: 900px) {
        .tl::before {
          left: 50%;
          transform: translateX(-1px);
        }
        .tl-month {
          margin-left: auto;
          margin-right: auto;
        }
        .tl-day {
          grid-template-columns: 1fr 56px 1fr;
        }
        .tl-node {
          grid-column: 2;
        }
        .tl-cards {
          grid-column: 1;
          align-items: flex-end;
        }
        .tl-cards .tl-card {
          width: min(100%, 26rem);
          border-left-width: 1px;
          border-right: 3px solid var(--tl-color);
        }
        .tl-day--right .tl-cards {
          grid-column: 3;
          align-items: flex-start;
        }
        .tl-day--right .tl-cards .tl-card {
          border-right-width: 1px;
          border-left: 3px solid var(--tl-color);
        }
      }

      @keyframes tl-in {
        from {
          opacity: 0;
          transform: translateY(4px);
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .tl-card {
          animation: none;
          transition: none;
        }
      }
    `,
  ],
})
export class TimelinePageComponent {
  private readonly timelineService = inject(TimelineService);
  private readonly prefs = inject(TimelinePreferencesService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly zooms = TIMELINE_ZOOMS;

  readonly sources = signal<TimelineSource[]>([]);
  readonly zoom = signal<TimelineZoom>('month');
  readonly anchor = signal<Date>(new Date());
  readonly items = signal<TimelineItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly query = signal('');
  readonly expandedId = signal<string | null>(null);
  readonly focusedDay = signal<string | null>(null);
  private readonly reloadTick = signal(0);
  /** Scroll to today/next item once per range, not on every source toggle. */
  private lastScrolledRange = '';

  readonly range = computed(() => rangeFor(this.anchor(), this.zoom()));

  readonly enabledKeys = computed<TimelineSourceKey[]>(() =>
    this.sources()
      .filter((s) => this.isEnabled(s))
      .map((s) => s.key),
  );

  readonly rangeLabel = computed(() => {
    const { start, end } = this.range();
    const zoom = this.zoom();
    if (zoom === 'month') return start.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
    if (zoom === 'quarter') {
      const from = start.toLocaleDateString(undefined, { month: 'short' });
      return `${from} – ${end.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}`;
    }
    const from = start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    return `${from} – ${end.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}`;
  });

  readonly filtered = computed(() => {
    const q = this.query().trim().toLowerCase();
    if (!q) return this.items();
    return this.items().filter(
      (i) => i.title.toLowerCase().includes(q) || (i.subtitle ?? '').toLowerCase().includes(q),
    );
  });

  readonly sourceCounts = computed(() => {
    const counts: Partial<Record<TimelineSourceKey, number>> = {};
    for (const i of this.items()) counts[i.source] = (counts[i.source] ?? 0) + 1;
    return counts;
  });

  private readonly byDay = computed(() => {
    const map = new Map<string, TimelineItem[]>();
    for (const item of this.filtered()) {
      const key = itemDayKey(item);
      const bucket = map.get(key);
      if (bucket) bucket.push(item);
      else map.set(key, [item]);
    }
    return map;
  });

  readonly months = computed<TimelineMonth[]>(() => {
    const todayKey = localIsoDate();
    const { start, end } = this.range();
    const keys = new Set(this.byDay().keys());
    // Always show a "Today" node when today falls inside the range.
    if (todayKey >= localIsoDate(start) && todayKey <= localIsoDate(end)) keys.add(todayKey);

    const months: TimelineMonth[] = [];
    for (const key of [...keys].sort()) {
      const date = fromDayKey(key);
      const monthKey = key.slice(0, 7);
      let month = months[months.length - 1];
      if (!month || month.key !== monthKey) {
        month = {
          key: monthKey,
          label: date.toLocaleDateString(undefined, { month: 'long', year: 'numeric' }),
          days: [],
        };
        months.push(month);
      }
      month.days.push({
        key,
        date,
        items: this.byDay().get(key) ?? [],
        isToday: key === todayKey,
        isPast: key < todayKey,
      });
    }
    return months;
  });

  readonly ribbon = computed<RibbonDay[]>(() => {
    const todayKey = localIsoDate();
    const { start, end } = this.range();
    const days: RibbonDay[] = [];
    for (let d = start; d <= end; d = addDays(d, 1)) {
      const key = localIsoDate(d);
      const items = this.byDay().get(key) ?? [];
      const perSource = new Map<TimelineSourceKey, number>();
      for (const i of items) perSource.set(i.source, (perSource.get(i.source) ?? 0) + 1);
      days.push({
        key,
        label: d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }),
        count: items.length,
        segments: [...perSource].map(([source, n]) => ({ source, share: n })),
        isToday: key === todayKey,
        isWeekend: d.getDay() === 0 || d.getDay() === 6,
        monthStart:
          d.getDate() === 1 && this.zoom() === 'quarter' ? d.toLocaleDateString(undefined, { month: 'short' }) : null,
      });
    }
    return days;
  });

  private readonly ribbonMax = computed(() => Math.max(1, ...this.ribbon().map((d) => d.count)));

  readonly pastCount = computed(() => {
    const now = Date.now();
    return this.filtered().filter((i) => new Date(i.ends_at ?? i.starts_at).getTime() < now).length;
  });

  readonly nextUp = computed(() => {
    const now = Date.now();
    return this.filtered().find((i) => new Date(i.starts_at).getTime() >= now) ?? null;
  });

  constructor() {
    this.prefs.init();
    this.timelineService
      .sources()
      .pipe(takeUntilDestroyed())
      .subscribe({
        next: (sources) => this.sources.set(sources),
        error: () => this.error.set('Timeline sources are unavailable.'),
      });

    const request = computed(() => ({
      start: localIsoDate(this.range().start),
      end: localIsoDate(this.range().end),
      sources: this.enabledKeys(),
      ready: this.sources().length > 0,
      tick: this.reloadTick(),
    }));

    toObservable(request)
      .pipe(
        debounceTime(0),
        switchMap((req) => {
          if (!req.ready) return of(null);
          // An empty list would make the API fall back to its defaults, so short-circuit.
          if (req.sources.length === 0) return of({ req, items: [] as TimelineItem[] });
          this.loading.set(true);
          this.error.set(null);
          return this.timelineService.list(req.start, req.end, req.sources).pipe(
            map((items) => ({ req, items })),
            catchError(() => {
              this.error.set('Please check your connection and try again.');
              return of(null);
            }),
          );
        }),
        tap(() => this.loading.set(false)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((result) => {
        if (!result) return;
        this.items.set(result.items);
        const rangeKey = `${result.req.start}|${result.req.end}`;
        if (rangeKey !== this.lastScrolledRange) {
          this.lastScrolledRange = rangeKey;
          setTimeout(() => this.scrollToInitialDay());
        }
      });
  }

  // ── Presentation helpers ──────────────────────────────────────────────────

  style(source: TimelineSourceKey): { icon: string; color: string } {
    return TIMELINE_SOURCE_STYLE[source];
  }

  sourceLabel(source: TimelineSourceKey): string {
    return this.sources().find((s) => s.key === source)?.label ?? source;
  }

  isEnabled(source: TimelineSource): boolean {
    return this.prefs.overrides()[source.key] ?? source.default_enabled;
  }

  barHeight(count: number): number {
    return count === 0 ? 0 : 15 + (85 * count) / this.ribbonMax();
  }

  weekday(date: Date): string {
    return date.toLocaleDateString(undefined, { weekday: 'short' });
  }

  timeLabel(item: TimelineItem): string {
    if (item.all_day) return 'All day';
    const opts: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit' };
    const start = new Date(item.starts_at).toLocaleTimeString([], opts);
    if (!item.ends_at) return start;
    const end = new Date(item.ends_at);
    return dayDiff(new Date(item.starts_at), end) === 0 ? `${start} – ${end.toLocaleTimeString([], opts)}` : start;
  }

  spanLabel(item: TimelineItem): string | null {
    if (!item.ends_at) return null;
    const days = dayDiff(new Date(item.starts_at), new Date(item.ends_at));
    if (days < 1) return null;
    const until = new Date(item.ends_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    return `${days + 1} days · until ${until}`;
  }

  fullDate(item: TimelineItem): string {
    return new Date(item.starts_at).toLocaleDateString(undefined, {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  }

  relative(item: TimelineItem): string {
    const days = dayDiff(new Date(), new Date(item.starts_at));
    return new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' }).format(days, 'day');
  }

  // ── Interactions ──────────────────────────────────────────────────────────

  onQuery(event: Event): void {
    this.query.set((event.target as HTMLInputElement).value);
  }

  setZoom(zoom: TimelineZoom): void {
    this.zoom.set(zoom);
  }

  shift(direction: 1 | -1): void {
    this.anchor.set(shiftAnchor(this.anchor(), this.zoom(), direction));
    this.expandedId.set(null);
  }

  goToday(): void {
    this.anchor.set(new Date());
    this.jumpTo(localIsoDate());
  }

  reload(): void {
    this.reloadTick.update((n) => n + 1);
  }

  toggleSource(source: TimelineSource): void {
    this.prefs.setSourceEnabled(source.key, !this.isEnabled(source));
  }

  toggleExpanded(id: string): void {
    this.expandedId.set(this.expandedId() === id ? null : id);
  }

  jumpTo(dayKey: string): void {
    this.focusedDay.set(dayKey);
    setTimeout(() =>
      document.getElementById(`tl-day-${dayKey}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
    );
  }

  openFromNext(item: TimelineItem): void {
    this.expandedId.set(item.id);
    this.jumpTo(itemDayKey(item));
  }

  open(item: TimelineItem, event: Event): void {
    event.stopPropagation();
    if (item.route) this.router.navigateByUrl(item.route);
  }

  private scrollToInitialDay(): void {
    const todayKey = localIsoDate();
    const keys = this.months().flatMap((m) => m.days.map((d) => d.key));
    const target = keys.find((k) => k >= todayKey);
    if (target && target !== keys[0]) {
      document.getElementById(`tl-day-${target}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  @HostListener('window:keydown', ['$event'])
  onKeydown(e: KeyboardEvent): void {
    const target = e.target as HTMLElement;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'ArrowLeft') this.shift(-1);
    else if (e.key === 'ArrowRight') this.shift(1);
    else if (e.key === 't') this.goToday();
  }
}
