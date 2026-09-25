import { DEV_TOOLS } from './data/dev-tools-registry';
import { DEVELOPER_ROUTES } from './developer.routes';

describe('DEVELOPER_ROUTES', () => {
  const toolPaths = DEVELOPER_ROUTES.map((r) => r.path).filter((p) => p !== '');

  it('mounts the dashboard at the empty path', () => {
    expect(DEVELOPER_ROUTES.some((r) => r.path === '' && r.loadComponent)).toBe(true);
  });

  it('has exactly one route per registered tool', () => {
    expect([...toolPaths].sort()).toEqual(DEV_TOOLS.map((t) => t.route).sort());
  });
});
