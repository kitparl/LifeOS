import { Component } from '@angular/core';
import { AiChatPanelComponent } from './ai-chat-panel.component';

@Component({
  selector: 'app-assistant-page',
  standalone: true,
  imports: [AiChatPanelComponent],
  template: `
    <!-- Desktop: embedded chat page filling the main column -->
    <div class="assistant-page assistant-page--desktop">
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
    :host {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
      height: 100%;
      overflow: hidden;
    }
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
      margin: 1.25rem;
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
        flex: 1;
        min-height: 0;
        height: 100%;
        overflow: hidden;
      }
    }
  `],
})
export class AssistantPageComponent {}
