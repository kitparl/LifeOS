import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { textToHex, hexToText } from './encodings.util';

@Component({
  selector: 'app-hex-text-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="hex-text"
      title="Hex ↔ Text"
      description="Convert between hexadecimal and plain text."
      icon="hash"
      forwardLabel="Text → Hex"
      backwardLabel="Hex → Text"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to convert to hex…"
    />
  `,
})
export class HexTextToolComponent {
  readonly encode = textToHex;
  readonly decode = hexToText;
}
