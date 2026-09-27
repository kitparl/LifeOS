import { Component } from '@angular/core';

/** What Split Bills keeps (and does not). Kept in one place so every screen says the same thing. */
@Component({
  selector: 'app-split-privacy-note',
  standalone: true,
  template: `
    <p class="text-xs" style="color: var(--text-muted)" data-testid="split-privacy-note">
      🔒 LifeOS never touches your money or sees your payments, and we don't collect bank or card details. A UPI id
      you add is shown only to people in this group and is erased when the link closes.
    </p>
  `,
})
export class SplitPrivacyNoteComponent {}
