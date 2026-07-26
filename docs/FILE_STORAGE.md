# File Storage & Uploads

LifeOS stores file bytes through the FastAPI `files` module. Browsers never read the upload directory directly — every download goes through authenticated (or public/token) API routes.

## Configuration

Set these in `backend/.env` (see `.env.example`):

| Variable | Default | Notes |
|----------|---------|-------|
| `STORAGE_BACKEND` | `local` | `local` or `s3`. Explicit — credentials alone do not switch backends. |
| `UPLOAD_DIR` | `./uploads` | Prefer an **absolute** path on the VPS, owned by the service user (e.g. `/var/lib/lifeos/uploads`). Relative paths are CWD-dependent and fragile across deploys. |
| `MAX_UPLOAD_BYTES` | 10485760 | Per-file cap. Keep in sync with Caddy (below). |
| `USER_STORAGE_QUOTA_BYTES` | 1 GiB | Soft-deleted files still count until purged. |
| `UPLOADS_PER_HOUR` | 100 | Per-user upload rate limit. |
| `DOWNLOAD_TOKEN_TTL_SECONDS` | 300 | Short-lived tokens for `<a href>` / `<img src>`. |
| `FILE_PURGE_AFTER_DAYS` | 30 | Soft-deleted rows older than this are removable via admin purge. |
| `ALLOWED_UPLOAD_TYPES` | (images, pdf, text, office, audio) | Comma-separated MIME allowlist. |
| `S3_BUCKET` / `S3_REGION` / `S3_ENDPOINT_URL` | | `S3_ENDPOINT_URL` is required for Cloudflare R2. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | | Used when `STORAGE_BACKEND=s3`. |

## Caddy

The Caddyfile in [SSL_CADDY.md](SSL_CADDY.md) reverse-proxies to FastAPI only. It must **not** serve the upload directory as static files.

Caddy rejects oversized bodies before FastAPI sees them. Set `request_body` max size to match `MAX_UPLOAD_BYTES`:

```caddyfile
yourdomain.com {
    request_body {
        max_size 10MB
    }
    reverse_proxy localhost:8000
    ...
}
```

Note: a Caddy-level oversize rejection returns Caddy’s HTML **413**, not the API’s JSON error shape.

## Deploys and backups

- `scripts/deploy.sh` rebuilds `backend/static/` but does not manage uploads. Keep `UPLOAD_DIR` **outside** the git tree (or at least outside paths wiped by deploy) so files survive `git pull` / static rebuilds.
- A database backup alone is **not** a full restore when using local storage — include the upload directory in backups.
- Switching `STORAGE_BACKEND=s3` needs no Angular, route, or schema change. Migrate existing local rows with:

```bash
cd backend && .venv/bin/python -m app.modules.files.backfill --target s3
# After verification:
.venv/bin/python -m app.modules.files.backfill --target s3 --delete-local
```

## Soft delete

`DELETE /api/v1/files/{id}` sets `deleted_at` and returns 204; bytes stay on disk/bucket. Soft-deleted rows are hidden from list/get/download but **still count** toward quota until `POST /api/v1/files/admin/purge` (admin-only).
