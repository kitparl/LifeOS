# File Storage & Attachments Hardening Prompt

You are a **Senior Software Architect** and **Senior Backend Engineer**.

LifeOS already has a working **`files` module**. Your job is **NOT** to rebuild it and **NOT** to create a second storage module. Extend and harden the existing one into a production-ready, storage-agnostic attachment system that can move from local disk to S3-compatible object storage (Amazon S3 / Cloudflare R2) without changing Angular code, REST contracts, or the database schema.

**Backward compatibility is mandatory.** Existing endpoints, existing rows in `file_records`, the Angular `FilesService`, the OCR module, and `app/tests/test_files.py` must all keep working.

---

# Current State (verify before changing anything)

Read these files first. They are the baseline you are extending.

## Backend

| Path | What it is |
|------|-----------|
| `backend/app/modules/files/api.py` | Router, `prefix="/files"`, mounted under `/api/v1` |
| `backend/app/modules/files/service.py` | `FileService` — upload / list / get / get_local_content / delete |
| `backend/app/modules/files/repository.py` | `FileRepository` — hard delete today, no soft delete |
| `backend/app/modules/files/models.py` | `FileRecord` → table `file_records` |
| `backend/app/modules/files/schemas.py` | `FileRecordResponse`, `FileUploadResponse` |
| `backend/app/modules/files/storage.py` | `FileStorage` — concrete class, local + S3 branches |
| `backend/app/core/config.py` | `upload_dir`, `max_upload_bytes`, `s3_bucket`, `s3_region`, `aws_access_key_id`, `aws_secret_access_key` |
| `backend/app/core/deps.py` | `get_current_user` — **JWT Bearer header only, no cookie fallback** |
| `backend/app/core/migrations.py` | Idempotent `ALTER TABLE` list — **this repo has no Alembic** |
| `backend/app/tests/test_files.py` | Upload / list / download / delete / 413 coverage |

## Existing endpoints (do not break these)

```
GET    /api/v1/files                   -> list[FileRecordResponse]  (metadata JSON)
POST   /api/v1/files/upload            -> FileUploadResponse, 201    (multipart: file, module, entity_id)
GET    /api/v1/files/{file_id}         -> FileRecordResponse         (metadata JSON, NOT bytes)
GET    /api/v1/files/{file_id}/content -> raw bytes
DELETE /api/v1/files/{file_id}         -> 204
```

Note that `GET /files/{id}` returns **metadata**, and bytes live at `/files/{id}/content`. Keep that split.

## Existing consumers

* `frontend/src/app/features/files/services/files.service.ts` — `list`, `upload`, `delete`, `contentUrl`
* `frontend/src/app/features/files/files-page.component.ts` — renders `<a [href]="contentUrl(f)">`
* `frontend/src/app/sync/sync.service.ts` — `shouldBypass()` excludes `/files/upload` and `/files/**/content` from the offline queue
* `backend/app/modules/ocr/service.py` — calls `FileService.upload(user_id, filename, content, content_type, "ocr", None)`

Any change to `FileService.upload()`'s signature must be applied to the OCR caller in the same change.

## Existing column names — use these, do not invent new ones

`file_records` currently has: `id`, `user_id`, `filename`, `content_type`, `size_bytes`, `storage_backend`, `storage_key`, `url`, `module`, `entity_id`, `created_at`.

LifeOS conventions you must follow:

* Ownership column is **`user_id`** (FK to `users.id`), never `owner_id`.
* Primary keys and FKs are **`String(36)`** holding a UUID string — never a native Postgres `UUID` type. The dev database is SQLite (`sqlite+aiosqlite`) and the test suite runs on in-memory SQLite, so native UUID/JSONB types break tests.
* Storage backend discriminator is **`storage_backend`**, not `storage_type`.
* Storage location is **`storage_key`** (a backend-relative key), not `storage_path`.
* The entity-type column is **`module`** today. Keep the name `module`; do not rename it to `entity_type`.

---

# Known Defects to Fix

These are real bugs in the current implementation. Each one must be fixed and covered by a test.

### D1 — Authenticated downloads are broken in the browser

