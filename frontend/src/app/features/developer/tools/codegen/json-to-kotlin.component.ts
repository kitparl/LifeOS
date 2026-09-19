import { Component } from '@angular/core';
import { JsonCodeGenToolComponent } from '../../shared/json-codegen-tool.component';
import { generateKotlin } from '../../shared/json-codegen.util';

@Component({
  selector: 'app-json-to-kotlin-tool',
  standalone: true,
  imports: [JsonCodeGenToolComponent],
  template: `
    <app-json-codegen-tool
      toolId="json-to-kotlin"
      title="JSON → Kotlin Data Class"
      description="Generate a Kotlin data class from JSON."
      icon="file-code-2"
      [generateFn]="generateKotlin"
    />
  `,
})
export class JsonToKotlinToolComponent {
  readonly generateKotlin = generateKotlin;
}
