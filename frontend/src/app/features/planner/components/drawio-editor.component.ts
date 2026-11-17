import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  effect,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ThemeService } from '../../../core/services/theme.service';
import { DRAWIO_VERSION } from '../drawio-version';
import { SaveStatus } from '../models/planner.models';
import { PlannerApiService } from '../services/planner-api.service';

const AUTOSAVE_DEBOUNCE_MS = 1500;

type ResolvedTheme = 'light' | 'dark';

interface DrawioMessage {
  event: string;
  xml?: string;
}

/**
 * Embeds the self-hosted draw.io editor (same-origin iframe, JSON embed protocol) and
 * auto-saves its xml. At most one save is in flight; edits made meanwhile become the next save.
 * The node is fixed for the component's lifetime (the host renders one editor per diagram).
 */
@Component({
  selector: 'app-drawio-editor',
  standalone: true,
  host: { class: 'relative block h-full w-full' },
  template: `
    <iframe #frame class="block h-full w-full border-0" [src]="src()" title="Diagram editor"></iframe>
    @let current = status();
    @if (current === 'dirty' || current === 'saving') {
      <span class="chip absolute bottom-3 right-3" style="color: var(--text-faint)">Saving…</span>
    } @else if (current === 'saved') {
      <span class="chip absolute bottom-3 right-3" style="color: var(--text-faint)">Saved</span>
    } @else if (current === 'error') {
      <span class="chip absolute bottom-3 right-3" role="alert" style="color: var(--danger)">
        Couldn't save —
        <button type="button" class="btn-ghost" style="min-height: 0; padding: 0 0.25rem" (click)="retry()">
          Retry
        </button>
      </span>
    } @else if (current === 'conflict') {
      <span class="chip absolute bottom-3 right-3" role="alert" style="color: var(--warning)">
        This diagram changed elsewhere.
        <button type="button" class="btn-ghost" style="min-height: 0; padding: 0 0.25rem" (click)="reloadFromServer()">
          Reload
        </button>
        <button type="button" class="btn-ghost" style="min-height: 0; padding: 0 0.25rem" (click)="overwrite()">
          Keep mine
        </button>
      </span>
    }
  `,
})
export class DrawioEditorComponent implements OnDestroy {
  private readonly api = inject(PlannerApiService);
  private readonly themeService = inject(ThemeService);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly frame = viewChild.required<ElementRef<HTMLIFrameElement>>('frame');

  readonly nodeId = input.required<string>();
  readonly statusChange = output<SaveStatus>();

  private readonly statusState = signal<SaveStatus>('idle');
  readonly status = this.statusState.asReadonly();

  private srcTheme: ResolvedTheme = this.themeService.resolved();
  protected readonly src = signal<SafeResourceUrl>(this.buildSrc(this.srcTheme));

  /** Latest xml not yet sent to the server (also kept after a failed save). */
  private pendingXml: string | null = null;
  private revision = 0;
  private inFlight = false;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private flushWaiters: (() => void)[] = [];
  private destroyed = false;

  constructor() {
    // Reloading the iframe drops editor state, so a theme switch waits until nothing is unsaved.
    effect(() => {
      const theme = this.themeService.resolved();
      const status = this.status();
      if (theme !== this.srcTheme && (status === 'idle' || status === 'saved')) {
        this.srcTheme = theme;
        this.src.set(this.buildSrc(theme));
      }
    });
  }

  @HostListener('window:message', ['$event'])
  onMessage(event: MessageEvent): void {
    if (event.source !== this.frame().nativeElement.contentWindow || event.origin !== location.origin) {
      return;
    }
    const message = parseDrawioMessage(event.data);
    if (message?.event === 'init') {
      this.loadFromServer();
    } else if ((message?.event === 'autosave' || message?.event === 'save') && typeof message.xml === 'string') {
      this.onChange(message.xml);
    }
  }

  /** Saves immediately if there are unsaved changes; resolves once saving settles. */
  flush(): Promise<void> {
    if (this.status() === 'dirty') {
      this.saveNow();
    }
    if (!this.isBusy()) {
      return Promise.resolve();
    }
    return new Promise((resolve) => this.flushWaiters.push(resolve));
  }

  retry(): void {
    if (this.pendingXml === null) {
      this.loadFromServer();
    } else {
      this.saveNow();
    }
  }

