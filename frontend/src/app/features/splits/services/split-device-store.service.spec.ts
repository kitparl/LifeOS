import { TestBed } from '@angular/core/testing';
import { DeviceSplitGroup } from '../models/split.models';
import { SPLIT_DEVICE_STORAGE_KEY, SplitDeviceStoreService } from './split-device-store.service';

const dinner: DeviceSplitGroup = {
  code: 'k7mq2p',
  name: 'Dinner',
  seatSecret: 'secret-a',
  displayName: 'Asha',
  role: 'creator',
};

describe('SplitDeviceStoreService', () => {
  beforeEach(() => localStorage.removeItem(SPLIT_DEVICE_STORAGE_KEY));
  afterEach(() => localStorage.removeItem(SPLIT_DEVICE_STORAGE_KEY));

  function create(): SplitDeviceStoreService {
    return TestBed.inject(SplitDeviceStoreService);
  }

  it('persists a saved group under lifeos-split-groups and finds it by code', () => {
    create().save(dinner);
    const stored = JSON.parse(localStorage.getItem(SPLIT_DEVICE_STORAGE_KEY)!) as DeviceSplitGroup[];
    expect(stored).toEqual([dinner]);
    TestBed.resetTestingModule();
    expect(create().find('k7mq2p')).toEqual(dinner);
  });

  it('keeps newest first and replaces a repeated code', () => {
    const store = create();
    store.save(dinner);
    store.save({ ...dinner, code: 'abcdef', name: 'Trip' });
    store.save({ ...dinner, seatSecret: 'secret-b' });
    expect(store.groups().map((g) => [g.code, g.seatSecret])).toEqual([
      ['k7mq2p', 'secret-b'],
      ['abcdef', 'secret-a'],
    ]);
  });

  it('removes one group from this device and persists the rest', () => {
    const store = create();
    store.save(dinner);
    store.save({ ...dinner, code: 'abcdef', name: 'Trip' });
    store.remove('k7mq2p');
    expect(store.groups().map((g) => g.code)).toEqual(['abcdef']);
    expect(store.find('k7mq2p')).toBeUndefined();
    expect((JSON.parse(localStorage.getItem(SPLIT_DEVICE_STORAGE_KEY)!) as DeviceSplitGroup[]).length).toBe(1);
  });

  it('ignores malformed storage and malformed rows', () => {
    localStorage.setItem(SPLIT_DEVICE_STORAGE_KEY, '{not json');
    expect(create().groups()).toEqual([]);
    TestBed.resetTestingModule();
    localStorage.setItem(SPLIT_DEVICE_STORAGE_KEY, JSON.stringify([dinner, { code: 'x' }, { ...dinner, role: 'admin' }]));
    expect(create().groups()).toEqual([dinner]);
  });
});
