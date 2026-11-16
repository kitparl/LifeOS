import { Component, Input, OnChanges } from '@angular/core';
import { chartSegments, formatMetric } from '../health.utils';
import { MetricPoint } from '../models/health.models';

interface Drawn {
  path: string;
  dots: { x: number; y: number }[];
}

const WIDTH = 480;
const HEIGHT = 170;
const PAD_LEFT = 44;
const PAD_RIGHT = 12;
const PAD_TOP = 12;
const PAD_BOTTOM = 22;

/** Daily values with a dashed rolling average. A day without a value breaks the line instead of drawing zero. */
@Component({
  selector: 'app-health-trend-chart',
  standalone: true,
  template: `
    @if (!hasData) {
      <p class="text-sm" style="color: var(--text-muted)" data-testid="health-trend-empty">
        No values in this range yet.
      </p>
    } @else {
      <svg
        [attr.viewBox]="'0 0 ' + width + ' ' + height"
        class="w-full h-auto"
        role="img"
        [attr.aria-label]="summary"
        data-testid="health-trend-chart"
      >
        <line [attr.x1]="padLeft" [attr.x2]="width - padRight" [attr.y1]="padTop" [attr.y2]="padTop" stroke="var(--border)" />
        <line [attr.x1]="padLeft" [attr.x2]="width - padRight" [attr.y1]="height - padBottom" [attr.y2]="height - padBottom" stroke="var(--border)" />
        <text [attr.x]="padLeft - 6" [attr.y]="padTop + 4" text-anchor="end" font-size="10" fill="var(--text-muted)">{{ maxLabel }}</text>
        <text [attr.x]="padLeft - 6" [attr.y]="height - padBottom" text-anchor="end" font-size="10" fill="var(--text-muted)">{{ minLabel }}</text>
        <text [attr.x]="padLeft" [attr.y]="height - 6" font-size="10" fill="var(--text-muted)">{{ firstDay }}</text>
        <text [attr.x]="width - padRight" [attr.y]="height - 6" text-anchor="end" font-size="10" fill="var(--text-muted)">{{ lastDay }}</text>
        @for (seg of rolling; track $index) {
          <path [attr.d]="seg.path" fill="none" stroke="var(--text-muted)" stroke-width="1.5" stroke-dasharray="4 3" />
        }
        @for (seg of daily; track $index) {
          <path [attr.d]="seg.path" fill="none" stroke="var(--primary)" stroke-width="2" />
          @for (d of seg.dots; track $index) {
            <circle [attr.cx]="d.x" [attr.cy]="d.y" r="3" fill="var(--primary)" />
          }
        }
      </svg>
      <p class="text-xs" style="color: var(--text-muted)">
        <span style="color: var(--primary)">━</span> daily value
        <span class="ml-2">╌</span> rolling average
      </p>
    }
  `,
})
export class HealthTrendChartComponent implements OnChanges {
  @Input({ required: true }) points: MetricPoint[] = [];
  @Input() rollingPoints: MetricPoint[] = [];
  @Input() label = '';
  @Input() unit = '';
  @Input() kind: 'int' | 'float' | 'clock' = 'float';

  readonly width = WIDTH;
  readonly height = HEIGHT;
  readonly padLeft = PAD_LEFT;
  readonly padRight = PAD_RIGHT;
  readonly padTop = PAD_TOP;
  readonly padBottom = PAD_BOTTOM;

  hasData = false;
  daily: Drawn[] = [];
  rolling: Drawn[] = [];
  minLabel = '';
  maxLabel = '';
  firstDay = '';
  lastDay = '';
  summary = '';

  ngOnChanges(): void {
    const values = [...this.points, ...this.rollingPoints].flatMap((p) => (p.value == null ? [] : [p.value]));
    this.hasData = this.points.some((p) => p.value != null);
    if (!this.hasData) {
      this.daily = [];
      this.rolling = [];
      return;
    }
    const low = Math.min(...values);
    const high = Math.max(...values);
    const span = high - low || 1;
    const n = Math.max(this.points.length - 1, 1);
    const x = (i: number) => PAD_LEFT + (i / n) * (WIDTH - PAD_LEFT - PAD_RIGHT);
    const y = (v: number) => HEIGHT - PAD_BOTTOM - ((v - low) / span) * (HEIGHT - PAD_TOP - PAD_BOTTOM);
    const draw = (series: MetricPoint[]): Drawn[] =>
      chartSegments(series).map((seg) => ({
        path: seg.map((d, i) => `${i === 0 ? 'M' : 'L'}${x(d.index).toFixed(1)} ${y(d.value).toFixed(1)}`).join(' '),
        dots: seg.length === 1 || this.points.length <= 40 ? seg.map((d) => ({ x: x(d.index), y: y(d.value) })) : [],
      }));
    this.daily = draw(this.points);
    this.rolling = draw(this.rollingPoints).map((s) => ({ ...s, dots: [] }));
    const shape = { key: this.label, unit: this.unit, kind: this.kind };
    this.minLabel = formatMetric(shape, low);
    this.maxLabel = formatMetric(shape, high);
    this.firstDay = this.points[0]?.day ?? '';
    this.lastDay = this.points[this.points.length - 1]?.day ?? '';
    const count = this.points.filter((p) => p.value != null).length;
    this.summary = `${this.label}: ${count} days with a value, from ${this.minLabel} to ${this.maxLabel}`;
  }
}
