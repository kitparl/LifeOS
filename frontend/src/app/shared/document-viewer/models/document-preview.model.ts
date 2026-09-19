export type PreviewType =
  | 'pdf'
  | 'image'
  | 'text'
  | 'csv'
  | 'markdown'
  | 'video'
  | 'audio'
  | 'unsupported';

export type PreviewStatus = 'ready' | 'processing' | 'failed';

export interface PreviewInfo {
  document_id: string;
  file_name: string;
  original_mime_type: string;
  preview_type: PreviewType;
  status: PreviewStatus;
  preview_url: string | null;
  download_url: string;
  page_count: number | null;
  error: string | null;
}

export interface DocumentViewerConfig {
  documentId: string;
  /** Optional hints only — the viewer never needs these to render correctly. */
  fileName?: string;
  mimeType?: string;
}
