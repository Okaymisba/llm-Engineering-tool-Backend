from supabase import create_client, Client
from dotenv import load_dotenv
import os
import jwt
from typing import Dict, Any
import requests

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

def get_supabase_client() -> Client:
    """
    Returns the initialized Supabase client instance.
    
    Returns:
        Client: The Supabase client instance
    """
    return supabase

def decode_jwt_token(access_token: str) -> Dict[str, Any]:
    """
    Decodes a JWT access token using Supabase's JWT secret.
    
    Args:
        access_token (str): The JWT access token to decode
        
    Returns:
        Dict[str, Any]: The decoded token payload
        
    Raises:
        jwt.InvalidTokenError: If the token is invalid or expired
    """
    try:
        # Supabase uses the JWT secret from the project settings
        # This is the same secret used to sign the JWT tokens
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            raise ValueError("SUPABASE_JWT_SECRET environment variable is not set")
            
        # Decode the token
        decoded_token = jwt.decode(
            access_token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase doesn't set the 'aud' claim
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")


def download_file_from_bucket(file_url: str, local_path: str) -> bool:
    try:
        response = requests.get(file_url, stream=True)
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def delete_file_from_bucket(file_url: str):
    bucket, path = parse_supabase_url(file_url)
    supabase.storage.from_("files").remove([path])

def parse_supabase_url(file_url: str):
    # Example: https://xyz.supabase.co/storage/v1/object/public/bucket_name/file.pdf
    parts = file_url.split("/object/public/")[-1]
    bucket, *file_parts = parts.split("/")
    path = "/".join(file_parts)
    return bucket, path

def insert_embeddings(document_uuid: str, embeddings: list[list[float]]):
    rows = [{"document_id": document_uuid, "embedding": e} for e in embeddings]
    supabase.table("embeddings").insert(rows).execute()