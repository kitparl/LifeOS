import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { base32Encode, base32Decode } from './encodings.util';

@Component({
  selector: 'app-base32-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="base32"
      title="Base32 Encode / Decode"
      description="Convert text to and from Base32 (RFC 4648)."
      icon="binary"
      forwardLabel="Encode"
      backwardLabel="Decode"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to Base32-encode…"
    />
  `,
})
export class Base32ToolComponent {
  readonly encode = base32Encode;
  readonly decode = base32Decode;
}
