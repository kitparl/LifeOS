import { Component, ElementRef, OnInit, ViewChild, inject } from '@angular/core';
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
  styles: [':host { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; }'],
  template: `
    <div style="display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: hidden;">

      <!-- Subtle assistant header -->
      <div class="shrink-0 flex items-center justify-between"
           style="padding: 0.5rem 0.875rem; border-bottom: 1px solid var(--border); background: var(--surface-2); min-height: 44px">
        <div class="flex items-center gap-1.5">
          <span style="font-size: 13px; font-weight: 600; color: var(--text)">Assistant</span>
          @if (statusLabel) {
            <span class="badge badge--default" style="font-size: 10px">{{ statusLabel }}</span>
          }
        </div>
        @if (messages.length > 0) {
          <button type="button" class="btn-ghost !px-2 !min-h-auto" style="font-size: 11px; color: var(--text-muted)" (click)="clearMessages()">
            Clear
          </button>
        }
      </div>

      <!-- Message list (this scrolls) -->
      <div #messagesList class="flex-1 min-h-0 overflow-y-auto" style="padding: 0.75rem 0.75rem 0.5rem">
        @if (messages.length === 0) {
          <div class="empty-state" style="padding: 2rem 1rem">
            <div style="font-size: 1.5rem; opacity: 0.3">◇</div>
            <p class="empty-state__title">Ask LifeOS</p>
            <p class="empty-state__desc">Goals, tasks, journal, runs, Q&A — powered by your data.</p>
          </div>
        }
        @for (m of messages; track $index) {
          <div class="chat-message" [class.chat-message--user]="m.role === 'user'" [class.chat-message--assistant]="m.role === 'assistant'">
            <div class="chat-bubble" [class.chat-bubble--user]="m.role === 'user'" [class.chat-bubble--assistant]="m.role === 'assistant'">
              <p style="white-space: pre-wrap; margin: 0; line-height: 1.55">{{ m.text }}</p>
              @if (m.sources && m.sources.length > 0) {
                <ul style="margin-top: 0.5rem; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 2px">
                  @for (s of m.sources; track s.source_id) {
                    <li style="font-size: 11px">
                      <a [routerLink]="s.route" style="color: var(--primary); text-decoration: underline">{{ s.title }}</a>
                    </li>
                  }
                </ul>
              }
            </div>
          </div>
        }
        @if (loading) {
          <div class="chat-message chat-message--assistant">
            <div class="chat-bubble chat-bubble--assistant">
              <span class="skeleton-text" style="display: block; width: 80%; height: 0.75rem"></span>
            </div>
          </div>
        }
        @if (error) {
          <p style="font-size: 12px; color: var(--danger); padding: 0.5rem 0">{{ error }}</p>
        }
      </div>

      <!-- Input form -->
      <form
        class="shrink-0 flex gap-1.5"
        style="padding: 0.625rem 0.75rem; border-top: 1px solid var(--border); background: var(--surface)"
        (ngSubmit)="send()"
      >
        <input
          class="input-field flex-1"
          style="font-size: 13px; min-height: 34px"
          type="text"
          placeholder="Ask anything…"
          [(ngModel)]="draft"
          name="draft"
          [disabled]="loading"
          autocomplete="off"
        />
        <button
          type="submit"
          class="btn-primary shrink-0"
          style="min-height: 34px; padding: 0 0.75rem; font-size: 12px"
          [disabled]="loading || !draft.trim()"
        >
          Send
        </button>
      </form>
    </div>

    <style>
      .chat-message {
        display: flex;
        margin-bottom: 0.625rem;
      }
      .chat-message--user {
        justify-content: flex-end;
      }
      .chat-message--assistant {
        justify-content: flex-start;
      }
      .chat-bubble {
        max-width: 88%;
        padding: 0.45rem 0.7rem;
        border-radius: 8px;
        font-size: 0.8125rem;
      }
      .chat-bubble--user {
        background: var(--primary);
        color: #fff;
      }
      .chat-bubble--assistant {
        background: var(--surface-2);
        border: 1px solid var(--border);
        color: var(--text);
      }
    </style>
  `,
})
export class AiChatPanelComponent implements OnInit {
  @ViewChild('messagesList') messagesList?: ElementRef<HTMLElement>;

  private readonly ai = inject(AiService);

  messages: ChatMessage[] = [];
  draft = '';
  loading = false;
  error = '';
  statusLabel = '';

  ngOnInit(): void {
    this.ai.status().subscribe({
      next: (s) => {
        this.statusLabel = s.enabled ? `RAG · ${s.indexed_chunks}` : 'local';
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
    this.scrollToBottom();
    this.ai.chat(text).subscribe({
      next: (res) => {
        this.messages.push({ role: 'assistant', text: res.reply, sources: res.sources });
        this.loading = false;
        this.scrollToBottom();
      },
      error: () => {
        this.error = 'Failed to get a response. Please try again.';
        this.loading = false;
      },
    });
  }

  clearMessages(): void {
    this.messages = [];
    this.error = '';
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messagesList?.nativeElement) {
        this.messagesList.nativeElement.scrollTop = this.messagesList.nativeElement.scrollHeight;
      }
    }, 50);
  }
}