`get_current_user` only reads an `Authorization: Bearer` header. Browsers cannot attach headers to `<a href>`, `<img src>`, or an iframe PDF preview, so `files-page.component.ts` line 25 opens `/api/v1/files/{id}/content` in a new tab and gets a **401**.

Fix by adding a **short-lived signed download token**:

```
POST /api/v1/files/{id}/download-token  -> { token, expires_at }   (Bearer auth required)
GET  /api/v1/files/{id}/content?token=  -> bytes                    (token OR Bearer accepted)
```

* Token is signed with `secret_key` (reuse `app/core/security.py`), scoped to a single `file_id` + `user_id`, TTL ≤ 5 minutes, and is **not** a general-purpose access token.
* The `Bearer` path must keep working unchanged so `test_files.py` stays green.
* Angular's `contentUrl()` becomes async (mint token, then build URL) or switches to blob download. State which you chose in the summary.

### D2 — `url` is persisted, which blocks the S3/R2 migration

`FileRecord.url` stores a fully-formed absolute URL, and `storage.py` hardcodes `https://{bucket}.s3.{region}.amazonaws.com/...`, which is wrong for Cloudflare R2 — an explicitly stated future target. Any local→S3 move would leave every existing row pointing at a stale URL.

Fix: **derive the URL at read time** from `storage_backend` + `storage_key` inside the storage layer. Keep the `url` field in the response schema (the frontend reads it) but stop treating the stored column as the source of truth. Leave the column in place, ignored, so old rows and `create_all` keep working.

### D3 — Size limit is enforced after the whole body is in memory

`api.py` does `content = await file.read()` and `service.py` checks the length afterwards, so a 5 GB upload is fully buffered into RAM before being rejected with 413.

Fix: stream the upload in chunks, count bytes as they arrive, and abort as soon as `max_upload_bytes` is exceeded. Compute `checksum_sha256` incrementally over the same stream. Delete any partial file on abort.

### D4 — No path-traversal guard on reads

`FileStorage.local_path()` joins `storage_key` from the database onto the upload root with no validation.

Fix: after resolving, assert the path is inside the root (`Path.resolve().is_relative_to(root)`) and raise a 404 otherwise. Keys must always be server-generated; never build a key from a client-supplied filename.

### D5 — `boto3` is not a declared dependency, and the S3 calls block the event loop

`storage.py` lazy-imports `boto3`, but it is absent from `backend/requirements.txt`, so the S3 branch fails at runtime. `_upload_s3` / `_delete_s3` are synchronous calls made from `async def` handlers, which blocks the whole event loop.

Fix: add the dependency explicitly and run S3 calls off the loop (`anyio.to_thread.run_sync` or `aioboto3`). Support a configurable `s3_endpoint_url` so Cloudflare R2 works.

### D6 — Non-atomic writes and orphaned bytes

A local write is a direct `write_bytes`, and there is no reconciliation if the DB transaction fails after the bytes land (orphan file) or if the tx rolls back after a successful `unlink` (row pointing at nothing).

Fix: write to a temp file in the same directory and `os.replace()` into place. Write bytes **before** the DB row, and on DB failure remove the file in a cleanup path. For deletes, see R6.

---

# Target Architecture

## Storage abstraction

Introduce a real interface. Business logic must never learn whether bytes live on disk or in a bucket.

```
StorageBackend            (ABC / Protocol)
├── LocalStorageBackend   (implement fully)
└── S3StorageBackend      (implement; must work for both AWS S3 and Cloudflare R2)
```

Required methods — keep the surface minimal:

```python
async def save(key: str, stream: AsyncIterator[bytes], content_type: str) -> StoredObject
async def open(key: str) -> AsyncIterator[bytes]         # streaming read
async def delete(key: str) -> None
async def exists(key: str) -> bool
async def stat(key: str) -> ObjectStat | None            # storage-level size / mtime only
def     public_url(key: str) -> str | None               # None when not publicly readable
async def signed_url(key: str, ttl_seconds: int) -> str  # presigned for S3/R2; token URL for local
```

Do **not** add `move()` or `copy()` — there is no caller for them. Do not add a `get_metadata()` that duplicates database metadata; `stat()` is storage-level only.

