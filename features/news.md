# Feature: News

LifeOS shows live news from [FreeNewsAPI](https://freenewsapi.ai) and lets you keep a personal library of saved articles grouped into collections. Saved articles expire automatically.

---

## Overview

| Capability | Description |
|------------|-------------|
| **Latest** | Newest English articles, with a remembered country chip (All · India · US · UK · Canada · Australia) |
| **Categories** | AI, Technology, Business, Finance, Science, Health, Sports, Entertainment, World, India, Politics, Climate, Startups |
| **Search** | Debounced keyword search with Country, Language, Date, Publisher (domain) and Sort filters; "Load more" paging |
| **Article page** | Title, publisher, author, date, description, a short excerpt, and **Read Original Article →** |
| **Saved** | Star any article. Filter All / Recent (7 days) / Expiring Soon (3 days). Shows "Saved 5 days ago · Expires in 25 days" |
| **Collections** | Create, rename, delete. One saved article can be in several collections; move it between them |

The whole module is behind the normal LifeOS login.

---

## What is stored (and what is not)

- **Not stored:** the news feed, article bodies, and images. Live news is fetched through the backend for each request and cached only briefly in memory (about 60 s on the server and 2 min in the browser).
- **Stored per user:** a lightweight snapshot of each saved article (URL, title, description, image URL, publisher, host, author, published time), collections, and collection memberships.
  - Tables: `news_saved_articles`, `news_collections`, `news_collection_articles`.
- **Expiry:** `expires_at = saved_at + ARTICLE_RETENTION_DAYS` (default 30). Expired articles are hidden and removed in two ways:
  - lazily, when you open Saved or Collections;
  - daily at 00:07 IST, by the `news_saved_purge` job.
  
  Removing an article also removes its collection memberships. The collections themselves stay.
- Saving the same URL twice returns the existing save ("Already saved"). Saving an expired article again starts a fresh retention window.

---

## Categories

FreeNewsAPI's search has no category filter, and its per-article category tags are unreliable, so each category maps to a search phrase or a country filter. The mapping lives in `backend/app/modules/news/categories.py`, the single source for it.

| Category | FreeNewsAPI params |
|----------|--------------------|
| All | *(none)* |
| AI | `q=artificial intelligence` |
| Technology / Business / Finance / Science / Health / Sports / Entertainment / Politics | `q=<category name, lowercase>` |
| World | `q=international` |
| India | `country=IN` |
| Climate | `q=climate change` |
| Startups | `q=startups` |

Feeds are sorted newest first, so broad words can match loosely. Search offers **Relevance** sorting for tighter matches.

---

## API (`/api/v1/news`, all authenticated)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/categories` | Category list `[{id, label}]` |
| GET | `/articles` | Live feed/search: `q` or `category`, `country`, `lang`, `host`, `date`, `sort`, `limit` (≤ 50), `offset` |
| GET | `/article?url=` | One article with `excerpt` (at most 3 paragraphs / 1,200 chars) |
| GET | `/saved?filter=all\|recent\|expiring&limit&offset` | Saved articles (paginated) |
| POST | `/saved` | Save a snapshot (201 new, 200 already saved) |
| DELETE | `/saved/{id}` | Remove a saved article |
| GET / POST | `/collections` | List (with counts) / create |
| PATCH / DELETE | `/collections/{id}` | Rename / delete (saved articles are kept) |
| GET / POST | `/collections/{id}/articles` | Members (paginated) / add `{saved_article_id}` |
| DELETE | `/collections/{id}/articles/{saved_id}` | Remove from collection |
| POST | `/collections/{id}/articles/{saved_id}/move` | Move to `{target_collection_id}` |

Vendor failures return `{"detail": {"code", "message"}}` with codes `timeout`, `rate_limit`, `provider_unavailable`, and `malformed_response`. Other codes:
- `article_unavailable` (404) for a missing article.
- `write_limit` (429) when the hourly save limit is hit.

---

## Settings (`backend/.env`)

| Variable | Default | Meaning |
|----------|---------|---------|
| `FREENEWS_API_BASE_URL` | `https://freenewsapi.ai` | Vendor base URL (no key needed) |
| `ARTICLE_RETENTION_DAYS` | `30` | Days a saved article is kept |
| `NEWS_PROXY_PER_MINUTE` | `60` | Per-user live-news requests per minute (in-process) |
| `NEWS_WRITES_PER_HOUR` | `300` | Per-user saves + new collections per hour |

---

## Code

- Backend: `backend/app/modules/news/`, with:
  - `client.py` (the only code that knows FreeNewsAPI URLs)
  - `categories.py`, `dedupe.py`, `cache.py`, `rate_limit.py`
  - `models.py`, `repository.py`, `service.py`, `api.py`
- Frontend: `frontend/src/app/features/news/`, with:
  - the hub (`?tab=latest|categories|search|saved|collections`)
  - the pages `/news/article?url=` and `/news/collections/:id`
- Tests: `backend/app/tests/test_news_*.py` and `features/news/**/*.spec.ts`.
