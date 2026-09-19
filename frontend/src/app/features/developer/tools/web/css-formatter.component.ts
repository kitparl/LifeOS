import { Component } from '@angular/core';
import { CodeActionToolComponent } from '../../shared/code-action-tool.component';
import { formatCss, minifyCss } from './css.util';

@Component({
  selector: 'app-css-formatter-tool',
  standalone: true,
  imports: [CodeActionToolComponent],
  template: `
    <app-code-action-tool
      toolId="css-formatter"
      title="CSS Formatter"
      description="Format or minify CSS."
      icon="code"
      [formatFn]="formatFn"
      [minifyFn]="minifyFn"
      placeholder=".btn { color: red; padding: 4px; }"
    />
  `,
})
export class CssFormatterToolComponent {
  readonly formatFn = (s: string): string => formatCss(s);
  readonly minifyFn = minifyCss;
}
