import { Component } from '@angular/core';

@Component({
  selector: 'app-ai-chat-panel',
  standalone: true,
  template: `
    <div class="panel !p-0 h-full flex flex-col">
      <div class="title-bar rounded-none border-x-0 border-t-0 shrink-0">AI Assistant</div>
      <div class="flex-1 p-3 text-sm text-gray-600 flex flex-col justify-center items-center text-center">
        <p class="font-medium text-[var(--xp-text)]">AI assistant — Phase 2</p>
        <p class="mt-2 text-xs">Personal context-aware coaching will appear here.</p>
      </div>
      <div class="border-t border-[var(--xp-border)] p-2">
        <input
          class="input-field text-xs"
          type="text"
          placeholder="Ask LifeOS… (coming soon)"
          disabled
        />
      </div>
    </div>
  `,
})
export class AiChatPanelComponent {}
