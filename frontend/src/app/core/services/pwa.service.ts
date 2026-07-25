import { Injectable, inject, signal } from '@angular/core';
import { SwUpdate, VersionReadyEvent } from '@angular/service-worker';
import { filter } from 'rxjs';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

/** How often to poll for a new build while the PWA stays open. */
const UPDATE_CHECK_INTERVAL_MS = 30 * 60 * 1000;

@Injectable({ providedIn: 'root' })
export class PwaService {
  private readonly swUpdate = inject(SwUpdate);
  private deferredPrompt: BeforeInstallPromptEvent | null = null;
  private applyingUpdate = false;

  readonly installAvailable = signal(false);
  readonly updateAvailable = signal(false);

  init(): void {
    window.addEventListener('beforeinstallprompt', this.handleBeforeInstallPrompt);
    if (!this.swUpdate.isEnabled) {
      return;
    }

    this.swUpdate.versionUpdates
      .pipe(filter((event): event is VersionReadyEvent => event.type === 'VERSION_READY'))
      .subscribe(() => {
        this.updateAvailable.set(true);
        void this.applyUpdate();
      });

    document.addEventListener('visibilitychange', this.handleVisibilityChange);
    window.addEventListener('focus', this.handleFocus);

    void this.checkForUpdate();
    setInterval(() => void this.checkForUpdate(), UPDATE_CHECK_INTERVAL_MS);
  }

  async promptInstall(): Promise<void> {
    if (!this.deferredPrompt) {
      return;
    }
    await this.deferredPrompt.prompt();
    await this.deferredPrompt.userChoice;
    this.deferredPrompt = null;
    this.installAvailable.set(false);
  }

  async applyUpdate(): Promise<void> {
    if (!this.swUpdate.isEnabled || this.applyingUpdate) {
      return;
    }
    this.applyingUpdate = true;
    try {
      await this.swUpdate.activateUpdate();
      window.location.reload();
    } catch {
      this.applyingUpdate = false;
    }
  }

  /** Returns true when a new version was found (the app reloads itself in that case). */
  async checkForUpdate(): Promise<boolean> {
    if (!this.swUpdate.isEnabled || document.visibilityState === 'hidden') {
      return false;
    }
    try {
      return await this.swUpdate.checkForUpdate();
    } catch {
      // Network / SW errors are non-fatal; next focus/interval will retry.
      return false;
    }
  }

  /**
   * Last-resort refresh for installed web apps (notably on iOS, where the app has
   * no reload control and its own isolated storage): drop the service worker and
   * every cached bundle, then load the current build from the network.
   */
  async hardRefresh(): Promise<void> {
    if (this.applyingUpdate) {
      return;
    }
    this.applyingUpdate = true;
    try {
      if ('caches' in window) {
        const keys = await caches.keys();
        await Promise.all(keys.map((key) => caches.delete(key)));
      }
      if ('serviceWorker' in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        await Promise.all(registrations.map((registration) => registration.unregister()));
      }
    } catch {
      // Fall through to the reload regardless — a plain reload may still help.
    }
    // Cache-busting query so iOS cannot serve index.html from its HTTP cache.
    window.location.replace(`${window.location.pathname}?reload=${Date.now()}`);
  }

  readonly handleBeforeInstallPrompt = (event: Event): void => {
    event.preventDefault();
    this.deferredPrompt = event as BeforeInstallPromptEvent;
    this.installAvailable.set(true);
  };

  private readonly handleVisibilityChange = (): void => {
    if (document.visibilityState === 'visible') {
      void this.checkForUpdate();
    }
  };

  private readonly handleFocus = (): void => {
    void this.checkForUpdate();
  };
}
