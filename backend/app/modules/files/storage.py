from pathlib import Path

from app.core.config import Settings


class FileStorage:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @property
    def use_s3(self) -> bool:
        return bool(
            self.settings.s3_bucket
            and self.settings.aws_access_key_id
            and self.settings.aws_secret_access_key
        )

    def local_path(self, storage_key: str) -> Path:
        return self.upload_dir / storage_key

    async def save(
        self,
        user_id: str,
        file_id: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> tuple[str, str, str]:
        safe_name = Path(filename).name
        if self.use_s3:
            key = f"{user_id}/{file_id}/{safe_name}"
            self._upload_s3(key, content, content_type)
            url = (
                f"https://{self.settings.s3_bucket}.s3."
                f"{self.settings.s3_region}.amazonaws.com/{key}"
            )
            return "s3", key, url

        rel_key = f"{user_id}/{file_id}_{safe_name}"
        path = self.local_path(rel_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        url = f"/api/v1/files/{file_id}/content"
        return "local", rel_key, url

    async def delete(self, storage_backend: str, storage_key: str) -> None:
        if storage_backend == "s3" and self.use_s3:
            self._delete_s3(storage_key)
            return
        path = self.local_path(storage_key)
        if path.exists():
            path.unlink()

    def _s3_client(self):
        import boto3

        return boto3.client(
            "s3",
            region_name=self.settings.s3_region,
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key,
        )

    def _upload_s3(self, key: str, content: bytes, content_type: str) -> None:
        client = self._s3_client()
        client.put_object(
            Bucket=self.settings.s3_bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    def _delete_s3(self, key: str) -> None:
        client = self._s3_client()
        client.delete_object(Bucket=self.settings.s3_bucket, Key=key)
