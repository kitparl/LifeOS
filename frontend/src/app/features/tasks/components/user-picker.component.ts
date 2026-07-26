import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { debounceTime, distinctUntilChanged, switchMap, of } from 'rxjs';
import { PublicUser } from '../../../core/models/auth.models';
import { UsernameService } from '../../../core/services/username.service';

@Component({
  selector: 'app-user-picker',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="relative">
      <input
        class="input-field w-full text-sm"
        [formControl]="query"
        [placeholder]="placeholder"
        autocomplete="off"
      />
      @if (results.length) {
        <ul
          class="absolute z-20 mt-1 max-h-48 w-full overflow-auto border border-[var(--xp-border)] bg-[var(--surface)]"
          style="box-shadow: var(--shadow-sm, 0 2px 8px rgba(0,0,0,.08))"
        >
          @for (u of results; track u.username) {
            <li>
              <button
                type="button"
                class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-[var(--primary-soft)]"
                (click)="select(u)"
              >
                <span class="font-medium">{{ '@' + u.username }}</span>
                <span style="color: var(--text-muted)">{{ u.display_name }}</span>
              </button>
            </li>
          }
        </ul>
      }
      @if (selected) {
        <p class="mt-1 text-xs" style="color: var(--text-muted)">
          <span class="chip text-xs">{{ '@' + selected.username }}</span>
          {{ selected.display_name }}
          <button type="button" class="ml-2 underline" (click)="clear()">Clear</button>
        </p>
      }
    </div>
  `,
})
export class UserPickerComponent {
  private readonly usernames = inject(UsernameService);
  private readonly fb = inject(FormBuilder);

  @Input() placeholder = 'Search by username…';
  @Output() readonly picked = new EventEmitter<PublicUser | null>();

  query = this.fb.nonNullable.control('');
  results: PublicUser[] = [];
  selected: PublicUser | null = null;

  constructor() {
    this.query.valueChanges
      .pipe(
        debounceTime(250),
        distinctUntilChanged(),
        switchMap((q) => {
          const term = (q || '').trim();
          if (term.length < 1) {
            this.results = [];
            return of([] as PublicUser[]);
          }
          return this.usernames.search(term, 10);
        }),
      )
      .subscribe((rows) => {
        this.results = rows;
      });
  }

  select(u: PublicUser): void {
    this.selected = u;
    this.results = [];
    this.query.setValue(u.username, { emitEvent: false });
    this.picked.emit(u);
  }

  clear(): void {
    this.selected = null;
    this.query.setValue('');
    this.picked.emit(null);
  }
}
