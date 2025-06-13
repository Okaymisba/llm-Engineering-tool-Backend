import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request
from services.supabase_client import (
    download_file_from_bucket, 
    delete_file_from_bucket, 
    insert_embeddings
)
from functions.extract_document_data.parse_pdf import parse_pdf
from functions.extract_document_data.parse_txt_file import parse_txt_file
from functions.extract_document_data.parse_docx import parse_docx
from functions.chunk_text.chunk_text import chunk_document_text
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

TMP_DIR = "tmp_files"

@router.post("/webhook/supabase-file-upload")
async def supabase_webhook(request: Request):
    payload = await request.json()
    
    # # Extract document metadata from frontend-sent payload
    document_uuid = payload["record"]["id"]
    file_name = payload["record"]["filename"]
    file_url = payload["record"]["file_url"]

    if not all([document_uuid, file_name, file_url]):
        raise HTTPException(status_code=400, detail="Missing file metadata")
   
    
    local_path = os.path.join(TMP_DIR, file_name)
    os.makedirs(TMP_DIR, exist_ok=True)

    try:
        # Download file from Supabase storage
        download_success = download_file_from_bucket(file_url, local_path)
        if not download_success:
            raise HTTPException(status_code=500, detail="Failed to download file")

        # Extract extension from file name
        _, file_extension = os.path.splitext(file_name)

        # Parse file based on extension
        if file_extension == '.pdf':
            text = parse_pdf(local_path)
        elif file_extension == '.txt':
            text = parse_txt_file(local_path)
        elif file_extension == '.docx':
            text = parse_docx(local_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Split text into 1000-char chunks
        chunks = chunk_document_text(text, chunk_size=1000)

        # Generate embeddings
        embeddings = []
        model = SentenceTransformer('all-MiniLM-L6-v2')

        for chunk in chunks:
            embedding = model.encode(chunk)
            embeddings.append(embedding.tolist())  # Convert numpy array to list
            
        # Insert into embeddings table
        insert_embeddings(document_uuid=document_uuid, embeddings=embeddings)

        return {"status": "success", "message": "Document processed successfully"}

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

    finally:
        # Clean up
        if os.path.exists(local_path):
            os.remove(local_path)
        delete_file_from_bucket(file_url)
    return {"status": "success", "message": "Document processed successfully"}

@router.get("/health")
async def health_check():
    return {"status": "ok"}
