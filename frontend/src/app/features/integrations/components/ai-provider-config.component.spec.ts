import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { AiProviderConfigStatus } from '../services/integrations.service';
import { AiProviderConfigComponent } from './ai-provider-config.component';

const api = `${environment.apiUrl}/integrations/ai/openai`;

function status(overrides: Partial<AiProviderConfigStatus> = {}): AiProviderConfigStatus {
  return {
    connection_id: 'c1',
    provider: 'openai',
    display_name: 'OpenAI',
    enabled: true,
    status: 'connected',
    configured: true,
    api_key_masked: '****4321',
    default_model: 'gpt-4o-mini',
    base_url: null,
    supports_base_url: true,
    last_tested_at: null,
    last_test_ok: true,
    models_refreshed_at: null,
    model_count: 2,
    models_refresh_error: null,
    ...overrides,
  };
}

const MODELS = {
  provider: 'openai',
  refreshed_at: null,
  models: [
    { model_id: 'gpt-4o-mini', display_name: 'gpt-4o-mini', capabilities: ['chat'] },
    { model_id: 'text-embedding-3-small', display_name: 'text-embedding-3-small', capabilities: ['embedding'] },
  ],
};

describe('AiProviderConfigComponent', () => {
  let fixture: ComponentFixture<AiProviderConfigComponent>;
  let component: AiProviderConfigComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiProviderConfigComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(AiProviderConfigComponent);
    component = fixture.componentInstance;
    component.provider = 'openai';
    component.displayName = 'OpenAI';
    component.description = 'GPT models';
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function init(s: AiProviderConfigStatus = status()): void {
    fixture.detectChanges();
    http.expectOne(`${api}/config`).flush(s);
    http.expectOne(`${api}/models`).flush(MODELS);
    fixture.detectChanges();
  }

  it('offers only chat models from the cached catalog', () => {
    init();
    expect(component.chatModels().map((m) => m.model_id)).toEqual(['gpt-4o-mini']);
    expect(component.selectedModel).toBe('gpt-4o-mini');
    expect(component.useCustomModel).toBeFalse();
  });

  it('shows a saved model missing from the catalog as a custom id and saves it as custom', () => {
    init(status({ default_model: 'gpt-9-preview' }));
    expect(component.useCustomModel).toBeTrue();
    expect(component.customModel).toBe('gpt-9-preview');

    component.keyInput = '  sk-new  ';
    component.save();
    const put = http.expectOne(`${api}/config`);
    expect(put.request.method).toBe('PUT');
    expect(put.request.body).toEqual({
      enabled: true,
      api_key: 'sk-new',
      default_model: 'gpt-9-preview',
      custom_model: true,
      base_url: null,
    });
    put.flush(status({ default_model: 'gpt-9-preview' }));
    http.expectOne(`${api}/models`).flush(MODELS);
    expect(component.message()).toBe('OpenAI settings saved');
    expect(component.keyInput).toBe('');
  });

  it('refreshes models and reports API errors from the coded detail', () => {
    init();
    component.refreshModels();
    http.expectOne(`${api}/models/refresh`).flush(
      { detail: { code: 'invalid_credential', message: 'Invalid or revoked OpenAI API key.' } },
      { status: 401, statusText: 'Unauthorized' },
    );
    expect(component.ok()).toBeFalse();
    expect(component.message()).toBe('Invalid or revoked OpenAI API key.');
  });
});
