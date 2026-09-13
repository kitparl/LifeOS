import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import {
  SPEAKING_CATEGORIES,
  SpeakingPractice,
  VocabularyWord,
  WRITING_CATEGORIES,
  WritingPractice,
} from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-communication-hub',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Communication</h1>
        <div class="flex gap-2">
          @if (tab() === 'vocabulary') {
            <a routerLink="/communication/vocabulary/new" class="btn-primary text-xs no-underline">Add Word</a>
          } @else if (tab() === 'writing') {
            <a routerLink="/communication/writing/new" class="btn-primary text-xs no-underline">New Writing</a>
          } @else {
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
        <form class="flex gap-2 text-sm" [formGroup]="vocabFilter" (ngSubmit)="searchVocabulary()">
          <input class="input-field !w-48" formControlName="search" placeholder="Search words…" />
          <button type="submit" class="btn-primary text-xs">Search</button>
        </form>
        @if (vocabTotal === 0) {
          <p class="text-sm" style="color: var(--text-muted)">No vocabulary yet.</p>
        } @else {
          <div class="panel !p-0 overflow-hidden">
            <table class="w-full text-sm">
              <thead class="border-b border-[var(--xp-border)] bg-[var(--surface-2)] text-left">
                <tr>
                  <th class="px-3 py-2">Word</th>
                  <th class="px-3 py-2">Meaning</th>
                  <th class="px-3 py-2">Mastery</th>
                  <th class="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                @for (w of vocabulary; track w.id) {
                  <tr class="border-b border-[var(--xp-border)] hover:bg-[var(--surface-2)]">
                    <td class="px-3 py-2">
                      <a [routerLink]="['/communication/vocabulary', w.id]" class="link">{{ w.word }}</a>
                    </td>
                    <td class="px-3 py-2 max-w-xs truncate">{{ w.meaning }}</td>
                    <td class="px-3 py-2">{{ w.mastery }}/5</td>
                    <td class="px-3 py-2">
                      <a [routerLink]="['/communication/vocabulary', w.id, 'edit']" class="text-xs underline">Edit</a>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
            <app-list-paginator
              [total]="vocabTotal"
              [pageSize]="pageSize"
              [currentPage]="vocabPage"
              (pageChange)="setVocabPage($event)"
            />
          </div>
        }
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
  private readonly fb = inject(FormBuilder);
  private readonly confirm = inject(ConfirmService);

  writingCategories = WRITING_CATEGORIES;
  speakingCategories = SPEAKING_CATEGORIES;
  tab = signal<'vocabulary' | 'writing' | 'speaking'>('vocabulary');
  tabs = [
    { id: 'vocabulary' as const, label: 'Vocabulary' },
    { id: 'writing' as const, label: 'Writing' },
    { id: 'speaking' as const, label: 'Speaking' },
  ];

  vocabulary: VocabularyWord[] = [];
  writing: WritingPractice[] = [];
  speaking: SpeakingPractice[] = [];
  vocabTotal = 0;
  writingTotal = 0;
  speakingTotal = 0;
  vocabPage = 1;
  writingPage = 1;
  speakingPage = 1;
  readonly pageSize = 25;

  vocabFilter = this.fb.nonNullable.group({ search: '' });

  ngOnInit(): void {
    this.loadAll();
  }

  setTab(id: 'vocabulary' | 'writing' | 'speaking'): void {
    this.tab.set(id);
  }

  loadAll(): void {
    this.loadVocabulary();
    this.loadWriting();
    this.loadSpeaking();
  }

  searchVocabulary(): void {
    this.vocabPage = 1;
    this.loadVocabulary();
  }

  loadVocabulary(): void {
    const search = this.vocabFilter.getRawValue().search;
    const offset = (this.vocabPage - 1) * this.pageSize;
    this.communication
      .listVocabulary({ search: search || undefined, limit: this.pageSize, offset })
      .subscribe({
        next: (result) => {
          this.vocabulary = result.items;
          this.vocabTotal = result.total;
          this.clampPage('vocab');
        },
      });
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

  setVocabPage(page: number): void {
    this.vocabPage = page;
    this.loadVocabulary();
  }

  setWritingPage(page: number): void {
    this.writingPage = page;
    this.loadWriting();
  }

  setSpeakingPage(page: number): void {
    this.speakingPage = page;
    this.loadSpeaking();
  }

  private clampPage(which: 'vocab' | 'writing' | 'speaking'): void {
    if (which === 'vocab') {
      const totalPages = Math.max(1, Math.ceil(this.vocabTotal / this.pageSize));
      if (this.vocabPage > totalPages) {
        this.vocabPage = totalPages;
        this.loadVocabulary();
      }
    } else if (which === 'writing') {
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
