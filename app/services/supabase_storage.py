import io
from pathlib import Path
from supabase import create_client, Client
from app.config.settings import settings
from app.config.logger import logger
import asyncer

class SupabaseStorage:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket = settings.SUPABASE_BUCKET

    def upload_file_path(self, local_path: Path, bucket_path: str) -> str:
        """Uploads a local file to Supabase and returns the public URL."""
        logger.info(f"Uploading {local_path} to Supabase at {bucket_path}")
        with open(local_path, "rb") as f:
            res = self.client.storage.from_(self.bucket).upload(
                file=f,
                path=bucket_path,
                file_options={"content-type": "audio/mpeg", "upsert": "true"}
            )
        return self.get_public_url(bucket_path)

    def upload_file_bytes(self, file_bytes: bytes, bucket_path: str, content_type: str = "audio/mpeg") -> str:
        """Uploads raw bytes to Supabase and returns the public URL."""
        logger.info(f"Uploading bytes to Supabase at {bucket_path}")
        res = self.client.storage.from_(self.bucket).upload(
            file=file_bytes,
            path=bucket_path,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        return self.get_public_url(bucket_path)

    def get_public_url(self, bucket_path: str) -> str:
        """Retrieves the public URL for a given path in the bucket."""
        return self.client.storage.from_(self.bucket).get_public_url(bucket_path)

    def download_file(self, bucket_path: str, local_path: Path):
        """Downloads a remote file from Supabase to a local path."""
        logger.info(f"Downloading {bucket_path} to {local_path}")
        res = self.client.storage.from_(self.bucket).download(bucket_path)
        with open(local_path, "wb") as f:
            f.write(res)
