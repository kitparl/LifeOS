import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { lifeosDb } from './lifeos-db';
import { SyncService } from './sync.service';

describe('SyncService', () => {
  let service: SyncService;

  beforeEach(async () => {
    await lifeosDb.syncOperations.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SyncService);
  });

  it('should report offline status when navigator is offline', () => {
    service.online.set(false);
    expect(service.status()).toBe('offline');
  });

  it('should build optimistic create response', () => {
    const res = service.buildOptimisticResponse('POST', { title: 'Test' }) as { id: string; title: string };
    expect(res.title).toBe('Test');
    expect(res.id).toContain('local-');
  });
});

describe('SyncService queue', () => {
  let service: SyncService;

  beforeEach(async () => {
    await lifeosDb.syncOperations.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SyncService);
  });

  it('should enqueue operations', async () => {
    await service.enqueue('POST', `${environment.apiUrl}/tasks`, { title: 'Offline task' });
    await service.refreshPendingCount();
    expect(service.pendingCount()).toBe(1);
  });
});