Selection of the active backend belongs in a FastAPI dependency (`get_storage_backend`) driven by config, injectable so tests can substitute a fake. Nothing outside the backend implementations may import `boto3` or touch `pathlib` for storage.

## Storage key layout

Keys are backend-relative and identical across backends, so a migration is a pure byte copy:

```
{module}/{entity_id | _unlinked}/{YYYY}/{MM}/{file_id}/original{ext}
{module}/{entity_id | _unlinked}/{YYYY}/{MM}/{file_id}/thumb.webp
```

The `{file_id}` directory exists so derived files (thumbnails, OCR previews) have a home without a second table. Extension is derived from the sniffed type, not the client filename.

`module` must be validated against an allowlist of **actual LifeOS modules**, not invented enterprise entities. Valid values are the real module names: `tasks`, `habits`, `goals`, `journal`, `routines`, `knowledge_notes`, `ocr`, `running`, `finance`, `wishlist`, `career`, `learning`, `mood`, `memory`, `calendar`, `voice`. Reject anything else with 400. There are no `projects`, `employees`, `customers`, or `invoices` in this codebase.

---

# New Requirements

### R1 — Trustworthy type validation

The client's `Content-Type` and filename extension are both untrusted.

* Sniff the real type from magic bytes (`filetype` or `python-magic`) and store the sniffed value in `content_type`.
* Reject when the sniffed type is not on the allowed list, or when it contradicts the extension.
* Configurable allowlist via env, defaulting to: images (`png`, `jpg`, `webp`, `gif`), `pdf`, plain text / markdown / csv, common office documents, and audio (`m4a`, `mp3`, `ogg`, `webm`) for the voice module.
* Serve every download with `X-Content-Type-Options: nosniff` and `Content-Disposition: attachment`, except for a small inline-safe allowlist (images and PDF). **Never** serve user-supplied HTML or SVG inline from the app origin — that is stored XSS against the LifeOS session.
* Keep the original client filename in `filename` for display only; it must never influence a path.

### R2 — Streaming download with range support

Serve bytes via `StreamingResponse`/`FileResponse` and honour the `Range` header, since voice recordings and OCR images need seek and preview. Send `ETag` (use `checksum_sha256`), `Content-Length`, and `Cache-Control: private, max-age=...`; return 304 on a matching `If-None-Match`.

### R3 — Per-user quota and upload rate limit

LifeOS is multi-user (`users` table, JWT auth, admin flag, task assignment between users). A global per-file cap is not enough.

* Configurable per-user total storage quota; return **413** with a clear message when exceeded.
* Configurable uploads-per-hour limit; return **429**.
* Expose usage at `GET /api/v1/files/usage` → `{ used_bytes, quota_bytes, file_count }`.

### R4 — Entity-scoped listing and pagination

```
GET /api/v1/files?module=&entity_id=&limit=&offset=   -> paginated, X-Total-Count header
```

Extend the existing `GET /api/v1/files` with optional filters rather than adding a separate `/entities/{type}/{id}/files` route — that shape does not match this codebase's routing. The current default `limit=100` must stay the default so existing callers see no behaviour change. Add a composite index on `(user_id, module, entity_id)`.

### R5 — Checksum semantics

`checksum_sha256` must have a stated purpose, not just exist as a column:

* Computed during the streaming upload (see D3).
* Used as the `ETag` for download caching (R2).
* Used to **deduplicate within a single user**: if the same user uploads identical bytes, reuse the existing stored object and create a new metadata row pointing at the same `storage_key`. Reference counting must be handled before delete, so removing one row does not orphan another's bytes. If you judge dedupe not worth the complexity, say so explicitly and drop it — do not half-implement it.

### R6 — Soft delete with a deferred sweeper

The spec must not say "delete the bytes, then soft-delete the row" — that leaves a live row pointing at nothing.

