import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { GoalsService } from './goals.service';

describe('GoalsService', () => {
  let service: GoalsService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(GoalsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should create a goal', () => {
    service.create({ title: 'Test goal', category: 'personal' }).subscribe((g) => {
      expect(g.title).toBe('Test goal');
    });
    const req = http.expectOne(`${environment.apiUrl}/goals`);
    expect(req.request.method).toBe('POST');
    req.flush({
      id: '1',
      title: 'Test goal',
      category: 'personal',
      status: 'active',
      progress: 0,
      description: null,
      notes: null,
      target_date: null,
      parent_id: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      archived_at: null,
      milestones: [],
    });
  });
});
