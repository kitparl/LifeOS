import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { base64Encode, base64Decode } from './encodings.util';

@Component({
  selector: 'app-base64-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="base64"
      title="Base64 Encode / Decode"
      description="Convert text to and from Base64. UTF-8 safe."
      icon="binary"
      forwardLabel="Encode"
      backwardLabel="Decode"
      [encodeFn]="encode"
      [decodeFn]="decode"
      [detectJson]="true"
      placeholder="Type or paste text to Base64-encode…"
    />
  `,
})
export class Base64ToolComponent {
  readonly encode = base64Encode;
  readonly decode = base64Decode;
}
