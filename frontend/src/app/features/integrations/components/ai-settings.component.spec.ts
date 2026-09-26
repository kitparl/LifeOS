import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { AiUseCase } from '../../ai/models/ai.models';
import { AiSettingsComponent } from './ai-settings.component';

const api = `${environment.apiUrl}/ai`;
const SETTINGS = { default_provider: null, timeout_seconds: 120, max_tokens: 1200, temperature: 0.3 };

function useCase(current: AiUseCase['current']): AiUseCase {
  return {
    use_case: 'reports.ai_briefing',
    display_name: 'Reports & Briefings',
    capability: 'chat',
    options: [
      { provider: 'openai', model: 'gpt-4o-mini', display_name: 'OpenAI · gpt-4o-mini', available: true },
      { provider: 'anthropic', model: 'claude-opus-5-5', display_name: 'Anthropic · Claude', available: true },
    ],
    current,
  };
}

const AUTO = { provider: 'openai', model: 'gpt-4o-mini', updated_at: null, available: true };
const PICKED = { provider: 'anthropic', model: 'claude-opus-5-5', updated_at: '2026-09-25T00:00:00Z', available: true };

describe('AiSettingsComponent', () => {
  let fixture: ComponentFixture<AiSettingsComponent>;
  let component: AiSettingsComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiSettingsComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(AiSettingsComponent);
    component = fixture.componentInstance;
    component.providers = [
      { provider: 'openai', display_name: 'OpenAI', description: '', oauth_required: false, group: 'ai' },
      { provider: 'anthropic', display_name: 'Anthropic', description: '', oauth_required: false, group: 'ai' },
    ];
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function init(current: AiUseCase['current']): void {
    component.ngOnChanges();
    http.expectOne(`${api}/settings`).flush(SETTINGS);
    http.expectOne(`${api}/use-cases`).flush([useCase(current)]);
    fixture.detectChanges();
  }

  it('groups models by provider and labels the automatic choice', () => {
    init(AUTO);
    const uc = component.useCases()[0];
    expect(component.groupsFor(uc).map((g) => g.provider)).toEqual(['openai', 'anthropic']);
    expect(component.automaticLabel(uc)).toBe('Automatic (OpenAI · gpt-4o-mini)');
    expect(component.valueFor(uc)).toBe('');
  });

  it('saves a model as soon as it is selected', () => {
    init(AUTO);
    component.onSelect(component.useCases()[0], component.modelValue('anthropic', 'claude-opus-5-5'));
    const put = http.expectOne(`${api}/use-cases/reports.ai_briefing/model`);
    expect(put.request.method).toBe('PUT');
    expect(put.request.body).toEqual({ provider: 'anthropic', model: 'claude-opus-5-5' });
    put.flush(useCase(PICKED));
    expect(component.valueFor(component.useCases()[0])).toBe(component.modelValue('anthropic', 'claude-opus-5-5'));
    expect(component.message()).toContain('Anthropic · claude-opus-5-5');
  });

  it('returns to automatic by clearing the selection', () => {
    init(PICKED);
    component.onSelect(component.useCases()[0], '');
    const del = http.expectOne(`${api}/use-cases/reports.ai_briefing/model`);
    expect(del.request.method).toBe('DELETE');
    del.flush(useCase(AUTO));
    expect(component.valueFor(component.useCases()[0])).toBe('');
  });

  it('keeps a saved model that is no longer listed visible in its provider group', () => {
    init({ ...PICKED, provider: 'openai', model: 'gpt-9-preview' });
    const uc = component.useCases()[0];
    expect(component.groupsFor(uc)[0].models).toContain('gpt-9-preview');
    expect(component.valueFor(uc)).toBe(component.modelValue('openai', 'gpt-9-preview'));
  });
});
