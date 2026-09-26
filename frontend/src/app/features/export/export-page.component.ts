import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ExportService } from './services/export.service';

@Component({
  selector: 'app-export-page',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="panel max-w-md">
      <form class="space-y-3 text-sm" [formGroup]="form" (ngSubmit)="download()">
        <div>
          <label class="form-label" for="export-module">Module</label>
          <select id="export-module" class="input-field" formControlName="module">
            @for (m of modules; track m) {
              <option [value]="m">{{ m }}</option>
            }
          </select>
        </div>
        <div>
          <label class="form-label" for="export-format">Format</label>
          <select id="export-format" class="input-field" formControlName="format">
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
          </select>
        </div>
        @if (message) {
          <p class="text-xs text-green-700">{{ message }}</p>
        }
        @if (error) {
          <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
        }
        <button type="submit" class="btn-primary" [disabled]="downloading">
          {{ downloading ? 'Downloading…' : 'Download' }}
        </button>
      </form>
    </div>
  `,
})
export class ExportPageComponent implements OnInit {
  private readonly exportService = inject(ExportService);
  private readonly fb = inject(FormBuilder);

  modules: string[] = [];
  downloading = false;
  message = '';
  error = '';

  form = this.fb.nonNullable.group({
    module: 'tasks',
    format: 'json' as 'json' | 'csv',
  });

  ngOnInit(): void {
    this.exportService.listModules().subscribe({
      next: (res) => (this.modules = res.modules),
    });
  }

  download(): void {
    const raw = this.form.getRawValue();
    this.downloading = true;
    this.message = '';
    this.error = '';
    this.exportService.download(raw.module, raw.format).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `lifeos-${raw.module}.${raw.format}`;
        a.click();
        URL.revokeObjectURL(url);
        this.message = 'Download started';
        this.downloading = false;
      },
      error: () => {
        this.error = 'Export failed';
        this.downloading = false;
      },
    });
  }
}
