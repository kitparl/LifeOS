import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WorkspaceTabsComponent } from './workspace-tabs.component';

describe('WorkspaceTabsComponent', () => {
  let fixture: ComponentFixture<WorkspaceTabsComponent>;
  let component: WorkspaceTabsComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkspaceTabsComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(WorkspaceTabsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('emits tab changes and preserves aria-selected', () => {
    const tabs: string[] = [];
    component.tabChange.subscribe((t) => tabs.push(t));
    component.onTabClick('preview');
    expect(tabs).toEqual(['preview']);

    fixture.componentRef.setInput('activeTab', 'preview');
    fixture.detectChanges();
    const preview = fixture.nativeElement.querySelector('#preview-tab') as HTMLButtonElement;
    expect(preview.getAttribute('aria-selected')).toBe('true');
  });

  it('hides preview/output tabs when disabled', () => {
    fixture.componentRef.setInput('showPreview', false);
    fixture.componentRef.setInput('showOutput', false);
    fixture.detectChanges();
    expect(component.getVisibleTabs()).toEqual(['edit']);
  });
});
