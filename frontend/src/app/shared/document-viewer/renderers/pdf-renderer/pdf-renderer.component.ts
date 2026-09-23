import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
  signal,
} from '@angular/core';
import type { PDFDocumentProxy, PDFPageProxy, PageViewport, RenderTask, TextLayer } from 'pdfjs-dist';

// Physical canvas-pixel ceiling shared by the DPR upscaling below — keeps a maxed-out
// zoom on a 3x-DPR display from asking the GPU for a canvas larger than mobile/older
// hardware can allocate. ~4096x4096, the safe floor across browsers.
const MAX_CANVAS_PIXELS = 16_777_216;
const MAX_CANVAS_DIM = 8192;

// Breathing room (px) kept between the fitted page and the viewer's edges.
const FIT_PADDING = 16;

@Component({
  selector: 'app-pdf-renderer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="pdf-renderer" #container>
      @if (loading()) {
        <p class="state-text">Loading PDF…</p>
      } @else if (error()) {
        <p class="state-text error">{{ error() }}</p>
      }
      <div class="page" [hidden]="loading() || !!error()">
        <canvas #canvas></canvas>
        <div class="textLayer" #textLayer></div>
      </div>
    </div>
  `,
  styles: [
    `
      .pdf-renderer {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        overflow: auto;
      }
      .state-text {
        color: var(--text-muted, #666);
        font-size: 0.875rem;
      }
      .state-text.error {
        color: var(--danger, #c0392b);
      }
      .page {
        position: relative;
        flex: none;
      }
      canvas {
        display: block;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
      }
      /* Selectable/searchable text overlay, positioned over the canvas by pdf.js's
         TextLayer. Rules trimmed from pdfjs-dist/web/pdf_viewer.css (just the
         .textLayer subset) rather than importing that whole viewer-chrome
         stylesheet, to stay consistent with the app's own theme. */
      .textLayer {
        --min-font-size: 1;
        --text-scale-factor: calc(var(--total-scale-factor) * var(--min-font-size));
        --min-font-size-inv: calc(1 / var(--min-font-size));
        position: absolute;
        inset: 0;
        text-align: initial;
        overflow: clip;
        opacity: 1;
        line-height: 1;
        text-size-adjust: none;
        forced-color-adjust: none;
        transform-origin: 0 0;
        caret-color: CanvasText;
        z-index: 0;
      }
      .textLayer :is(span, br) {
        color: transparent;
        position: absolute;
        white-space: pre;
        cursor: text;
        transform-origin: 0% 0%;
      }
      .textLayer > :not(.markedContent) {
        z-index: 1;
        --font-height: 0;
        font-size: calc(var(--text-scale-factor) * var(--font-height));
        --scale-x: 1;
        --rotate: 0deg;
        transform: rotate(var(--rotate)) scaleX(var(--scale-x)) scale(var(--min-font-size-inv));
      }
      .textLayer .markedContent {
        display: contents;
      }
      .textLayer span[role='img'] {
        user-select: none;
        cursor: default;
      }
      .textLayer ::selection {
        background: color-mix(in srgb, AccentColor, transparent 75%);
      }
      .textLayer .endOfContent {
        display: block;
        position: absolute;
        inset: 100% 0 0;
        z-index: 0;
        cursor: default;
        user-select: none;
      }
    `,
  ],
})
export class PdfRendererComponent implements OnChanges, OnDestroy {
  @Input({ required: true }) src!: string;
  @Input() zoom = 1;
  @Input() rotation = 0;
  @Input() pageIndex = 1;

  @Output() pageCountChange = new EventEmitter<number>();
  @Output() loadError = new EventEmitter<string>();

  @ViewChild('container', { static: true }) containerRef!: ElementRef<HTMLDivElement>;
  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('textLayer', { static: true }) textLayerRef!: ElementRef<HTMLDivElement>;

  loading = signal(true);
  error = signal<string | null>(null);

  private pdfjsModule: typeof import('pdfjs-dist') | null = null;
  private pdfDoc: PDFDocumentProxy | null = null;
  private renderTask: RenderTask | null = null;
  private textLayerTask: TextLayer | null = null;
  private resizeObserver: ResizeObserver | null = null;
  private resizeDebounce: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  /** Scale that fits the current page inside the viewer; `zoom` multiplies on top of it. */
  private fitScale = 1;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['src']) {
      this.setupResizeObserver();
      void this.loadDocument();
    } else if (this.pdfDoc && (changes['pageIndex'] || changes['rotation'])) {
      void this.renderPage(true);
    } else if (this.pdfDoc && changes['zoom']) {
      void this.renderPage(false);
    }
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.resizeObserver?.disconnect();
    if (this.resizeDebounce !== null) clearTimeout(this.resizeDebounce);
    this.renderTask?.cancel();
    this.textLayerTask?.cancel();
    void this.pdfDoc?.destroy();
  }

  private setupResizeObserver(): void {
    this.resizeObserver?.disconnect();
    this.resizeObserver = new ResizeObserver(() => {
      if (this.resizeDebounce !== null) clearTimeout(this.resizeDebounce);
      // Debounced: a modal resize/maximize/orientation-change fires many resize
      // events in quick succession — only the settled size should trigger a re-fit.
      this.resizeDebounce = setTimeout(() => {
        if (!this.destroyed && this.pdfDoc) void this.renderPage(true);
      }, 120);
    });
    this.resizeObserver.observe(this.containerRef.nativeElement);
  }

  private async ensurePdfjs(): Promise<typeof import('pdfjs-dist')> {
    if (!this.pdfjsModule) {
      const pdfjs = await import('pdfjs-dist');
      // Served as a static asset (see angular.json "assets") — a `new URL(pkg-path,
      // import.meta.url)` pattern only gets rewritten by the Angular/esbuild builder
      // for worker files inside this project's own src tree, not for paths reaching
      // into node_modules, so that form silently 404s here.
      pdfjs.GlobalWorkerOptions.workerSrc = '/pdfjs/pdf.worker.min.mjs';
      this.pdfjsModule = pdfjs;
    }
    return this.pdfjsModule;
  }

  private async loadDocument(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const pdfjs = await this.ensurePdfjs();

      void this.pdfDoc?.destroy();
      const loadingTask = pdfjs.getDocument(this.src);
      const doc = await loadingTask.promise;
      if (this.destroyed) {
        void doc.destroy();
        return;
      }
      this.pdfDoc = doc;
      this.pageCountChange.emit(doc.numPages);
      this.loading.set(false);
      await this.renderPage(true);
    } catch (err) {
      if (this.destroyed) return;
      console.error('[PdfRenderer] failed to load PDF', err);
      const message = 'Could not load this PDF.';
      this.error.set(message);
      this.loading.set(false);
      this.loadError.emit(message);
    }
  }

  /**
   * @param recomputeFit Recompute the fit-to-viewer baseline scale first — needed
   *   whenever the page, rotation, or viewer size changed, but not on a plain zoom
   *   step (which multiplies on top of the existing baseline).
   */
  private async renderPage(recomputeFit: boolean): Promise<void> {
    if (!this.pdfDoc) return;
    const pdfjs = await this.ensurePdfjs();
    const pageNumber = Math.min(Math.max(1, this.pageIndex), this.pdfDoc.numPages);
    const page = await this.pdfDoc.getPage(pageNumber);
    if (this.destroyed) return;

    if (recomputeFit) {
      this.fitScale = this.computeFitScale(page);
    }
    const viewport = page.getViewport({ scale: this.fitScale * this.zoom, rotation: this.rotation });

    const canvas = this.canvasRef.nativeElement;
    const outputScale = new pdfjs.OutputScale();
    outputScale.limitCanvas(viewport.width, viewport.height, MAX_CANVAS_PIXELS, MAX_CANVAS_DIM);
    canvas.width = Math.floor(viewport.width * outputScale.sx);
    canvas.height = Math.floor(viewport.height * outputScale.sy);
    canvas.style.width = `${Math.floor(viewport.width)}px`;
    canvas.style.height = `${Math.floor(viewport.height)}px`;

    this.renderTask?.cancel();
    this.renderTask = page.render({
      canvas,
      viewport,
      transform: outputScale.scaled ? [outputScale.sx, 0, 0, outputScale.sy, 0, 0] : undefined,
    });
    const rendered = this.renderTask.promise.catch(() => {
      // Superseded by a newer render (page/zoom/resize changed mid-render) — ignore.
    });

    void this.renderTextLayer(pdfjs, page, viewport);
    await rendered;
  }

  /** Selectable/searchable text, positioned to line up with the canvas above it. */
  private async renderTextLayer(
    pdfjs: typeof import('pdfjs-dist'),
    page: PDFPageProxy,
    viewport: PageViewport,
  ): Promise<void> {
    this.textLayerTask?.cancel();
    const container = this.textLayerRef.nativeElement;
    container.replaceChildren();
    // Our viewport is already the final CSS-pixel size (fit * zoom baked in), so the
    // text layer needs no further scaling of its own — see pdf.js's --scale-factor.
    container.style.setProperty('--total-scale-factor', '1');

    const layer = new pdfjs.TextLayer({
      textContentSource: page.streamTextContent(),
      container,
      viewport,
    });
    this.textLayerTask = layer;
    try {
      await layer.render();
    } catch {
      // Cancelled by a newer render — ignore.
    }
  }

  private computeFitScale(page: PDFPageProxy): number {
    const container = this.containerRef.nativeElement;
    const availableWidth = container.clientWidth - FIT_PADDING * 2;
    const availableHeight = container.clientHeight - FIT_PADDING * 2;
    if (availableWidth <= 0 || availableHeight <= 0) return 1;

    const unscaled = page.getViewport({ scale: 1, rotation: this.rotation });
    return Math.min(availableWidth / unscaled.width, availableHeight / unscaled.height);
  }
}
