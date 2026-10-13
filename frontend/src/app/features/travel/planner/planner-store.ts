import { HttpErrorResponse, HttpStatusCode } from '@angular/common/http';
import { DestroyRef, Injectable, computed, inject, signal } from '@angular/core';
import { Observable, catchError, firstValueFrom, switchMap, throwError } from 'rxjs';
import { JoinResult, MyPlan, PlanDocument, PublicPlanView, ResolvedLink, ShareSession } from '../models/share.models';
import { GeoLookup, Suggestions } from '../models/travel.models';
import { LatLngBias, newSessionToken, suggestionStream } from '../utils/place-suggestions';
import { isShortMapsLink, parseMapsLink } from './maps-link';
import { PlannerApiService } from './planner-api.service';
import { StoredDraft, StoredIdentity, plannerStorage } from './planner-identity';

export type SaveState = 'idle' | 'saving' | 'saved' | 'offline' | 'error' | 'conflict';
export type PlannerMode = 'loading' | 'unavailable' | 'viewing' | 'editing' | 'locked';
export type Unavailable = 'not_found' | 'gone' | 'error';
export type PlanEdit = (doc: PlanDocument) => PlanDocument;

export const MAX_UNDO = 20;
export const SAVE_DELAY_MS = 800;
const RETRY_MAX_MS = 30_000;

/**
 * The friend planner's state (one per page): the shared plan, who the friend is, their own plan,
 * and autosave. Saving is optimistic: the screen changes at once, one save is in flight at a time
 * with the last confirmed revision (`If-Match`), failures retry with backoff, and the friend's
 * text is kept in this browser until the server has it (requirements FR-F3, D-17, T-11).
 */
@Injectable()
export class PlannerStore {
  private readonly api = inject(PlannerApiService);

  readonly code = signal('');
  readonly view = signal<PublicPlanView | null>(null);
  readonly unavailable = signal<Unavailable | null>(null);
  readonly identity = signal<StoredIdentity | null>(null);
  /** The friend's plan as the server last confirmed it (status, revision, sent state). */
  readonly mine = signal<MyPlan | null>(null);
  /** What the friend sees and edits (may be ahead of `mine` while saving). */
  readonly doc = signal<PlanDocument | null>(null);
  readonly saveState = signal<SaveState>('idle');
  readonly askWho = signal(false);
  readonly ownerHint = signal(false);
  readonly removed = signal(false);
  readonly lostAccess = signal(false);
  readonly toast = signal<{ message: string; undo: boolean } | null>(null);
  readonly restorable = signal<StoredDraft<PlanDocument> | null>(null);
  private readonly history = signal<PlanDocument[]>([]);

  readonly canUndo = computed(() => this.history().length > 0);
  readonly ownerName = computed(() => this.view()?.owner_name ?? '');
  readonly isFinal = computed(() => !!this.view()?.is_final);
  readonly mode = computed<PlannerMode>(() => {
    if (this.unavailable()) return 'unavailable';
    if (!this.view()) return 'loading';
    if (this.isFinal()) return 'locked';
    return this.mine() && !this.removed() ? 'editing' : 'viewing';
  });
  /** The plan on screen: the final plan once locked, else the friend's own, else the trip's. */
  readonly shown = computed<PlanDocument | null>(() => {
    const view = this.view();
    if (!view) return null;
    if (view.is_final) return view.plan;
    return this.doc() ?? view.plan;
  });
  readonly pending = computed(() => ['saving', 'offline', 'error', 'conflict'].includes(this.saveState()));

  private token: string | null = null;
  private revision = 0;
  private inFlight = false;
  private dirty = false;
  private timer: ReturnType<typeof setTimeout> | undefined;
  private retryDelay = 2000;
  private latestServerRevision: number | null = null;
  private queued: PlanEdit[] = [];
  private waiters: ((ok: boolean) => void)[] = [];
  private searchSession = newSessionToken();
  private afterJoin: (() => void)[] = [];

  constructor() {
    const online = () => {
      if (this.saveState() === 'offline' || this.saveState() === 'error') this.flush();
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('online', online);
      inject(DestroyRef).onDestroy(() => {
        window.removeEventListener('online', online);
        clearTimeout(this.timer);
      });
    }
  }

