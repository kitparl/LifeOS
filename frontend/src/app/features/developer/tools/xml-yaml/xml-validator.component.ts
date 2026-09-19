import { Component } from '@angular/core';
import { XmlActionToolComponent } from './xml-action-tool.component';

@Component({
  selector: 'app-xml-validator-tool',
  standalone: true,
  imports: [XmlActionToolComponent],
  template: `
    <app-xml-action-tool
      toolId="xml-validator"
      title="XML Validator"
      description="Validate XML and get a clear error message."
      mode="validate"
    />
  `,
})
export class XmlValidatorToolComponent {}
