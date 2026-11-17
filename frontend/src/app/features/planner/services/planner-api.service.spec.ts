import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { PlannerApiService } from './planner-api.service';

describe('PlannerApiService', () => {
  let service: PlannerApiService;
  let http: HttpTestingController;
  const api = `${environment.apiUrl}/planner/nodes`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(PlannerApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('saves content with PUT and the base revision', () => {
    service.saveContent('n1', { content: '<mxfile/>', base_revision: 3 }).subscribe((c) => {
      expect(c.revision).toBe(4);
    });
    const req = http.expectOne(`${api}/n1/content`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ content: '<mxfile/>', base_revision: 3 });
    req.flush({ content: '<mxfile/>', revision: 4 });
  });

  it('updates a node with PATCH', () => {
    service.update('n1', { name: 'Renamed' }).subscribe();
    const req = http.expectOne(`${api}/n1`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ name: 'Renamed' });
    req.flush({});
  });
});
