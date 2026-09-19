import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { parseJsonOrThrow } from './json.util';
import { parseYaml, stringifyYaml } from '../../shared/yaml.util';

@Component({
  selector: 'app-json-to-yaml-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="json-to-yaml"
      title="JSON → YAML"
      description="Convert between JSON and YAML."
      icon="file-code"
      forwardLabel="JSON → YAML"
      backwardLabel="YAML → JSON"
      [encodeFn]="toYaml"
      [decodeFn]="toJson"
      placeholder='{"name": "Ada", "active": true}'
    />
  `,
})
export class JsonToYamlToolComponent {
  readonly toYaml = (json: string): string => stringifyYaml(parseJsonOrThrow(json));
  readonly toJson = (yaml: string): string => JSON.stringify(parseYaml(yaml), null, 2);
}
