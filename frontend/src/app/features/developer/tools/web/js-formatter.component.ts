import { Component } from '@angular/core';
import { CodeActionToolComponent } from '../../shared/code-action-tool.component';
import { reindentCode, minifyCode } from '../../shared/brace-formatter.util';

@Component({
  selector: 'app-js-formatter-tool',
  standalone: true,
  imports: [CodeActionToolComponent],
  template: `
    <app-code-action-tool
      toolId="js-formatter"
      title="JavaScript Formatter"
      description="Format (re-indent) or minify JavaScript. A lightweight formatter — it fixes indentation by bracket depth rather than fully reflowing the code."
      icon="code"
      [formatFn]="formatFn"
      [minifyFn]="minifyFn"
      placeholder="function greet(name) {&#10;return 'Hello ' + name;&#10;}"
    />
  `,
})
export class JsFormatterToolComponent {
  readonly formatFn = (s: string): string => reindentCode(s);
  readonly minifyFn = minifyCode;
}
