import { RouteDraw } from './route-draw';

describe('RouteDraw', () => {
  it('adds, undoes and redoes points', () => {
    const draw = new RouteDraw();
    expect(draw.canUndo).toBeFalse();
    draw.add([1, 1]);
    draw.add([2, 2]);
    draw.undo();
    expect(draw.points).toEqual([[1, 1]]);
    expect(draw.canRedo).toBeTrue();
    draw.redo();
    expect(draw.points).toEqual([
      [1, 1],
      [2, 2],
    ]);
  });

  it('drops the redo branch after a new edit', () => {
    const draw = new RouteDraw();
    draw.add([1, 1]);
    draw.add([2, 2]);
    draw.undo();
    draw.add([3, 3]);
    expect(draw.canRedo).toBeFalse();
    expect(draw.points).toEqual([
      [1, 1],
      [3, 3],
    ]);
  });

  it('removes points and can undo a removal', () => {
    const draw = new RouteDraw();
    draw.add([1, 1]);
    draw.add([2, 2]);
    draw.add([3, 3]);
    draw.removeAt(1);
    expect(draw.points).toEqual([
      [1, 1],
      [3, 3],
    ]);
    draw.removeLast();
    draw.undo();
    draw.undo();
    expect(draw.points.length).toBe(3);
  });

  it('reset starts a fresh history', () => {
    const draw = new RouteDraw();
    draw.add([1, 1]);
    draw.reset([[5, 5]]);
    expect(draw.points).toEqual([[5, 5]]);
    expect(draw.canUndo).toBeFalse();
    draw.removeLast();
    draw.removeLast(); // no-op on empty
    expect(draw.points).toEqual([]);
  });
});
