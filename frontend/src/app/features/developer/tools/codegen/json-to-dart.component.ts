import { Component } from '@angular/core';
import { JsonCodeGenToolComponent } from '../../shared/json-codegen-tool.component';
import { generateDart } from '../../shared/json-codegen.util';

@Component({
  selector: 'app-json-to-dart-tool',
  standalone: true,
  imports: [JsonCodeGenToolComponent],
  template: `
    <app-json-codegen-tool
      toolId="json-to-dart"
      title="JSON → Dart Model"
      description="Generate a Dart model class (with fromJson) from JSON."
      icon="file-code-2"
      [generateFn]="generateDart"
    />
  `,
})
export class JsonToDartToolComponent {
  readonly generateDart = generateDart;
}