  // ---- loading -----------------------------------------------------------------------------

  async load(code: string): Promise<void> {
    this.code.set(code);
    this.unavailable.set(null);
    try {
      this.view.set(await firstValueFrom(this.api.view(code)));
    } catch (err) {
      const status = (err as HttpErrorResponse).status;
      this.unavailable.set(status === HttpStatusCode.NotFound ? 'not_found' : status === HttpStatusCode.Gone ? 'gone' : 'error');
      return;
    }
    const identity = plannerStorage.identity(code);
    if (!identity) return;
    this.identity.set(identity);
    this.token = plannerStorage.token(code)?.token ?? null;
    try {
      const me = await firstValueFrom(this.withToken((t) => this.api.me(code, t)));
      this.identity.set({ ...identity, contributor: me.contributor });
      if (me.plan) this.setMine(me.plan);
    } catch {
      return; // withToken already recorded "removed" / "lost access"; viewing still works
    }
    const draft = plannerStorage.draft<PlanDocument>(code);
    const mine = this.mine();
    if (draft && mine && !this.isFinal() && JSON.stringify(draft.doc) !== JSON.stringify(mine.document)) {
      this.restorable.set(draft);
    }
  }

  /** Re-reads the shared plan (e.g. after the owner locked it while the friend was editing). */
  async refreshView(): Promise<void> {
    try {
      this.view.set(await firstValueFrom(this.api.view(this.code())));
    } catch {
      // keep what is on screen
    }
  }

  // ---- identity ----------------------------------------------------------------------------

  async joinWithName(name: string): Promise<void> {
    await this.joined(await firstValueFrom(this.api.joinName(this.code(), name)));
  }

  /** Returns false when the Google account is the owner's (nothing is created). */
  async joinWithGoogle(credential: string): Promise<boolean> {
    const result = await firstValueFrom(this.api.joinGoogle(this.code(), credential));
    if ('owner' in result) {
      this.ownerHint.set(true);
      this.askWho.set(false);
      this.queued = [];
      this.afterJoin = [];
      return false;
    }
    await this.joined(result);
    return true;
  }

  async upgradeToGoogle(credential: string): Promise<void> {
    const result = await firstValueFrom(this.withToken((t) => this.api.upgradeGoogle(this.code(), t, credential)));
    this.remember(result);
  }

  /** Runs `action` now if the friend has said who they are, else right after they do. */
  whenIdentified(action: () => void): void {
    if (this.identity()) {
      action();
      return;
    }
    this.afterJoin.push(action);
    this.askWho.set(true);
  }

  forgetMe(): void {
    plannerStorage.setIdentity(this.code(), null);
    plannerStorage.setToken(this.code(), null);
    plannerStorage.setDraft(this.code(), null);
    this.identity.set(null);
    this.token = null;
    this.mine.set(null);
    this.doc.set(null);
    this.history.set([]);
    this.saveState.set('idle');
  }

  private async joined(result: JoinResult): Promise<void> {
    this.remember(result);
    this.removed.set(false);
    this.lostAccess.set(false);
    if (result.plan) this.setMine(result.plan);
    this.askWho.set(false);
    const queued = this.queued;
    this.queued = [];
    for (const edit of queued) await this.edit(edit);
    const actions = this.afterJoin;
    this.afterJoin = [];
    actions.forEach((action) => action());
  }

  private remember(result: JoinResult): void {
    const identity = { deviceSecret: result.device_secret, contributor: result.contributor };
    plannerStorage.setIdentity(this.code(), identity);
    this.identity.set(identity);
    this.useSession(result);
  }

  private useSession(session: ShareSession): void {
    this.token = session.token;
    plannerStorage.setToken(this.code(), { token: session.token, expiresAt: session.expires_at });
  }

