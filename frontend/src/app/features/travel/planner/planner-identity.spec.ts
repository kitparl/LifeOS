import { isInAppBrowser, plannerStorage } from './planner-identity';

describe('planner identity', () => {
  afterEach(() => localStorage.removeItem('tp:k7mq2p3x'));

  it('recognises in-app browsers where Google blocks sign-in', () => {
    expect(isInAppBrowser('Mozilla/5.0 (iPhone) AppleWebKit Mobile/15E148 Instagram 300.0')).toBeTrue();
    expect(isInAppBrowser('Mozilla/5.0 (Linux; Android 14; wv) AppleWebKit Chrome/120 Mobile WhatsApp/2.24')).toBeTrue();
    expect(isInAppBrowser('Mozilla/5.0 (iPhone) AppleWebKit/605 Version/17.0 Mobile/15E148 Safari/604.1')).toBeFalse();
    expect(isInAppBrowser('Mozilla/5.0 (Windows NT 10.0) Chrome/120.0 Safari/537.36')).toBeFalse();
  });

  it('remembers the friend per link and survives broken storage values', () => {
    const identity = { deviceSecret: 's'.repeat(32), contributor: { id: 'c1', kind: 'name' as const, display_name: 'Asha' } };
    plannerStorage.setIdentity('k7mq2p3x', identity);
    expect(plannerStorage.identity('k7mq2p3x')).toEqual(identity);
    localStorage.setItem('tp:k7mq2p3x', '{not json');
    expect(plannerStorage.identity('k7mq2p3x')).toBeNull();
  });
});
