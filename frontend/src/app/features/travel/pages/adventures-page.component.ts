import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { apiErrorMessage } from '../../../core/utils/http';
import { ADVENTURE_KINDS, Adventure, AdventureKind } from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';

/** Treks, hikes, road trips… (spec §14). */
@Component({
  selector: 'app-travel-adventures-page',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="space-y-3">
      <form class="panel flex flex-wrap items-end gap-2 text-sm" (submit)="$event.preventDefault(); create()">
        <div class="flex min-w-[12rem] flex-1 flex-col gap-1">
          <label class="form-label" for="adv-name">New adventure</label>
          <input id="adv-name" name="name" class="input-field" maxlength="200" placeholder="e.g. Hampta Pass trek" [(ngModel)]="name" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="form-label" for="adv-kind">Type</label>
          <select id="adv-kind" name="kind" class="input-field" [(ngModel)]="kind">
            @for (k of kinds; track k.id) {
              <option [value]="k.id">{{ k.label }}</option>
            }
          </select>
        </div>
        <button type="submit" class="btn-primary text-xs" [disabled]="!name.trim() || busy()">Create</button>
        @if (error()) {
          <p class="w-full text-xs" style="color: var(--danger)">{{ error() }}</p>
        }
      </form>

      @if (!adventures().length) {
        <p class="text-sm" style="color: var(--text-muted)">No adventures yet. Create one, then draw its route or import a GPX.</p>
      }
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        @for (a of adventures(); track a.id) {
          <div class="panel cursor-pointer space-y-1 text-sm" role="link" tabindex="0" (click)="open(a.id)" (keydown.enter)="open(a.id)">
            <div class="flex items-start justify-between gap-2">
              <span class="font-medium text-[var(--xp-blue)] underline">⛰️ {{ a.name }}</span>
              <span class="chip text-xs">{{ kindLabel(a.kind) }}</span>
            </div>
            <p class="text-xs capitalize" style="color: var(--text-muted)">
              {{ a.difficulty ?? 'difficulty not set' }} · {{ a.route_id ? 'has a route' : 'no route yet' }}
            </p>
          </div>
        }
      </div>
    </div>
  `,
})
export class AdventuresPageComponent implements OnInit {
  private readonly api = inject(TravelApiService);
  private readonly router = inject(Router);

  readonly kinds = ADVENTURE_KINDS;
  readonly adventures = signal<Adventure[]>([]);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  name = '';
  kind: AdventureKind = 'trek';

  ngOnInit(): void {
    this.api.listAdventures({ limit: 100 }).subscribe({ next: (page) => this.adventures.set(page.items) });
  }

  kindLabel(kind: AdventureKind): string {
    return ADVENTURE_KINDS.find((k) => k.id === kind)?.label ?? kind;
  }

  create(): void {
    this.busy.set(true);
    this.api.createAdventure({ name: this.name.trim(), kind: this.kind }).subscribe({
      next: (d) => void this.router.navigate(['/travel/adventures', d.adventure.id]),
      error: (err) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(err, 'Could not create the adventure'));
      },
    });
  }

  open(id: string): void {
    void this.router.navigate(['/travel/adventures', id]);
  }
}
