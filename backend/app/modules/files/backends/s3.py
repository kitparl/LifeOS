from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from io import BytesIO

import anyio
from fastapi import HTTPException, status

from app.core.config import Settings
from app.modules.files.backends.base import ObjectStat, StorageBackend, StoredObject


class S3StorageBackend(StorageBackend):
    def __init__(self, settings: Settings):
        if not settings.s3_bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        self.settings = settings
        self.bucket = settings.s3_bucket

    def _client(self):
        import boto3

        kwargs: dict = {
            "region_name": self.settings.s3_region,
            "aws_access_key_id": self.settings.aws_access_key_id or None,
            "aws_secret_access_key": self.settings.aws_secret_access_key or None,
        }
        if self.settings.s3_endpoint_url:
            kwargs["endpoint_url"] = self.settings.s3_endpoint_url
        return boto3.client("s3", **kwargs)

    async def save(
        self,
        key: str,
        stream: AsyncIterator[bytes],
        content_type: str,
    ) -> StoredObject:
        digest = hashlib.sha256()
        buf = BytesIO()
        size = 0
        async for chunk in stream:
            buf.write(chunk)
            digest.update(chunk)
            size += len(chunk)
        body = buf.getvalue()

        def _put() -> None:
            self._client().put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
            )

        await anyio.to_thread.run_sync(_put)
        return StoredObject(key=key, size_bytes=size, checksum_sha256=digest.hexdigest())

    async def open(self, key: str) -> AsyncIterator[bytes]:
        def _get() -> bytes:
            try:
                resp = self._client().get_object(Bucket=self.bucket, Key=key)
                return resp["Body"].read()
            except Exception as exc:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File content missing") from exc

        data = await anyio.to_thread.run_sync(_get)

        async def _iter() -> AsyncIterator[bytes]:
            offset = 0
            while offset < len(data):
                end = min(offset + 64 * 1024, len(data))
                yield data[offset:end]
                offset = end

        return _iter()

    async def delete(self, key: str) -> None:
        def _del() -> None:
            self._client().delete_object(Bucket=self.bucket, Key=key)

        await anyio.to_thread.run_sync(_del)

    async def exists(self, key: str) -> bool:
        def _head() -> bool:
            try:
                self._client().head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False

        return await anyio.to_thread.run_sync(_head)

    async def stat(self, key: str) -> ObjectStat | None:
        def _head() -> ObjectStat | None:
            try:
                resp = self._client().head_object(Bucket=self.bucket, Key=key)
                return ObjectStat(size_bytes=int(resp["ContentLength"]), mtime=None)
            except Exception:
                return None

        return await anyio.to_thread.run_sync(_head)

    def public_url(self, key: str) -> str | None:
        # Bucket stays private; public access is proxied/presigned by the app.
        return None

    async def signed_url(self, key: str, ttl_seconds: int) -> str:
        def _presign() -> str:
            return self._client().generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=ttl_seconds,
            )

        return await anyio.to_thread.run_sync(_presign)
