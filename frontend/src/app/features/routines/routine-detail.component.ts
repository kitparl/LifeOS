import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import {
  Routine,
  formatDaysLabel,
  formatTimeLabel,
  ROUTINE_AREAS,
} from './models/routine.models';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { RoutinesService } from './services/routines.service';

@Component({
  selector: 'app-routine-detail',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (routine; as r) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ r.name }}</h1>
            <p class="text-xs" style="color: var(--text-muted)">
              {{ daysLabel(r.days_of_week) }} · {{ r.timezone }} ·
              {{ r.is_active ? 'active' : 'paused' }}
            </p>
            @if (r.start_date || r.end_date) {
              <p class="text-xs" style="color: var(--text-muted)">
                Period:
                {{ r.start_date ? (r.start_date | date: 'mediumDate') : '…' }}
                –
                {{ r.end_date ? (r.end_date | date: 'mediumDate') : '…' }}
              </p>
            }
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/routines', r.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            @if (r.is_active) {
              <button type="button" class="btn-ghost text-xs" (click)="deactivate()">Deactivate</button>
            } @else {
              <button type="button" class="btn-ghost text-xs" (click)="activate()">Activate</button>
            }
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">
              Delete
            </button>
          </div>
        </div>

        @if (r.description) {
          <div class="panel text-sm">
            <p class="whitespace-pre-wrap" style="color: var(--text)">{{ r.description }}</p>
          </div>
        }

        @if (r.skip_dates.length) {
          <div class="panel text-sm">
            <p class="font-medium mb-2">Skip days</p>
            <div class="flex flex-wrap gap-1.5">
              @for (d of r.skip_dates; track d) {
                <span class="chip">{{ d }}</span>
              }
            </div>
          </div>
        }

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">
            Schedule ({{ r.blocks.length }} blocks)
          </div>
          @if (r.blocks.length === 0) {
            <p class="p-3 text-sm" style="color: var(--text-muted)">No blocks yet.</p>
          } @else {
            <table class="w-full text-sm">
              <thead class="border-b border-[var(--xp-border)] bg-[var(--surface-2)] text-left">
                <tr>
                  <th class="px-3 py-2">Time</th>
                  <th class="px-3 py-2">Title</th>
                  <th class="px-3 py-2">Area</th>
                  <th class="px-3 py-2">Category</th>
                  <th class="px-3 py-2">Habits</th>
                </tr>
              </thead>
              <tbody>
                @for (b of r.blocks; track b.id) {
                  <tr class="border-b border-[var(--xp-border)]">
                    <td class="px-3 py-2 whitespace-nowrap">
                      {{ formatTime(b.start_time) }} – {{ formatTime(b.end_time) }}
                    </td>
                    <td class="px-3 py-2">
                      {{ b.title }}
                      @if (b.notes) {
                        <p class="text-xs" style="color: var(--text-muted)">{{ b.notes }}</p>
                      }
                    </td>
                    <td class="px-3 py-2">{{ areaLabel(b.area) }}</td>
                    <td class="px-3 py-2 capitalize">{{ b.category }}</td>
                    <td class="px-3 py-2 text-xs" style="color: var(--text-muted)">
                      {{ habitNames(b) }}
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          }
        </div>

        <p class="text-xs" style="color: var(--text-muted)">
          Active routines appear automatically on
          <a routerLink="/calendar" class="underline">Calendar</a>
          for matching days.
        </p>

        <p class="text-xs" style="color: var(--text-faint)">
          Updated {{ r.updated_at | date: 'medium' }}
        </p>

        <a routerLink="/routines" class="text-sm underline" style="color: var(--xp-blue)">Back to routines</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading routine…</p>
    } @else {
      <p class="text-sm text-red-700">Routine not found.</p>
    }
  `,
})
export class RoutineDetailComponent implements OnInit {
  private readonly routinesService = inject(RoutinesService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly confirm = inject(ConfirmService);

  routine: Routine | null = null;
  loading = false;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading = true;
    this.routinesService.get(id).subscribe({
      next: (r) => {
        this.routine = r;
        this.loading = false;
      },
      error: () => {
        this.routine = null;
        this.loading = false;
      },
    });
  }

  daysLabel(days: number[]): string {
    return formatDaysLabel(days);
  }

  formatTime(t: string): string {
    return formatTimeLabel(t);
  }

  areaLabel(area: string): string {
    return ROUTINE_AREAS.find((a) => a.value === area)?.label ?? area;
  }

  habitNames(b: { habits?: { name: string }[] }): string {
    const names = b.habits?.map((h) => h.name) ?? [];
    return names.length ? names.join(', ') : '—';
  }

  deactivate(): void {
    if (!this.routine) return;
    this.routinesService.update(this.routine.id, { is_active: false }).subscribe({
      next: (r) => (this.routine = r),
    });
  }

  activate(): void {
    if (!this.routine) return;
    this.routinesService.update(this.routine.id, { is_active: true }).subscribe({
      next: (r) => (this.routine = r),
    });
  }

  async remove(): Promise<void> {
    if (!this.routine) return;
    const ok = await this.confirm.confirm('Delete this routine permanently?');
    if (!ok) return;
    this.routinesService.delete(this.routine.id).subscribe({
      next: () => this.router.navigate(['/routines']),
    });
  }
}
