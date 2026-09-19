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
} from '@angular/core';
import type { PDFDocumentProxy, RenderTask } from 'pdfjs-dist';

@Component({
  selector: 'app-pdf-renderer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="pdf-renderer">
      @if (loading) {
        <p class="state-text">Loading PDF…</p>
      } @else if (error) {
        <p class="state-text error">{{ error }}</p>
      }
      <canvas #canvas [hidden]="loading || !!error"></canvas>
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
      canvas {
        max-width: 100%;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
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

  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;

  loading = true;
  error: string | null = null;

  private pdfDoc: PDFDocumentProxy | null = null;
  private renderTask: RenderTask | null = null;
  private destroyed = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['src']) {
      void this.loadDocument();
    } else if (this.pdfDoc && (changes['pageIndex'] || changes['zoom'] || changes['rotation'])) {
      void this.renderPage();
    }
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.renderTask?.cancel();
    void this.pdfDoc?.destroy();
  }

  private async loadDocument(): Promise<void> {
    this.loading = true;
    this.error = null;
    try {
      const pdfjs = await import('pdfjs-dist');
      pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        'pdfjs-dist/build/pdf.worker.min.mjs',
        import.meta.url,
      ).toString();

      void this.pdfDoc?.destroy();
      const loadingTask = pdfjs.getDocument(this.src);
      const doc = await loadingTask.promise;
      if (this.destroyed) {
        void doc.destroy();
        return;
      }
      this.pdfDoc = doc;
      this.pageCountChange.emit(doc.numPages);
      this.loading = false;
      await this.renderPage();
    } catch {
      if (this.destroyed) return;
      this.error = 'Could not load this PDF.';
      this.loading = false;
      this.loadError.emit(this.error);
    }
  }

  private async renderPage(): Promise<void> {
    if (!this.pdfDoc) return;
    const pageNumber = Math.min(Math.max(1, this.pageIndex), this.pdfDoc.numPages);
    const page = await this.pdfDoc.getPage(pageNumber);
    if (this.destroyed) return;

    const viewport = page.getViewport({ scale: this.zoom, rotation: this.rotation });
    const canvas = this.canvasRef.nativeElement;
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    this.renderTask?.cancel();
    this.renderTask = page.render({ canvas, viewport });
    try {
      await this.renderTask.promise;
    } catch {
      // Superseded by a newer render (page/zoom changed mid-render) — ignore.
    }
  }
}
