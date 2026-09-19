import { Component } from '@angular/core';
import { JsonActionToolComponent } from './json-action-tool.component';

@Component({
  selector: 'app-json-formatter-tool',
  standalone: true,
  imports: [JsonActionToolComponent],
  template: `
    <app-json-action-tool
      toolId="json-formatter"
      title="JSON Formatter"
      description="Pretty-print JSON with configurable indentation."
      mode="format"
    />
  `,
})
export class JsonFormatterToolComponent {}
