import { Component } from '@angular/core';
import { JsonCodeGenToolComponent } from '../../shared/json-codegen-tool.component';
import { generateGo } from '../../shared/json-codegen.util';

@Component({
  selector: 'app-json-to-go-tool',
  standalone: true,
  imports: [JsonCodeGenToolComponent],
  template: `
    <app-json-codegen-tool
      toolId="json-to-go"
      title="JSON → Go Struct"
      description="Generate a Go struct (with json tags) from JSON."
      icon="file-code-2"
      [generateFn]="generateGo"
    />
  `,
})
export class JsonToGoToolComponent {
  readonly generateGo = generateGo;
}
