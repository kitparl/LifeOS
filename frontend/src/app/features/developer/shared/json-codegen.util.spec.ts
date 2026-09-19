import { generateTypeScript, generatePython, generateGo } from './json-codegen.util';

const SAMPLE = { id: 1, name: 'Ada', active: true, tags: ['a', 'b'], address: { city: 'London' } };

describe('json-codegen.util', () => {
  it('generates a TypeScript interface with nested types', () => {
    const ts = generateTypeScript('Person', SAMPLE, { optionalFields: false, nullableFields: false, useType: false });
    expect(ts).toContain('interface Person {');
    expect(ts).toContain('id: number;');
    expect(ts).toContain('name: string;');
    expect(ts).toContain('tags: string[];');
    expect(ts).toContain('interface Address {');
    expect(ts).toContain('address: Address;');
  });

  it('generates a TypeScript type alias when requested', () => {
    const ts = generateTypeScript('Person', SAMPLE, { optionalFields: false, nullableFields: false, useType: true });
    expect(ts).toContain('type Person = {');
  });

  it('generates a Python dataclass', () => {
    const py = generatePython('Person', SAMPLE, { optionalFields: false, nullableFields: false, useType: false });
    expect(py).toContain('@dataclass');
    expect(py).toContain('class Person:');
    expect(py).toContain('name: str');
  });

  it('generates a Go struct with json tags', () => {
    const go = generateGo('Person', SAMPLE);
    expect(go).toContain('type Person struct {');
    expect(go).toContain('Name string `json:"name"`');
  });
});
