import { ConfirmService } from './confirm.service';

describe('ConfirmService', () => {
  it('defaults to a destructive "Delete" confirmation', async () => {
    const service = new ConfirmService();
    const result = service.confirm('Remove it?');
    expect(service.acceptLabel()).toBe('Delete');
    expect(service.danger()).toBeTrue();
    service.accept();
    expect(await result).toBeTrue();
  });

  it('accepts a custom, non-destructive action label', async () => {
    const service = new ConfirmService();
    const result = service.confirm('Mark places visited?', 'Complete trip?', { acceptLabel: 'Complete trip', danger: false });
    expect(service.acceptLabel()).toBe('Complete trip');
    expect(service.danger()).toBeFalse();
    service.cancel();
    expect(await result).toBeFalse();
    service.confirm('Again');
    expect(service.acceptLabel()).toBe('Delete');
  });
});
