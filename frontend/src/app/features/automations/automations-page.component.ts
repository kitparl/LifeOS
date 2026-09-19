import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { PaginatedListState } from '../../shared/pagination/paginated-list.state';
import { AutomationRule, AutomationsService } from './services/automations.service';

@Component({
  selector: 'app-automations-page',
  standalone: true,
  imports: [ReactiveFormsModule, ListPaginatorComponent],
  template: `
    <div class="space-y-4">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">
          <span>New rule</span>
          <button type="button" class="btn-primary text-xs ml-auto" (click)="evaluate()">Evaluate rules</button>
        </div>
        <form class="grid gap-2 p-3 text-sm sm:grid-cols-2" [formGroup]="form" (ngSubmit)="add()">
          <input class="input-field" formControlName="name" placeholder="Rule name" />
          <select class="input-field" formControlName="trigger_type">
            <option value="no_journal_days">No journal for N days</option>
            <option value="budget_exceeded">Budget exceeded</option>
            <option value="running_goal_missed">Running goal missed</option>
          </select>
          <select class="input-field" formControlName="action_type">
            <option value="notify">Notify</option>
            <option value="generate_report">Generate report</option>
            <option value="telegram">Telegram (stub)</option>
          </select>
          <input class="input-field" formControlName="condition_json" placeholder='{"days":3} or {"category":"food"}' />
          <button type="submit" class="btn-primary text-xs sm:col-span-2 !w-fit" [disabled]="form.invalid">Add rule</button>
        </form>
      </div>
      <div class="panel !p-0 overflow-hidden">
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (r of rules; track r.id) {
            <li class="flex justify-between gap-2 px-3 py-2">
              <div>
                <p class="font-medium">{{ r.name }}</p>
                <p class="text-xs" style="color: var(--text-muted)">{{ r.trigger_type }} → {{ r.action_type }}</p>
              </div>
              <button type="button" class="text-xs" style="color: var(--danger)" (click)="remove(r.id)">Delete</button>
            </li>
          }
        </ul>
        <app-list-paginator
          [total]="paging.total"
          [pageSize]="paging.pageSize"
          [currentPage]="paging.currentPage"
          (pageChange)="setPage($event)"
        />
      </div>
      @if (evalResults) {
        <div class="panel text-sm">
          <p class="font-medium mb-2">Last evaluation: {{ evalResults.triggered }}/{{ evalResults.evaluated }} triggered</p>
          <ul class="space-y-1">
            @for (res of evalResults.results; track res.rule_name) {
              <li>{{ res.rule_name }}: {{ res.triggered ? '✓' : '—' }} {{ res.message }}</li>
            }
          </ul>
        </div>
      }
    </div>
  `,
})
export class AutomationsPageComponent implements OnInit {
  private readonly automations = inject(AutomationsService);
  private readonly fb = inject(FormBuilder);
  rules: AutomationRule[] = [];
  readonly paging = new PaginatedListState();
  evalResults: { evaluated: number; triggered: number; results: { rule_name: string; triggered: boolean; message: string | null }[] } | null = null;
  form = this.fb.nonNullable.group({
    name: '',
    trigger_type: 'no_journal_days',
    action_type: 'notify',
    condition_json: '{"days":3}',
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.automations.list({ limit: this.paging.pageSize, offset: this.paging.offset }).subscribe({
      next: (result) => {
        this.rules = result.items;
        this.paging.total = result.total;
        this.clampPage();
      },
    });
  }

  setPage(page: number): void {
    this.paging.setPage(page);
    this.load();
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.paging.total / this.paging.pageSize));
    if (this.paging.currentPage > totalPages) {
      this.paging.setPage(totalPages);
      this.load();
    }
  }

  add(): void {
    if (this.form.invalid) return;
    this.automations.create(this.form.getRawValue()).subscribe({
      next: () => {
        this.form.reset({ trigger_type: 'no_journal_days', action_type: 'notify', condition_json: '{"days":3}' });
        this.paging.setPage(1);
        this.load();
      },
    });
  }

  remove(id: string): void {
    this.automations.delete(id).subscribe({ next: () => this.load() });
  }

  evaluate(): void {
    this.automations.evaluate().subscribe({ next: (r) => (this.evalResults = r) });
  }
}
