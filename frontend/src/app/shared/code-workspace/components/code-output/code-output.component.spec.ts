import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CodeOutputComponent } from './code-output.component';

describe('CodeOutputComponent', () => {
  let fixture: ComponentFixture<CodeOutputComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CodeOutputComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(CodeOutputComponent);
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
});
