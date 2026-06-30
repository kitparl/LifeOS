import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FileUploadComponent } from '../../shared/file-upload/file-upload.component';
import { WISHLIST_CATEGORIES, WishlistCategory } from './models/wishlist.models';
import { WishlistService } from './services/wishlist.service';

@Component({
  selector: 'app-wishlist-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, FileUploadComponent],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Item' : 'New Wishlist Item' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Title</label>
            <input class="input-field" formControlName="title" />
          </div>
          <div>
            <label class="mb-1 block">Category</label>
            <select class="input-field" formControlName="category">
              @for (c of categories; track c.value) {
                <option [value]="c.value">{{ c.label }}</option>
              }
            </select>
          </div>
          <div>
            <label class="mb-1 block">Description</label>
            <textarea class="input-field min-h-[80px]" formControlName="description"></textarea>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block">Est. cost</label>
              <input class="input-field" type="number" min="0" step="0.01" formControlName="cost" />
            </div>
            <div>
              <label class="mb-1 block">Progress (%)</label>
              <input class="input-field" type="number" min="0" max="100" formControlName="progress" />
            </div>
          </div>
          <div>
            <label class="mb-1 block">Image</label>
            <app-file-upload module="wishlist" [entityId]="itemId" (uploaded)="onImageUploaded($event)" />
            <input class="input-field mt-2" formControlName="image_url" placeholder="Or paste image URL…" />
          </div>
          <div>
            <label class="mb-1 block">Notes</label>
            <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
          </div>
          @if (error) {
            <p class="text-xs text-red-700">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">{{ saving ? 'Saving…' : 'Save' }}</button>
            <a routerLink="/wishlist" class="input-field !w-auto inline-flex items-center no-underline text-gray-700">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class WishlistFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly wishlistService = inject(WishlistService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  categories = WISHLIST_CATEGORIES;
  isEdit = false;
  itemId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    category: ['other' as WishlistCategory, Validators.required],
    description: [''],
    cost: [null as number | null],
    progress: [0, [Validators.min(0), Validators.max(100)]],
    image_url: [''],
    notes: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.itemId = id;
      this.wishlistService.get(id).subscribe({
        next: (item) =>
          this.form.patchValue({
            title: item.title,
            category: item.category,
            description: item.description ?? '',
            cost: item.cost,
            progress: item.progress,
            image_url: item.image_url ?? '',
            notes: item.notes ?? '',
          }),
      });
    }
  }

  onImageUploaded(url: string): void {
    this.form.patchValue({ image_url: url });
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.getRawValue();
    const payload = {
      title: raw.title,
      category: raw.category,
      description: raw.description || null,
      cost: raw.cost,
      progress: raw.progress,
      image_url: raw.image_url || null,
      notes: raw.notes || null,
    };
    const req =
      this.isEdit && this.itemId
        ? this.wishlistService.update(this.itemId, payload)
        : this.wishlistService.create(payload);
    req.subscribe({
      next: (item) => this.router.navigate(['/wishlist', item.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save';
        this.saving = false;
      },
    });
  }
}
