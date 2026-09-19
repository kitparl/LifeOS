import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import {
  SPEAKING_CATEGORIES,
  SpeakingPractice,
  WRITING_CATEGORIES,
  WritingPractice,
} from './models/communication.models';
import { CommunicationService } from './services/communication.service';
import { VocabularyHubComponent } from './vocabulary/vocabulary-hub.component';

@Component({
  selector: 'app-communication-hub',
  standalone: true,
  imports: [RouterLink, ListPaginatorComponent, VocabularyHubComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Communication</h1>
        <div class="flex gap-2">
          @if (tab() === 'writing') {
            <a routerLink="/communication/writing/new" class="btn-primary text-xs no-underline">New Writing</a>
          } @else if (tab() === 'speaking') {
            <a routerLink="/communication/speaking/new" class="btn-primary text-xs no-underline">New Practice</a>
          }
        </div>
      </div>

      <div class="tab-bar" role="tablist">
        @for (t of tabs; track t.id) {
          <button
            type="button"
            role="tab"
            class="tab-bar__btn"
            [class.active]="tab() === t.id"
            [attr.aria-selected]="tab() === t.id"
            (click)="setTab(t.id)"
          >
            {{ t.label }}
          </button>
        }
      </div>

      @if (tab() === 'vocabulary') {
        <app-vocabulary-hub />
      }

      @if (tab() === 'writing') {
        @if (writingTotal === 0) {
          <p class="text-sm" style="color: var(--text-muted)">No writing practice yet.</p>
        } @else {
          <ul class="divide-y divide-[var(--xp-border)] panel !p-0 text-sm">
            @for (w of writing; track w.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2 hover:bg-[var(--surface-2)]">
                <div>
                  <a [routerLink]="['/communication/writing', w.id]" class="link">{{ w.title }}</a>
                  <p class="text-xs capitalize" style="color: var(--text-muted)">{{ w.category }}</p>
                </div>
                <div class="flex items-center gap-2">
                  <a [routerLink]="['/communication/writing', w.id, 'edit']" class="text-xs underline">Edit</a>
                  <button type="button" class="text-xs underline" style="color: var(--danger)" (click)="removeWriting(w)">Delete</button>
                </div>
              </li>
            }
          </ul>
          <app-list-paginator
            [total]="writingTotal"
            [pageSize]="pageSize"
            [currentPage]="writingPage"
            (pageChange)="setWritingPage($event)"
          />
        }
      }

      @if (tab() === 'speaking') {
        @if (speakingTotal === 0) {
          <p class="text-sm" style="color: var(--text-muted)">No speaking practice yet.</p>
        } @else {
          <ul class="divide-y divide-[var(--xp-border)] panel !p-0 text-sm">
            @for (s of speaking; track s.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2 hover:bg-[var(--surface-2)]">
                <div>
                  <a [routerLink]="['/communication/speaking', s.id]" class="link">{{ s.title }}</a>
                  <p class="text-xs capitalize" style="color: var(--text-muted)">{{ s.category.replace('_', ' ') }}</p>
                </div>
                <a [routerLink]="['/communication/speaking', s.id, 'edit']" class="text-xs underline">Edit</a>
              </li>
            }
          </ul>
          <app-list-paginator
            [total]="speakingTotal"
            [pageSize]="pageSize"
            [currentPage]="speakingPage"
            (pageChange)="setSpeakingPage($event)"
          />
        }
      }
    </div>
  `,
})
export class CommunicationHubComponent implements OnInit {
  private readonly communication = inject(CommunicationService);
  private readonly confirm = inject(ConfirmService);

  writingCategories = WRITING_CATEGORIES;
  speakingCategories = SPEAKING_CATEGORIES;
  tab = signal<'vocabulary' | 'writing' | 'speaking'>('vocabulary');
  tabs = [
    { id: 'vocabulary' as const, label: 'Vocabulary' },
    { id: 'writing' as const, label: 'Writing' },
    { id: 'speaking' as const, label: 'Speaking' },
  ];

  writing: WritingPractice[] = [];
  speaking: SpeakingPractice[] = [];
  writingTotal = 0;
  speakingTotal = 0;
  writingPage = 1;
  speakingPage = 1;
  readonly pageSize = 25;

  ngOnInit(): void {
    this.loadWriting();
    this.loadSpeaking();
  }

  setTab(id: 'vocabulary' | 'writing' | 'speaking'): void {
    this.tab.set(id);
  }

  loadWriting(): void {
    const offset = (this.writingPage - 1) * this.pageSize;
    this.communication.listWriting({ limit: this.pageSize, offset }).subscribe({
      next: (result) => {
        this.writing = result.items;
        this.writingTotal = result.total;
        this.clampPage('writing');
      },
    });
  }

  loadSpeaking(): void {
    const offset = (this.speakingPage - 1) * this.pageSize;
    this.communication.listSpeaking({ limit: this.pageSize, offset }).subscribe({
      next: (result) => {
        this.speaking = result.items;
        this.speakingTotal = result.total;
        this.clampPage('speaking');
      },
    });
  }

  setWritingPage(page: number): void {
    this.writingPage = page;
    this.loadWriting();
  }

  setSpeakingPage(page: number): void {
    this.speakingPage = page;
    this.loadSpeaking();
  }

  private clampPage(which: 'writing' | 'speaking'): void {
    if (which === 'writing') {
      const totalPages = Math.max(1, Math.ceil(this.writingTotal / this.pageSize));
      if (this.writingPage > totalPages) {
        this.writingPage = totalPages;
        this.loadWriting();
      }
    } else {
      const totalPages = Math.max(1, Math.ceil(this.speakingTotal / this.pageSize));
      if (this.speakingPage > totalPages) {
        this.speakingPage = totalPages;
        this.loadSpeaking();
      }
    }
  }

  async removeWriting(item: WritingPractice): Promise<void> {
    const ok = await this.confirm.confirm(`Delete writing "${item.title}" permanently?`, 'Delete writing');
    if (!ok) return;
    this.communication.deleteWriting(item.id).subscribe({
      next: () => this.loadWriting(),
    });
  }
}
