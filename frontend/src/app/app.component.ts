import { Component, OnInit, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { PwaService } from './core/services/pwa.service';
import { ThemeService } from './core/services/theme.service';
import { SyncService } from './sync/sync.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class AppComponent implements OnInit {
  private readonly sync = inject(SyncService);
  private readonly theme = inject(ThemeService);
  private readonly pwa = inject(PwaService);

  ngOnInit(): void {
    this.theme.init();
    this.pwa.init();
    void this.sync.init();
  }
}