* `DELETE /api/v1/files/{id}` sets `deleted_at` and returns 204. Bytes stay.
* Soft-deleted rows are excluded from every read path, but **still count** toward the user's quota until purged. State this in the API docs so the behaviour is not surprising.
* A purge routine (`POST /api/v1/files/admin/purge`, admin-only, plus a callable service function) removes bytes for rows soft-deleted more than N days ago, then hard-deletes the row.
* Because the current `FileRepository.delete()` does a hard delete, keep a hard-delete path available for internal callers such as OCR cleanup.

### R7 — Visibility

`visibility` is `private` (default) or `public`. Private is the only mode reachable without an explicit opt-in.

* Public files get a stable, unguessable route: `GET /api/v1/files/public/{file_id}` with no auth, `Cache-Control: public`.
* Flipping visibility is an explicit `PATCH /api/v1/files/{id}` operation with `{ visibility }`, and it must be logged.
* On S3/R2 the bucket stays private; public access is still proxied or presigned. Do not make buckets world-readable.

### R8 — Storage migration path

Migration from local to S3/R2 must require no schema, API, or frontend change.

* A backfill command that walks rows with `storage_backend='local'`, copies bytes to the new backend under the identical key, verifies `checksum_sha256`, then flips the row's `storage_backend` in a transaction.
* Resumable and idempotent — safe to re-run after interruption.
* A dual-read window: reads must resolve per-row via `storage_backend`, never via the globally configured default.
* Local bytes are only removed after a verified copy, on a separate opt-in pass.

---

# Schema Changes

New columns on `file_records`. All nullable or defaulted so existing rows survive.

| Column | Type | Notes |
|--------|------|-------|
| `checksum_sha256` | `VARCHAR(64)` | nullable; null for pre-existing rows |
| `extension` | `VARCHAR(16)` | derived from sniffed type |
| `visibility` | `VARCHAR(16) DEFAULT 'private'` | |
| `deleted_at` | `TIMESTAMP` | soft delete |
| `updated_at` | `TIMESTAMP` | |

**Migration mechanism — read this carefully.** This repo does **not** use Alembic. `alembic` appears in `requirements.txt` but there is no `alembic.ini` and no `versions/` directory; the schema comes from `Base.metadata.create_all()` in the `main.py` lifespan plus the idempotent `ALTER TABLE` list in `backend/app/core/migrations.py`.

Therefore:

* Add the new columns to the `FileRecord` model **and** append them to `_COLUMNS_TO_ENSURE` in `app/core/migrations.py`, matching the existing style (see the `tasks` soft-delete entries at the end of that list).
* If a column needs a value backfilled for old rows, use `_STRING_DEFAULTS_TO_BACKFILL` or add a dedicated backfill function in the same module.
* **Do not introduce Alembic as part of this task.** Baselining ~36 modules of existing tables is a separate, deliberate piece of work; a half-wired Alembic setup would fight `create_all` and corrupt dev databases.
* Do not drop or rename the existing `url` column (see D2) — leave it present and unused.

---

# Configuration

All settings go in the existing `Settings` class in `backend/app/core/config.py` (pydantic-settings, `.env`). Reuse what is already there; do not create a parallel config module.

Already present, keep: `upload_dir`, `max_upload_bytes`, `s3_bucket`, `s3_region`, `aws_access_key_id`, `aws_secret_access_key`.

To add:

```
STORAGE_BACKEND=local            # local | s3 — explicit, replaces "S3 if creds happen to be set"
S3_ENDPOINT_URL=                 # required for Cloudflare R2
ALLOWED_UPLOAD_TYPES=            # comma-separated MIME allowlist
USER_STORAGE_QUOTA_BYTES=
UPLOADS_PER_HOUR=
DOWNLOAD_TOKEN_TTL_SECONDS=300
FILE_PURGE_AFTER_DAYS=30
```

Note the behaviour change: today the backend is chosen implicitly by whether S3 credentials are set, which means adding credentials for an unrelated feature silently reroutes all uploads. Make it explicit via `STORAGE_BACKEND`, defaulting to `local`.

**Do not hardcode any absolute path.** In particular, do not introduce `/opt/myapp/...`; nothing in this repo uses that path, and `scripts/deploy.sh` works from repo-relative directories. The current default `upload_dir="./uploads"` is CWD-relative and sits inside the deploy tree, which is fragile across deploys — recommend an absolute path supplied via `UPLOAD_DIR` in the VPS `.env`, created and owned by the service user, and document it in `docs/` rather than baking it into code.

