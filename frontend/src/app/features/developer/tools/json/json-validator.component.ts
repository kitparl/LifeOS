import { Component } from '@angular/core';
import { JsonActionToolComponent } from './json-action-tool.component';

@Component({
  selector: 'app-json-validator-tool',
  standalone: true,
  imports: [JsonActionToolComponent],
  template: `
    <app-json-action-tool
      toolId="json-validator"
      title="JSON Validator"
      description="Validate JSON and get a precise error location."
      mode="validate"
    />
  `,
})
export class JsonValidatorToolComponent {}
