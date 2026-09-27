/** Split Bills API shapes. Amounts are integer paise. */

export type SplitExpiry = 'session' | '1h' | '6h' | '24h' | '3d' | '7d' | '30d';

export const SPLIT_EXPIRY_OPTIONS: { value: SplitExpiry; label: string }[] = [
  { value: 'session', label: 'This session (up to 12 h)' },
  { value: '1h', label: '1 hour' },
  { value: '6h', label: '6 hours' },
  { value: '24h', label: '24 hours' },
  { value: '3d', label: '3 days' },
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
];

export interface SplitGroupCreatePayload {
  name: string;
  creator_name: string;
  expiry: SplitExpiry;
}

export interface SplitJoinPayload {
  display_name: string;
}

export interface SplitExpensePayload {
  title: string;
  amount_rupees: number;
  paid_by: string;
  member_ids: string[];
}

export interface SplitSettlementPayload {
  payee_member_id: string;
  amount_rupees: number;
  method: SplitSettlementMethod;
}

export interface SplitMemberUpdatePayload {
  upi_vpa: string | null;
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

export interface SplitMemberBalance {
  member_id: string;
  display_name: string;
  net_paise: number;
}

/** One payer -> payee debt. `amount_*` is the price still to pay now (pending payments set aside). */
export interface SplitDebt {
  payer_member_id: string;
  payer_name: string;
  payee_member_id: string;
  payee_name: string;
  outstanding_paise: number;
  pending_paise: number;
  amount_paise: number;
  amount_rupees: string;
  /** `upi://pay?...` for that price; null when the payee has no UPI id or nothing is left to pay. */
  upi_uri: string | null;
}

export interface SplitBalances {
  nets: SplitMemberBalance[];
  debts: SplitDebt[];
}

/** A signed-in user's kept group (Finance → Splits); outlives the link. */
export interface SplitHistoryItem {
  code: string;
  name: string;
  url_path: string;
  expires_at: string;
  ended_at: string | null;
  is_open: boolean;
  my_net_paise: number | null;
  kept_at: string;
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

/** Mirrors the server's `name@bank` check (the server lower-cases before validating). */
export const UPI_VPA_PATTERN = /^[a-z0-9._-]{2,64}@[a-z0-9.-]{2,64}$/i;
