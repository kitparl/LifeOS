export type WishlistStatus = 'in_progress' | 'completed' | 'delayed';
export type WishlistPriority = 'high' | 'medium' | 'low';

export interface WishlistItem {
  id: string;
  title: string;
  description: string | null;
  category: string;
  target_year: number | null;
  achieved_date: string | null;
  status: WishlistStatus;
  priority: WishlistPriority;
  notes: string | null;
  image_url: string | null;
  photos: string[];
  created_at: string;
  updated_at: string;
}

export interface WishlistListItem {
  id: string;
  title: string;
  category: string;
  target_year: number | null;
  achieved_date: string | null;
  status: WishlistStatus;
  priority: WishlistPriority;
  image_url: string | null;
  updated_at: string;
}

export type WishlistStatusFilter = '' | 'incomplete' | WishlistStatus;

export const WISHLIST_STATUSES: { value: WishlistStatus; label: string }[] = [
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'delayed', label: 'Delayed' },
];

export const WISHLIST_STATUS_FILTERS: { value: WishlistStatusFilter; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'incomplete', label: 'Incomplete' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'delayed', label: 'Delayed' },
  { value: 'completed', label: 'Completed' },
];

export function wishlistStatusBadge(status: WishlistStatus | string): string {
  switch (status) {
    case 'completed':
      return 'badge badge--success';
    case 'delayed':
      return 'badge badge--warning';
    case 'in_progress':
      return 'badge badge--info';
    default:
      return 'badge badge--default';
  }
}

export function wishlistStatusAccent(status: WishlistStatus | string): string {
  switch (status) {
    case 'completed':
      return 'var(--success)';
    case 'delayed':
      return 'var(--warning)';
    case 'in_progress':
      return 'var(--info)';
    default:
      return 'var(--xp-border)';
  }
}

export const WISHLIST_PRIORITIES: { value: WishlistPriority; label: string }[] = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];
