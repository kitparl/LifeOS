import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { escapeStringLiteral, unescapeStringLiteral } from './string-escape.util';

@Component({
  selector: 'app-string-escape-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="string-escape"
      title="String Escape / Unescape"
      description="Escape or unescape a string for use as a code literal (JSON/JS-style escaping)."
      icon="code"
      forwardLabel="Escape"
      backwardLabel="Unescape"
      [encodeFn]="encode"
      [decodeFn]="decode"
      placeholder="Type or paste text to escape…"
    />
  `,
})
export class StringEscapeToolComponent {
  readonly encode = escapeStringLiteral;
  readonly decode = unescapeStringLiteral;
}
