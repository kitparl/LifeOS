import { Component } from '@angular/core';
import { JsonCodeGenToolComponent } from '../../shared/json-codegen-tool.component';
import { generatePython } from '../../shared/json-codegen.util';

@Component({
  selector: 'app-json-to-python-tool',
  standalone: true,
  imports: [JsonCodeGenToolComponent],
  template: `
    <app-json-codegen-tool
      toolId="json-to-python"
      title="JSON → Python Model"
      description="Generate a Python dataclass from JSON."
      icon="file-code-2"
      [generateFn]="generatePython"
    />
  `,
})
export class JsonToPythonToolComponent {
  readonly generatePython = generatePython;
}
