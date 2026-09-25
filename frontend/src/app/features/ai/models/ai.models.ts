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

export interface AiModelOption {
  provider: string;
  model: string;
  display_name: string;
  available: boolean;
}

export interface AiCurrentSelection {
  provider: string;
  model: string;
  updated_at: string | null;
  available: boolean;
}

export interface AiUseCase {
  use_case: string;
  display_name: string;
  capability: string;
  options: AiModelOption[];
  current: AiCurrentSelection | null;
}

export interface AiUseCaseModelUpdate {
  provider: string;
  model: string;
  custom?: boolean;
}

export interface AiUseCaseHistoryItem {
  provider: string;
  model: string;
  effective_from: string;
  effective_to: string | null;
}

export interface AiSettings {
  default_provider: string | null;
  timeout_seconds: number;
  max_tokens: number;
  temperature: number;
}
