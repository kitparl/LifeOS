import { TestBed } from '@angular/core/testing';
import { LanguageRegistryService } from './language-registry.service';

describe('LanguageRegistryService', () => {
  let service: LanguageRegistryService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LanguageRegistryService);
  });

  it('registers built-in languages and looks them up by id and extension', () => {
    expect(service.getLanguage('javascript')?.name).toBe('JavaScript');
    expect(service.getLanguageByExtension('.py')?.id).toBe('python');
    expect(service.getAllLanguages().length).toBeGreaterThanOrEqual(18);
  });

  it('reports execution support', () => {
    expect(service.isExecutionSupported('javascript')).toBeTrue();
    expect(service.isExecutionSupported('markdown')).toBeFalse();
    expect(service.getExecutionType('sql')).toBe('wasm');
    expect(service.getExecutableLanguages().some((l) => l.id === 'python')).toBeTrue();
  });

  it('allows registering a custom language and searching', () => {
    service.registerLanguage({
      id: 'kotlin',
      name: 'Kotlin',
      extension: '.kt',
      supportsExecution: false,
      executionType: 'none',
    });
    expect(service.getLanguage('kotlin')?.extension).toBe('.kt');
    expect(service.searchLanguages('kot').length).toBe(1);
  });
});
