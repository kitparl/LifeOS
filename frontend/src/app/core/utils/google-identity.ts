/**
 * Google Identity Services ("Sign in with Google"), shared by the LifeOS login page and the
 * shared trip planner. Identity only: no extra scopes are ever requested.
 */

export interface GoogleIdApi {
  initialize(config: { client_id: string; callback: (res: { credential?: string }) => void }): void;
  renderButton(parent: HTMLElement, options: Record<string, unknown>): void;
}

/** Minimal typing for the Google Identity Services global we use. */
declare const google: { accounts: { id: GoogleIdApi } };

export const GOOGLE_GSI_SRC = 'https://accounts.google.com/gsi/client';
let googleScriptPromise: Promise<void> | null = null;

/** Load the Google Identity Services script once per page. */
export function loadGoogleScript(): Promise<void> {
  if (!googleScriptPromise) {
    googleScriptPromise = new Promise<void>((resolve, reject) => {
      const script = document.createElement('script');
      script.src = GOOGLE_GSI_SRC;
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => {
        googleScriptPromise = null;
        reject(new Error('Failed to load Google Identity Services'));
      };
      document.head.appendChild(script);
    });
  }
  return googleScriptPromise;
}

/** The loaded `google.accounts.id` API (call after {@link loadGoogleScript} resolves). */
export function googleId(): GoogleIdApi {
  return google.accounts.id;
}
