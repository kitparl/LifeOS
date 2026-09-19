import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { base58Encode, base58Decode } from './encodings.util';

@Component({
  selector: 'app-base58-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="base58"
      title="Base58 Encode / Decode"
      description="Convert text to and from Base58 (Bitcoin alphabet)."
      icon="binary"
      forwardLabel="Encode"
      backwardLabel="Decode"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to Base58-encode…"
    />
  `,
})
export class Base58ToolComponent {
  readonly encode = base58Encode;
  readonly decode = base58Decode;
}
