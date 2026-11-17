import { HttpErrorResponse } from '@angular/common/http';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Observable, Subject, of, throwError } from 'rxjs';
import { ThemeService } from '../../../core/services/theme.service';
import { PlannerContent } from '../models/planner.models';
import { PlannerApiService, PlannerContentSave } from '../services/planner-api.service';
import { DrawioEditorComponent } from './drawio-editor.component';

describe('DrawioEditorComponent', () => {
  let fixture: ComponentFixture<DrawioEditorComponent>;
  let component: DrawioEditorComponent;
  let api: jasmine.SpyObj<PlannerApiService>;
  let drawioWindow: Window;
  let postSpy: jasmine.Spy;
  let stubFrame: HTMLIFrameElement;

  beforeEach(async () => {
    api = jasmine.createSpyObj<PlannerApiService>('PlannerApiService', ['getContent', 'saveContent']);
    api.getContent.and.returnValue(of({ content: '<server/>', revision: 1 }));
    api.saveContent.and.callFake((_id: string, body: PlannerContentSave) =>
      of({ content: body.content, revision: body.base_revision + 1 }),
    );

    await TestBed.configureTestingModule({
      imports: [DrawioEditorComponent],
      providers: [{ provide: PlannerApiService, useValue: api }],
    }).compileComponents();

    fixture = TestBed.createComponent(DrawioEditorComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('nodeId', 'n1');
    fixture.detectChanges();

    // A real same-origin window stands in for the draw.io iframe's contentWindow.
    stubFrame = document.createElement('iframe');
    document.body.appendChild(stubFrame);
    drawioWindow = stubFrame.contentWindow as Window;
    postSpy = spyOn(drawioWindow, 'postMessage');
    const frame: HTMLIFrameElement = fixture.nativeElement.querySelector('iframe');
    Object.defineProperty(frame, 'contentWindow', { get: () => drawioWindow });
  });

  afterEach(() => stubFrame.remove());

  const send = (data: object, source: Window = drawioWindow, origin = location.origin): void => {
    window.dispatchEvent(new MessageEvent('message', { data: JSON.stringify(data), source, origin }));
  };

  const posted = (): Record<string, unknown>[] =>
    postSpy.calls.allArgs().map(([data]) => JSON.parse(data as string) as Record<string, unknown>);

  const initAndLoad = (): void => {
    send({ event: 'init' });
    postSpy.calls.reset();
  };

  it('builds the iframe src for the pinned draw.io version in embed JSON mode', () => {
    const src: string = fixture.nativeElement.querySelector('iframe').getAttribute('src');
    expect(src).toContain('/drawio/32.6.10/index.html?embed=1&proto=json');
  });

  it('loads the fetched xml into draw.io on init', () => {
    send({ event: 'init' });

    expect(api.getContent).toHaveBeenCalledWith('n1');
    expect(posted()).toEqual([{ action: 'load', xml: '<server/>', autosave: 1 }]);
    expect(postSpy.calls.mostRecent().args[1]).toBe(location.origin);
  });

  it('debounces autosaves into one save with the latest xml and base revision', fakeAsync(() => {
    initAndLoad();

    send({ event: 'autosave', xml: '<a/>' });
    expect(component.status()).toBe('dirty');
    tick(500);
    send({ event: 'autosave', xml: '<b/>' });
    tick(1499);
    expect(api.saveContent).not.toHaveBeenCalled();
    tick(1);

    expect(api.saveContent).toHaveBeenCalledTimes(1);
    expect(api.saveContent).toHaveBeenCalledWith('n1', { content: '<b/>', base_revision: 1 });
    expect(component.status()).toBe('saved');
  }));

  it('keeps one save in flight and sends changes made during it with the new revision', fakeAsync(() => {
    const firstSave = new Subject<PlannerContent>();
    api.saveContent.and.returnValues(
      firstSave as Observable<PlannerContent>,
      of({ content: '<b/>', revision: 3 }),
    );
    initAndLoad();

    send({ event: 'autosave', xml: '<a/>' });
    tick(1500);
    expect(component.status()).toBe('saving');
    send({ event: 'autosave', xml: '<b/>' });
    tick(1500);
    expect(api.saveContent).toHaveBeenCalledTimes(1);

    firstSave.next({ content: '<a/>', revision: 2 });
    firstSave.complete();

    expect(api.saveContent).toHaveBeenCalledTimes(2);
    expect(api.saveContent.calls.mostRecent().args).toEqual(['n1', { content: '<b/>', base_revision: 2 }]);
    expect(component.status()).toBe('saved');
  }));

  it('shows conflict on 409 and overwrite saves local xml on the current server revision', fakeAsync(() => {
    api.saveContent.and.returnValue(throwError(() => new HttpErrorResponse({ status: 409 })));
    initAndLoad();

    send({ event: 'autosave', xml: '<mine/>' });
    tick(1500);
    expect(component.status()).toBe('conflict');

    send({ event: 'autosave', xml: '<mine2/>' });
    tick(1500);
    expect(api.saveContent).toHaveBeenCalledTimes(1);

    api.getContent.and.returnValue(of({ content: '<theirs/>', revision: 5 }));
    api.saveContent.and.returnValue(of({ content: '<mine2/>', revision: 6 }));
    component.overwrite();

    expect(api.saveContent.calls.mostRecent().args).toEqual(['n1', { content: '<mine2/>', base_revision: 5 }]);
    expect(component.status()).toBe('saved');
  }));

  it('reloadFromServer discards local changes and loads the server xml', fakeAsync(() => {
    api.saveContent.and.returnValue(throwError(() => new HttpErrorResponse({ status: 409 })));
    initAndLoad();
    send({ event: 'autosave', xml: '<mine/>' });
    tick(1500);

    api.getContent.and.returnValue(of({ content: '<theirs/>', revision: 5 }));
    component.reloadFromServer();

    expect(posted()).toEqual([{ action: 'load', xml: '<theirs/>', autosave: 1 }]);
    expect(component.status()).toBe('idle');
    tick(1500);
    expect(api.saveContent).toHaveBeenCalledTimes(1);
  }));

  it('shows error on 503 and retry re-sends the same xml', fakeAsync(() => {
    api.saveContent.and.returnValue(throwError(() => new HttpErrorResponse({ status: 503 })));
    initAndLoad();

    send({ event: 'autosave', xml: '<a/>' });
    tick(1500);
    expect(component.status()).toBe('error');

    api.saveContent.and.returnValue(of({ content: '<a/>', revision: 2 }));
    component.retry();

    expect(api.saveContent).toHaveBeenCalledTimes(2);
    expect(api.saveContent.calls.mostRecent().args).toEqual(['n1', { content: '<a/>', base_revision: 1 }]);
    expect(component.status()).toBe('saved');
  }));

  it('flush saves pending changes immediately and emits status changes', async () => {
    const emitted: string[] = [];
    component.statusChange.subscribe((s) => emitted.push(s));
    initAndLoad();
    send({ event: 'autosave', xml: '<a/>' });

    await component.flush();

    expect(api.saveContent).toHaveBeenCalledWith('n1', { content: '<a/>', base_revision: 1 });
    expect(emitted).toEqual(['idle', 'dirty', 'saving', 'saved']);
  });

  it('ignores messages from a foreign source or origin and malformed payloads', fakeAsync(() => {
    send({ event: 'init' }, window);
    send({ event: 'init' }, drawioWindow, 'https://evil.example');
    window.dispatchEvent(new MessageEvent('message', { data: 'not json', source: drawioWindow, origin: location.origin }));
    window.dispatchEvent(new MessageEvent('message', { data: { event: 'init' }, source: drawioWindow, origin: location.origin }));
    send({ event: 'autosave', xml: '<evil/>' }, window);
    tick(1500);

    expect(api.getContent).not.toHaveBeenCalled();
    expect(postSpy).not.toHaveBeenCalled();
    expect(api.saveContent).not.toHaveBeenCalled();
    expect(component.status()).toBe('idle');
  }));

  it('defers the theme switch until there are no unsaved changes', fakeAsync(() => {
    const src = (): string => fixture.nativeElement.querySelector('iframe').getAttribute('src');
    const theme = TestBed.inject(ThemeService);
    theme.resolved.set('light');
    fixture.detectChanges();
    initAndLoad();

    send({ event: 'autosave', xml: '<a/>' });
    theme.resolved.set('dark');
    fixture.detectChanges();
    expect(src()).toContain('dark=0');

    tick(1500);
    fixture.detectChanges();
    expect(src()).toContain('dark=1');
  }));

  it('saves changes still in the debounce window when destroyed', fakeAsync(() => {
    initAndLoad();
    send({ event: 'autosave', xml: '<a/>' });

    fixture.destroy();

    expect(api.saveContent).toHaveBeenCalledWith('n1', { content: '<a/>', base_revision: 1 });
  }));

  it('renders the status copy for each state', fakeAsync(() => {
    const chip = (): string => (fixture.nativeElement as HTMLElement).textContent?.replace(/\s+/g, ' ').trim() ?? '';
    api.saveContent.and.returnValue(throwError(() => new HttpErrorResponse({ status: 409 })));
    initAndLoad();

    send({ event: 'autosave', xml: '<a/>' });
    fixture.detectChanges();
    expect(chip()).toContain('Saving…');

    tick(1500);
    fixture.detectChanges();
    expect(chip()).toContain('This diagram changed elsewhere.');
    expect(chip()).toContain('Reload');
    expect(chip()).toContain('Keep mine');
  }));
});
