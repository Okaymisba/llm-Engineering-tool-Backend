from supabase import create_client, Client
from dotenv import load_dotenv
import os
import jwt
from typing import Dict, Any

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



# access_token="eyJhbGciOiJIUzI1NiIsImtpZCI6IldhRDRDVk4xcm03UkZpRG4iLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL25wenhyd2VnamZ2cHh2b2ppbnBtLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJiMWRmMjZhMS0xYzc4LTQ4NjQtODlkMS05NDMzODNhYmQzZWMiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQ5NzMyNjY0LCJpYXQiOjE3NDk3MjkwNjQsImVtYWlsIjoiaXJmYW5zb29tcm8zNzBAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCIsImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jS3ZnNVd3TWJLLVl6bF9CVzJwZE95eXdYY0hhNWt0XzNaQUFBdWEyUGZ6QVRvZ1FBcjA9czk2LWMiLCJlbWFpbCI6ImlyZmFuc29vbXJvMzcwQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmdWxsX25hbWUiOiJBYmR1bCBXYXNheSIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJBYmR1bCBXYXNheSIsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0t2ZzVXd01iSy1ZemxfQlcycGRPeXl3WGNIYTVrdF8zWkFBQXVhMlBmekFUb2dRQXIwPXM5Ni1jIiwicHJvdmlkZXJfaWQiOiIxMTI4MzMwNDU1NDE4ODAwODc2MTkiLCJzdWIiOiIxMTI4MzMwNDU1NDE4ODAwODc2MTkiLCJ1c2VybmFtZSI6Ildhc2F5MTIifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJvYXV0aCIsInRpbWVzdGFtcCI6MTc0OTcyOTA2NH1dLCJzZXNzaW9uX2lkIjoiZWQxMDkwZGEtMTZiYi00NjhiLTgzOGUtNWViZTZhMmM1ZWFkIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.kJhzQhk6ZzumiaWUwOQDXqopg8RiU-GDB6JQcWxLLM0"
# print(decode_jwt_token(access_token)["sub"])