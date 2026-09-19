import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { csvToJson, jsonToCsv } from './csv.util';
import { parseJsonOrThrow } from './json.util';

@Component({
  selector: 'app-csv-json-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="csv-json"
      title="CSV ↔ JSON"
      description="Convert between CSV (first row = headers) and a JSON array of objects."
      icon="table-properties"
      forwardLabel="CSV → JSON"
      backwardLabel="JSON → CSV"
      [encodeFn]="toJson"
      [decodeFn]="toCsv"
      placeholder="name,age&#10;Ada,36&#10;Alan,41"
    />
  `,
})
export class CsvJsonToolComponent {
  readonly toJson = (csv: string): string => JSON.stringify(csvToJson(csv), null, 2);
  readonly toCsv = (json: string): string => jsonToCsv(parseJsonOrThrow(json));
}
