import { CdkDragDrop, CdkDropListGroup } from '@angular/cdk/drag-drop';
import { DOCUMENT } from '@angular/common';
import { Component, HostListener, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute } from '@angular/router';
import { apiErrorMessage } from '../../../core/utils/http';
import { PlanStop } from '../models/share.models';
import { LatLngBias } from '../utils/place-suggestions';
import { PlannerAddStopComponent } from './components/add-stop-sheet.component';
import { PlannerDayComponent } from './components/day-section.component';
import { PlannerDayRailComponent } from './components/day-rail.component';
import { PlannerFirstRunComponent } from './components/first-run.component';
import { PlannerHeaderComponent } from './components/planner-header.component';
import { PlannerMapComponent } from './components/planner-map.component';
import { PlannerMeComponent } from './components/me-panel.component';
import { PlannerSendComponent } from './components/send-bar.component';
import { PlannerSheetComponent } from './components/planner-sheet.component';
import { PlannerThemeComponent } from './components/planner-theme.component';
import { PlannerToastComponent } from './components/undo-toast.component';
import { PlannerWhoComponent } from './components/who-are-you-sheet.component';
import { StopFields, addDay, addStop, moveStopToDay, newStop, nudgeStop, removeDay, removeStop, updateStop } from './plan-ops';
import { COPY } from './planner-copy';
import { plannerStorage } from './planner-identity';
import { PlannerStore } from './planner-store';

type Tab = 'plan' | 'map' | 'me';

/**
 * The public friend planner at /t/<code>: a separate, friendly app (own scoped design under
 * `.tp-root`) on top of the LifeOS shell. Phone: one column with Plan | Map | Me tabs and a sticky
 * Send bar. Tablet: plan + map. Desktop: days | stops | map (requirements FR-F1..F10, NFR-UX).
 */
@Component({
  selector: 'app-planner-page',
  standalone: true,
  imports: [
    CdkDropListGroup,
    PlannerThemeComponent,
    PlannerHeaderComponent,
    PlannerDayRailComponent,
    PlannerDayComponent,
    PlannerMapComponent,
    PlannerMeComponent,
    PlannerSendComponent,
    PlannerAddStopComponent,
    PlannerWhoComponent,
    PlannerSheetComponent,
    PlannerToastComponent,
    PlannerFirstRunComponent,
  ],
  providers: [PlannerStore],
  templateUrl: './planner-page.component.html',
  styleUrl: './planner-page.component.css',
})
export class PlannerPageComponent implements OnInit, OnDestroy {
  readonly store = inject(PlannerStore);
  private readonly route = inject(ActivatedRoute);
  private readonly title = inject(Title);
  private readonly document = inject(DOCUMENT);

  readonly copy = COPY;
  readonly tabs: readonly Tab[] = ['plan', 'map', 'me'];
  readonly tab = signal<Tab>('plan');
  /** Tablet and up show the map beside the plan; phones only on the Map tab. */
  readonly wide = signal(false);
  private wideQuery: MediaQueryList | null = null;
  private readonly onWide = (e: MediaQueryListEvent) => this.wide.set(e.matches);
  readonly meOpen = signal(false);
  readonly firstRun = signal(!plannerStorage.firstRunDone());
  readonly sheet = signal<{ day: number; stop: PlanStop | null } | null>(null);
  readonly whoError = signal<string | null>(null);
  readonly busy = signal(false);
  private referrerMeta: HTMLMetaElement | null = null;
  private previousTitle = '';

  readonly plan = computed(() => this.store.shown());
  readonly editable = computed(() => this.store.mode() === 'viewing' || this.store.mode() === 'editing');
  readonly showOwnerShortcut = computed(() => !!this.store.view()?.viewer_is_owner || this.store.ownerHint());
  readonly manageLink = computed(() => this.store.view()?.manage_path ?? '/travel/trips');
  readonly sheetDayLabel = computed(() => {
    const s = this.sheet();
    return s ? this.dayLabel(s.day) : null;
  });

  ngOnInit(): void {
    const code = this.route.snapshot.paramMap.get('code') ?? '';
    // The page's own requests never send the address (the code) to other sites.
    this.referrerMeta = this.document.createElement('meta');
    this.referrerMeta.name = 'referrer';
    this.referrerMeta.content = 'no-referrer';
    this.document.head.appendChild(this.referrerMeta);
    this.previousTitle = this.title.getTitle();
    this.wideQuery = matchMedia('(min-width: 640px)');
    this.wide.set(this.wideQuery.matches);
    this.wideQuery.addEventListener('change', this.onWide);
    void this.store.load(code).then(() => {
      const name = this.store.view()?.trip.name;
      if (name) this.title.setTitle(name);
    });
  }

  ngOnDestroy(): void {
    this.wideQuery?.removeEventListener('change', this.onWide);
    this.referrerMeta?.remove();
    this.title.setTitle(this.previousTitle);
  }

  // ---- leaving with unsaved work -----------------------------------------------------------

  canLeave(): boolean {
    return !this.store.pending() || confirm(COPY.leaveWarning);
  }

