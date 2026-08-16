import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { MarkdownService } from '../../shared/markdown/markdown.service';
import { WritingPractice } from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-writing-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (item; as w) {
      <div class="space-y-3" style="max-width: 760px">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold" style="color: var(--text)">{{ w.title }}</h1>
            <p class="text-xs capitalize" style="color: var(--text-muted)">{{ w.category.replace('_', ' ') }}</p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/communication/writing', w.id, 'edit']" class="btn-secondary text-xs no-underline">Edit</a>
            <button type="button" class="btn-danger text-xs" (click)="remove()">Delete</button>
          </div>
        </div>

        <div class="panel">
          @if (!w.content) {
            <p class="text-sm" style="color: var(--text-muted); font-style: italic">No content.</p>
          } @else {
            <div class="prose-content" [innerHTML]="safeMarkdown(w.content)"></div>
          }
        </div>

        <a routerLink="/communication" class="link text-sm">← Back to Communication</a>
      </div>
    } @else if (loading) {
      <div class="empty-state">
        <div class="skeleton" style="width: 200px; height: 16px"></div>
      </div>
    } @else {
      <p class="text-sm" style="color: var(--danger)">Writing not found.</p>
    }
  `,
})
export class WritingDetailComponent implements OnInit {
  private readonly communication = inject(CommunicationService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  private readonly markdown = inject(MarkdownService);
  private readonly sanitizer = inject(DomSanitizer);

  item: WritingPractice | null = null;
  loading = false;

  safeMarkdown(markdown: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(this.markdown.render(markdown));
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loading = true;
      this.communication.getWriting(id).subscribe({
        next: (w) => {
          this.item = w;
          this.loading = false;
        },
        error: () => {
          this.item = null;
          this.loading = false;
        },
      });
    }
  }

  remove(): void {
    if (!this.item || !confirm('Delete this writing?')) return;
    this.communication.deleteWriting(this.item.id).subscribe({
      next: () => this.router.navigate(['/communication']),
    });
  }
}
