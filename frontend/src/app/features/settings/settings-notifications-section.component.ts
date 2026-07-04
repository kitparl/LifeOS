import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { NotificationsService } from '../notifications/services/notifications.service';

@Component({
  selector: 'app-settings-notifications-section',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="panel !p-0 overflow-hidden">
      <div class="title-bar rounded-none border-x-0 border-t-0">Telegram notifications</div>
      <form class="space-y-2 p-3 text-sm" [formGroup]="settingsForm" (ngSubmit)="saveSettings()">
        <label class="flex items-center gap-2">
          <input type="checkbox" formControlName="telegram_enabled" />
          Enable Telegram notifications
        </label>
        <input class="input-field" formControlName="telegram_chat_id" placeholder="Telegram chat ID" />
        <button type="submit" class="btn-primary text-xs">Save settings</button>
      </form>
    </div>
  `,
})
export class SettingsNotificationsSectionComponent implements OnInit {
  private readonly notificationsService = inject(NotificationsService);
  private readonly fb = inject(FormBuilder);

  settingsForm = this.fb.nonNullable.group({
    telegram_enabled: [false],
    telegram_chat_id: [''],
  });

  ngOnInit(): void {
    this.notificationsService.getSettings().subscribe({
      next: (s) =>
        this.settingsForm.patchValue({
          telegram_enabled: s.telegram_enabled,
          telegram_chat_id: s.telegram_chat_id ?? '',
        }),
    });
  }

  saveSettings(): void {
    const raw = this.settingsForm.getRawValue();
    this.notificationsService
      .updateSettings({
        telegram_enabled: raw.telegram_enabled,
        telegram_chat_id: raw.telegram_chat_id || null,
      })
      .subscribe();
  }
}
