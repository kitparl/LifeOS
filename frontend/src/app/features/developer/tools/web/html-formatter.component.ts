import { Component } from '@angular/core';
import { CodeActionToolComponent } from '../../shared/code-action-tool.component';
import { formatHtml, minifyHtml } from './html.util';

@Component({
  selector: 'app-html-formatter-tool',
  standalone: true,
  imports: [CodeActionToolComponent],
  template: `
    <app-code-action-tool
      toolId="html-formatter"
      title="HTML Formatter"
      description="Format or minify HTML."
      icon="code"
      [formatFn]="formatFn"
      [minifyFn]="minifyFn"
      placeholder="<div><p>Hello</p></div>"
    />
  `,
})
export class HtmlFormatterToolComponent {
  readonly formatFn = (s: string): string => formatHtml(s);
  readonly minifyFn = minifyHtml;
}
