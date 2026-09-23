import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DevHistoryEntry, DevHistoryService } from './dev-history.service';
import { DevHistoryPanelComponent } from './dev-history-panel.component';

describe('DevHistoryPanelComponent', () => {
  let fixture: ComponentFixture<DevHistoryPanelComponent>;
  let component: DevHistoryPanelComponent;
  let historyService: DevHistoryService;
  // Unique per test: IndexedDB persists across specs within the same browser
  // session, so a shared toolId would accumulate entries from earlier tests.
  let toolId: string;
  const longInput = 'x'.repeat(300);
  const longOutput = 'y'.repeat(300);

  beforeEach(async () => {
    toolId = `test-tool-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    TestBed.configureTestingModule({ imports: [DevHistoryPanelComponent] });
    historyService = TestBed.inject(DevHistoryService);
    fixture = TestBed.createComponent(DevHistoryPanelComponent);
    component = fixture.componentInstance;
    component.toolId = toolId;
    // ngOnInit (via detectChanges) registers the cached signal for this toolId
    // FIRST — addEntry's own internal refresh only updates a signal that's
    // already in the service's cache, so it must run after this, not before.
    fixture.detectChanges();
    await historyService.addEntry(toolId, longInput, longOutput);
    // Expand the "History (n)" section so the row (and its buttons) render.
    component.expanded.set(true);
    fixture.detectChanges();
  });

  function entryRow(): HTMLLIElement {
    return fixture.nativeElement.querySelector('li');
  }

  function findButton(text: string): HTMLButtonElement {
    const buttons: HTMLButtonElement[] = Array.from(entryRow().querySelectorAll('button'));
    const match = buttons.find((b) => b.textContent?.trim() === text);
    if (!match) throw new Error(`No button with text "${text}"`);
    return match;
  }

  it('keeps the summary lines truncated', () => {
    const [inLine, outLine]: HTMLParagraphElement[] = Array.from(entryRow().querySelectorAll('p'));
    expect(inLine.className).toContain('truncate');
    expect(outLine.className).toContain('truncate');
  });

  it('emits reuse with the full entry when "Use" is clicked', () => {
    const emitted: DevHistoryEntry[] = [];
    component.reuse.subscribe((e) => emitted.push(e));

    findButton('Use').click();

    expect(emitted.length).toBe(1);
    expect(emitted[0].input).toBe(longInput);
    expect(emitted[0].output).toBe(longOutput);
  });

  it('expands on "View" to show the full, untruncated In/Out', () => {
    expect(entryRow().querySelector('textarea')).toBeNull();

    findButton('View').click();
    fixture.detectChanges();

    const textareas: HTMLTextAreaElement[] = Array.from(entryRow().querySelectorAll('textarea'));
    expect(textareas.length).toBe(2);
    expect(textareas[0].value).toBe(longInput);
    expect(textareas[1].value).toBe(longOutput);

    // Toggles back.
    findButton('Hide').click();
    fixture.detectChanges();
    expect(entryRow().querySelector('textarea')).toBeNull();
  });

  it('wires Copy In / Copy Out to the full entry text, not the truncated summary', () => {
    findButton('View').click();
    fixture.detectChanges();

    const copyButtons: HTMLButtonElement[] = Array.from(entryRow().querySelectorAll('app-copy-button button'));
    expect(copyButtons.map((b) => b.textContent?.trim())).toEqual(['Copy In', 'Copy Out']);
  });

  it('emits reuse from "Use in tool" inside the expanded detail', () => {
    findButton('View').click();
    fixture.detectChanges();

    const emitted: DevHistoryEntry[] = [];
    component.reuse.subscribe((e) => emitted.push(e));

    findButton('Use in tool').click();

    expect(emitted.length).toBe(1);
    expect(emitted[0].input).toBe(longInput);
  });

  it('still deletes an entry via Delete, unaffected by the new actions', async () => {
    // remove() fires the service call without awaiting it (it's a plain (click)
    // handler) — spy through to the real implementation and await its return
    // value, rather than guessing at NgZone stability (IndexedDB's own
    // event-based completion doesn't reliably participate in that).
    const deleteSpy = spyOn(historyService, 'deleteEntry').and.callThrough();

    findButton('Delete').click();
    await deleteSpy.calls.mostRecent().returnValue;
    fixture.detectChanges();

    expect(component.entries().length).toBe(0);
  });
});
