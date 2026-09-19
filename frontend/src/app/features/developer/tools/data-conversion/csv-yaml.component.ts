import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { csvToJson, jsonToCsv } from '../json/csv.util';
import { parseYaml, stringifyYaml } from '../../shared/yaml.util';

@Component({
  selector: 'app-csv-yaml-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="csv-yaml"
      title="CSV ↔ YAML"
      description="Convert between CSV (first row = headers) and YAML."
      icon="table-properties"
      forwardLabel="CSV → YAML"
      backwardLabel="YAML → CSV"
      [encodeFn]="toYaml"
      [decodeFn]="toCsv"
      placeholder="name,age&#10;Ada,36"
    />
  `,
})
export class CsvYamlToolComponent {
  readonly toYaml = (csv: string): string => stringifyYaml(csvToJson(csv));
  readonly toCsv = (yaml: string): string => jsonToCsv(parseYaml(yaml));
}
