import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LEARNING_TYPES, LearningListItem, LearningType } from './models/learning.models';
import { LearningService } from './services/learning.service';

@Component({
  selector: 'app-learning-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Learning</h1>
        <a routerLink="/learning/new" class="btn-primary text-xs no-underline">New Item</a>
      </div>
      <form class="flex gap-2 text-sm" [formGroup]="filters" (ngSubmit)="load()">
        <select class="input-field !w-auto" formControlName="item_type">
          <option value="">All types</option>
          @for (t of types; track t.value) {
            <option [value]="t.value">{{ t.label }}</option>
          }
        </select>
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>
      @if (loading) {
        <p class="text-sm text-gray-600">Loading…</p>
      } @else if (items.length === 0) {
        <div class="panel"><p class="text-sm text-gray-600">No learning items yet.</p></div>
      } @else {
        <ul class="panel !p-0 divide-y divide-[var(--xp-border)] text-sm">
          @for (item of items; track item.id) {
            <li class="flex items-center justify-between gap-2 px-3 py-2">
              <div>
                <a [routerLink]="['/learning', item.id, 'edit']" class="text-[var(--xp-blue)] underline">{{ item.title }}</a>
                <p class="text-xs text-gray-600 capitalize">{{ item.item_type }} · {{ item.status }} · {{ item.progress }}%</p>
              </div>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class LearningListComponent implements OnInit {
  private readonly learningService = inject(LearningService);
  private readonly fb = inject(FormBuilder);
  types = LEARNING_TYPES;
  items: LearningListItem[] = [];
  loading = false;
  filters = this.fb.nonNullable.group({ item_type: '' });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const t = this.filters.getRawValue().item_type;
    this.learningService.list(t || undefined).subscribe({
      next: (data) => {
        this.items = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}

@Component({
  selector: 'app-learning-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg panel !p-0 overflow-hidden">
      <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit' : 'New' }} Learning Item</div>
      <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
        <input class="input-field" formControlName="title" placeholder="Title" />
        <select class="input-field" formControlName="item_type">
          @for (t of types; track t.value) {
            <option [value]="t.value">{{ t.label }}</option>
          }
        </select>
        <input class="input-field" formControlName="provider" placeholder="Provider / author" />
        <input class="input-field" formControlName="url" placeholder="URL" />
        <select class="input-field" formControlName="status">
          <option value="planned">Planned</option>
          <option value="in_progress">In progress</option>
          <option value="completed">Completed</option>
          <option value="paused">Paused</option>
        </select>
        <input class="input-field" type="number" min="0" max="100" formControlName="progress" />
        <textarea class="input-field min-h-[60px]" formControlName="notes" placeholder="Notes"></textarea>
        <div class="flex gap-2">
          <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">Save</button>
          <a routerLink="/learning" class="input-field !w-auto inline-flex items-center no-underline">Cancel</a>
        </div>
      </form>
    </div>
  `,
})
export class LearningFormComponent implements OnInit {
  private readonly learningService = inject(LearningService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  types = LEARNING_TYPES;
  isEdit = false;
  itemId: string | null = null;
  saving = false;
  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    item_type: ['book'],
    provider: [''],
    url: [''],
    status: ['planned'],
    progress: [0],
    notes: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.itemId = id;
      this.learningService.get(id).subscribe({
        next: (item) =>
          this.form.patchValue({
            title: item.title,
            item_type: item.item_type,
            provider: item.provider ?? '',
            url: item.url ?? '',
            status: item.status,
            progress: item.progress,
            notes: item.notes ?? '',
          }),
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.getRawValue();
    const payload = {
      title: raw.title,
      item_type: raw.item_type as LearningType,
      provider: raw.provider || null,
      url: raw.url || null,
      status: raw.status,
      progress: raw.progress,
      notes: raw.notes || null,
    };
    const req =
      this.isEdit && this.itemId
        ? this.learningService.update(this.itemId, payload)
        : this.learningService.create(payload);
    req.subscribe({
      next: () => this.router.navigate(['/learning']),
      error: () => (this.saving = false),
    });
  }
}
