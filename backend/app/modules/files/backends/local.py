from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import HTTPException, status

from app.modules.files.backends.base import ObjectStat, StorageBackend, StoredObject


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if not candidate.is_relative_to(self.root):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        return candidate

    async def save(
        self,
        key: str,
        stream: AsyncIterator[bytes],
        content_type: str,
    ) -> StoredObject:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_")
        try:
            with os.fdopen(fd, "wb") as tmp:
                async for chunk in stream:
                    tmp.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            os.replace(tmp_name, path)
        except Exception:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
        return StoredObject(key=key, size_bytes=size, checksum_sha256=digest.hexdigest())

    async def open(self, key: str) -> AsyncIterator[bytes]:
        path = self._resolve(key)
        if not path.is_file():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File content missing")

        async def _iter() -> AsyncIterator[bytes]:
            with path.open("rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk

        return _iter()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.is_file():
            path.unlink()

    async def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).is_file()
        except HTTPException:
            return False

    async def stat(self, key: str) -> ObjectStat | None:
        try:
            path = self._resolve(key)
        except HTTPException:
            return None
        if not path.is_file():
            return None
        st = path.stat()
        return ObjectStat(size_bytes=st.st_size, mtime=st.st_mtime)

    def public_url(self, key: str) -> str | None:
        return None

    async def signed_url(self, key: str, ttl_seconds: int) -> str:
        # Local backend has no native signed URLs; callers use app download tokens.
        raise NotImplementedError("Local storage uses application download tokens")
