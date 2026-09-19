import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { parseYaml, stringifyYaml } from '../../shared/yaml.util';
import { parseJsonOrThrow } from '../json/json.util';

@Component({
  selector: 'app-yaml-json-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="yaml-json"
      title="YAML ↔ JSON"
      description="Convert between YAML and JSON."
      icon="file-code"
      forwardLabel="YAML → JSON"
      backwardLabel="JSON → YAML"
      [encodeFn]="toJson"
      [decodeFn]="toYaml"
      placeholder="name: Ada&#10;active: true"
    />
  `,
})
export class YamlJsonToolComponent {
  readonly toJson = (yaml: string): string => JSON.stringify(parseYaml(yaml), null, 2);
  readonly toYaml = (json: string): string => stringifyYaml(parseJsonOrThrow(json));
}