  /** Runs a call with the share token; on 401 renews it once with the device secret and retries. */
  private withToken<T>(call: (token: string) => Observable<T>): Observable<T> {
    const renewAndRetry = (): Observable<T> => {
      const identity = this.identity();
      if (!identity) return throwError(() => new HttpErrorResponse({ status: HttpStatusCode.Unauthorized }));
      return this.api.renew(this.code(), identity.deviceSecret).pipe(
        switchMap((session) => {
          this.useSession(session);
          return call(session.token);
        }),
      );
    };
    const first = this.token ? call(this.token) : renewAndRetry();
    return first.pipe(
      catchError((err: HttpErrorResponse) => (err.status === HttpStatusCode.Unauthorized && this.token ? renewAndRetry() : throwError(() => err))),
      catchError((err: HttpErrorResponse) => {
        if (err.status === HttpStatusCode.Forbidden) this.removed.set(true);
        if (err.status === HttpStatusCode.Unauthorized && this.identity()) {
          this.lostAccess.set(true);
          plannerStorage.setIdentity(this.code(), null);
          this.identity.set(null);
          this.token = null;
        }
        return throwError(() => err);
      }),
    );
  }

  // ---- editing -----------------------------------------------------------------------------

  /** Applies an edit; the first one asks "Who are you?" and starts the friend's own plan. */
  async edit(edit: PlanEdit): Promise<void> {
    if (this.isFinal() || this.removed()) return;
    if (!this.identity()) {
      this.queued.push(edit);
      this.askWho.set(true);
      return;
    }
    if (!this.mine()) {
      try {
        this.setMine(await firstValueFrom(this.withToken((t) => this.api.startPlan(this.code(), t))));
      } catch (err) {
        if ((err as HttpErrorResponse).status === HttpStatusCode.Conflict) await this.refreshView();
        return;
      }
    }
    const current = this.doc();
    if (!current) return;
    this.history.update((h) => [...h.slice(-(MAX_UNDO - 1)), current]);
    this.doc.set(edit(current));
    this.changed();
  }

  /** Remove with an "Undo" toast (deleting must never lose a friend's text). */
  async removeWithUndo(edit: PlanEdit, message: string): Promise<void> {
    await this.edit(edit);
    this.toast.set({ message, undo: true });
  }

  undo(): void {
    const history = this.history();
    if (!history.length || this.isFinal()) return;
    this.doc.set(history[history.length - 1]);
    this.history.set(history.slice(0, -1));
    this.toast.set(null);
    this.changed();
  }

  async startOver(): Promise<void> {
    const before = this.doc();
    await this.whenSaved();
    const plan = await firstValueFrom(this.withToken((t) => this.api.resetPlan(this.code(), t, this.revision)));
    if (before) this.history.update((h) => [...h.slice(-(MAX_UNDO - 1)), before]);
    this.setMine(plan);
  }

  restoreUnsaved(): void {
    const draft = this.restorable();
    this.restorable.set(null);
    if (!draft) return;
    this.doc.set(draft.doc);
    this.changed();
  }

  discardUnsaved(): void {
    this.restorable.set(null);
    plannerStorage.setDraft(this.code(), null);
  }

  // ---- saving ------------------------------------------------------------------------------

  private setMine(plan: MyPlan): void {
    this.mine.set(plan);
    this.revision = plan.revision;
    this.doc.set(plan.document);
  }

