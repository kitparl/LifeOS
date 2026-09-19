import { TestBed } from '@angular/core/testing';
import { DevHistoryService } from './dev-history.service';

describe('DevHistoryService', () => {
  let service: DevHistoryService;
  const toolId = `test-tool-${Date.now()}`;

  beforeEach(() => {
    service = TestBed.inject(DevHistoryService);
  });

  it('records an entry and exposes it via a reactive signal', async () => {
    const history = service.getHistory(toolId);
    await service.addEntry(toolId, 'hello', 'world');
    expect(history().length).toBe(1);
    expect(history()[0].input).toBe('hello');
    expect(history()[0].output).toBe('world');
  });

  it('ignores entries where both input and output are empty', async () => {
    const empty = `${toolId}-empty`;
    const history = service.getHistory(empty);
    await service.addEntry(empty, '', '');
    expect(history().length).toBe(0);
  });

  it('never records entries for excluded (sensitive) tool IDs', async () => {
    const history = service.getHistory('password-generator');
    await service.addEntry('password-generator', 'anything', 'hunter2');
    expect(history().length).toBe(0);
  });

  it('deletes a single entry and clears all history for a tool', async () => {
    const clearId = `${toolId}-clear`;
    const history = service.getHistory(clearId);
    await service.addEntry(clearId, 'a', 'A');
    await service.addEntry(clearId, 'b', 'B');
    expect(history().length).toBe(2);

    const idToDelete = history()[0].id!;
    await service.deleteEntry(clearId, idToDelete);
    expect(history().length).toBe(1);

    await service.clearHistory(clearId);
    expect(history().length).toBe(0);
  });
});
