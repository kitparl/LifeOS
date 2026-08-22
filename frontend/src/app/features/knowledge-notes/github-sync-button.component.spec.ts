import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { GitHubSyncButtonComponent } from './github-sync-button.component';
import { IntegrationsService } from '../integrations/services/integrations.service';

describe('GitHubSyncButtonComponent', () => {
  let fixture: ComponentFixture<GitHubSyncButtonComponent>;
  let component: GitHubSyncButtonComponent;
  let integrations: jasmine.SpyObj<IntegrationsService>;

  beforeEach(async () => {
    integrations = jasmine.createSpyObj('IntegrationsService', ['syncSectionToGitHub']);
    integrations.syncSectionToGitHub.and.returnValue(
      of({ status: 'synced', message: 'Pushed', md_path: 'notes/a/b/c.md', synced_at: null })
    );

    await TestBed.configureTestingModule({
      imports: [GitHubSyncButtonComponent],
      providers: [{ provide: IntegrationsService, useValue: integrations }],
    }).compileComponents();

    fixture = TestBed.createComponent(GitHubSyncButtonComponent);
    component = fixture.componentInstance;
    component.sectionId = 'section-1';
    component.configured = true;
    fixture.detectChanges();
  });

  it('calls sync API once per click', async () => {
    await component.sync();
    expect(integrations.syncSectionToGitHub).toHaveBeenCalledTimes(1);
    expect(integrations.syncSectionToGitHub).toHaveBeenCalledWith('section-1');
  });

  it('ignores second click while syncing', async () => {
    integrations.syncSectionToGitHub.and.returnValue(
      of({ status: 'synced', message: 'Pushed', md_path: null, synced_at: null })
    );
    component.syncing.set(true);
    await component.sync();
    expect(integrations.syncSectionToGitHub).not.toHaveBeenCalled();
  });

  it('runs beforeSync then syncs', async () => {
    const before = jasmine.createSpy('beforeSync').and.resolveTo();
    component.beforeSync = before;
    await component.sync();
    expect(before).toHaveBeenCalled();
    expect(integrations.syncSectionToGitHub).toHaveBeenCalled();
  });

  it('emits syncError on failure', async () => {
    integrations.syncSectionToGitHub.and.returnValue(
      throwError(() => ({ error: { detail: 'GitHub not configured' } }))
    );
    const errors: string[] = [];
    component.syncError.subscribe((msg) => errors.push(msg));
    await component.sync();
    expect(errors).toEqual(['GitHub not configured']);
  });
});
