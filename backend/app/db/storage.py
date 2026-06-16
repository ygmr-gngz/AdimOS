import re
import unicodedata
from app.db.supabase import get_supabase_client

def slugify_filename(filename: str) -> str:
    """Türkçe karakter ve boşlukları temizler, Supabase-safe key üretir."""
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")
    filename = re.sub(r"[^\w\.\-]", "_", filename)
    filename = re.sub(r"_+", "_", filename)
    return filename.strip("_").lower()

def _clean_path(file_name: str) -> str:
    """Path'teki sadece dosya adı kısmını slugify eder, klasör yapısını korur."""
    parts = file_name.split("/")
    parts[-1] = slugify_filename(parts[-1])
    return "/".join(parts)

def upload_file(bucket_name: str, file_name: str, file_data: bytes):
    supabase = get_supabase_client()
    clean = _clean_path(file_name)
    response = supabase.storage.from_(bucket_name).upload(clean, file_data)
    return response

def download_file(bucket_name: str, file_name: str, download_path: str):
    supabase = get_supabase_client()
    clean = _clean_path(file_name)
    response = supabase.storage.from_(bucket_name).download(clean)
    with open(download_path, "wb") as file:
        file.write(response)
    return download_path

def delete_file(bucket_name: str, file_name: str):
    supabase = get_supabase_client()
    clean = _clean_path(file_name)
    response = supabase.storage.from_(bucket_name).remove([clean])
    return response
