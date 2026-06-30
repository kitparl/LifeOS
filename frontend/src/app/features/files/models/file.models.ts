export interface FileRecord {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  storage_backend: string;
  url: string;
  module: string | null;
  entity_id: string | null;
  created_at: string;
}
