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

export const WISHLIST_STATUSES: { value: WishlistStatus; label: string }[] = [
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'delayed', label: 'Delayed' },
];

export const WISHLIST_PRIORITIES: { value: WishlistPriority; label: string }[] = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];