  private changed(): void {
    plannerStorage.setDraft(this.code(), { revision: this.revision, doc: this.doc(), savedAt: new Date().toISOString() });
    this.saveState.set('saving');
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.flush(), SAVE_DELAY_MS);
  }

  private flush(): void {
    clearTimeout(this.timer);
    if (this.inFlight) {
      this.dirty = true;
      return;
    }
    const doc = this.doc();
    if (!doc || !this.mine() || this.saveState() === 'conflict') return;
    this.inFlight = true;
    this.dirty = false;
    this.saveState.set('saving');
    this.withToken((t) => this.api.savePlan(this.code(), t, this.revision, doc)).subscribe({
      next: (plan) => {
        this.inFlight = false;
        this.revision = plan.revision;
        this.mine.set({ ...plan, document: doc });
        this.retryDelay = 2000;
        if (this.dirty || this.doc() !== doc) {
          this.flush();
          return;
        }
        plannerStorage.setDraft(this.code(), null);
        this.saveState.set('saved');
        this.settle(true);
      },
      error: (err: HttpErrorResponse) => {
        this.inFlight = false;
        this.saveFailed(err);
      },
    });
  }

  private saveFailed(err: HttpErrorResponse): void {
    switch (err.status) {
      case HttpStatusCode.PreconditionFailed:
        this.latestServerRevision = (err.error?.detail?.revision as number | undefined) ?? null;
        this.saveState.set('conflict');
        break;
      case HttpStatusCode.Conflict:
        this.saveState.set('idle');
        void this.refreshView();
        break;
      case HttpStatusCode.Forbidden:
      case HttpStatusCode.Unauthorized:
        this.saveState.set('error');
        break;
      case HttpStatusCode.UnprocessableEntity:
      case HttpStatusCode.PayloadTooLarge:
        this.saveState.set('error');
        break;
      default:
        // Network down (0), server busy (429/5xx): keep the text and retry with backoff.
        this.saveState.set('offline');
        this.timer = setTimeout(() => this.flush(), this.retryDelay);
        this.retryDelay = Math.min(this.retryDelay * 2, RETRY_MAX_MS);
        break;
    }
    // Anyone waiting (e.g. Send) hears now; offline saves keep retrying in the background.
    this.settle(false);
  }

  /** "Load the newer plan": take what another device saved. */
  async reloadNewer(): Promise<void> {
    const me = await firstValueFrom(this.withToken((t) => this.api.me(this.code(), t)));
    if (me.plan) this.setMine(me.plan);
    this.history.set([]);
    plannerStorage.setDraft(this.code(), null);
    this.saveState.set('saved');
  }

  /** "Keep mine": save this device's plan over the newer one. */
  keepMine(): void {
    if (this.latestServerRevision !== null) this.revision = this.latestServerRevision;
    this.saveState.set('saving');
    this.flush();
  }

  /** Resolves once everything typed so far is saved (false if saving failed). */
  whenSaved(): Promise<boolean> {
    if (!this.pending() || this.saveState() === 'conflict') return Promise.resolve(this.saveState() !== 'conflict');
    return new Promise((resolve) => {
      this.waiters.push(resolve);
      if (!this.inFlight) this.flush();
    });
  }

  private settle(ok: boolean): void {
    const waiters = this.waiters;
    this.waiters = [];
    waiters.forEach((resolve) => resolve(ok));
  }

  async send(message: string | null): Promise<boolean> {
    if (!(await this.whenSaved())) return false;
    try {
      const plan = await firstValueFrom(this.withToken((t) => this.api.submit(this.code(), t, message)));
      this.mine.set({ ...plan, document: this.doc() ?? plan.document });
      return true;
    } catch (err) {
      if ((err as HttpErrorResponse).status === HttpStatusCode.Conflict) await this.refreshView();
      return false;
    }
  }

  // ---- adding places -----------------------------------------------------------------------

  /** Place search on the owner's key through the backend (capped per link; see `fallback_reason`). */
  suggestions(query$: Observable<string>, bias?: () => LatLngBias): Observable<Suggestions> {
    return suggestionStream(
      query$,
      (q, center) => this.withToken((t) => this.api.autocomplete(this.code(), t, q, this.searchSession, center)),
      bias,
    );
  }

  /** Picking a suggestion ends the Places session (Google bills a search and its pick together). */
  pickSuggestion(placeId: string): Promise<GeoLookup> {
    const session = this.searchSession;
    this.searchSession = newSessionToken();
    return firstValueFrom(this.withToken((t) => this.api.placeDetails(this.code(), t, placeId, session)));
  }

  /** A pasted Google Maps link: full links are read here, short app links by the backend. */
  async readLink(url: string): Promise<ResolvedLink | null> {
    if (!isShortMapsLink(url)) return parseMapsLink(url);
    try {
      const link = await firstValueFrom(this.withToken((t) => this.api.resolveLink(this.code(), t, url)));
      return link.name || link.lat !== null ? link : null;
    } catch {
      return null;
    }
  }
}
