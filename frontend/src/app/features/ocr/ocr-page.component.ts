import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { filesFromClipboard, filesFromDataTransfer } from '../../shared/file-upload/clipboard-files';
import { OcrDocument, OcrService } from './services/ocr.service';

@Component({
  selector: 'app-ocr-page',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">OCR Pipeline</h1>
      <div class="grid gap-4 lg:grid-cols-2">
        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Upload document</div>
          <div class="space-y-2 p-3 text-sm">
            <select class="input-field" [formControl]="uploadForm.controls.doc_type">
              <option value="bill">Bill</option>
              <option value="certificate">Certificate</option>
              <option value="receipt">Receipt</option>
              <option value="note">Note</option>
              <option value="document">Document</option>
            </select>
            <div
              class="flex flex-col items-center justify-center gap-2 rounded border border-dashed px-3 py-4 text-center outline-none"
              tabindex="0"
              [style.border-color]="dragOver ? 'var(--xp-blue)' : 'var(--xp-border)'"
              [style.background]="
                dragOver
                  ? 'color-mix(in srgb, var(--xp-blue) 12%, transparent)'
                  : 'color-mix(in srgb, var(--primary-soft) 35%, transparent)'
              "
              [class.opacity-60]="uploading"
              (paste)="onPaste($event)"
              (dragover)="onDragOver($event)"
              (dragleave)="dragOver = false"
              (drop)="onDrop($event)"
            >
              <p class="text-sm font-medium">Upload for OCR</p>
              <p class="text-xs" style="color: var(--text-muted)">
                PDF, images, text — choose, paste (Ctrl/Cmd+V), or drop
              </p>
              <input #fileInput type="file" class="hidden" (change)="onFile($event)" [disabled]="uploading" />
              <button type="button" class="btn-primary text-xs" [disabled]="uploading" (click)="fileInput.click()">
                {{ uploading ? 'Uploading…' : 'Choose file' }}
              </button>
              @if (uploadError) {
                <p class="text-xs" style="color: var(--danger)">{{ uploadError }}</p>
              }
            </div>
          </div>
        </div>
        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Paste text</div>
          <form class="space-y-2 p-3 text-sm" [formGroup]="textForm" (ngSubmit)="submitText()">
            <input class="input-field" formControlName="filename" placeholder="Filename" />
            <textarea class="input-field min-h-[80px]" formControlName="text" placeholder="Paste receipt or note text"></textarea>
            <button type="submit" class="btn-primary text-xs">Process text</button>
          </form>
        </div>
      </div>
      <ul class="panel !p-0 divide-y divide-[var(--xp-border)] text-sm">
        @for (doc of docs; track doc.id) {
          <li class="px-3 py-2">
            <div class="flex justify-between gap-2">
              <span class="font-medium">{{ doc.filename }} <span class="text-xs text-gray-500">({{ doc.doc_type }})</span></span>
              <button type="button" class="text-xs" style="color: var(--danger)" (click)="remove(doc.id)">Delete</button>
            </div>
            <p class="mt-1 text-gray-700 whitespace-pre-wrap">{{ doc.extracted_text }}</p>
          </li>
        } @empty {
          <li class="px-3 py-4 text-gray-600">No OCR documents yet.</li>
        }
      </ul>
    </div>
  `,
})
export class OcrPageComponent implements OnInit {
  private readonly ocr = inject(OcrService);
  private readonly fb = inject(FormBuilder);
  docs: OcrDocument[] = [];
  uploading = false;
  dragOver = false;
  uploadError = '';
  uploadForm = this.fb.nonNullable.group({ doc_type: 'document' });
  textForm = this.fb.nonNullable.group({ filename: 'pasted.txt', text: '', doc_type: 'document' });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.ocr.list().subscribe({ next: (d) => (this.docs = d) });
  }

  onFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (file) this.upload(file);
  }

  onPaste(event: ClipboardEvent): void {
    const files = filesFromClipboard(event);
    if (!files.length) return;
    event.preventDefault();
    this.upload(files[0]);
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = true;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = false;
    const files = filesFromDataTransfer(event.dataTransfer);
    if (files[0]) this.upload(files[0]);
  }

  private upload(file: File): void {
    this.uploading = true;
    this.uploadError = '';
    this.ocr.upload(file, this.uploadForm.getRawValue().doc_type).subscribe({
      next: () => {
        this.uploading = false;
        this.load();
      },
      error: () => {
        this.uploading = false;
        this.uploadError = 'Upload failed';
      },
    });
  }

  submitText(): void {
    const v = this.textForm.getRawValue();
    this.ocr.createFromText({ filename: v.filename, doc_type: v.doc_type, text: v.text }).subscribe({
      next: () => {
        this.textForm.patchValue({ text: '' });
        this.load();
      },
    });
  }

  remove(id: string): void {
    this.ocr.delete(id).subscribe({ next: () => this.load() });
  }
}
