import { Component } from '@angular/core';
import { AiChatPanelComponent } from '../dashboard/widgets/ai-chat-panel.component';

@Component({
  selector: 'app-assistant-page',
  standalone: true,
  imports: [AiChatPanelComponent],
  template: `
    <div class="flex h-[min(72dvh,40rem)] min-h-0 flex-col">
      <h1 class="mb-3 text-lg font-semibold">AI Assistant</h1>
      <div class="min-h-0 flex-1">
        <app-ai-chat-panel />
      </div>
    </div>
  `,
})
export class AssistantPageComponent {}
