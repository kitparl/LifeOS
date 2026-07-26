from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class StoredObject:
    key: str
    size_bytes: int
    checksum_sha256: str | None = None


@dataclass(frozen=True)
class ObjectStat:
    size_bytes: int
    mtime: float | None = None


class StorageBackend(ABC):
    """Minimal storage interface. Business logic must not import pathlib/boto3."""

    @abstractmethod
    async def save(
        self,
        key: str,
        stream: AsyncIterator[bytes],
        content_type: str,
    ) -> StoredObject:
        ...

    @abstractmethod
    async def open(self, key: str) -> AsyncIterator[bytes]:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    async def stat(self, key: str) -> ObjectStat | None:
        ...

    @abstractmethod
    def public_url(self, key: str) -> str | None:
        ...

    @abstractmethod
    async def signed_url(self, key: str, ttl_seconds: int) -> str:
        ...
