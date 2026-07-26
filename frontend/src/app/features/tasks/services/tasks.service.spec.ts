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

  it('should list assigned_to_me scope', () => {
    service.list({ scope: 'assigned_to_me' }).subscribe((rows) => {
      expect(rows.length).toBe(0);
    });
    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/tasks` && r.params.get('scope') === 'assigned_to_me');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('should assign a task', () => {
    service.assign('t1', { assignee_username: 'bob' }).subscribe((a) => {
      expect(a.status).toBe('pending');
    });
    const req = http.expectOne(`${environment.apiUrl}/tasks/t1/assign`);
    expect(req.request.method).toBe('POST');
    req.flush({
      id: 'a1',
      task_id: 't1',
      assignee_user_id: 'u2',
      assigned_by_user_id: 'u1',
      status: 'pending',
      reason: null,
      assigned_at: new Date().toISOString(),
      accepted_at: null,
      rejected_at: null,
      cancelled_at: null,
      completed_at: null,
    });
  });
});
