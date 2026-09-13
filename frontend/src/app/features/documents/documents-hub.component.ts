import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { TabHubComponent } from '../../shared/tab-hub/tab-hub.component';
import { FilesPageComponent } from '../files/files-page.component';
import { OcrPageComponent } from '../ocr/ocr-page.component';

type DocumentsTab = 'library' | 'scan';

@Component({
  selector: 'app-documents-hub',
  standalone: true,
  imports: [TabHubComponent, FilesPageComponent, OcrPageComponent],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Documents</h1>

      <app-tab-hub [tabs]="tabs" [activeId]="tab()" (tabChange)="setTab($event)" />

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
  private readonly destroyRef = inject(DestroyRef);

  readonly tab = signal<DocumentsTab>('library');
  readonly tabs = [
    { id: 'library' as const, label: 'Library' },
    { id: 'scan' as const, label: 'Scan / OCR' },
  ];

  ngOnInit(): void {
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const t = params.get('tab');
      this.tab.set(t === 'scan' ? 'scan' : 'library');
    });
  }

  setTab(id: string): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id === 'library' ? null : id },
      queryParamsHandling: 'merge',
    });
  }
}
