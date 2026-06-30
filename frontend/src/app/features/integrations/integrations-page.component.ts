import { Component, OnInit, inject } from '@angular/core';
import {
  IntegrationConnection,
  IntegrationProvider,
  IntegrationsService,
} from './services/integrations.service';

@Component({
  selector: 'app-integrations-page',
  standalone: true,
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">Integration Hub</h1>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        @for (p of providers; track p.provider) {
          <div class="panel text-sm">
            <p class="font-medium">{{ p.display_name }}</p>
            <p class="text-gray-600 text-xs mt-1">{{ p.description }}</p>
            @if (isConnected(p.provider)) {
              <p class="text-xs text-green-700 mt-2">Connected</p>
              <div class="flex gap-2 mt-2">
                <button type="button" class="btn-primary text-xs" (click)="sync(p.provider)">Sync</button>
                <button type="button" class="text-xs text-red-700" (click)="disconnect(p.provider)">Remove</button>
              </div>
            } @else {
              <button type="button" class="btn-primary text-xs mt-2" (click)="connect(p.provider)">Connect</button>
            }
          </div>
        }
      </div>
      @if (lastSyncMsg) {
        <p class="text-sm text-gray-600">{{ lastSyncMsg }}</p>
      }
    </div>
  `,
})
export class IntegrationsPageComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);
  providers: IntegrationProvider[] = [];
  connections: IntegrationConnection[] = [];
  lastSyncMsg: string | null = null;

  ngOnInit(): void {
    this.integrations.providers().subscribe({ next: (p) => (this.providers = p) });
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
