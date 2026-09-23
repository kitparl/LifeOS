import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NAV_LUCIDE_ICON_PROVIDERS } from '../../../shared/layout/nav-lucide';
import { DevHistoryEntry } from './dev-history.service';
import { TextTransformToolComponent } from './text-transform-tool.component';

describe('TextTransformToolComponent', () => {
  let fixture: ComponentFixture<TextTransformToolComponent>;
  let component: TextTransformToolComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TextTransformToolComponent],
      providers: [provideRouter([]), ...NAV_LUCIDE_ICON_PROVIDERS],
    });
    fixture = TestBed.createComponent(TextTransformToolComponent);
    component = fixture.componentInstance;
    component.title = 'Test Tool';
    component.description = 'A test tool';
    component.toolId = `test-tool-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    component.encodeFn = (v) => v.toUpperCase();
    component.decodeFn = (v) => v.toLowerCase();
    fixture.detectChanges();
  });

  it('loads a reused entry into the input and recomputes the output', () => {
    const entry: DevHistoryEntry = { toolId: component.toolId, input: 'reused text', output: 'anything', createdAt: new Date().toISOString() };

    component.onReuse(entry);

    expect(component.input()).toBe('reused text');
    expect(component.output()).toBe('REUSED TEXT');
    expect(component.error()).toBeNull();
  });

  it('focuses the main input when reusing an entry', () => {
    const textarea: HTMLTextAreaElement = fixture.nativeElement.querySelector('textarea');
    const focusSpy = spyOn(textarea, 'focus');
    const scrollSpy = spyOn(textarea, 'scrollIntoView');

    component.onReuse({ toolId: component.toolId, input: 'x', output: '', createdAt: new Date().toISOString() });

    expect(focusSpy).toHaveBeenCalled();
    expect(scrollSpy).toHaveBeenCalled();
  });

  it('reuses an entry recorded in backward mode using the current mode', () => {
    component.setMode('backward');
    const entry: DevHistoryEntry = { toolId: component.toolId, input: 'MiXeD', output: 'mixed', createdAt: new Date().toISOString() };

    component.onReuse(entry);

    expect(component.input()).toBe('MiXeD');
    expect(component.output()).toBe('mixed');
  });
});
