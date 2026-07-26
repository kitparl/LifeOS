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
  checksum_sha256?: string | null;
  extension?: string | null;
  visibility?: string;
}

export interface DownloadToken {
  token: string;
  expires_at: string;
}

export interface FileUsage {
  used_bytes: number;
  quota_bytes: number;
  file_count: number;
}
