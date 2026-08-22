import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CodeWorkspaceComponent } from '../../shared/code-workspace';
import { MarkdownImportButtonComponent } from '../../shared/markdown/markdown-import-button.component';
import { MarkdownImportResult } from '../../shared/markdown/markdown-import.service';
import { MarkdownExportButtonComponent } from '../../shared/markdown/markdown-export-button.component';
import { WRITING_CATEGORIES, WritingCategory } from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-writing-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, CodeWorkspaceComponent, MarkdownImportButtonComponent, MarkdownExportButtonComponent],
  template: `
    <div style="max-width: 760px">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar flex items-center justify-between gap-2">
          <span>{{ isEdit ? 'Edit Writing' : 'New Writing' }}</span>
          <div class="flex items-center gap-1">
            <app-markdown-import-button
              [currentContent]="form.controls.content.value"
              [currentTitle]="form.controls.title.value"
              (imported)="onMarkdownImported($event)"
              (importError)="error = $event"
            />
            <app-markdown-export-button
              [content]="form.controls.content.value"
              [filename]="form.controls.title.value || 'writing'"
              (exportError)="error = $event"
            />
          </div>
        </div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div class="grid grid-cols-2 gap-3">
            <div class="col-span-2 sm:col-span-1">
              <label class="form-label" for="title">Title</label>
              <input id="title" class="input-field mt-1" formControlName="title" placeholder="Give it a title…" />
            </div>
            <div>
              <label class="form-label" for="category">Category</label>
              <select id="category" class="input-field mt-1" formControlName="category">
                @for (c of categories; track c.value) {
                  <option [value]="c.value">{{ c.label }}</option>
                }
              </select>
            </div>
          </div>

          <div>
            <label class="form-label" style="margin-bottom: 0.35rem; display: block">Content</label>
            @if (editorReady) {
              <div style="min-height: 320px; height: 46vh; overflow: hidden">
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
                  (contentChange)="onContentChange($event)"
                />
              </div>
            }
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
export class WritingFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly communication = inject(CommunicationService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  categories = WRITING_CATEGORIES;
  isEdit = false;
  itemId: string | null = null;
  saving = false;
  error = '';
  editorReady = false;
  editorContent = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    category: ['notes' as WritingCategory, Validators.required],
    content: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.itemId = id;
      this.communication.getWriting(id).subscribe({
        next: (w) => {
          const content = w.content ?? '';
          this.form.patchValue({ title: w.title, category: w.category, content });
          this.editorContent = content;
          this.editorReady = true;
        },
      });
    } else {
      this.editorReady = true;
    }
  }

  onContentChange(content: string): void {
    this.editorContent = content;
    this.form.controls.content.setValue(content, { emitEvent: false });
  }

  onMarkdownImported(result: MarkdownImportResult): void {
    this.error = '';
    this.editorContent = result.content;
    this.form.controls.content.setValue(result.content, { emitEvent: false });
    if (result.title) {
      this.form.controls.title.setValue(result.title, { emitEvent: false });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.getRawValue();
    const req =
      this.isEdit && this.itemId
        ? this.communication.updateWriting(this.itemId, raw)
        : this.communication.createWriting(raw);
    req.subscribe({
      next: (w) => this.router.navigate(['/communication/writing', w.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save';
        this.saving = false;
      },
    });
  }
}
