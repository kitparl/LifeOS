export interface SearchResultItem {
  module: string;
  entity_type: string;
  id: string;
  title: string;
  subtitle: string | null;
  route: string;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResultItem[];
}
