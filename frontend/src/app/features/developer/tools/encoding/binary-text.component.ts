import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { textToBinary, binaryToText } from './encodings.util';

@Component({
  selector: 'app-binary-text-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="binary-text"
      title="Binary ↔ Text"
      description="Convert between binary (0/1) and plain text."
      icon="binary"
      forwardLabel="Text → Binary"
      backwardLabel="Binary → Text"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to convert to binary…"
    />
  `,
})
export class BinaryTextToolComponent {
  readonly encode = textToBinary;
  readonly decode = binaryToText;
}
