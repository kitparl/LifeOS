import { HttpErrorResponse, HttpStatusCode } from '@angular/common/http';
import { Component, OnInit, computed, inject, input, output, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { saveBlob } from '../../../core/utils/download';
import { apiErrorMessage } from '../../../core/utils/http';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { ShareActionsComponent } from '../../../shared/share/share-actions.component';
import { PlanDocument, TripShare, VersionDetail, VersionRow } from '../models/share.models';
import { ShareApiService } from '../services/share-api.service';
import { TRIP_SHARE_TEXT } from '../utils/plan-summary';
import { ShareLockDialogComponent } from './share-lock-dialog.component';
import { ShareVersionPreviewComponent } from './share-version-preview.component';
import { ShareVersionRowComponent, VersionAction } from './share-version-row.component';

/**
 * "Share & collaborate" on a trip: one link friends open in the separate planner, their versions
 * (latest edited first), and lock / apply. Keeps the normal LifeOS look (requirements FR-O1..O5).
 */
@Component({
  selector: 'app-trip-share-panel',
  standalone: true,
  imports: [ShareActionsComponent, ShareVersionRowComponent, ShareVersionPreviewComponent, ShareLockDialogComponent],
  template: `
    <details class="panel text-sm" [open]="startOpen()" data-testid="trip-share-panel">
      <summary class="cursor-pointer font-medium">
        Share &amp; collaborate
        @if (share(); as s) {
          <span class="chip ml-1 text-xs">{{ stateLabel() }}</span>
        }
      </summary>
      <div class="mt-2 space-y-3">
        @if (error()) {
          <p class="text-xs" style="color: var(--danger)" role="alert">{{ error() }}</p>
        }
        @if (loading()) {
          <div class="skeleton h-16 rounded"></div>
        } @else if (!share()) {
          <p>
            Share one link and friends can build their own version of this plan in a simple planner, no account needed.
            Nothing changes in your trip until you choose a version.
          </p>
          <p class="text-xs" style="color: var(--text-muted)">
            Friends will see the trip name, description, dates, days and stops, including their notes.
          </p>
          <button type="button" class="btn-primary text-xs" data-testid="share-create" [disabled]="busy()" (click)="create()">Create link</button>
        } @else {
          @let s = share()!;
          @if (s.state === 'revoked') {
            <p>This link is turned off. Friends' plans are kept.</p>
            <button type="button" class="btn-primary text-xs" [disabled]="busy()" (click)="newLink()">Create a new link</button>
          } @else {
            @if (s.state === 'locked') {
              <p data-testid="share-locked">The plan is final. Friends see it read-only.</p>
            }
            <app-share-actions [name]="tripName()" [urlPath]="s.url_path" [text]="shareText" testIdPrefix="trip-share" />
            <div class="flex flex-wrap gap-2">
              @if (s.state === 'locked') {
                <button type="button" class="btn-secondary text-xs" data-testid="share-unlock" [disabled]="busy()" (click)="unlock()">Unlock for changes</button>
              }
              <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="newLink()">New link</button>
              <button type="button" class="text-xs" style="color: var(--danger)" [disabled]="busy()" (click)="revoke()">Turn off link</button>
            </div>
          }

          <fieldset class="space-y-2 rounded border border-[var(--xp-border)] p-2">
            <legend class="px-1 text-xs font-medium">Who can make a plan</legend>
            <label class="flex items-center gap-2 text-xs">
              <input type="checkbox" [checked]="s.require_google" [disabled]="busy()" (change)="setRequireGoogle(!s.require_google)" />
              Require Google sign-in
            </label>
            <label class="block text-xs">
              Only these Gmail addresses (one per line; empty = anyone with the link)
              <textarea
                #emails
                class="input-field mt-1 w-full text-xs"
                rows="2"
                [value]="s.allowed_emails.join('\\n')"
              ></textarea>
            </label>
            <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="saveEmails(emails.value)">Save list</button>
          </fieldset>

          @if (s.contributors.length) {
            <div class="space-y-1">
              <h3 class="text-xs font-medium">People helping ({{ s.contributors.length }})</h3>
              <ul class="space-y-1">
                @for (c of s.contributors; track c.id) {
                  <li class="flex items-center justify-between gap-2 text-xs">
                    <span>
                      {{ c.display_name }}@if (c.google_email) { ({{ c.google_email }}) }
                      @if (c.removed) { <span class="chip">Removed</span> }
                    </span>
                    @if (!c.removed) {
                      <button type="button" style="color: var(--danger)" [disabled]="busy()" (click)="removeContributor(c.id, c.display_name)">Remove</button>
                    }
                  </li>
                }
              </ul>
            </div>
          }

          <div class="space-y-2">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <h3 class="text-xs font-medium">Versions (latest first)</h3>
              <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="snapshot()">Save my current trip as a version</button>
            </div>
            <ul class="space-y-2" data-testid="share-versions">
              @for (v of versions(); track v.id) {
                <app-share-version-row [row]="v" [busy]="busy()" (act)="onAction(v, $event)" (rename)="rename(v, $event)" />
              }
            </ul>
          </div>
        }
      </div>
    </details>

    <app-share-version-preview [version]="preview()" [original]="compareWith()" (closed)="closePreview()" />
    <app-share-lock-dialog
      [version]="lockTarget()"
      [busy]="busy()"
      [tripDays]="tripDays()"
      [tripStart]="tripStart()"
      (confirmed)="lock($event)"
      (closed)="lockTarget.set(null)"
    />
  `,
})
export class TripSharePanelComponent implements OnInit {
  private readonly api = inject(ShareApiService);
  private readonly confirm = inject(ConfirmService);

  readonly tripId = input.required<string>();
  readonly tripName = input.required<string>();
  readonly tripDays = input(0);
  readonly tripStart = input<string | null>(null);
  readonly startOpen = input(false);
  /** The trip's itinerary was replaced (apply): the page reloads the trip. */
  readonly applied = output<void>();

  readonly shareText = TRIP_SHARE_TEXT;
  readonly share = signal<TripShare | null>(null);
  readonly versions = signal<VersionRow[]>([]);
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly preview = signal<VersionDetail | null>(null);
  readonly compareWith = signal<PlanDocument | null>(null);
  readonly lockTarget = signal<VersionRow | null>(null);

  readonly stateLabel = computed(() => {
    const state = this.share()?.state;
    return state === 'locked' ? 'Final plan' : state === 'revoked' ? 'Link off' : 'Link on';
  });

  ngOnInit(): void {
    this.api.get(this.tripId()).subscribe({
      next: (share) => {
        this.share.set(share);
        this.loading.set(false);
        this.loadVersions();
      },
      error: (err: unknown) => {
        this.loading.set(false);
        if (!(err instanceof HttpErrorResponse && err.status === HttpStatusCode.NotFound)) {
          this.error.set(apiErrorMessage(err, 'Could not load sharing'));
        }
      },
    });
  }

  private loadVersions(): void {
    this.api.versions(this.tripId()).subscribe({
      next: (rows) => this.versions.set(rows),
      error: (err) => this.error.set(apiErrorMessage(err, 'Could not load versions')),
    });
  }

  /** Runs a call with the busy flag and error handling; `done` gets the result. */
  private run<T>(call: Observable<T>, done: (value: T) => void, fallback = 'Something went wrong'): void {
    this.busy.set(true);
    this.error.set(null);
    call.subscribe({
      next: (value) => {
        this.busy.set(false);
        done(value);
      },
      error: (err) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(err, fallback));
      },
    });
  }

  private setShare = (share: TripShare): void => {
    this.share.set(share);
    this.loadVersions();
  };

  create(): void {
    this.run(this.api.create(this.tripId()), this.setShare, 'Could not create the link');
  }

  async revoke(): Promise<void> {
    const ok = await this.confirm.confirm(
      'The link stops working for everyone. Friends\' plans are kept and you can create a new link later.',
      'Turn off this link?',
      { acceptLabel: 'Turn off' },
    );
    if (ok) this.run(this.api.revoke(this.tripId()), this.setShare);
  }

  async newLink(): Promise<void> {
    const ok =
      this.share()?.state === 'revoked' ||
      (await this.confirm.confirm('The current link stops working. Share the new one with your friends.', 'Create a new link?', {
        acceptLabel: 'Create new link',
        danger: false,
      }));
    if (ok) this.run(this.api.newLink(this.tripId()), this.setShare);
  }

  unlock(): void {
    this.run(this.api.unlock(this.tripId()), this.setShare);
  }

  setRequireGoogle(value: boolean): void {
    this.run(this.api.updateSettings(this.tripId(), { require_google: value }), this.setShare);
  }

  saveEmails(raw: string): void {
    const emails = raw
      .split(/[\s,;]+/)
      .map((e) => e.trim())
      .filter(Boolean);
    this.run(this.api.updateSettings(this.tripId(), { allowed_emails: emails }), this.setShare, 'Check the email addresses');
  }

  async removeContributor(id: string, name: string): Promise<void> {
    const ok = await this.confirm.confirm(`${name} can no longer edit. Their plan is kept.`, `Remove ${name}?`, { acceptLabel: 'Remove' });
    if (ok) this.run(this.api.removeContributor(this.tripId(), id), this.setShare);
  }

  snapshot(): void {
    this.run(this.api.snapshotTrip(this.tripId()), () => this.loadVersions());
  }

  rename(row: VersionRow, label: string): void {
    this.run(this.api.rename(this.tripId(), row.id, label), () => this.loadVersions());
  }

  onAction(row: VersionRow, action: VersionAction): void {
    switch (action) {
      case 'preview':
        return this.openPreview(row, false);
      case 'compare':
        return this.openPreview(row, true);
      case 'pdf':
        return this.run(this.api.versionPdf(this.tripId(), row.id), (blob) => saveBlob(blob, `${row.label}.pdf`), 'Could not create the PDF');
      case 'apply':
        return void this.applyOnly(row);
      case 'lock':
        return this.lockTarget.set(row);
      case 'delete':
        return void this.deleteVersion(row);
    }
  }

  private openPreview(row: VersionRow, compare: boolean): void {
    const originalId = this.share()?.original_version_id;
    this.run(this.api.version(this.tripId(), row.id), (detail) => {
      if (!compare || !originalId) {
        this.compareWith.set(null);
        this.preview.set(detail);
        return;
      }
      this.run(this.api.version(this.tripId(), originalId), (original) => {
        this.compareWith.set(original.document);
        this.preview.set(detail);
      });
    });
  }

  closePreview(): void {
    this.preview.set(null);
    this.compareWith.set(null);
  }

  private async applyOnly(row: VersionRow): Promise<void> {
    const ok = await this.confirm.confirm(
      `Your trip's days and stops are replaced by "${row.label}". A backup of your current trip is saved first.`,
      'Apply to my trip?',
      { acceptLabel: 'Apply', danger: false },
    );
    if (ok) this.run(this.api.apply(this.tripId(), row.id), () => this.afterApply());
  }

  lock(apply: boolean): void {
    const target = this.lockTarget();
    if (!target) return;
    this.run(this.api.lock(this.tripId(), target.id, apply), (result) => {
      this.lockTarget.set(null);
      this.setShare(result.share);
      if (result.applied) this.applied.emit();
    });
  }

  private afterApply(): void {
    this.loadVersions();
    this.applied.emit();
  }

  private async deleteVersion(row: VersionRow): Promise<void> {
    const ok = await this.confirm.confirm(`"${row.label}" will be deleted.`, 'Delete this version?');
    if (ok) this.run(this.api.deleteVersion(this.tripId(), row.id), () => this.loadVersions());
  }
}
