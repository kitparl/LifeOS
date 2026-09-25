import { Component, OnInit, inject } from '@angular/core';
import { AiProviderConfigComponent } from './components/ai-provider-config.component';
import { AiSettingsComponent } from './components/ai-settings.component';
import { GithubConfigComponent } from './components/github-config.component';
import { GoogleCalendarConfigComponent } from './components/google-calendar-config.component';
import { TelegramConfigComponent } from './components/telegram-config.component';
import { WordnikConfigComponent } from './components/wordnik-config.component';
import {
  IntegrationConnection,
  IntegrationProvider,
  IntegrationsService,
} from './services/integrations.service';

@Component({
  selector: 'app-integrations-page',
  standalone: true,
  imports: [
    TelegramConfigComponent,
    GithubConfigComponent,
    GoogleCalendarConfigComponent,
    AiProviderConfigComponent,
    AiSettingsComponent,
    WordnikConfigComponent,
  ],
  template: `
    <div class="space-y-4">
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        @for (p of generalProviders; track p.provider) {
          @if (p.provider === 'telegram') {
            <app-telegram-config
              [displayName]="p.display_name"
              [description]="p.description"
              (connectionsChanged)="loadConnections()"
            />
          } @else if (p.provider === 'github') {
            <app-github-config
              [displayName]="p.display_name"
              [description]="p.description"
              (connectionsChanged)="loadConnections()"
            />
          } @else if (p.provider === 'google_calendar') {
            <app-google-calendar-config
              [displayName]="p.display_name"
              [description]="p.description"
              (connectionsChanged)="loadConnections()"
            />
          } @else if (p.provider === 'wordnik') {
            <app-wordnik-config
              [displayName]="p.display_name"
              [description]="p.description"
              (connectionsChanged)="loadConnections()"
            />
          } @else {
            <div class="panel text-sm">
              <p class="font-medium">{{ p.display_name }}</p>
              <p class="text-gray-600 text-xs mt-1">{{ p.description }}</p>
              @if (isConnected(p.provider)) {
                <p class="text-xs text-green-700 mt-2">Connected</p>
                <div class="flex gap-2 mt-2">
                  <button type="button" class="btn-primary text-xs" (click)="sync(p.provider)">Sync</button>
                  <button type="button" class="text-xs" style="color: var(--danger)" (click)="disconnect(p.provider)">Remove</button>
                </div>
              } @else {
                <button type="button" class="btn-primary text-xs mt-2" (click)="connect(p.provider)">Connect</button>
              }
            </div>
          }
        }
      </div>
      @if (lastSyncMsg) {
        <p class="text-sm" style="color: var(--text-muted)">{{ lastSyncMsg }}</p>
      }

      @if (aiProviders.length) {
        <section class="space-y-3 pt-2" aria-labelledby="ai-integration-heading" data-testid="ai-integration-section">
          <div>
            <h2 id="ai-integration-heading" class="font-medium">AI Integration</h2>
            <p class="text-xs" style="color: var(--text-muted)">
              Bring your own API keys for LLM providers, then choose which model each LifeOS feature uses.
            </p>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            @for (p of aiProviders; track p.provider) {
              <app-ai-provider-config
                [provider]="p.provider"
                [displayName]="p.display_name"
                [description]="p.description"
                (connectionsChanged)="onAiProviderChanged()"
              />
            }
          </div>
          <app-ai-settings [providers]="aiProviders" [reloadKey]="aiReloadKey" />
        </section>
      }
    </div>
  `,
})
export class IntegrationsPageComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);
  generalProviders: IntegrationProvider[] = [];
  aiProviders: IntegrationProvider[] = [];
  connections: IntegrationConnection[] = [];
  lastSyncMsg: string | null = null;
  aiReloadKey = 0;

  ngOnInit(): void {
    this.integrations.providers().subscribe({
      next: (providers) => {
        this.generalProviders = providers.filter((p) => p.group !== 'ai');
        this.aiProviders = providers.filter((p) => p.group === 'ai');
      },
    });
    this.loadConnections();
  }

  onAiProviderChanged(): void {
    this.aiReloadKey++;
    this.loadConnections();
  }

  loadConnections(): void {
    this.integrations.list().subscribe({ next: (c) => (this.connections = c) });
  }

  isConnected(provider: string): boolean {
    return this.connections.some((c) => c.provider === provider && c.enabled);
  }

  connId(provider: string): string | undefined {
    return this.connections.find((c) => c.provider === provider)?.id;
  }

  connect(provider: string): void {
    this.integrations.connect(provider).subscribe({ next: () => this.loadConnections() });
  }

  disconnect(provider: string): void {
    const id = this.connId(provider);
    if (!id) return;
    this.integrations.remove(id).subscribe({ next: () => this.loadConnections() });
  }

  sync(provider: string): void {
    const id = this.connId(provider);
    if (!id) return;
    this.integrations.sync(id).subscribe({
      next: (r) => {
        this.lastSyncMsg = r.message;
        this.loadConnections();
      },
    });
  }
}
