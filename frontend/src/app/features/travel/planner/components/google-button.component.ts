import { AfterViewInit, Component, ElementRef, NgZone, ViewChild, inject, output, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../../../core/services/auth.service';
import { googleId, loadGoogleScript } from '../../../../core/utils/google-identity';

/**
 * Google's own "Continue with Google" button (identity only, the instance's existing OAuth client).
 * Emits the ID token; reports `failed` when Google can't load here (offline, blocked, in-app browser).
 */
@Component({
  selector: 'app-planner-google-button',
  standalone: true,
  template: `
    @if (state() === 'loading') {
      <div class="placeholder" aria-hidden="true"></div>
    }
    <div #slot class="slot" [class.hidden]="state() === 'failed'"></div>
  `,
  styles: [
    `
      :host { display: block; min-height: 44px; }
      .placeholder { height: 44px; border-radius: 999px; background: var(--tp-surface-2); }
      .slot { display: flex; justify-content: center; }
      .hidden { display: none; }
    `,
  ],
})
export class PlannerGoogleButtonComponent implements AfterViewInit {
  private readonly auth = inject(AuthService);
  private readonly zone = inject(NgZone);
  @ViewChild('slot') private slot?: ElementRef<HTMLElement>;

  readonly credential = output<string>();
  readonly failed = output<void>();
  readonly state = signal<'loading' | 'ready' | 'failed'>('loading');

  async ngAfterViewInit(): Promise<void> {
    try {
      const [clientId] = await Promise.all([firstValueFrom(this.auth.getGoogleClientId()), loadGoogleScript()]);
      const el = this.slot?.nativeElement;
      if (!clientId || !el) throw new Error('Google sign-in is not available');
      googleId().initialize({
        client_id: clientId,
        callback: (res) => this.zone.run(() => (res.credential ? this.credential.emit(res.credential) : this.fail())),
      });
      const dark = matchMedia('(prefers-color-scheme: dark)').matches;
      googleId().renderButton(el, {
        type: 'standard',
        theme: dark ? 'filled_black' : 'outline',
        size: 'large',
        text: 'continue_with',
        shape: 'pill',
        width: Math.min(400, el.clientWidth || 320),
      });
      this.state.set('ready');
    } catch {
      this.fail();
    }
  }

  private fail(): void {
    this.state.set('failed');
    this.failed.emit();
  }
}
