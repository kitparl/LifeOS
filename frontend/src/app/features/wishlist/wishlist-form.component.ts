import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FileUploadComponent } from '../../shared/file-upload/file-upload.component';
import { TypeSelectComponent } from '../../shared/type-select/type-select.component';
import { FilesService } from '../files/services/files.service';
import {
  WISHLIST_PRIORITIES,
  WISHLIST_STATUSES,
  WishlistPriority,
  WishlistStatus,
} from './models/wishlist.models';
import { WishlistService } from './services/wishlist.service';

interface PhotoItem {
  url: string;
  preview: string;
}

@Component({
  selector: 'app-wishlist-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, FileUploadComponent, TypeSelectComponent],
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
            <app-type-select
              formControlName="category"
              placeholder="Select or create a category…"
              [options]="categories()"
              (created)="onCategoryCreated($event)"
            />
          </div>
          <div>
            <label class="mb-1 block">Description</label>
            <textarea class="input-field min-h-[80px]" formControlName="description"></textarea>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block">Target year</label>
              <input class="input-field" type="number" min="1900" max="2200" formControlName="target_year" placeholder="e.g. 2027" />
            </div>
            <div>
              <label class="mb-1 block">Achieved date</label>
              <input class="input-field" type="date" formControlName="achieved_date" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block">Status</label>
              <select class="input-field" formControlName="status">
                @for (s of statuses; track s.value) {
                  <option [value]="s.value">{{ s.label }}</option>
                }
              </select>
            </div>
            <div>
              <label class="mb-1 block">Priority</label>
              <select class="input-field" formControlName="priority">
                @for (p of priorities; track p.value) {
                  <option [value]="p.value">{{ p.label }}</option>
                }
              </select>
            </div>
          </div>
          <div>
            <label class="mb-1 block">Images</label>
            @if (photos.length) {
              <div class="mb-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
                @for (photo of photos; track photo.url; let i = $index) {
                  <div class="relative overflow-hidden rounded border border-[var(--xp-border)]">
                    <img [src]="photo.preview || photo.url" alt="Photo {{ i + 1 }}" class="h-28 w-full object-cover" />
                    <button
                      type="button"
                      class="absolute right-1 top-1 rounded px-1.5 py-0.5 text-[10px]"
                      style="background: var(--surface); color: var(--danger); border: 1px solid var(--xp-border)"
                      (click)="removePhoto(i)"
                    >
                      Remove
                    </button>
                  </div>
                }
              </div>
            }
            <app-file-upload
              label="Add images"
              hint="Images — choose, paste (Ctrl/Cmd+V), or drop (multiple OK)"
              accept="image/*"
              module="wishlist"
              [entityId]="itemId"
              [multiple]="true"
              [knownChecksums]="photoChecksums"
              (uploaded)="onImageUploaded($event)"
            />
            <input
              class="input-field mt-2"
              [value]="externalUrl"
              (input)="externalUrl = $any($event.target).value"
              (change)="addExternalUrl()"
              placeholder="Or paste an image URL and press Enter…"
              (keydown.enter)="$event.preventDefault(); addExternalUrl()"
            />
          </div>
          <div>
            <label class="mb-1 block">Notes</label>
            <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
          </div>
          @if (error) {
            <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">{{ saving ? 'Saving…' : 'Save' }}</button>
            <a routerLink="/wishlist" class="btn-secondary no-underline">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class WishlistFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly wishlistService = inject(WishlistService);
  private readonly filesService = inject(FilesService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly categories = signal<string[]>([]);
  statuses = WISHLIST_STATUSES;
  priorities = WISHLIST_PRIORITIES;
  isEdit = false;
  itemId: string | null = null;
  saving = false;
  error = '';
  photos: PhotoItem[] = [];
  photoChecksums: string[] = [];
  externalUrl = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    category: ['other', Validators.required],
    description: [''],
    target_year: [null as number | null],
    achieved_date: [''],
    status: ['in_progress' as WishlistStatus, Validators.required],
    priority: ['medium' as WishlistPriority, Validators.required],
    notes: [''],
  });

  ngOnInit(): void {
    this.wishlistService.listCategories().subscribe({ next: (c) => this.categories.set(c) });

    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.itemId = id;
      this.wishlistService.get(id).subscribe({
        next: (item) => {
          this.form.patchValue({
            title: item.title,
            category: item.category,
            description: item.description ?? '',
            target_year: item.target_year,
            achieved_date: item.achieved_date ? item.achieved_date.slice(0, 10) : '',
            status: item.status,
            priority: item.priority,
            notes: item.notes ?? '',
          });
          this.photos = [];
          this.photoChecksums = [];
          const urls = item.photos?.length ? item.photos : item.image_url ? [item.image_url] : [];
          for (const u of urls) this.addPhoto(u);
        },
      });
    }
  }

  onCategoryCreated(name: string): void {
    this.categories.update((list) => (list.includes(name) ? list : [...list, name].sort()));
    this.wishlistService.createCategory(name).subscribe({ next: (c) => this.categories.set(c) });
  }

  onImageUploaded(url: string): void {
    if (this.photos.some((p) => p.url === url)) return;
    this.addPhoto(url);
  }

  addExternalUrl(): void {
    const url = this.externalUrl.trim();
    if (!url) return;
    if (this.photos.some((p) => p.url === url)) {
      this.externalUrl = '';
      return;
    }
    this.addPhoto(url);
    this.externalUrl = '';
  }

  removePhoto(index: number): void {
    this.photos = this.photos.filter((_, i) => i !== index);
    this.refreshPhotoChecksums();
  }

  private addPhoto(url: string): void {
    this.photos = [...this.photos, { url, preview: url }];
    const fileId = url.match(/\/files\/([0-9a-f-]{36})\/content/i)?.[1];
    if (fileId) {
      this.filesService.tokenUrl(fileId).subscribe({
        next: (preview) => {
          this.photos = this.photos.map((p) => (p.url === url ? { ...p, preview } : p));
        },
      });
      this.filesService.get(fileId).subscribe({
        next: (record) => {
          if (record.checksum_sha256) {
            this.photoChecksums = [...this.photoChecksums, record.checksum_sha256];
          }
        },
      });
    }
  }

  private refreshPhotoChecksums(): void {
    const ids = this.photos
      .map((p) => p.url.match(/\/files\/([0-9a-f-]{36})\/content/i)?.[1])
      .filter((id): id is string => !!id);
    if (!ids.length) {
      this.photoChecksums = [];
      return;
    }
    const sums: string[] = [];
    let pending = ids.length;
    for (const id of ids) {
      this.filesService.get(id).subscribe({
        next: (record) => {
          if (record.checksum_sha256) sums.push(record.checksum_sha256);
          pending -= 1;
          if (pending === 0) this.photoChecksums = [...sums];
        },
        error: () => {
          pending -= 1;
          if (pending === 0) this.photoChecksums = [...sums];
        },
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.getRawValue();
    const photoUrls = this.photos.map((p) => p.url);
    const payload = {
      title: raw.title,
      category: raw.category,
      description: raw.description || null,
      target_year: raw.target_year,
      achieved_date: raw.achieved_date || null,
      status: raw.status,
      priority: raw.priority,
      photos: photoUrls,
      image_url: photoUrls[0] ?? null,
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
