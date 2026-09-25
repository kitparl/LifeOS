import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { AiModelsResponse, AiProviderConfigStatus } from '../services/integrations.service';
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
    supports_model_listing: true,
    last_tested_at: null,
    last_test_ok: true,
    models_refreshed_at: null,
    model_count: 2,
    models_refresh_error: null,
    ...overrides,
  };
}

const MODELS: AiModelsResponse = {
  provider: 'openai',
  refreshed_at: null,
  models: [
    { model_id: 'gpt-4o-mini', display_name: 'gpt-4o-mini', capabilities: ['chat'], source: 'fetched' },
    { model_id: 'text-embedding-3-small', display_name: 'e', capabilities: ['embedding'], source: 'fetched' },
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

  it('offers only chat models as the default model', () => {
    init();
    expect(component.defaultModelOptions()).toEqual(['gpt-4o-mini']);
    expect(component.selectedModel).toBe('gpt-4o-mini');
  });

  it('keeps a saved default that is no longer listed and saves it unchanged', () => {
    init(status({ default_model: 'gpt-9-preview' }));
    expect(component.defaultModelOptions()).toContain('gpt-9-preview');

    component.keyInput = '  sk-new  ';
    component.save();
    const put = http.expectOne(`${api}/config`);
    expect(put.request.body).toEqual({
      enabled: true,
      default_model: 'gpt-9-preview',
      api_key: 'sk-new',
      custom_model: true,
      base_url: null,
    });
    put.flush(status({ default_model: 'gpt-9-preview' }));
    http.expectOne(`${api}/models`).flush(MODELS);
    expect(component.message()).toBe('OpenAI settings saved');
    expect(component.keyInput).toBe('');
  });

  it('adds a model id by hand and shows it in the list', () => {
    init();
    component.newModelId = ' gpt-9-preview ';
    component.addModel();
    const add = http.expectOne(`${api}/models`);
    expect(add.request.method).toBe('POST');
    expect(add.request.body).toEqual({ model_id: 'gpt-9-preview', capability: 'chat' });
    add.flush({
      ...MODELS,
      models: [...MODELS.models, { model_id: 'gpt-9-preview', display_name: 'gpt-9-preview', capabilities: ['chat'], source: 'manual' }],
    });
    expect(component.newModelId).toBe('');
    expect(component.defaultModelOptions()).toEqual(['gpt-4o-mini', 'gpt-9-preview']);
  });

  it('tests one model and records the result per model', () => {
    init();
    component.testModel('gpt-4o-mini');
    expect(component.testResults()['gpt-4o-mini']).toBe('pending');
    http.expectOne(`${api}/models/test`).flush({ ok: false, detail: 'OpenAI rejected the request (HTTP 404).', model_id: 'gpt-4o-mini' });
    expect(component.testResults()['gpt-4o-mini']).toEqual({ ok: false, detail: 'OpenAI rejected the request (HTTP 404).' });
  });

  it('filters long lists and reports coded API errors on fetch', () => {
    init();
    component.filter.set('embed');
    expect(component.visibleModels().map((m) => m.model_id)).toEqual(['text-embedding-3-small']);

    component.refreshModels();
    http.expectOne(`${api}/models/refresh`).flush(
      { detail: { code: 'invalid_credential', message: 'Invalid or revoked OpenAI API key.' } },
      { status: 401, statusText: 'Unauthorized' },
    );
    expect(component.ok()).toBeFalse();
    expect(component.message()).toBe('Invalid or revoked OpenAI API key.');
  });
});
