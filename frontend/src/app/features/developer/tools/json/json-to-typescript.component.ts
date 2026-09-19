import { Component } from '@angular/core';
import { JsonCodeGenToolComponent } from '../../shared/json-codegen-tool.component';
import { generateTypeScript } from '../../shared/json-codegen.util';

@Component({
  selector: 'app-json-to-typescript-tool',
  standalone: true,
  imports: [JsonCodeGenToolComponent],
  template: `
    <app-json-codegen-tool
      toolId="json-to-typescript"
      title="JSON → TypeScript"
      description="Generate a TypeScript interface or type from JSON."
      icon="file-code-2"
      [generateFn]="generateTypeScript"
      [showUseType]="true"
    />
  `,
})
export class JsonToTypeScriptToolComponent {
  readonly generateTypeScript = generateTypeScript;
}
