import { Component, output } from '@angular/core';

/** Stands in for Google's button in specs (no Google script is ever loaded in tests). */
@Component({
  selector: 'app-planner-google-button',
  standalone: true,
  template: '<button type="button" data-testid="google-stub" (click)="credential.emit(\'google-id-token\')">Continue with Google</button>',
})
export class GoogleButtonStubComponent {
  readonly credential = output<string>();
  readonly failed = output<void>();
}
