import { HttpErrorResponse } from '@angular/common/http';

/** One live FreeNewsAPI article (proxied, never stored). Only id/url/title are guaranteed. */
export interface NewsArticle {
  id: string;
  url: string;
  title: string;
  description: string | null;
  published_at: string | null;
  host: string | null;
  sitename: string | null;
  country: string | null;
  lang: string | null;
  author: string | null;
  categories: string[] | null;
  image: string | null;
  /** The current user's saved row for this URL, if any. */
  saved_article_id: string | null;
}

export interface NewsArticlePage {
  items: NewsArticle[];
  total: number;
  total_is_lower_bound: boolean;
  offset: number;
  limit: number;
  has_more: boolean;
}

export interface NewsArticleDetail extends NewsArticle {
  /** First paragraphs only; the full body is never returned. */
  excerpt: string[];
}

export interface NewsCategory {
  id: string;
  label: string;
}

export type NewsDatePreset = 'today' | 'yesterday' | '24h' | '48h' | '7d' | '30d';
export type NewsSort = 'date' | 'relevance';

export interface NewsQuery {
  q?: string;
  category?: string;
  country?: string;
  lang?: string;
  host?: string;
  date?: NewsDatePreset;
  sort?: NewsSort;
  limit?: number;
  offset?: number;
}

export interface SavedArticle {
  id: string;
  article_external_id: string | null;
  article_url: string;
  title: string;
  description: string | null;
  image: string | null;
  publisher: string | null;
  host: string | null;
  author: string | null;
  published_at: string | null;
  saved_at: string;
  expires_at: string;
  collection_ids: string[];
  already_saved: boolean;
}

export type SavedArticleCreate = Pick<
  SavedArticle,
  'article_external_id' | 'article_url' | 'title' | 'description' | 'image' | 'publisher' | 'host' | 'author' | 'published_at'
>;

export interface SavedArticlePage {
  items: SavedArticle[];
  total: number;
}

export type SavedFilter = 'all' | 'recent' | 'expiring';

export interface NewsCollection {
  id: string;
  name: string;
  article_count: number;
  created_at: string;
  updated_at: string;
}

/** Fields shared by live and saved articles, so cards and rows can render either. */
export interface ArticleView {
  url: string;
  title: string;
  description: string | null;
  image: string | null;
  publisher: string | null;
  published_at: string | null;
  country?: string | null;
  category?: string | null;
}

export function publisherOf(article: Pick<NewsArticle, 'sitename' | 'host'>): string | null {
  return article.sitename || article.host || null;
}

export function toArticleView(article: NewsArticle): ArticleView {
  return {
    url: article.url,
    title: article.title,
    description: article.description,
    image: article.image,
    publisher: publisherOf(article),
    published_at: article.published_at,
    country: article.country,
    category: article.categories?.[0] ?? null,
  };
}

export function savedToArticleView(saved: SavedArticle): ArticleView {
  return {
    url: saved.article_url,
    title: saved.title,
    description: saved.description,
    image: saved.image,
    publisher: saved.publisher || saved.host,
    published_at: saved.published_at,
  };
}

export function toSavedArticleCreate(article: NewsArticle): SavedArticleCreate {
  return {
    article_external_id: article.id,
    article_url: article.url,
    title: article.title,
    description: article.description,
    image: article.image,
    publisher: publisherOf(article),
    host: article.host,
    author: article.author,
    published_at: article.published_at,
  };
}

export type NewsErrorCode =
  | 'offline'
  | 'timeout'
  | 'rate_limit'
  | 'write_limit'
  | 'provider_unavailable'
  | 'malformed_response'
  | 'article_unavailable'
  | 'unknown';

const KNOWN_CODES: readonly NewsErrorCode[] = [
  'timeout',
  'rate_limit',
  'write_limit',
  'provider_unavailable',
  'malformed_response',
  'article_unavailable',
];

export function newsErrorCode(err: unknown): NewsErrorCode {
  if (!(err instanceof HttpErrorResponse)) return 'unknown';
  if (err.status === 0) return 'offline';
  const code = (err.error as { detail?: { code?: unknown } } | null)?.detail?.code;
  return typeof code === 'string' && (KNOWN_CODES as readonly string[]).includes(code)
    ? (code as NewsErrorCode)
    : 'unknown';
}

const ERROR_MESSAGES: Record<NewsErrorCode, string> = {
  offline: "You're offline. Check your connection and try again.",
  timeout: 'The news service took too long to respond. Please try again.',
  rate_limit: 'Too many requests right now. Please wait a moment and try again.',
  write_limit: 'You have saved a lot this hour. Please try again later.',
  provider_unavailable: "We couldn't load the latest news. Please try again.",
  malformed_response: "We couldn't read the news service's response. Please try again.",
  article_unavailable: 'This article is no longer available.',
  unknown: 'Something went wrong. Please try again.',
};

export function newsErrorMessage(code: NewsErrorCode): string {
  return ERROR_MESSAGES[code];
}

export interface NewsOption<T extends string = string> {
  id: T;
  label: string;
}

/** Country chips/filters. '' means all countries (no vendor filter). */
export const NEWS_COUNTRIES: readonly NewsOption[] = [
  { id: '', label: 'All' },
  { id: 'IN', label: 'India' },
  { id: 'US', label: 'US' },
  { id: 'GB', label: 'UK' },
  { id: 'CA', label: 'Canada' },
  { id: 'AU', label: 'Australia' },
];

export const NEWS_LANGUAGES: readonly NewsOption[] = [
  { id: '', label: 'Any language' },
  { id: 'en', label: 'English' },
  { id: 'hi', label: 'Hindi' },
  { id: 'es', label: 'Spanish' },
  { id: 'fr', label: 'French' },
  { id: 'de', label: 'German' },
];

export const NEWS_DATE_OPTIONS: readonly NewsOption<NewsDatePreset | ''>[] = [
  { id: '', label: 'Any time' },
  { id: 'today', label: 'Today' },
  { id: '24h', label: 'Last 24 hours' },
  { id: '48h', label: 'Last 48 hours' },
  { id: '7d', label: 'Last 7 days' },
  { id: '30d', label: 'Last 30 days' },
];

export const NEWS_SORT_OPTIONS: readonly NewsOption<NewsSort>[] = [
  { id: 'date', label: 'Newest' },
  { id: 'relevance', label: 'Relevance' },
];

/** Matches the backend's publisher/host allowlist. */
export const NEWS_HOST_PATTERN = /^([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/;
