import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LifeTimelineItem, LifeTimelineService } from './services/life-timeline.service';

@Component({
  selector: 'app-life-timeline-page',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">Complete Life Timeline</h1>
      <div class="panel !p-0 overflow-hidden max-w-lg">
        <div class="title-bar rounded-none border-x-0 border-t-0">Add milestone</div>
        <form class="space-y-2 p-3 text-sm" [formGroup]="form" (ngSubmit)="addMilestone()">
          <input class="input-field" formControlName="title" placeholder="Milestone title" />
          <input class="input-field" type="date" formControlName="milestone_date" />
          <textarea class="input-field min-h-[60px]" formControlName="description" placeholder="Description"></textarea>
          <input class="input-field" formControlName="tags" placeholder="Tags (comma-separated)" />
          <button type="submit" class="btn-primary text-xs" [disabled]="form.invalid">Add milestone</button>
        </form>
      </div>
      <ul class="panel !p-0 divide-y divide-[var(--xp-border)] text-sm">
        @for (item of items; track item.id + item.item_type) {
          <li class="px-3 py-2">
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-xs uppercase px-1.5 py-0.5 rounded bg-gray-200">{{ item.item_type }}</span>
              @if (item.ai_generated) {
                <span class="text-xs text-purple-700">AI</span>
              }
              <span class="text-xs text-gray-500">{{ item.occurred_at | date:'mediumDate' }}</span>
            </div>
            @if (item.route) {
              <a [routerLink]="item.route" class="font-medium text-[var(--xp-blue)] underline">{{ item.title }}</a>
            } @else {
              <p class="font-medium">{{ item.title }}</p>
            }
            @if (item.description) {
              <p class="text-gray-700 mt-1">{{ item.description }}</p>
            }
            @if (item.tags) {
              <p class="text-xs text-gray-500 mt-1">{{ item.tags }}</p>
            }
          </li>
        } @empty {
          <li class="px-3 py-4 text-gray-600">No timeline events yet.</li>
        }
      </ul>
    </div>
  `,
})
export class LifeTimelinePageComponent implements OnInit {
  private readonly timeline = inject(LifeTimelineService);
  private readonly fb = inject(FormBuilder);
  items: LifeTimelineItem[] = [];
  form = this.fb.nonNullable.group({
    title: '',
    milestone_date: new Date().toISOString().slice(0, 10),
    description: '',
    tags: '',
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.timeline.list().subscribe({ next: (i) => (this.items = i) });
  }

  addMilestone(): void {
    if (this.form.invalid) return;
    const v = this.form.getRawValue();
    this.timeline.createMilestone({
      title: v.title,
      milestone_date: v.milestone_date,
      description: v.description || undefined,
      tags: v.tags || undefined,
    }).subscribe({
      next: () => {
        this.form.reset({ milestone_date: new Date().toISOString().slice(0, 10) });
        this.load();
      },
    });
  }
}
