import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { htmlEncode, htmlDecode } from '../encoding/encodings.util';

@Component({
  selector: 'app-html-escape-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="html-escape"
      title="HTML Escape / Unescape"
      description="Escape or unescape HTML special characters."
      icon="code"
      forwardLabel="Escape"
      backwardLabel="Unescape"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to escape…"
    />
  `,
})
export class HtmlEscapeToolComponent {
  readonly encode = htmlEncode;
  readonly decode = htmlDecode;
}
