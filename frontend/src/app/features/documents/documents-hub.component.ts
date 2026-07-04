import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FilesPageComponent } from '../files/files-page.component';
import { OcrPageComponent } from '../ocr/ocr-page.component';

type DocumentsTab = 'library' | 'scan';

@Component({
  selector: 'app-documents-hub',
  standalone: true,
  imports: [FilesPageComponent, OcrPageComponent],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Documents</h1>

      <div class="flex gap-1 border-b border-[var(--xp-border)] text-sm">
        @for (t of tabs; track t.id) {
          <button
            type="button"
            class="px-3 py-2"
            [class.bg-[var(--xp-blue)]="tab() === t.id"
            [class.text-white]="tab() === t.id"
            (click)="setTab(t.id)"
          >
            {{ t.label }}
          </button>
        }
      </div>

      @if (tab() === 'library') {
        <app-files-page />
      } @else {
        <app-ocr-page />
      }
    </div>
  `,
})
export class DocumentsHubComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly tab = signal<DocumentsTab>('library');
  readonly tabs = [
    { id: 'library' as const, label: 'Library' },
    { id: 'scan' as const, label: 'Scan / OCR' },
  ];

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      const t = params.get('tab');
      this.tab.set(t === 'scan' ? 'scan' : 'library');
    });
  }

  setTab(id: DocumentsTab): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id === 'library' ? null : id },
      queryParamsHandling: 'merge',
    });
  }
}
