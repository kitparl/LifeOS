import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MemoryItem, MemoryService } from './services/memory.service';

@Component({
  selector: 'app-memory-page',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">AI Memory</h1>
      @if (summary) {
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="panel text-sm"><p class="text-gray-600">Total memories</p><p class="text-xl font-semibold">{{ summary.total }}</p></div>
          @for (cat of categoryEntries; track cat[0]) {
            <div class="panel text-sm"><p class="text-gray-600 capitalize">{{ cat[0] }}</p><p class="text-xl font-semibold">{{ cat[1] }}</p></div>
          }
        </div>
      }
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Add memory</div>
        <form class="grid gap-2 p-3 text-sm sm:grid-cols-2" [formGroup]="form" (ngSubmit)="add()">
          <input class="input-field" formControlName="memory_key" placeholder="Key (e.g. preferred_run_time)" />
          <select class="input-field" formControlName="category">
            <option value="preference">Preference</option>
            <option value="goal">Goal</option>
            <option value="pattern">Pattern</option>
            <option value="history">History</option>
            <option value="fact">Fact</option>
          </select>
          <textarea class="input-field sm:col-span-2 min-h-[60px]" formControlName="memory_value" placeholder="Value"></textarea>
          <input class="input-field" type="number" min="1" max="5" formControlName="importance" />
          <button type="submit" class="btn-primary text-xs" [disabled]="form.invalid">Save</button>
        </form>
      </div>
      <ul class="panel !p-0 divide-y divide-[var(--xp-border)] text-sm">
        @for (item of items; track item.id) {
          <li class="flex justify-between gap-2 px-3 py-2">
            <div>
              <p class="font-medium">{{ item.memory_key }} <span class="text-xs text-gray-500 capitalize">({{ item.category }})</span></p>
              <p class="text-gray-700">{{ item.memory_value }}</p>
            </div>
            <button type="button" class="text-xs text-red-700 shrink-0" (click)="remove(item.id)">Delete</button>
          </li>
        } @empty {
          <li class="px-3 py-4 text-gray-600">No memories yet.</li>
        }
      </ul>
    </div>
  `,
})
export class MemoryPageComponent implements OnInit {
  private readonly memory = inject(MemoryService);
  private readonly fb = inject(FormBuilder);
  items: MemoryItem[] = [];
  summary: { total: number; by_category: Record<string, number> } | null = null;
  categoryEntries: [string, number][] = [];
  form = this.fb.nonNullable.group({
    memory_key: '',
    memory_value: '',
    category: 'fact',
    importance: 3,
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.memory.list().subscribe({ next: (d) => (this.items = d) });
    this.memory.summary().subscribe({
      next: (s) => {
        this.summary = s;
        this.categoryEntries = Object.entries(s.by_category);
      },
    });
  }

  add(): void {
    if (this.form.invalid) return;
    this.memory.create(this.form.getRawValue()).subscribe({ next: () => { this.form.reset({ category: 'fact', importance: 3 }); this.load(); } });
  }

  remove(id: string): void {
    this.memory.delete(id).subscribe({ next: () => this.load() });
  }
}