  @HostListener('window:beforeunload', ['$event'])
  onBeforeUnload(event: BeforeUnloadEvent): void {
    if (this.store.pending()) event.preventDefault();
  }

  @HostListener('document:keydown', ['$event'])
  onKey(event: KeyboardEvent): void {
    if (!(event.key === 'z' || event.key === 'Z') || !(event.ctrlKey || event.metaKey) || event.shiftKey) return;
    const target = event.target as HTMLElement | null;
    if (target?.closest('input, textarea, [contenteditable="true"]')) return; // the browser's own text undo
    event.preventDefault();
    this.store.undo();
  }

  // ---- labels --------------------------------------------------------------------------------

  dayLabel(index: number): string {
    const date = this.dayDate(index);
    return date ? `${COPY.day(index + 1)} · ${date}` : COPY.day(index + 1);
  }

  dayDate(index: number): string | null {
    const start = this.store.view()?.trip.start_date;
    if (!start) return null;
    const d = new Date(`${start}T00:00:00`);
    d.setDate(d.getDate() + index);
    return d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' });
  }

  /** Search near the day's places, else near any place in the plan. */
  biasFor = (): LatLngBias => {
    const plan = this.plan();
    const day = this.sheet()?.day ?? 0;
    const place = plan?.days[day]?.stops.find((s) => s.place)?.place ?? plan?.days.flatMap((d) => d.stops).find((s) => s.place)?.place;
    return place ? { lat: place.lat, lng: place.lng } : null;
  };

  // ---- editing -------------------------------------------------------------------------------

  openAdd(day: number): void {
    this.store.whenIdentified(() => this.sheet.set({ day, stop: null }));
  }

  openStop(day: number, stop: PlanStop): void {
    this.store.whenIdentified(() => this.sheet.set({ day, stop }));
  }

  saveStop(fields: StopFields): void {
    const target = this.sheet();
    if (!target) return;
    this.sheet.set(null);
    void this.store.edit((doc) =>
      target.stop ? updateStop(doc, target.day, target.stop.id, fields) : addStop(doc, target.day, newStop(fields)),
    );
  }

  removeOpenStop(): void {
    const target = this.sheet();
    if (!target?.stop) return;
    this.sheet.set(null);
    void this.store.removeWithUndo((doc) => removeStop(doc, target.day, target.stop!.id), COPY.removed(target.stop.title));
  }

  nudge(day: number, index: number, direction: -1 | 1): void {
    void this.store.edit((doc) => nudgeStop(doc, day, index, direction));
  }

  dropped(event: CdkDragDrop<number>): void {
    const fromDay = event.previousContainer.data;
    const toDay = event.container.data;
    if (fromDay === toDay && event.previousIndex === event.currentIndex) return;
    void this.store.edit((doc) => moveStopToDay(doc, fromDay, event.previousIndex, toDay, event.currentIndex));
  }

  addDay(): void {
    void this.store.edit(addDay);
  }

  removeDay(day: number): void {
    void this.store.removeWithUndo((doc) => removeDay(doc, day), COPY.removed(COPY.day(day + 1)));
  }

  /** Phone tabs: each section starts at its top. */
  selectTab(tab: Tab): void {
    this.tab.set(tab);
    this.document.querySelector('.tp-root.page')?.scrollTo({ top: 0 });
  }

  jumpTo(day: number): void {
    this.document.getElementById(`tp-day-${day}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ---- identity and sending ----------------------------------------------------------------

  async joinWithName(name: string): Promise<void> {
    await this.identify(() => this.store.joinWithName(name));
  }

  async joinWithGoogle(credential: string): Promise<void> {
    await this.identify(() => this.store.joinWithGoogle(credential));
  }

  private async identify(join: () => Promise<unknown>): Promise<void> {
    this.busy.set(true);
    this.whoError.set(null);
    try {
      await join();
    } catch (err) {
      this.whoError.set(apiErrorMessage(err, COPY.googleFailed));
    } finally {
      this.busy.set(false);
    }
  }

  async upgrade(credential: string): Promise<void> {
    try {
      await this.store.upgradeToGoogle(credential);
    } catch (err) {
      this.store.toast.set({ message: apiErrorMessage(err, COPY.googleFailed), undo: false });
    }
  }

  async send(message: string | null): Promise<void> {
    this.busy.set(true);
    const ok = await this.store.send(message);
    this.busy.set(false);
    this.store.toast.set({ message: ok ? COPY.sent(this.store.ownerName()) : COPY.saveError, undo: false });
  }

  async startOver(): Promise<void> {
    if (!confirm(COPY.me.startOverConfirm)) return;
    this.meOpen.set(false);
    await this.store.startOver();
  }

  forget(): void {
    if (!confirm(COPY.me.forgetConfirm)) return;
    this.meOpen.set(false);
    this.store.forgetMe();
  }

  finishFirstRun(): void {
    plannerStorage.setFirstRunDone();
    this.firstRun.set(false);
  }

  retry(): void {
    void this.store.load(this.store.code());
  }
}
