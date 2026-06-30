import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
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
  imports: [ReactiveFormsModule, RouterLink],
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

      @if (tab() === 'vocabulary') {
        <form class="flex gap-2 text-sm" [formGroup]="vocabFilter" (ngSubmit)="loadVocabulary()">
          <input class="input-field !w-48" formControlName="search" placeholder="Search words…" />
          <button type="submit" class="btn-primary text-xs">Search</button>
        </form>
        @if (vocabulary.length === 0) {
          <p class="text-sm text-gray-600">No vocabulary yet.</p>
        } @else {
          <div class="panel !p-0 overflow-hidden">
            <table class="w-full text-sm">
              <thead class="border-b border-[var(--xp-border)] bg-[#e8e8e8] text-left">
                <tr>
                  <th class="px-3 py-2">Word</th>
                  <th class="px-3 py-2">Meaning</th>
                  <th class="px-3 py-2">Mastery</th>
                  <th class="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                @for (w of vocabulary; track w.id) {
                  <tr class="border-b border-[var(--xp-border)] hover:bg-[#d6e4f7]">
                    <td class="px-3 py-2">
                      <a [routerLink]="['/communication/vocabulary', w.id]" class="text-[var(--xp-blue)] underline">{{ w.word }}</a>
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
          </div>
        }
      }

      @if (tab() === 'writing') {
        @if (writing.length === 0) {
          <p class="text-sm text-gray-600">No writing practice yet.</p>
        } @else {
          <ul class="divide-y divide-[var(--xp-border)] panel !p-0 text-sm">
            @for (w of writing; track w.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2 hover:bg-[#d6e4f7]">
                <div>
                  <a [routerLink]="['/communication/writing', w.id]" class="text-[var(--xp-blue)] underline">{{ w.title }}</a>
                  <p class="text-xs text-gray-600 capitalize">{{ w.category }}</p>
                </div>
                <a [routerLink]="['/communication/writing', w.id, 'edit']" class="text-xs underline">Edit</a>
              </li>
            }
          </ul>
        }
      }

      @if (tab() === 'speaking') {
        @if (speaking.length === 0) {
          <p class="text-sm text-gray-600">No speaking practice yet.</p>
        } @else {
          <ul class="divide-y divide-[var(--xp-border)] panel !p-0 text-sm">
            @for (s of speaking; track s.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2 hover:bg-[#d6e4f7]">
                <div>
                  <a [routerLink]="['/communication/speaking', s.id]" class="text-[var(--xp-blue)] underline">{{ s.title }}</a>
                  <p class="text-xs text-gray-600 capitalize">{{ s.category.replace('_', ' ') }}</p>
                </div>
                <a [routerLink]="['/communication/speaking', s.id, 'edit']" class="text-xs underline">Edit</a>
              </li>
            }
          </ul>
        }
      }
    </div>
  `,
})
export class CommunicationHubComponent implements OnInit {
  private readonly communication = inject(CommunicationService);
  private readonly fb = inject(FormBuilder);

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

  vocabFilter = this.fb.nonNullable.group({ search: '' });

  ngOnInit(): void {
    this.loadAll();
  }

  setTab(id: 'vocabulary' | 'writing' | 'speaking'): void {
    this.tab.set(id);
  }

  loadAll(): void {
    this.loadVocabulary();
    this.communication.listWriting().subscribe({ next: (w) => (this.writing = w) });
    this.communication.listSpeaking().subscribe({ next: (s) => (this.speaking = s) });
  }

  loadVocabulary(): void {
    const search = this.vocabFilter.getRawValue().search;
    this.communication.listVocabulary(search || undefined).subscribe({ next: (v) => (this.vocabulary = v) });
  }
}
