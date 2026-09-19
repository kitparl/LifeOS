import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { xmlToJsObject, jsObjectToXml } from './xml.util';
import { parseJsonOrThrow } from '../json/json.util';

@Component({
  selector: 'app-xml-json-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="xml-json"
      title="XML ↔ JSON"
      description="Convert between XML and JSON. Attributes become @attr keys; mixed text becomes #text."
      icon="file-code"
      forwardLabel="XML → JSON"
      backwardLabel="JSON → XML"
      [encodeFn]="toJson"
      [decodeFn]="toXml"
      placeholder="<root><item id=&quot;1&quot;>Hello</item></root>"
    />
  `,
})
export class XmlJsonToolComponent {
  readonly toJson = (xml: string): string => JSON.stringify(xmlToJsObject(xml), null, 2);
  readonly toXml = (json: string): string => jsObjectToXml(parseJsonOrThrow(json));
}
