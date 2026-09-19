import { parseYaml, stringifyYaml } from './yaml.util';

describe('yaml.util', () => {
  it('parses a simple mapping', () => {
    expect(parseYaml('name: Ada\nactive: true\ncount: 3')).toEqual({ name: 'Ada', active: true, count: 3 });
  });

  it('parses a sequence of mappings', () => {
    const yaml = 'items:\n  - id: 1\n    name: a\n  - id: 2\n    name: b';
    expect(parseYaml(yaml)).toEqual({ items: [{ id: 1, name: 'a' }, { id: 2, name: 'b' }] });
  });

  it('round-trips JSON -> YAML -> JSON for nested data', () => {
    const original = { name: 'Ada', tags: ['a', 'b'], meta: { active: true, count: 2 } };
    const yaml = stringifyYaml(original);
    expect(parseYaml(yaml)).toEqual(original);
  });

  it('throws a clear error for malformed inline flow values', () => {
    expect(() => parseYaml('key: [1, 2,]')).toThrowError(/Invalid YAML/);
  });
});
