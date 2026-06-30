import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { CareerService } from './services/career.service';

@Component({
  selector: 'app-career-page',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">Career</h1>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Profile</div>
        <form class="grid gap-2 p-3 text-sm sm:grid-cols-2" [formGroup]="profileForm" (ngSubmit)="saveProfile()">
          <input class="input-field" formControlName="headline" placeholder="Headline" />
          <input class="input-field" formControlName="github_username" placeholder="GitHub username" />
          <input class="input-field sm:col-span-2" formControlName="linkedin_url" placeholder="LinkedIn URL" />
          <input class="input-field sm:col-span-2" formControlName="resume_url" placeholder="Resume URL" />
          <button type="submit" class="btn-primary text-xs sm:col-span-2 !w-fit">Save profile</button>
        </form>
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Projects</div>
          <form class="space-y-2 border-b border-[var(--xp-border)] p-3 text-sm" [formGroup]="projectForm" (ngSubmit)="addProject()">
            <input class="input-field" formControlName="name" placeholder="Project name" />
            <input class="input-field" formControlName="tech_stack" placeholder="Tech stack" />
            <button type="submit" class="btn-primary text-xs">Add project</button>
          </form>
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (p of projects; track p['id']) {
              <li class="flex justify-between gap-2 px-3 py-2">
                <span>{{ p['name'] }}</span>
                <button type="button" class="text-xs text-red-700" (click)="removeProject($any(p).id)">Delete</button>
              </li>
            }
          </ul>
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Applications</div>
          <form class="space-y-2 border-b border-[var(--xp-border)] p-3 text-sm" [formGroup]="appForm" (ngSubmit)="addApplication()">
            <input class="input-field" formControlName="company" placeholder="Company" />
            <input class="input-field" formControlName="role" placeholder="Role" />
            <select class="input-field" formControlName="status">
              <option value="applied">Applied</option>
              <option value="interview">Interview</option>
              <option value="offer">Offer</option>
              <option value="rejected">Rejected</option>
            </select>
            <button type="submit" class="btn-primary text-xs">Add application</button>
          </form>
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (a of applications; track a['id']) {
              <li class="flex justify-between gap-2 px-3 py-2">
                <span>{{ a['company'] }} — {{ a['role'] }} <span class="text-gray-500">({{ a['status'] }})</span></span>
                <button type="button" class="text-xs text-red-700" (click)="removeApplication($any(a).id)">Delete</button>
              </li>
            }
          </ul>
        </div>
      </div>

      @if (analytics) {
        <p class="text-sm text-gray-600">
          {{ analytics['total_projects'] }} projects · {{ analytics['total_applications'] }} applications
        </p>
      }
    </div>
  `,
})
export class CareerPageComponent implements OnInit {
  private readonly career = inject(CareerService);
  private readonly fb = inject(FormBuilder);

  projects: Record<string, unknown>[] = [];
  applications: Record<string, unknown>[] = [];
  analytics: Record<string, unknown> | null = null;

  profileForm = this.fb.nonNullable.group({
    headline: [''],
    github_username: [''],
    linkedin_url: [''],
    resume_url: [''],
  });

  projectForm = this.fb.nonNullable.group({ name: [''], tech_stack: [''] });
  appForm = this.fb.nonNullable.group({ company: [''], role: [''], status: ['applied'] });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.career.getProfile().subscribe({
      next: (p) =>
        this.profileForm.patchValue({
          headline: (p['headline'] as string) ?? '',
          github_username: (p['github_username'] as string) ?? '',
          linkedin_url: (p['linkedin_url'] as string) ?? '',
          resume_url: (p['resume_url'] as string) ?? '',
        }),
    });
    this.career.listProjects().subscribe({ next: (d) => (this.projects = d) });
    this.career.listApplications().subscribe({ next: (d) => (this.applications = d) });
    this.career.analytics().subscribe({ next: (d) => (this.analytics = d) });
  }

  saveProfile(): void {
    const raw = this.profileForm.getRawValue();
    this.career.updateProfile({ ...raw }).subscribe();
  }

  addProject(): void {
    const raw = this.projectForm.getRawValue();
    if (!raw.name) return;
    this.career.createProject(raw).subscribe({ next: () => this.load() });
    this.projectForm.reset();
  }

  removeProject(id: string): void {
    this.career.deleteProject(id).subscribe({ next: () => this.load() });
  }

  addApplication(): void {
    const raw = this.appForm.getRawValue();
    if (!raw.company || !raw.role) return;
    this.career.createApplication(raw).subscribe({ next: () => this.load() });
    this.appForm.reset({ company: '', role: '', status: 'applied' });
  }

  removeApplication(id: string): void {
    this.career.deleteApplication(id).subscribe({ next: () => this.load() });
  }
}
