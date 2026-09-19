import { Component } from '@angular/core';
import { JsonCodeGenToolComponent } from '../../shared/json-codegen-tool.component';
import { generatePydantic } from '../../shared/json-codegen.util';

@Component({
  selector: 'app-json-to-pydantic-tool',
  standalone: true,
  imports: [JsonCodeGenToolComponent],
  template: `
    <app-json-codegen-tool
      toolId="json-to-pydantic"
      title="JSON → Pydantic Model"
      description="Generate a Pydantic model from JSON."
      icon="file-code-2"
      [generateFn]="generatePydantic"
    />
  `,
})
export class JsonToPydanticToolComponent {
  readonly generatePydantic = generatePydantic;
}
