import { TestBed } from '@angular/core/testing';
import { ThemeIntegrationService } from './theme-integration.service';
import { ThemeService } from '../../../../core/services/theme.service';

describe('ThemeIntegrationService', () => {
  let service: ThemeIntegrationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ThemeIntegrationService);
    TestBed.inject(ThemeService).init();
  });

  it('resolves editor theme tokens from CSS variables', () => {
    const dark = service.getEditorTheme('dark');
    expect(dark.background).toContain('--surface');
    expect(dark.foreground).toContain('--text');
    const vars = service.getThemeVariables('light');
    expect(vars['--editor-background']).toBeTruthy();
  });

  it('emits a resolved light or dark theme', (done) => {
    const sub = service.subscribeToTheme((theme) => {
      expect(theme === 'light' || theme === 'dark').toBeTrue();
      sub.unsubscribe();
      done();
    });
  });
});
