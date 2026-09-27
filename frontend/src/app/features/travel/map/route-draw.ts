/**
 * Pure state for "Draw your own trek" (spec §15): add/remove points with undo and redo.
 * Kept free of Leaflet so it is trivially testable; the page renders `points` as a line.
 */
export type LatLngTuple = [number, number];

export class RouteDraw {
  private history: LatLngTuple[][] = [[]];
  private cursor = 0;

  get points(): readonly LatLngTuple[] {
    return this.history[this.cursor];
  }

  get canUndo(): boolean {
    return this.cursor > 0;
  }

  get canRedo(): boolean {
    return this.cursor < this.history.length - 1;
  }

  add(point: LatLngTuple): void {
    this.commit([...this.points, point]);
  }

  removeLast(): void {
    if (this.points.length) this.commit(this.points.slice(0, -1));
  }

  removeAt(index: number): void {
    if (index >= 0 && index < this.points.length) this.commit(this.points.filter((_, i) => i !== index));
  }

  undo(): void {
    if (this.canUndo) this.cursor--;
  }

  redo(): void {
    if (this.canRedo) this.cursor++;
  }

  reset(points: readonly LatLngTuple[] = []): void {
    this.history = [[...points]];
    this.cursor = 0;
  }

  private commit(next: LatLngTuple[]): void {
    // A new edit after undo discards the redo branch, like every editor.
    this.history = [...this.history.slice(0, this.cursor + 1), next];
    this.cursor = this.history.length - 1;
  }
}
