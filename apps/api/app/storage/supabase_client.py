import functools
from supabase import create_client, Client
from app.config import settings


@functools.lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def upload_file(storage_path: str, content: bytes, content_type: str = "text/csv") -> None:
    client = get_supabase_client()
    client.storage.from_(settings.storage_bucket).upload(
        path=storage_path,
        file=content,
        file_options={"content-type": content_type},
    )


def download_file(storage_path: str) -> bytes:
    client = get_supabase_client()
    return client.storage.from_(settings.storage_bucket).download(storage_path)
