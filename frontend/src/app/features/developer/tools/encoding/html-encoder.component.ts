import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { htmlEncode, htmlDecode } from './encodings.util';

@Component({
  selector: 'app-html-encoder-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="html-encoder"
      title="HTML Encode / Decode"
      description="Convert text to and from HTML entities."
      icon="code"
      forwardLabel="Encode"
      backwardLabel="Decode"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to HTML-encode…"
    />
  `,
})
export class HtmlEncoderToolComponent {
  readonly encode = htmlEncode;
  readonly decode = htmlDecode;
}
