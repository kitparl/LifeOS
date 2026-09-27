/** Split Bills API shapes. Amounts are integer paise. */

export type SplitExpiry = 'session' | '24h' | '7d';

export const SPLIT_EXPIRY_OPTIONS: { value: SplitExpiry; label: string }[] = [
  { value: 'session', label: 'This session' },
  { value: '24h', label: '24 hours' },
  { value: '7d', label: '7 days' },
];

export interface SplitGroupCreatePayload {
  name: string;
  creator_name: string;
  expiry: SplitExpiry;
}

/** One-time create/join response; the only place the raw seat secret appears. */
export interface SplitSeatIssued {
  code: string;
  url_path: string;
  member_id: string;
  seat_secret: string;
  expires_at: string;
}

export interface SplitMember {
  id: string;
  display_name: string;
  seat_no: number;
  is_creator: boolean;
  upi_vpa: string | null;
  joined_at: string;
}

export interface SplitShare {
  member_id: string;
  amount_paise: number;
}

export interface SplitExpense {
  id: string;
  title: string;
  amount_paise: number;
  paid_by: string;
  created_by: string;
  expense_date: string;
  created_at: string;
  shares: SplitShare[];
}

export type SplitSettlementStatus = 'paid' | 'confirmed';
export type SplitSettlementMethod = 'upi' | 'cash';

export interface SplitSettlement {
  id: string;
  payer_member_id: string;
  payee_member_id: string;
  amount_paise: number;
  status: SplitSettlementStatus;
  method: SplitSettlementMethod;
  paid_at: string;
  confirmed_at: string | null;
}

export interface SplitGroupView {
  code: string;
  name: string;
  url_path: string;
  created_at: string;
  expires_at: string;
  ended_at: string | null;
  is_open: boolean;
  members: SplitMember[];
  expenses: SplitExpense[];
  settlements: SplitSettlement[];
  my_member_id: string | null;
  is_creator: boolean;
  in_history: boolean | null;
}

export type SplitRole = 'creator' | 'member';

/** A row of the on-device list (`lifeos-split-groups`). Not an account — per browser only. */
export interface DeviceSplitGroup {
  code: string;
  name: string;
  seatSecret: string;
  displayName: string;
  role: SplitRole;
}