# Deployment

* The upload directory must **not** be exposed directly by Caddy. All reads go through FastAPI so auth and visibility are enforced. Confirm the Caddyfile in `docs/SSL_CADDY.md` does not serve it.
* Caddy will reject an oversized body before FastAPI ever sees it, so `request_body max_size` must be set to match `MAX_UPLOAD_SIZE`, and the two values must be documented together. Note the resulting error is a Caddy-level 413, not the API's JSON error shape.
* Note in `docs/` that the upload directory must survive deploys and be included in backups; a database backup alone is not a full restore.

---

# Deliverables

1. `StorageBackend` interface plus `LocalStorageBackend` and a working `S3StorageBackend` (S3 + R2).
2. `get_storage_backend` dependency and config-driven selection.
3. Updated `FileRecord` model **and** matching `_COLUMNS_TO_ENSURE` entries.
4. Updated Pydantic schemas, keeping existing response fields intact.
5. Streaming upload with incremental size check and checksum (D3).
6. Streaming download with range, ETag, and correct disposition headers (R2).
7. Signed download tokens plus the Angular change that uses them (D1).
8. Quota, rate limit, and `GET /files/usage` (R3).
9. Filtered, paginated listing with the new composite index (R4).
10. Soft delete plus purge routine (R6).
11. Visibility handling and `PATCH /files/{id}` (R7).
12. Migration/backfill command for local → S3/R2 (R8).
13. `boto3`/`aioboto3` and the type-sniffing library added to `backend/requirements.txt`.
14. Angular: a reusable attachment component consistent with the existing UI (see the UI rules — reuse the current design system, do not introduce a new one), wired into at least task detail, and an updated `FilesService`.
15. Tests in `backend/app/tests/test_files.py` covering: traversal rejection, type-sniff rejection, oversized stream abort, quota 413, rate limit 429, range request, token download, soft delete then purge, and public visibility.

# Non-Goals

Explicitly out of scope — do not implement, but note where a hook would go:

* Antivirus scanning and EXIF stripping.
* Thumbnail generation (reserve the key slot only).
* Multipart/resumable uploads for very large files.
* Offline queueing of uploads — `sync.service.ts` deliberately bypasses them; keep that.
* Introducing Alembic.
* Cross-user file sharing beyond the existing task-collaboration model.

# Acceptance Criteria

1. `pytest` passes from `backend/`, including the pre-existing `test_files.py` assertions unmodified.
2. Every existing endpoint keeps its current path, method, status code, and response fields.
3. Rows created before this change remain listable, downloadable, and deletable.
4. Clicking a file in the Angular files page opens or downloads it successfully — no 401.
5. Uploading a `.svg` or `.html` file is either rejected or served as an attachment, never inline.
6. `grep` finds no `boto3` or `pathlib` storage usage outside the backend implementations.
7. Switching `STORAGE_BACKEND=s3` requires no change to Angular, routes, schema, or services.
8. Nothing outside `backend/app/modules/files/` constructs a storage path or URL.

# Code Quality

Follow the conventions already in this codebase rather than generic best practice:

* Module layout is `api.py` / `service.py` / `repository.py` / `models.py` / `schemas.py`. There is no `router.py` anywhere — do not create one.
* Routers are declared as `APIRouter(prefix=..., tags=[...])` and registered in `main.py` under `/api/v1`.
* Handlers are `async def` with `user: User = Depends(get_current_user)` and `db: AsyncSession = Depends(get_db)`.
* SQLAlchemy 2.x async style: `Mapped`, `mapped_column`, `select()`, `AsyncSession`.
* Errors are raised as `fastapi.HTTPException` from the service layer — that is the established pattern; there are no global exception handlers to hook into.
* Keep handlers thin, business logic in services, database access in repositories, and byte handling only inside storage backends.
* Type hints throughout. Do not add comments that restate the code.

Report at the end: what you changed, what you deliberately skipped, and any assumption you had to make.
