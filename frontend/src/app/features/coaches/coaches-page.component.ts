import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { CoachesService } from './services/coaches.service';

@Component({
  selector: 'app-coaches-page',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="space-y-4 max-w-2xl">
      <h1 class="text-lg font-semibold">AI Life Coaches</h1>
      <form class="panel space-y-2 text-sm" [formGroup]="form" (ngSubmit)="ask()">
        <select class="input-field" formControlName="coach_type">
          @for (t of types; track t) {
            <option [value]="t">{{ t }}</option>
          }
        </select>
        <textarea class="input-field min-h-[80px]" formControlName="message" placeholder="Ask your coach…"></textarea>
        <button type="submit" class="btn-primary text-xs" [disabled]="form.invalid || loading">Ask coach</button>
      </form>
      @if (reply) {
        <div class="panel text-sm whitespace-pre-wrap">{{ reply }}</div>
        @if (context) {
          <p class="text-xs text-gray-600">Context: {{ context }}</p>
        }
      }
    </div>
  `,
})
export class CoachesPageComponent implements OnInit {
  private readonly coaches = inject(CoachesService);
  private readonly fb = inject(FormBuilder);
  types: string[] = [];
  reply: string | null = null;
  context: string | null = null;
  loading = false;
  form = this.fb.nonNullable.group({ coach_type: 'running', message: '' });

  ngOnInit(): void {
    this.coaches.types().subscribe({
      next: (r) => {
        this.types = r.types;
        if (r.types.length) this.form.patchValue({ coach_type: r.types[0] });
      },
    });
  }

  ask(): void {
    if (this.form.invalid) return;
    const { coach_type, message } = this.form.getRawValue();
    this.loading = true;
    this.coaches.chat(coach_type, message).subscribe({
      next: (r) => {
        this.reply = r.reply;
        this.context = r.context_summary;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
