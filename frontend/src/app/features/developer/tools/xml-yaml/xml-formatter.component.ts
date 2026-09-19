import { Component } from '@angular/core';
import { XmlActionToolComponent } from './xml-action-tool.component';

@Component({
  selector: 'app-xml-formatter-tool',
  standalone: true,
  imports: [XmlActionToolComponent],
  template: `
    <app-xml-action-tool
      toolId="xml-formatter"
      title="XML Formatter"
      description="Pretty-print XML with configurable indentation."
      mode="format"
    />
  `,
})
export class XmlFormatterToolComponent {}
