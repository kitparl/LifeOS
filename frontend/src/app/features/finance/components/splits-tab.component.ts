import { DatePipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { SplitHistoryItem } from '../../splits/models/split.models';
import { formatInr } from '../../splits/utils/money';

/**
 * Split groups kept in this account's history. They stay here on any device and after
 * the link expires; an expired group opens read-only.
 */
@Component({
  selector: 'app-finance-splits-tab',
  standalone: true,
  imports: [DatePipe, RouterLink],
  template: `
    <div class="space-y-3">
      <div class="flex justify-end">
        <a class="btn-primary text-xs" routerLink="/splits">+ New split</a>
      </div>

      <div class="panel !p-0 overflow-hidden">
        @if (history.length) {
          <ul class="divide-y divide-[var(--xp-border)] text-sm" data-testid="finance-split-history">
            @for (item of history; track item.code) {
              <li class="flex items-center justify-between gap-2 px-3 py-2" data-testid="finance-split-row">
                <div class="min-w-0">
                  <p class="truncate">{{ item.name }}</p>
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{ item.is_open ? 'Open until ' + (item.expires_at | date: 'dd MMM, HH:mm') : 'Link closed · read-only' }}
                  </p>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  @if (item.my_net_paise !== null) {
                    <span class="text-xs" [style.color]="item.my_net_paise < 0 ? 'var(--danger)' : 'var(--text-muted)'">
                      {{ netLabel(item.my_net_paise) }}
                    </span>
                  }
                  <a class="text-xs" [routerLink]="item.url_path">Open</a>
                </div>
              </li>
            }
          </ul>
        } @else {
          <p class="p-3 text-sm" style="color: var(--text-muted)">
            No split groups yet. Groups you create while signed in, or keep from a group page, show up here.
          </p>
        }
      </div>
    </div>
  `,
})
export class SplitsTabComponent {
  @Input() history: SplitHistoryItem[] = [];

  netLabel(netPaise: number): string {
    if (netPaise === 0) return 'Settled';
    return netPaise > 0 ? `You get ${formatInr(netPaise)}` : `You owe ${formatInr(-netPaise)}`;
  }
}
