import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-running-goals-tab',
  standalone: true,
  imports: [ReactiveFormsModule],
  host: { class: 'contents' },
  template: `
    <div class="panel !p-0 overflow-hidden" style="max-width: 400px">
      <div class="title-bar">Running Goals</div>
      <form class="space-y-3 p-4 text-sm" [formGroup]="settingsForm" (ngSubmit)="saveSettings.emit()">
        <div>
          <label class="form-label">Weekly goal (km)</label>
          <input class="input-field mt-1" type="number" step="0.1" formControlName="weekly_goal_km" />
        </div>
        <div>
          <label class="form-label">Target marathon</label>
          <input class="input-field mt-1" formControlName="target_marathon_name" placeholder="Race name" />
        </div>
        <div>
          <label class="form-label">Marathon date</label>
          <input class="input-field mt-1" type="date" formControlName="target_marathon_date" />
        </div>
        <div>
          <label class="form-label">Half marathon date</label>
          <input class="input-field mt-1" type="date" formControlName="target_half_marathon_date" />
        </div>
        <button type="submit" class="btn-primary text-xs w-full" [disabled]="settingsForm.invalid">Save goals</button>
      </form>
    </div>
    <style>
      .form-label {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text);
      }
    </style>
  `,
})
export class RunningGoalsTabComponent {
  @Input({ required: true }) settingsForm!: FormGroup;
  @Output() readonly saveSettings = new EventEmitter<void>();
}
