import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { parseJsonOrThrow } from '../json/json.util';
import { jsonToToml, tomlToJson } from './toml.util';

@Component({
  selector: 'app-json-toml-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="json-toml"
      title="JSON ↔ TOML"
      description="Convert between JSON and TOML (tables, arrays, and scalars — no dates or inline tables)."
      icon="file-code"
      forwardLabel="JSON → TOML"
      backwardLabel="TOML → JSON"
      [encodeFn]="toToml"
      [decodeFn]="toJson"
      placeholder='{"name": "Ada", "active": true}'
    />
  `,
})
export class JsonTomlToolComponent {
  readonly toToml = (json: string): string => jsonToToml(parseJsonOrThrow(json));
  readonly toJson = (toml: string): string => JSON.stringify(tomlToJson(toml), null, 2);
}
