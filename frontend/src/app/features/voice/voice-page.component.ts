import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { VoiceNote, VoiceService } from './services/voice.service';

@Component({
  selector: 'app-voice-page',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="space-y-4 max-w-2xl">
      <h1 class="text-lg font-semibold">Voice</h1>
      <p class="text-sm text-gray-600">Type transcripts to simulate voice notes and commands (e.g. "go to tasks", "search goals").</p>
      <form class="panel space-y-2 text-sm" [formGroup]="commandForm" (ngSubmit)="runCommand()">
        <textarea class="input-field min-h-[60px]" formControlName="transcript" placeholder="Voice command…"></textarea>
        <button type="submit" class="btn-primary text-xs" [disabled]="commandForm.invalid">Run command</button>
        @if (commandResult) {
          <p class="text-gray-700">{{ commandResult }}</p>
          @if (commandRoute) {
            <button type="button" class="btn-primary text-xs" (click)="navigate()">Go</button>
          }
        }
      </form>
      <form class="panel space-y-2 text-sm" [formGroup]="noteForm" (ngSubmit)="saveNote()">
        <input class="input-field" formControlName="title" placeholder="Note title (optional)" />
        <textarea class="input-field min-h-[60px]" formControlName="transcript" placeholder="Voice note transcript…"></textarea>
        <button type="submit" class="btn-primary text-xs" [disabled]="noteForm.invalid">Save note</button>
      </form>
      <ul class="panel !p-0 divide-y divide-[var(--xp-border)] text-sm">
        @for (n of notes; track n.id) {
          <li class="flex justify-between gap-2 px-3 py-2">
            <div>
              <p class="font-medium">{{ n.title || 'Note' }} <span class="text-xs text-gray-500">({{ n.note_type }})</span></p>
              <p>{{ n.transcript }}</p>
              @if (n.command_result) { <p class="text-xs text-gray-600">{{ n.command_result }}</p> }
            </div>
            <button type="button" class="text-xs text-red-700 shrink-0" (click)="remove(n.id)">Delete</button>
          </li>
        }
      </ul>
    </div>
  `,
})
export class VoicePageComponent implements OnInit {
  private readonly voice = inject(VoiceService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  notes: VoiceNote[] = [];
  commandResult: string | null = null;
  commandRoute: string | null = null;
  commandForm = this.fb.nonNullable.group({ transcript: '' });
  noteForm = this.fb.nonNullable.group({ title: '', transcript: '' });

  ngOnInit(): void {
    this.voice.list().subscribe({ next: (n) => (this.notes = n) });
  }

  runCommand(): void {
    const { transcript } = this.commandForm.getRawValue();
    this.voice.command(transcript).subscribe({
      next: (r) => {
        this.commandResult = r.message;
        this.commandRoute = r.route;
        this.voice.list().subscribe({ next: (n) => (this.notes = n) });
      },
    });
  }

  navigate(): void {
    if (this.commandRoute) this.router.navigateByUrl(this.commandRoute);
  }

  saveNote(): void {
    const v = this.noteForm.getRawValue();
    this.voice.createNote(v.transcript, v.title || undefined).subscribe({
      next: () => {
        this.noteForm.reset();
        this.voice.list().subscribe({ next: (n) => (this.notes = n) });
      },
    });
  }

  remove(id: string): void {
    this.voice.delete(id).subscribe({
      next: () => this.voice.list().subscribe({ next: (n) => (this.notes = n) }),
    });
  }
}
