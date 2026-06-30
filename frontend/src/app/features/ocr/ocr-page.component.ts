import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
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
            <input type="file" class="text-sm" (change)="onFile($event)" />
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
              <button type="button" class="text-xs text-red-700" (click)="remove(doc.id)">Delete</button>
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
    if (!file) return;
    this.ocr.upload(file, this.uploadForm.getRawValue().doc_type).subscribe({ next: () => this.load() });
    input.value = '';
  }

  submitText(): void {
    const v = this.textForm.getRawValue();
    this.ocr.createFromText({ filename: v.filename, doc_type: v.doc_type, text: v.text }).subscribe({
      next: () => { this.textForm.patchValue({ text: '' }); this.load(); },
    });
  }

  remove(id: string): void {
    this.ocr.delete(id).subscribe({ next: () => this.load() });
  }
}
