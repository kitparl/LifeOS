import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { textToAscii, asciiToText } from './encodings.util';

@Component({
  selector: 'app-ascii-text-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="ascii-text"
      title="ASCII ↔ Text"
      description="Convert between character codes and plain text."
      icon="type"
      forwardLabel="Text → Codes"
      backwardLabel="Codes → Text"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to convert to character codes…"
    />
  `,
})
export class AsciiTextToolComponent {
  readonly encode = textToAscii;
  readonly decode = asciiToText;
}
