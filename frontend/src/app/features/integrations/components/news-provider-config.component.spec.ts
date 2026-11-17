import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { IntegrationsService, NewsProviderConfigStatus } from '../services/integrations.service';
import { NewsProviderConfigComponent } from './news-provider-config.component';

const status = (over: Partial<NewsProviderConfigStatus> = {}): NewsProviderConfigStatus => ({
  connection_id: 'c1',
  enabled: true,
  status: 'connected',
  configured: true,
  keys: [
    { id: 'k1', masked: '****1234', state: 'quota_exhausted', retry_at: '2999-01-01T00:00:00Z' },
    { id: 'k2', masked: '****5678', state: 'ok', retry_at: null },
  ],
  last_tested_at: null,
  last_test_ok: null,
  ...over,
});

describe('NewsProviderConfigComponent', () => {
  let integrations: jasmine.SpyObj<IntegrationsService>;

  function create() {
    const fixture = TestBed.createComponent(NewsProviderConfigComponent);
    fixture.componentInstance.provider = 'freenewsapi';
    fixture.componentInstance.displayName = 'FreeNewsAPI';
    fixture.componentInstance.description = 'Live news feed';
    fixture.detectChanges();
    return fixture;
  }

  beforeEach(() => {
    integrations = jasmine.createSpyObj('IntegrationsService', [
      'getNewsProvider',
      'saveNewsProviderConfig',
      'removeNewsProviderKey',
      'testNewsProvider',
    ]);
    integrations.getNewsProvider.and.returnValue(of(status()));
    TestBed.configureTestingModule({
      imports: [NewsProviderConfigComponent],
      providers: [{ provide: IntegrationsService, useValue: integrations }],
    });
  });

  it('lists the keys in order with their state', () => {
    const fixture = create();
    const rows = fixture.nativeElement.querySelectorAll('[data-testid="news-provider-keys"] li');
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain('****1234');
    expect(rows[0].textContent).toContain('Quota used up');
    expect(rows[1].textContent).toContain('Active');
  });

  it('adds a key and shows the updated list', () => {
    const updated = status({ keys: [...status().keys, { id: 'k3', masked: '****9012', state: 'ok', retry_at: null }] });
    integrations.saveNewsProviderConfig.and.returnValue(of(updated));
    const fixture = create();
    fixture.componentInstance.keyInput = ' new-key-9012 ';
    fixture.componentInstance.addKey();
    expect(integrations.saveNewsProviderConfig).toHaveBeenCalledWith('freenewsapi', { api_key: 'new-key-9012' });
    expect(fixture.componentInstance.config()?.keys.length).toBe(3);
    expect(fixture.componentInstance.keyInput).toBe('');
  });

  it('refuses a blank key without calling the API', () => {
    const fixture = create();
    fixture.componentInstance.keyInput = '   ';
    fixture.componentInstance.addKey();
    expect(integrations.saveNewsProviderConfig).not.toHaveBeenCalled();
    expect(fixture.componentInstance.message()).toBe('Paste an API key first');
  });

  it('removes a single key by id', () => {
    integrations.removeNewsProviderKey.and.returnValue(of(status({ keys: [status().keys[1]] })));
    const fixture = create();
    fixture.componentInstance.removeKey(status().keys[0]);
    expect(integrations.removeNewsProviderKey).toHaveBeenCalledWith('freenewsapi', 'k1');
    expect(fixture.componentInstance.config()?.keys.map((k) => k.id)).toEqual(['k2']);
  });
});
