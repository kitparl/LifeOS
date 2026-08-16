import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CodeWorkspaceComponent } from '../../shared/code-workspace';
import {
  ContentConverterService,
  DataMigrationService,
} from '../../shared/code-workspace/services/migration';
import { SPEAKING_CATEGORIES, SpeakingCategory } from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-speaking-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, CodeWorkspaceComponent],
  template: `
    <div style="max-width: 680px">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar">{{ isEdit ? 'Edit Practice' : 'New Speaking Practice' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div class="grid grid-cols-2 gap-3">
            <div class="col-span-2 sm:col-span-1">
              <label class="form-label" for="sp-title">Title</label>
              <input id="sp-title" class="input-field mt-1" formControlName="title" placeholder="Topic or question title" />
            </div>
            <div>
              <label class="form-label" for="sp-category">Category</label>
              <select id="sp-category" class="input-field mt-1" formControlName="category">
                @for (c of categories; track c.value) {
                  <option [value]="c.value">{{ c.label }}</option>
                }
              </select>
            </div>
          </div>

          <div>
            <label class="form-label" for="sp-prompt">Prompt / Question</label>
            <textarea id="sp-prompt" class="input-field mt-1" style="min-height: 72px; resize: vertical" formControlName="prompt" placeholder="What was asked…"></textarea>
          </div>

          <div>
            <label class="form-label" style="margin-bottom: 0.35rem; display: block">Your Response</label>
            @if (editorReady) {
              <div style="min-height: 240px; height: 280px; overflow: hidden">
                <app-code-workspace
                  [content]="editorContent"
                  mode="markdown"
                  language="markdown"
                  [showPreview]="true"
                  [showToolbar]="true"
                  [showRunButton]="false"
                  [showLanguageSelector]="false"
                  [showOutput]="false"
                  defaultViewMode="write"
                  (contentChange)="onResponseChange($event)"
                />
              </div>
            }
          </div>

          <div>
            <label class="form-label" for="sp-notes">Notes / Feedback</label>
            <textarea id="sp-notes" class="input-field mt-1" style="min-height: 56px; resize: vertical" formControlName="notes" placeholder="Key takeaways, improvements…"></textarea>
          </div>

          @if (error) {
            <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">{{ saving ? 'Saving…' : 'Save' }}</button>
            <a routerLink="/communication" class="btn-secondary no-underline">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class SpeakingFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly communication = inject(CommunicationService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly converter = inject(ContentConverterService);
  private readonly migration = inject(DataMigrationService);

  categories = SPEAKING_CATEGORIES;
  isEdit = false;
  itemId: string | null = null;
  saving = false;
  error = '';
  editorReady = false;
  editorContent = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    category: ['hr' as SpeakingCategory, Validators.required],
    prompt: ['', Validators.required],
    response: [''],
    notes: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.itemId = id;
      this.communication.getSpeaking(id).subscribe({
        next: (s) => {
          void this.loadResponse(s.response ?? '').then((response) => {
            this.form.patchValue({
              title: s.title,
              category: s.category,
              prompt: s.prompt,
              response,
              notes: s.notes ?? '',
            });
            this.editorContent = response;
            this.editorReady = true;
          });
        },
      });
    } else {
      this.editorReady = true;
    }
  }

  onResponseChange(content: string): void {
    this.form.controls.response.setValue(content, { emitEvent: false });
  }

  private async loadResponse(content: string): Promise<string> {
    if (!content.trimStart().startsWith('<')) {
      return content;
    }
    const record = await this.migration.migrateComponent('SpeakingFormComponent', content);
    if (record.status === 'completed' && record.convertedContent) {
      return record.convertedContent;
    }
    const fallback = await this.converter.htmlToMarkdown(content);
    return fallback.markdown || content;
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.getRawValue();
    const payload = {
      title: raw.title,
      category: raw.category,
      prompt: raw.prompt,
      response: raw.response || null,
      notes: raw.notes || null,
    };
    const req =
      this.isEdit && this.itemId
        ? this.communication.updateSpeaking(this.itemId, payload)
        : this.communication.createSpeaking(payload);
    req.subscribe({
      next: (s) => this.router.navigate(['/communication/speaking', s.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save';
        this.saving = false;
      },
    });
  }
}
