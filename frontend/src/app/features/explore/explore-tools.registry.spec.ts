import { EXPLORE_HOME_TITLE, EXPLORE_TOOLS, exploreToolRoute, resolveExploreTitle, toAuthenticatedUrl } from './explore-tools.registry';

describe('Explore Tools registry', () => {
  it('registers Developer as a free tool mapped to the authenticated /developer route', () => {
    const developer = EXPLORE_TOOLS.find((t) => t.id === 'developer');
    expect(developer).toBeDefined();
    expect(exploreToolRoute(developer!)).toBe('/explore/developer');
    expect(developer!.authRoute).toBe('/developer');
  });

  it('has unique ids and paths', () => {
    expect(new Set(EXPLORE_TOOLS.map((t) => t.id)).size).toBe(EXPLORE_TOOLS.length);
    expect(new Set(EXPLORE_TOOLS.map((t) => t.path)).size).toBe(EXPLORE_TOOLS.length);
  });

  describe('toAuthenticatedUrl', () => {
    it('maps a tool root', () => {
      expect(toAuthenticatedUrl('/explore/developer')).toBe('/developer');
    });

    it('keeps the sub-path', () => {
      expect(toAuthenticatedUrl('/explore/developer/base64')).toBe('/developer/base64');
    });

    it('keeps the query string and fragment', () => {
      expect(toAuthenticatedUrl('/explore/developer/base64?mode=decode#out')).toBe('/developer/base64?mode=decode#out');
    });

    it('sends the Explore home and unknown tools to the app home', () => {
      expect(toAuthenticatedUrl('/explore')).toBe('/');
      expect(toAuthenticatedUrl('/explore?x=1')).toBe('/');
      expect(toAuthenticatedUrl('/explore/unknown-tool/page')).toBe('/');
    });

    it('does not treat look-alike prefixes as Explore URLs', () => {
      expect(toAuthenticatedUrl('/explorer/developer')).toBe('/');
    });
  });

  describe('resolveExploreTitle', () => {
    it('uses the tool label inside a tool', () => {
      expect(resolveExploreTitle('/explore/developer/base64?x=1')).toBe('Developer');
    });

    it('falls back to the Explore Tools title', () => {
      expect(resolveExploreTitle('/explore')).toBe(EXPLORE_HOME_TITLE);
      expect(resolveExploreTitle('/explore/nope')).toBe(EXPLORE_HOME_TITLE);
    });
  });
});
