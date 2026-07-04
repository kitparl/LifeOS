import { Component } from '@angular/core';
import { AiChatPanelComponent } from '../dashboard/widgets/ai-chat-panel.component';

@Component({
  selector: 'app-assistant-page',
  standalone: true,
  imports: [AiChatPanelComponent],
  template: `
    <!-- Desktop: embedded chat page -->
    <div class="assistant-page assistant-page--desktop">
      <h1 class="mb-3 text-lg font-semibold">AI Assistant</h1>
      <div class="assistant-page__panel">
        <app-ai-chat-panel />
      </div>
    </div>

    <!-- Mobile: full-viewport chat when /assistant is opened directly -->
    <div class="assistant-page assistant-page--mobile">
      <app-ai-chat-panel />
    </div>
  `,
  styles: [`
    .assistant-page--mobile {
      display: flex;
      flex-direction: column;
      position: fixed;
      left: 0;
      right: 0;
      top: 48px;
      bottom: calc(52px + env(safe-area-inset-bottom, 0px));
      background: var(--page-bg);
      z-index: 5;
      overflow: hidden;
    }
    .assistant-page--desktop {
      display: none;
    }
    .assistant-page__panel {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
      height: min(72dvh, 40rem);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      overflow: hidden;
      background: var(--surface);
    }
    @media (min-width: 1024px) {
      .assistant-page--mobile {
        display: none;
      }
      .assistant-page--desktop {
        display: flex;
        flex-direction: column;
        min-height: 0;
      }
    }
  `],
})
export class AssistantPageComponent {}
