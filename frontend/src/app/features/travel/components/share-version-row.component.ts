import { DatePipe } from '@angular/common';
import { Component, computed, input, output, signal } from '@angular/core';
import { VersionRow } from '../models/share.models';
import { statusBadge, summaryLine } from '../utils/plan-summary';

export type VersionAction = 'preview' | 'compare' | 'pdf' | 'apply' | 'lock' | 'delete';

/** One version in the owner's list: who made it, its status, how it differs from the Original, actions. */
@Component({
  selector: 'app-share-version-row',
  standalone: true,
  imports: [DatePipe],
  template: `
    @let v = row();
    <li class="space-y-1 rounded border border-[var(--xp-border)] p-2" [attr.data-testid]="'version-' + v.id">
      <div class="flex flex-wrap items-center gap-2">
        @if (renaming()) {
          <input
            #label
            class="input-field min-w-[10rem] flex-1 text-sm"
            maxlength="80"
            aria-label="Version name"
            [value]="v.label"
            (keydown.enter)="saveName(label.value)"
            (keydown.escape)="renaming.set(false)"
          />
          <button type="button" class="btn-primary text-xs" (click)="saveName(label.value)">Save</button>
        } @else {
          <span class="font-medium">{{ v.label }}</span>
          @if (v.kind !== 'original') {
            <button type="button" class="text-xs underline" [attr.aria-label]="'Rename ' + v.label" (click)="renaming.set(true)">Rename</button>
          }
        }
        <span class="chip text-xs" data-testid="version-badge">{{ badge() }}</span>
        @if (v.edited_since_sent) {
          <span class="text-xs" style="color: var(--text-muted)">edited since sent</span>
        }
      </div>
      <p class="text-xs" style="color: var(--text-muted)">
        {{ v.author_name }}@if (v.author_email) { ({{ v.author_email }}) }
        @if (v.contributor_removed) { · removed }
        · updated {{ v.updated_at | date: 'medium' }}
      </p>
      <p class="text-xs" data-testid="version-summary">{{ summary() }}</p>
      @if (v.message) {
        <p class="text-xs italic">“{{ v.message }}”</p>
      }
      <div class="flex flex-wrap gap-2 pt-1">
        <button type="button" class="btn-secondary text-xs" (click)="act.emit('preview')">Preview</button>
        @if (v.kind !== 'original') {
          <button type="button" class="btn-secondary text-xs" (click)="act.emit('compare')">Compare</button>
        }
        <button type="button" class="btn-secondary text-xs" (click)="act.emit('pdf')">PDF</button>
        <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="act.emit('apply')">Apply to my trip</button>
        @if (!v.is_locked && v.kind !== 'backup') {
          <button type="button" class="btn-primary text-xs" [disabled]="busy()" data-testid="version-lock" (click)="act.emit('lock')">Lock this version</button>
        }
        @if (!v.is_locked && v.kind !== 'original') {
          <button type="button" class="text-xs" style="color: var(--danger)" [disabled]="busy()" (click)="act.emit('delete')">Delete</button>
        }
      </div>
    </li>
  `,
})
export class ShareVersionRowComponent {
  readonly row = input.required<VersionRow>();
  readonly busy = input(false);
  readonly act = output<VersionAction>();
  readonly rename = output<string>();

  readonly renaming = signal(false);
  readonly badge = computed(() => statusBadge(this.row()));
  readonly summary = computed(() => summaryLine(this.row()));

  saveName(label: string): void {
    const trimmed = label.trim();
    if (trimmed && trimmed !== this.row().label) this.rename.emit(trimmed);
    this.renaming.set(false);
  }
}
