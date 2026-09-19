import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { textToUnicodeEscape, unicodeEscapeToText } from './encodings.util';

@Component({
  selector: 'app-unicode-converter-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="unicode-converter"
      title="Unicode Converter"
      description="Convert text to and from \\uXXXX Unicode escape sequences."
      icon="globe"
      forwardLabel="Text → \\u"
      backwardLabel="\\u → Text"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to escape…"
    />
  `,
})
export class UnicodeConverterToolComponent {
  readonly encode = textToUnicodeEscape;
  readonly decode = unicodeEscapeToText;
}