  /** Conflict resolution: discard local changes and show the server's version. */
  reloadFromServer(): void {
    this.clearDebounce();
    this.pendingXml = null;
    this.loadFromServer();
  }

  /** Conflict resolution: save the local xml on top of the server's current revision. */
  overwrite(): void {
    this.clearDebounce();
    this.inFlight = true;
    this.setStatus('saving');
    this.api.getContent(this.nodeId()).subscribe({
      next: ({ revision }) => {
        this.inFlight = false;
        this.revision = revision;
        this.saveNow();
      },
      error: () => {
        this.inFlight = false;
        this.setStatus('error');
      },
    });
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    // Don't lose edits made within the debounce window when the editor is closed.
    if (this.debounceTimer !== null) {
      this.saveNow();
    }
  }

  private onChange(xml: string): void {
    this.pendingXml = xml;
    if (this.status() === 'conflict') {
      return; // keep the latest xml for "Keep mine"; saving would only conflict again
    }
    this.setStatus('dirty');
    this.clearDebounce();
    this.debounceTimer = setTimeout(() => {
      this.debounceTimer = null;
      this.saveNow();
    }, AUTOSAVE_DEBOUNCE_MS);
  }

  private saveNow(): void {
    this.clearDebounce();
    if (this.inFlight || this.pendingXml === null) {
      return; // an in-flight request picks up pendingXml when it completes
    }
    const xml = this.pendingXml;
    this.pendingXml = null;
    this.inFlight = true;
    this.setStatus('saving');
    this.api.saveContent(this.nodeId(), { content: xml, base_revision: this.revision }).subscribe({
      next: ({ revision }) => {
        this.inFlight = false;
        this.revision = revision;
        if (this.pendingXml === null) {
          this.setStatus('saved');
        } else if (this.debounceTimer === null) {
          this.saveNow();
        }
      },
      error: (err: unknown) => {
        this.inFlight = false;
        this.pendingXml ??= xml;
        this.clearDebounce();
        this.setStatus(err instanceof HttpErrorResponse && err.status === 409 ? 'conflict' : 'error');
      },
    });
  }

  private loadFromServer(): void {
    this.api.getContent(this.nodeId()).subscribe({
      next: ({ content, revision }) => {
        this.revision = revision;
        this.postToDrawio({ action: 'load', xml: content, autosave: 1 });
        this.setStatus('idle');
      },
      error: () => this.setStatus('error'),
    });
  }

  private postToDrawio(message: object): void {
    this.frame().nativeElement.contentWindow?.postMessage(JSON.stringify(message), location.origin);
  }

  private setStatus(status: SaveStatus): void {
    this.statusState.set(status);
    if (!this.destroyed) {
      this.statusChange.emit(status);
    }
    if (!this.isBusy()) {
      this.flushWaiters.forEach((resolve) => resolve());
      this.flushWaiters = [];
    }
  }

  private isBusy(): boolean {
    const status = this.status();
    return status === 'dirty' || status === 'saving';
  }

  private clearDebounce(): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
  }

  private buildSrc(theme: ResolvedTheme): SafeResourceUrl {
    // Flags verified against draw.io 32.6.10 (js/diagramly/Init.js, EditorUi.js). `ui=dark` is a
    // legacy theme that Init.js redirects to `dark=1`; keeping `ui=min` and setting `dark`
    // explicitly gives the same layout in both themes.
    const params = [
      'embed=1',
      'proto=json',
      'spin=1',
      'ui=min',
      `dark=${theme === 'dark' ? 1 : 0}`,
      'noSaveBtn=1',
      'noExitBtn=1',
      'saveAndExit=0',
      'libraries=1',
      'offline=1',
      'stealth=1',
      'pwa=0',
      'plugins=0',
    ].join('&');
    return this.sanitizer.bypassSecurityTrustResourceUrl(`/drawio/${DRAWIO_VERSION}/index.html?${params}`);
  }
}

function parseDrawioMessage(data: unknown): DrawioMessage | null {
  if (typeof data !== 'string') {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(data);
    return typeof parsed === 'object' && parsed !== null && typeof (parsed as DrawioMessage).event === 'string'
      ? (parsed as DrawioMessage)
      : null;
  } catch {
    return null;
  }
}
