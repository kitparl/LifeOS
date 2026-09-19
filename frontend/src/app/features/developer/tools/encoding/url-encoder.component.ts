import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { urlEncode, urlDecode } from './encodings.util';

@Component({
  selector: 'app-url-encoder-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="url-encoder"
      title="URL Encode / Decode"
      description="Percent-encode or decode a URL or URI component."
      icon="link"
      forwardLabel="Encode"
      backwardLabel="Decode"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to URL-encode…"
    />
  `,
})
export class UrlEncoderToolComponent {
  readonly encode = urlEncode;
  readonly decode = urlDecode;
}
