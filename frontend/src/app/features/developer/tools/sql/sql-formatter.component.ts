import { Component } from '@angular/core';
import { CodeActionToolComponent } from '../../shared/code-action-tool.component';
import { formatSql, minifySql } from './sql.util';

@Component({
  selector: 'app-sql-formatter-tool',
  standalone: true,
  imports: [CodeActionToolComponent],
  template: `
    <app-code-action-tool
      toolId="sql-formatter"
      title="SQL Formatter"
      description="Format or minify a SQL statement — no database connection. A lightweight keyword-based formatter, not a full SQL parser."
      icon="database"
      [formatFn]="formatFn"
      [minifyFn]="minifyFn"
      placeholder="select id, name from users where active = true order by name"
    />
  `,
})
export class SqlFormatterToolComponent {
  readonly formatFn = formatSql;
  readonly minifyFn = minifySql;
}
