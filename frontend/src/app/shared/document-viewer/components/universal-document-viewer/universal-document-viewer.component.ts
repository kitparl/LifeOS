import { DecimalPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DocumentViewerService } from '../../document-viewer.service';
import { DocumentViewerConfig, PreviewInfo, PreviewType } from '../../models/document-preview.model';
import { ImageRendererComponent } from '../../renderers/image-renderer/image-renderer.component';
import { MediaRendererComponent } from '../../renderers/media-renderer/media-renderer.component';
import { PdfRendererComponent } from '../../renderers/pdf-renderer/pdf-renderer.component';
import { TextRendererComponent } from '../../renderers/text-renderer/text-renderer.component';
import { DocumentPreviewApiService } from '../../services/document-preview-api.service';

const INITIAL_POLL_DELAY_MS = 1000;
const MAX_POLL_DELAY_MS = 8000;
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 4;

type ViewerState = 'loading' | 'processing' | 'ready' | 'failed' | 'unsupported';

@Component({
  selector: 'app-universal-document-viewer',
  standalone: true,
  imports: [ImageRendererComponent, PdfRendererComponent, TextRendererComponent, MediaRendererComponent, DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="viewer" [attr.aria-busy]="state() === 'loading' || state() === 'processing'">
      @switch (state()) {
        @case ('loading') {
          <div class="viewer-state">
            <p>Loading…</p>
          </div>
        }
        @case ('processing') {
          <div class="viewer-state">
            <p>Preparing preview…</p>
            <p class="viewer-state__hint">Converting this document — this can take a few seconds.</p>
          </div>
        }
        @case ('failed') {
          <div class="viewer-state">
            <p class="viewer-state__error">{{ errorMessage() }}</p>
            <button type="button" class="btn-secondary text-xs" (click)="retry()">Retry</button>
          </div>
        }
        @case ('unsupported') {
          <div class="viewer-state">
            <p>Preview not available for this file type.</p>
            <button type="button" class="btn-secondary text-xs" (click)="download()">Download</button>
          </div>
        }
        @case ('ready') {
          @if (previewType() === 'pdf' && previewUrl()) {
            <app-pdf-renderer
              [src]="previewUrl()!"
              [zoom]="zoom()"
              [rotation]="rotation()"
              [pageIndex]="pageIndex()"
              (pageCountChange)="pageCount.set($event)"
              (loadError)="onRendererError($event)"
            />
          } @else if (previewType() === 'image' && previewUrl()) {
            <app-image-renderer [src]="previewUrl()!" [alt]="fileName()" [zoom]="zoom()" [rotation]="rotation()" />
          } @else if ((previewType() === 'video' || previewType() === 'audio') && previewUrl()) {
            <app-media-renderer [src]="previewUrl()!" [kind]="previewType() === 'video' ? 'video' : 'audio'" />
          } @else if (textPreviewType()) {
            @if (textPreviewType(); as tpt) {
              <app-text-renderer [documentId]="config.documentId" [previewType]="tpt" />
            }
          }
        }
      }
    </div>

    @if (state() === 'ready' && (previewType() === 'pdf' || previewType() === 'image')) {
      <div class="viewer-toolbar" role="toolbar" aria-label="Preview controls">
        <button type="button" class="viewer-toolbar__btn" title="Zoom out" aria-label="Zoom out" (click)="zoomOut()">
          −
        </button>
        <span class="viewer-toolbar__zoom">{{ zoom() * 100 | number: '1.0-0' }}%</span>
        <button type="button" class="viewer-toolbar__btn" title="Zoom in" aria-label="Zoom in" (click)="zoomIn()">
          +
        </button>
        <button type="button" class="viewer-toolbar__btn" title="Rotate" aria-label="Rotate" (click)="rotate()">
          ⟳
        </button>
        @if (previewType() === 'pdf' && pageCount(); as count) {
          @if (count > 1) {
            <span class="viewer-toolbar__sep"></span>
            <button
              type="button"
              class="viewer-toolbar__btn"
              title="Previous page"
              aria-label="Previous page"
              [disabled]="pageIndex() <= 1"
              (click)="prevPage()"
            >
              ‹
            </button>
            <span class="viewer-toolbar__page">Page {{ pageIndex() }} of {{ count }}</span>
            <button
              type="button"
              class="viewer-toolbar__btn"
              title="Next page"
              aria-label="Next page"
              [disabled]="pageIndex() >= count"
              (click)="nextPage()"
            >
              ›
            </button>
          }
        }
      </div>
    }
  `,
  styles: [
    `
      :host {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 260px;
      }
      .viewer {
        flex: 1;
        min-height: 0;
        overflow: hidden;
        display: flex;
      }
      .viewer-state {
        margin: auto;
        text-align: center;
        color: var(--text-muted, #666);
        font-size: 0.875rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        align-items: center;
      }
      .viewer-state__hint {
        font-size: 0.75rem;
      }
      .viewer-state__error {
        color: var(--danger, #c0392b);
      }
      .viewer-toolbar {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.4rem 0.5rem;
        border-top: 1px solid var(--xp-border, #ccc);
        font-size: 0.8rem;
      }
      .viewer-toolbar__btn {
        border: 1px solid var(--xp-border, #ccc);
        background: var(--surface, #fff);
        border-radius: 4px;
        width: 1.75rem;
        height: 1.75rem;
        line-height: 1;
        cursor: pointer;
      }
      .viewer-toolbar__btn:disabled {
        opacity: 0.4;
        cursor: default;
      }
      .viewer-toolbar__zoom,
      .viewer-toolbar__page {
        min-width: 3.5rem;
        text-align: center;
        color: var(--text-muted, #666);
      }
      .viewer-toolbar__sep {
        width: 1px;
        height: 1.25rem;
        background: var(--xp-border, #ccc);
        margin: 0 0.25rem;
      }
    `,
  ],
})
export class UniversalDocumentViewerComponent implements OnChanges, OnDestroy {
  @Input({ required: true }) config!: DocumentViewerConfig;

  private readonly api = inject(DocumentPreviewApiService);
  private readonly viewerService = inject(DocumentViewerService);
  private readonly destroyRef = inject(DestroyRef);

  readonly state = signal<ViewerState>('loading');
  readonly previewType = signal<PreviewType | null>(null);
  readonly previewUrl = signal<string | null>(null);
  readonly errorMessage = signal<string | null>(null);
  readonly fileName = signal('');

  readonly zoom = signal(1);
  readonly rotation = signal(0);
  readonly pageIndex = signal(1);
  readonly pageCount = signal<number | null>(null);

  readonly textPreviewType = computed<'text' | 'csv' | 'markdown' | null>(() => {
    const t = this.previewType();
    return t === 'text' || t === 'csv' || t === 'markdown' ? t : null;
  });

  private pollDelay = INITIAL_POLL_DELAY_MS;
  private pollTimeoutId: ReturnType<typeof setTimeout> | null = null;
  private currentDocumentId: string | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['config']) {
      this.fileName.set(this.config.fileName ?? '');
      this.resetViewState();
      this.currentDocumentId = this.config.documentId;
      this.load();
    }
  }

  ngOnDestroy(): void {
    this.clearPoll();
  }

  @HostListener('keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (this.state() !== 'ready') return;
    if (event.key === '+' || event.key === '=') {
      this.zoomIn();
      event.preventDefault();
    } else if (event.key === '-') {
      this.zoomOut();
      event.preventDefault();
    } else if (event.key === 'ArrowLeft' && this.previewType() === 'pdf') {
      this.prevPage();
    } else if (event.key === 'ArrowRight' && this.previewType() === 'pdf') {
      this.nextPage();
    }
  }

  private resetViewState(): void {
    this.clearPoll();
    this.pollDelay = INITIAL_POLL_DELAY_MS;
    this.state.set('loading');
    this.previewType.set(null);
    this.previewUrl.set(null);
    this.errorMessage.set(null);
    this.zoom.set(1);
    this.rotation.set(0);
    this.pageIndex.set(1);
    this.pageCount.set(null);
    this.viewerService.setInfo(null);
  }

  retry(): void {
    this.pollDelay = INITIAL_POLL_DELAY_MS;
    this.state.set('loading');
    this.load(true);
  }

  private load(retry = false): void {
    const documentId = this.config.documentId;
    this.api
      .getPreviewInfo(documentId, { retry })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (info) => this.onInfo(documentId, info),
        error: () => this.onLoadFailure(documentId, 'Could not load this file.'),
      });
  }

  private onInfo(documentId: string, info: PreviewInfo): void {
    if (documentId !== this.currentDocumentId) return; // Stale response from a previous document.
    this.viewerService.setInfo(info);
    this.fileName.set(info.file_name);
    this.previewType.set(info.preview_type);

    if (info.status === 'processing') {
      this.state.set('processing');
      this.schedulePoll();
      return;
    }
    if (info.status === 'failed') {
      this.onLoadFailure(documentId, info.error ?? 'Preview failed.');
      return;
    }
    if (info.preview_type === 'unsupported') {
      this.state.set('unsupported');
      return;
    }
    this.resolveRenderable(documentId, info);
  }

  private resolveRenderable(documentId: string, info: PreviewInfo): void {
    if (info.preview_type === 'text' || info.preview_type === 'csv' || info.preview_type === 'markdown') {
      this.state.set('ready');
      return;
    }
    this.api
      .previewUrl(documentId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (url) => {
          if (documentId !== this.currentDocumentId) return;
          this.previewUrl.set(url);
          this.state.set('ready');
        },
        error: () => this.onLoadFailure(documentId, 'Could not load this preview.'),
      });
  }

  private schedulePoll(): void {
    this.clearPoll();
    const documentId = this.currentDocumentId;
    this.pollTimeoutId = setTimeout(() => {
      if (documentId !== this.currentDocumentId) return;
      this.pollDelay = Math.min(this.pollDelay * 2, MAX_POLL_DELAY_MS);
      this.load();
    }, this.pollDelay);
  }

  private clearPoll(): void {
    if (this.pollTimeoutId !== null) {
      clearTimeout(this.pollTimeoutId);
      this.pollTimeoutId = null;
    }
  }

  private onLoadFailure(documentId: string, message: string): void {
    if (documentId !== this.currentDocumentId) return;
    this.state.set('failed');
    this.errorMessage.set(message);
  }

  onRendererError(message: string): void {
    this.state.set('failed');
    this.errorMessage.set(message);
  }

  download(): void {
    this.api.downloadUrl(this.config.documentId).subscribe((url) => {
      window.open(url, '_blank', 'noopener');
    });
  }

  zoomIn(): void {
    this.zoom.update((z) => Math.min(MAX_ZOOM, Math.round((z + 0.25) * 100) / 100));
  }

  zoomOut(): void {
    this.zoom.update((z) => Math.max(MIN_ZOOM, Math.round((z - 0.25) * 100) / 100));
  }

  rotate(): void {
    this.rotation.update((r) => (r + 90) % 360);
  }

  prevPage(): void {
    this.pageIndex.update((p) => Math.max(1, p - 1));
  }

  nextPage(): void {
    const count = this.pageCount();
    this.pageIndex.update((p) => (count ? Math.min(count, p + 1) : p + 1));
  }
}
