import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AiSourceItem } from '../../ai/models/ai.models';
import { AiService } from '../../ai/services/ai.service';

interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  sources?: AiSourceItem[];
}

@Component({
  selector: 'app-ai-chat-panel',
  standalone: true,
  imports: [FormsModule, RouterLink],
  template: `
    <div class="panel !p-0 h-full flex flex-col">
      <div class="title-bar rounded-none border-x-0 border-t-0 shrink-0 flex items-center justify-between pr-2">
        <span>AI Assistant</span>
        @if (statusLabel) {
          <span class="text-[10px] font-normal opacity-80">{{ statusLabel }}</span>
        }
      </div>

      <div class="flex-1 overflow-y-auto p-2 space-y-2 text-sm min-h-0">
        @if (messages.length === 0) {
          <p class="text-xs text-gray-600 text-center py-4">
            Ask about your goals, tasks, journal, runs, or Q&A. Answers use your LifeOS data.
          </p>
        }
        @for (m of messages; track $index) {
          <div
            class="rounded px-2 py-1.5"
            [class.bg-[#d6e4f7]]="m.role === 'user'"
            [class.bg-[#f5f5f0]]="m.role === 'assistant'"
          >
            <p class="whitespace-pre-wrap">{{ m.text }}</p>
            @if (m.sources && m.sources.length > 0) {
              <ul class="mt-1 space-y-0.5 text-xs">
                @for (s of m.sources; track s.source_id) {
                  <li>
                    <a [routerLink]="s.route" class="text-[var(--xp-blue)] underline">{{ s.title }}</a>
                  </li>
                }
              </ul>
            }
          </div>
        }
        @if (loading) {
          <p class="text-xs text-gray-500">Thinking…</p>
        }
        @if (error) {
          <p class="text-xs text-red-700">{{ error }}</p>
        }
      </div>

      <form class="border-t border-[var(--xp-border)] p-2 flex gap-1" (ngSubmit)="send()">
        <input
          class="input-field text-xs flex-1"
          type="text"
          placeholder="Ask LifeOS…"
          [(ngModel)]="draft"
          name="draft"
          [disabled]="loading"
        />
        <button type="submit" class="btn-primary text-xs shrink-0" [disabled]="loading || !draft.trim()">
          Send
        </button>
      </form>
    </div>
  `,
})
export class AiChatPanelComponent implements OnInit {
  private readonly ai = inject(AiService);

  messages: ChatMessage[] = [];
  draft = '';
  loading = false;
  error = '';
  statusLabel = '';

  ngOnInit(): void {
    this.ai.status().subscribe({
      next: (s) => {
        this.statusLabel = s.enabled
          ? `RAG · ${s.indexed_chunks} indexed`
          : 'No API key · local context';
      },
    });
  }

  send(): void {
    const text = this.draft.trim();
    if (!text || this.loading) return;
    this.messages.push({ role: 'user', text });
    this.draft = '';
    this.loading = true;
    this.error = '';
    this.ai.chat(text).subscribe({
      next: (res) => {
        this.messages.push({ role: 'assistant', text: res.reply, sources: res.sources });
        this.loading = false;
      },
      error: () => {
        this.error = 'Failed to get a response';
        this.loading = false;
      },
    });
  }
}
