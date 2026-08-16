import { Component, OnInit, inject, signal } from '@angular/core';
import {
  FormArray,
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { DateChipsComponent } from '../../shared/date-chips/date-chips.component';
import { TypeSelectComponent } from '../../shared/type-select/type-select.component';
import { HabitListItem } from '../habits/models/habit.models';
import { HabitsService } from '../habits/services/habits.service';
import {
  ROUTINE_AREAS,
  ROUTINE_CATEGORIES,
  RoutineArea,
  WEEKDAYS,
  defaultCategoryForArea,
} from './models/routine.models';
import { RoutinesService } from './services/routines.service';

@Component({
  selector: 'app-routine-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DateChipsComponent, TypeSelectComponent],
  template: `
    <div class="max-w-2xl space-y-3">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">
          {{ isEdit ? 'Edit Routine' : 'New Routine' }} — Details
        </div>
        <form class="space-y-4 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Name</label>
            <input class="input-field" formControlName="name" placeholder="Weekday Focus" />
          </div>

          <div>
            <label class="mb-1 block">Description</label>
            <textarea
              class="input-field min-h-[60px]"
              formControlName="description"
              placeholder="Protect time for DSA, gym, learning…"
            ></textarea>
          </div>

          <div>
            <label class="mb-1 block">Timezone</label>
            <input class="input-field" formControlName="timezone" placeholder="Asia/Kolkata" />
          </div>

          <div class="grid gap-3 sm:grid-cols-2">
            <div>
              <label class="mb-1 block">Period start</label>
              <input class="input-field" type="date" formControlName="start_date" />
            </div>
            <div>
              <label class="mb-1 block">Period end (optional)</label>
              <input class="input-field" type="date" formControlName="end_date" />
            </div>
          </div>

          <div>
            <label class="mb-1 block">Skip days</label>
            <p class="mb-1 text-xs" style="color: var(--text-muted)">
              Exclude specific dates even if that weekday is normally active.
            </p>
            <app-date-chips formControlName="skip_dates" />
          </div>

          <div>
            <label class="mb-1 block">Active days</label>
            <div class="flex flex-wrap gap-2">
              @for (d of weekdays; track d.value) {
                <label class="flex items-center gap-1 text-xs border border-[var(--xp-border)] px-2 py-1">
                  <input
                    type="checkbox"
                    [checked]="isDaySelected(d.value)"
                    (change)="toggleDay(d.value, $event)"
                  />
                  {{ d.short }}
                </label>
              }
            </div>
          </div>

          @if (isEdit) {
            <label class="flex items-center gap-2">
              <input type="checkbox" formControlName="is_active" />
              Active (show on Calendar)
            </label>
          }

          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving || !hasDays()">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/routines" class="btn-secondary no-underline">Cancel</a>
          </div>
          @if (error) {
            <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
          }
        </form>
      </div>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Time blocks</div>
        <div class="space-y-3 p-4 text-sm" [formGroup]="form">
          <div class="mb-2 flex items-center justify-between">
            <p class="text-xs" style="color: var(--text-muted)">One block by default — add more as needed.</p>
            <button type="button" class="btn-secondary text-xs" (click)="addBlock()">+ Block</button>
          </div>

          <div class="space-y-3" formArrayName="blocks">
            @for (ctrl of blocks.controls; track $index; let i = $index) {
              <div class="border border-[var(--xp-border)] p-3 space-y-2" [formGroupName]="i">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs" style="color: var(--text-muted)">Block {{ i + 1 }}</span>
                  <button
                    type="button"
                    class="text-xs text-red-700 underline"
                    (click)="removeBlock(i)"
                    [disabled]="blocks.length <= 1"
                  >
                    Remove
                  </button>
                </div>
                <div>
                  <label class="mb-1 block text-xs">Title</label>
                  <input class="input-field" formControlName="title" placeholder="DSA practice" />
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <label class="mb-1 block text-xs">Start</label>
                    <input class="input-field" type="time" formControlName="start_time" />
                  </div>
                  <div>
                    <label class="mb-1 block text-xs">End</label>
                    <input class="input-field" type="time" formControlName="end_time" />
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <label class="mb-1 block text-xs">Area</label>
                    <app-type-select
                      formControlName="area"
                      placeholder="Select or create area…"
                      [options]="areaOptions()"
                      (created)="onAreaCreated($event)"
                    />
                  </div>
                  <div>
                    <label class="mb-1 block text-xs">Calendar category</label>
                    <app-type-select
                      formControlName="category"
                      placeholder="Select or create category…"
                      [options]="categoryOptions()"
                      (created)="onCategoryCreated($event)"
                    />
                  </div>
                </div>
                  <div>
                    <label class="mb-1 block text-xs">Notes</label>
                    <input class="input-field" formControlName="notes" placeholder="Optional" />
                  </div>
                  <div class="space-y-2 rounded border border-[var(--xp-border)] p-2.5" style="background: var(--surface-2, var(--surface))">
                    <label class="block text-xs font-medium">Block source</label>
                    <div class="grid gap-2 sm:grid-cols-2">
                      <label
                        class="flex cursor-pointer items-start gap-2 rounded border px-2.5 py-2 text-xs"
                        [style.border-color]="linkModeAt(i) === 'custom' ? 'var(--info)' : 'var(--xp-border)'"
                        [style.background]="linkModeAt(i) === 'custom' ? 'var(--info-soft)' : 'transparent'"
                      >
                        <input
                          type="radio"
                          class="mt-0.5"
                          [name]="'linkMode-' + i"
                          [checked]="linkModeAt(i) === 'custom'"
                          (change)="setLinkMode(i, 'custom')"
                        />
                        <span>
                          <span class="block font-medium">Custom item</span>
                          <span style="color: var(--text-muted)">Use this block’s title as-is</span>
                        </span>
                      </label>
                      <label
                        class="flex cursor-pointer items-start gap-2 rounded border px-2.5 py-2 text-xs"
                        [style.border-color]="linkModeAt(i) === 'habits' ? 'var(--info)' : 'var(--xp-border)'"
                        [style.background]="linkModeAt(i) === 'habits' ? 'var(--info-soft)' : 'transparent'"
                      >
                        <input
                          type="radio"
                          class="mt-0.5"
                          [name]="'linkMode-' + i"
                          [checked]="linkModeAt(i) === 'habits'"
                          (change)="setLinkMode(i, 'habits')"
                        />
                        <span>
                          <span class="block font-medium">Link habits</span>
                          <span style="color: var(--text-muted)">Track against existing habits</span>
                        </span>
                      </label>
                    </div>

                    @if (linkModeAt(i) === 'habits') {
                      @if (availableHabits.length === 0) {
                        <p class="text-xs" style="color: var(--text-muted)">
                          No active habits yet.
                          <a routerLink="/habits/new" class="underline" style="color: var(--xp-blue)">Create a habit</a>
                          first, then come back.
                        </p>
                      } @else {
                        <div class="flex flex-wrap gap-1.5">
                          @for (h of availableHabits; track h.id) {
                            <label
                              class="flex cursor-pointer items-center gap-1.5 rounded border px-2 py-1 text-xs"
                              [style.border-color]="isHabitSelected(i, h.id) ? 'var(--info)' : 'var(--xp-border)'"
                              [style.background]="isHabitSelected(i, h.id) ? 'var(--info-soft)' : 'transparent'"
                            >
                              <input
                                type="checkbox"
                                [checked]="isHabitSelected(i, h.id)"
                                (change)="toggleHabit(i, h.id, $event)"
                              />
                              {{ h.name }}
                            </label>
                          }
                        </div>
                        <p class="text-[10px]" style="color: var(--text-muted)">
                          Pick one or more habits this time block represents.
                        </p>
                      }
                    }
                  </div>
                </div>
              }
            </div>

          <div class="flex gap-2">
            <button type="button" class="btn-primary" [disabled]="form.invalid || saving || !hasDays()" (click)="submit()">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/routines" class="btn-secondary no-underline">Cancel</a>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class RoutineFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly routinesService = inject(RoutinesService);
  private readonly habitsService = inject(HabitsService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  weekdays = WEEKDAYS;
  areaOptions = signal<string[]>(ROUTINE_AREAS.map((a) => a.value));
  categoryOptions = signal<string[]>(ROUTINE_CATEGORIES.map((c) => c.value));
  availableHabits: HabitListItem[] = [];
  isEdit = false;
  routineId: string | null = null;
  saving = false;
  error = '';
  selectedDays = new Set<number>([0, 1, 2, 3, 4]);

  form = this.fb.nonNullable.group({
    name: ['Weekday Focus', Validators.required],
    description: [''],
    timezone: ['Asia/Kolkata', Validators.required],
    start_date: [new Date().toISOString().slice(0, 10), Validators.required],
    end_date: [''],
    skip_dates: [[] as string[]],
    is_active: [true],
    blocks: this.fb.array([this.newBlockGroup()]),
  });

  get blocks(): FormArray {
    return this.form.get('blocks') as FormArray;
  }

  ngOnInit(): void {
    this.habitsService.list(true).subscribe({
      next: (habits) => (this.availableHabits = habits),
    });
    this.routinesService.listAreas().subscribe({ next: (a) => this.areaOptions.set(a) });
    this.routinesService.listCategories().subscribe({ next: (c) => this.categoryOptions.set(c) });
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.routineId = id;
      this.routinesService.get(id).subscribe({
        next: (r) => {
          this.selectedDays = new Set(r.days_of_week);
          this.form.patchValue({
            name: r.name,
            description: r.description ?? '',
            timezone: r.timezone,
            start_date: r.start_date ? r.start_date.slice(0, 10) : '',
            end_date: r.end_date ? r.end_date.slice(0, 10) : '',
            skip_dates: r.skip_dates ?? [],
            is_active: r.is_active,
          });
          this.blocks.clear();
          if (r.blocks.length === 0) {
            this.addBlock();
          } else {
            for (const b of r.blocks) {
              this.blocks.push(
                this.newBlockGroup(
                  b.title,
                  b.start_time.slice(0, 5),
                  b.end_time.slice(0, 5),
                  b.area,
                  b.category,
                  b.notes ?? '',
                  b.habit_ids ?? b.habits?.map((h) => h.id) ?? [],
                ),
              );
            }
          }
        },
      });
    }
  }

  newBlockGroup(
    title = '',
    start = '09:00',
    end = '10:00',
    area: RoutineArea = 'other',
    category = defaultCategoryForArea(area),
    notes = '',
    habitIds: string[] = [],
  ) {
    return this.fb.nonNullable.group({
      title: [title, Validators.required],
      start_time: [start, Validators.required],
      end_time: [end, Validators.required],
      area: [area as RoutineArea, Validators.required],
      category: [category, Validators.required],
      notes: [notes],
      habit_ids: [habitIds as string[]],
      link_mode: [habitIds.length > 0 ? ('habits' as const) : ('custom' as const)],
    });
  }

  onAreaCreated(name: string): void {
    this.areaOptions.update((list) => (list.includes(name) ? list : [...list, name].sort()));
    this.routinesService.createArea(name).subscribe({ next: (a) => this.areaOptions.set(a) });
  }

  onCategoryCreated(name: string): void {
    this.categoryOptions.update((list) => (list.includes(name) ? list : [...list, name].sort()));
    this.routinesService.createCategory(name).subscribe({ next: (c) => this.categoryOptions.set(c) });
  }

  habitIdsAt(index: number): string[] {
    return (this.blocks.at(index).get('habit_ids')?.value as string[]) || [];
  }

  linkModeAt(index: number): 'custom' | 'habits' {
    return (this.blocks.at(index).get('link_mode')?.value as 'custom' | 'habits') || 'custom';
  }

  setLinkMode(index: number, mode: 'custom' | 'habits'): void {
    const group = this.blocks.at(index);
    group.patchValue({
      link_mode: mode,
      habit_ids: mode === 'custom' ? [] : this.habitIdsAt(index),
    });
  }

  isHabitSelected(index: number, habitId: string): boolean {
    return this.habitIdsAt(index).includes(habitId);
  }

  toggleHabit(index: number, habitId: string, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    const current = this.habitIdsAt(index);
    const next = checked
      ? [...current, habitId]
      : current.filter((id) => id !== habitId);
    this.blocks.at(index).patchValue({ habit_ids: next, link_mode: 'habits' });
  }

  addBlock(): void {
    this.blocks.push(this.newBlockGroup());
  }

  removeBlock(index: number): void {
    if (this.blocks.length <= 1) return;
    this.blocks.removeAt(index);
  }

  onAreaChange(index: number): void {
    const group = this.blocks.at(index);
    const area = group.get('area')?.value as RoutineArea;
    group.patchValue({ category: defaultCategoryForArea(area) });
  }

  isDaySelected(day: number): boolean {
    return this.selectedDays.has(day);
  }

  toggleDay(day: number, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked) this.selectedDays.add(day);
    else this.selectedDays.delete(day);
  }

  hasDays(): boolean {
    return this.selectedDays.size > 0;
  }

  submit(): void {
    if (this.form.invalid || !this.hasDays()) return;
    this.saving = true;
    this.error = '';
    const raw = this.form.getRawValue();
    const blocks = raw.blocks.map((b, i) => ({
      title: b.title,
      start_time: b.start_time.length === 5 ? `${b.start_time}:00` : b.start_time,
      end_time: b.end_time.length === 5 ? `${b.end_time}:00` : b.end_time,
      area: b.area,
      category: b.category,
      notes: b.notes || null,
      sort_order: i,
      habit_ids: b.link_mode === 'habits' ? b.habit_ids || [] : [],
    }));

    const payload = {
      name: raw.name,
      description: raw.description || null,
      days_of_week: [...this.selectedDays].sort((a, b) => a - b),
      timezone: raw.timezone,
      start_date: raw.start_date,
      end_date: raw.end_date || null,
      skip_dates: raw.skip_dates || [],
      blocks,
      ...(this.isEdit ? { is_active: raw.is_active } : {}),
    };

    const req =
      this.isEdit && this.routineId
        ? this.routinesService.update(this.routineId, payload)
        : this.routinesService.create(payload);

    req.subscribe({
      next: (routine) => this.router.navigate(['/routines', routine.id]),
      error: (err) => {
        const detail = err?.error?.detail;
        this.error =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d: { msg?: string }) => d.msg).join(', ')
              : 'Failed to save routine';
        this.saving = false;
      },
    });
  }
}
