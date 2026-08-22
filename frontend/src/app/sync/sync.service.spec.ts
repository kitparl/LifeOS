import { HttpClient, HttpErrorResponse, HttpHeaders, HttpResponse, provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import { lifeosDb } from './lifeos-db';
import { SyncService } from './sync.service';

describe('SyncService', () => {
  let service: SyncService;
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await lifeosDb.syncOperations.clear();
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), SyncService],
    });
    service = TestBed.inject(SyncService);
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    service.online.set(true);
  });

  afterEach(() => {
    httpMock.verify();
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

  it('should enqueue operations', async () => {
    await service.enqueue('POST', `${environment.apiUrl}/tasks`, { title: 'Offline task' });
    await service.refreshPendingCount();
    expect(service.pendingCount()).toBe(1);
    expect(service.pendingSummary()).toContain('POST');
  });

  it('should drop non-retryable 404 operations during flush', async () => {
    const url = `${environment.apiUrl}/tasks/local-123`;
    await service.enqueue('PATCH', url, { title: 'Updated' });

    spyOn(http, 'request').and.returnValue(
      throwError(
        () => new HttpErrorResponse({ status: 404, statusText: 'Not Found', url }),
      ),
    );

    await service.flush();

    expect(service.pendingCount()).toBe(0);
    expect(service.status()).toBe('synced');
  });

  it('should clear queue after successful replay', async () => {
    const url = `${environment.apiUrl}/preferences/nav`;
    await service.enqueue('PUT', url, { value: { visible: ['dashboard'] } });

    spyOn(http, 'request').and.returnValue(
      of(new HttpResponse({ status: 200, headers: new HttpHeaders({ 'X-Sync-Replay': '1' }) })),
    );

    await service.flush();

    expect(service.pendingCount()).toBe(0);
    expect(service.status()).toBe('synced');
  });
});
