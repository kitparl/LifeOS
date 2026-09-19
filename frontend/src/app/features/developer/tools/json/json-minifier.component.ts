import { Component } from '@angular/core';
import { JsonActionToolComponent } from './json-action-tool.component';

@Component({
  selector: 'app-json-minifier-tool',
  standalone: true,
  imports: [JsonActionToolComponent],
  template: `
    <app-json-action-tool
      toolId="json-minifier"
      title="JSON Minifier"
      description="Minify JSON by removing all non-essential whitespace."
      mode="minify"
    />
  `,
})
export class JsonMinifierToolComponent {}
