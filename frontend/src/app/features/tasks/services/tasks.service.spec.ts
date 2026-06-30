import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { TasksService } from './tasks.service';

describe('TasksService', () => {
  let service: TasksService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(TasksService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should create a task', () => {
    service.create({ title: 'Test task', priority: 'high' }).subscribe((t) => {
      expect(t.title).toBe('Test task');
    });
    const req = http.expectOne(`${environment.apiUrl}/tasks`);
    expect(req.request.method).toBe('POST');
    req.flush({
      id: '1',
      title: 'Test task',
      description: null,
      status: 'pending',
      priority: 'high',
      category: null,
      tags: [],
      due_date: null,
      parent_id: null,
      goal_id: null,
      recurrence: 'none',
      completed_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      subtasks: [],
    });
  });
});
