import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CodeOutputComponent } from './code-output.component';

describe('CodeOutputComponent', () => {
  let fixture: ComponentFixture<CodeOutputComponent>;
  let component: CodeOutputComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CodeOutputComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(CodeOutputComponent);
    component = fixture.componentInstance;

    if (!navigator.clipboard) {
      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: { writeText: () => Promise.resolve() },
      });
    }
    spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.resolve());
  });

  it('renders stdout, errors, and execution time', () => {
    fixture.componentRef.setInput('result', {
      success: false,
      stdout: 'hello',
      stderr: 'boom',
      error: 'failed',
      executionTimeMs: 12,
      exitCode: 1,
    });
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('hello');
    expect(text).toMatch(/boom|failed/);
    expect(text).toContain('12');
    expect(fixture.nativeElement.querySelector('[role="log"]')).toBeTruthy();
  });

  it('copies stdout only, without banners or metadata', async () => {
    fixture.componentRef.setInput('result', {
      success: true,
      stdout: '1',
      stderr: '',
      executionTimeMs: 0,
      exitCode: 0,
    });
    fixture.detectChanges();

    const copyBtn = fixture.nativeElement.querySelector(
      '[aria-label="Copy output to clipboard"]'
    ) as HTMLButtonElement;
    copyBtn.click();
    await fixture.whenStable();

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('1');
    const copied = (navigator.clipboard.writeText as jasmine.Spy).calls.mostRecent().args[0] as string;
    expect(copied).not.toContain('=== Output ===');
    expect(copied).not.toContain('Execution time');
    expect(copied).not.toContain('Exit code');
    expect(copied).not.toContain('Completed successfully');
  });

  it('copies visible stderr and error text without section labels', async () => {
    fixture.componentRef.setInput('result', {
      success: false,
      stdout: 'out',
      stderr: 'err',
      error: 'failed',
      executionTimeMs: 9,
      exitCode: 1,
    });
    fixture.detectChanges();

    await component.copyOutput();
    const copied = (navigator.clipboard.writeText as jasmine.Spy).calls.mostRecent().args[0] as string;
    expect(copied).toBe('out\nerr\nfailed');
    expect(copied).not.toContain('=== Errors ===');
    expect(copied).not.toContain('=== Error ===');
  });

  it('emits cleared when trash is clicked', () => {
    const cleared = jasmine.createSpy('cleared');
    component.cleared.subscribe(cleared);
    fixture.componentRef.setInput('result', {
      success: true,
      stdout: '1',
      stderr: '',
    });
    fixture.detectChanges();

    const clearBtn = fixture.nativeElement.querySelector(
      '[aria-label="Clear output"]'
    ) as HTMLButtonElement;
    clearBtn.click();
    expect(cleared).toHaveBeenCalled();
  });
});
