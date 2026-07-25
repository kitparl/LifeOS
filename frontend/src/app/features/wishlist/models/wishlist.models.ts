export interface WishlistItem {
  id: string;
  title: string;
  description: string | null;
  category: string;
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
  category: string;
  cost: number | null;
  progress: number;
  image_url: string | null;
  updated_at: string;
}
