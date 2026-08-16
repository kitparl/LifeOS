import { AfterViewInit, Directive, ElementRef, OnDestroy, inject } from '@angular/core';
import { FilesService } from '../../features/files/services/files.service';

const FILE_CONTENT_URL = /\/api\/v1\/files\/([0-9a-f-]{36})\/content/i;

/**
 * Rewrites private `/api/v1/files/{id}/content` img/src and a/href values to
 * short-lived token URLs so markdown previews can render uploaded files.
 */
@Directive({
  selector: '[appFileImageSrc]',
  standalone: true,
})
export class FileImageSrcDirective implements AfterViewInit, OnDestroy {
  private readonly el = inject(ElementRef<HTMLElement>);
  private readonly files = inject(FilesService);
  private observer?: MutationObserver;
  private readonly cache = new Map<string, string>();
  private rewriting = false;

  ngAfterViewInit(): void {
    this.rewrite();
    this.observer = new MutationObserver(() => this.rewrite());
    this.observer.observe(this.el.nativeElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['src', 'href'],
    });
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }

  private rewrite(): void {
    if (this.rewriting) return;
    this.rewriting = true;
    try {
      const root = this.el.nativeElement;
      const nodes = [
        ...Array.from(root.querySelectorAll('img[src]')),
        ...Array.from(root.querySelectorAll('a[href]')),
      ] as HTMLElement[];
      for (const node of nodes) {
        const attr = node.tagName === 'IMG' ? 'src' : 'href';
        const value = node.getAttribute(attr) || '';
        if (value.includes('token=')) continue;
        const match = value.match(FILE_CONTENT_URL);
        if (!match) continue;
        const id = match[1];
        const cached = this.cache.get(id);
        if (cached) {
          if (value !== cached) node.setAttribute(attr, cached);
          continue;
        }
        this.files.tokenUrl(id).subscribe({
          next: (url) => {
            this.cache.set(id, url);
            node.setAttribute(attr, url);
          },
        });
      }
    } finally {
      this.rewriting = false;
    }
  }
}
