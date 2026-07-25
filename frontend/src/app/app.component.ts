import { Component, OnInit, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { NavPreferencesService } from './core/services/nav-preferences.service';
import { PwaService } from './core/services/pwa.service';
import { ThemeService } from './core/services/theme.service';
import { SyncService } from './sync/sync.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet />',
  styles: [
    `
      :host {
        display: block;
        height: 100dvh;
        overflow: hidden;
      }
    `,
  ],
})
export class AppComponent implements OnInit {
  private readonly sync = inject(SyncService);
  private readonly theme = inject(ThemeService);
  private readonly pwa = inject(PwaService);
  private readonly navPrefs = inject(NavPreferencesService);
  private readonly auth = inject(AuthService);

  ngOnInit(): void {
    this.theme.init();
    this.navPrefs.init();
    this.pwa.init();
    void this.sync.init();
    const user = this.auth.user();
    if (user?.timezone) {
      this.theme.setTimezone(user.timezone);
    }
  }
}
