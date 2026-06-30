import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { SearchResultItem } from './models/search.models';
import { SearchService } from './services/search.service';

@Component({
  selector: 'app-search-page',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Search</h1>
      <form class="flex gap-2 text-sm" [formGroup]="form" (ngSubmit)="search()">
        <input class="input-field flex-1" formControlName="q" placeholder="Search across all modules…" />
        <button type="submit" class="btn-primary text-xs">Search</button>
      </form>

      @if (loading) {
        <p class="text-sm text-gray-600">Searching…</p>
      } @else if (searched && results.length === 0) {
        <p class="text-sm text-gray-600">No results for "{{ lastQuery }}".</p>
      } @else if (results.length > 0) {
        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">{{ results.length }} results</div>
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (r of results; track r.id + r.module) {
              <li class="px-3 py-2 hover:bg-[#d6e4f7]">
                <a [routerLink]="r.route" class="block">
                  <p class="font-medium text-[var(--xp-blue)]">{{ r.title }}</p>
                  <p class="text-xs text-gray-600 capitalize">{{ r.module }} · {{ r.entity_type }}</p>
                  @if (r.subtitle) {
                    <p class="text-xs text-gray-500 truncate">{{ r.subtitle }}</p>
                  }
                </a>
              </li>
            }
          </ul>
        </div>
      }
    </div>
  `,
})
export class SearchPageComponent implements OnInit {
  private readonly searchService = inject(SearchService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);

  form = this.fb.nonNullable.group({ q: '' });
  results: SearchResultItem[] = [];
  loading = false;
  searched = false;
  lastQuery = '';

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      const q = params.get('q');
      if (q) {
        this.form.patchValue({ q });
        this.search();
      }
    });
  }

  search(): void {
    const q = this.form.getRawValue().q.trim();
    if (!q) return;
    this.loading = true;
    this.lastQuery = q;
    this.searchService.search(q).subscribe({
      next: (res) => {
        this.results = res.results;
        this.searched = true;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
