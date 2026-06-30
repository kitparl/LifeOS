export interface AiStatus {
  enabled: boolean;
  provider: string;
  indexed_chunks: number;
  embedding_chunks: number;
}

export interface AiSourceItem {
  source_type: string;
  source_id: string;
  title: string;
  route: string;
  snippet: string;
  score: number;
}

export interface AiChatResponse {
  reply: string;
  sources: AiSourceItem[];
}

export interface AiIndexResponse {
  indexed: number;
  embedded: number;
}
