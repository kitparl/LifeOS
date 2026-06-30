export type WishlistCategory = 'travel' | 'cars' | 'house' | 'countries' | 'experiences' | 'other';

export interface WishlistItem {
  id: string;
  title: string;
  description: string | null;
  category: WishlistCategory;
  cost: number | null;
  progress: number;
  notes: string | null;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface WishlistListItem {
  id: string;
  title: string;
  category: WishlistCategory;
  cost: number | null;
  progress: number;
  image_url: string | null;
  updated_at: string;
}

export const WISHLIST_CATEGORIES: { value: WishlistCategory; label: string }[] = [
  { value: 'travel', label: 'Travel' },
  { value: 'cars', label: 'Cars' },
  { value: 'house', label: 'House' },
  { value: 'countries', label: 'Countries' },
  { value: 'experiences', label: 'Experiences' },
  { value: 'other', label: 'Other' },
];
