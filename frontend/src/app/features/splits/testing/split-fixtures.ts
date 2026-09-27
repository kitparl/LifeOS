import { SplitGroupView, SplitMember } from '../models/split.models';

/** Spec-only builders for Split Bills API payloads. */

export function member(id: string, name: string, seatNo: number, upi: string | null = null): SplitMember {
  return {
    id,
    display_name: name,
    seat_no: seatNo,
    is_creator: seatNo === 0,
    upi_vpa: upi,
    joined_at: '2026-09-27T10:00:00Z',
  };
}

export function groupView(overrides: Partial<SplitGroupView> = {}): SplitGroupView {
  return {
    code: 'k7mq2p',
    name: 'Dinner',
    url_path: '/s/k7mq2p',
    created_at: '2026-09-27T10:00:00Z',
    expires_at: new Date(Date.now() + 5 * 3_600_000).toISOString(),
    ended_at: null,
    is_open: true,
    members: [member('m-a', 'Asha', 0)],
    expenses: [],
    settlements: [],
    my_member_id: null,
    is_creator: false,
    in_history: null,
    ...overrides,
  };
}
