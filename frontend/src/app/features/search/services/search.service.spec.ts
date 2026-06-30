import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { SearchService } from './search.service';

describe('SearchService', () => {
  let service: SearchService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SearchService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should search with query params', () => {
    service.search('habit', 10).subscribe((res) => {
      expect(res.query).toBe('habit');
      expect(res.total).toBe(1);
    });
    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/search`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('q')).toBe('habit');
    expect(req.request.params.get('limit')).toBe('10');
    req.flush({
      query: 'habit',
      total: 1,
      results: [
        {
          module: 'habits',
          entity_type: 'habit',
          id: '1',
          title: 'Morning run',
          subtitle: null,
          route: '/habits/1',
        },
      ],
    });
  });
});
