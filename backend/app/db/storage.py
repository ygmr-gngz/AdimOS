from app.db.supabase import get_supabase_client

def upload_file(bucket_name:str, file_name:str, file_data: bytes):
    supabase = get_supabase_client()
    response = supabase.storage.from_(bucket_name).upload(file_name, file_data)
    return response

def download_file(bucket_name:str, file_name:str, download_path:str):
    supabase = get_supabase_client()
    response = supabase.storage.from_(bucket_name).download(file_name)
    with open(download_path, "wb") as file:
        file.write(response)
    return download_path

def delete_file(bucket_name:str, file_name:str):
    supabase = get_supabase_client()
    response = supabase.storage.from_(bucket_name).remove([file_name])
    return response
