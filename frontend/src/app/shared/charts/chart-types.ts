export interface ChartPoint {
  label: string;
  value: number;
}

export interface HeatmapCell {
  date: string;
  value: number;
  completed?: boolean;
}
