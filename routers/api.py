from typing import Annotated, List
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, File, UploadFile
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session
from models.__init__ import get_db
from models.user import User
from models.api_list import APIList
from models.documents import Documents
from auth import get_current_user
from functions.generate_api_key.generate_api_key import generate_api_key
from functions.extract_document_data.extract_document_data import extract_document_data
from functions.chunk_text.chunk_text import chunk_document_text
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter()

class GenApiResponse(BaseModel):
    api_key: str

class ApiKeyInfo(BaseModel):
    api_key: str
    label: str
    instructions: str
    total_tokens: int
    tokens_used: int
    tokens_remaining: int
    token_limit_per_day: int
    created_at: str
    last_used_at: str

class UpdateInstructionsRequest(BaseModel):
    instructions: str

class UpdateTokenLimitRequest(BaseModel):
    token_limit: int

class AddDocumentRequest(BaseModel):
    chunk_text: str

@router.post("/generate-api", response_model=GenApiResponse)
async def generate_api(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    label: str = None,
    token_limit: int = None,
    instructions: str = None
):
    # Check if user is verified
    if not current_user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="User account is not verified. Please verify your account first."
        )
    
    # Get max API keys limit from environment variable
    max_api_keys = int(os.getenv("MAX_API_KEYS", "3"))
    
    # Count existing API keys for the user
    existing_api_keys = db.query(APIList).filter(
        APIList.main_table_user_id == current_user.id
    ).count()
    
    # Check if user has reached the maximum limit
    if existing_api_keys >= max_api_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum API key limit reached. You can only create up to {max_api_keys} API keys."
        )
    
    # Generate new API key
    new_api_key = generate_api_key()
    
    # Set token limit (use environment variable if not provided)
    token_limit = token_limit or int(os.getenv("FREE_TOKENS", "1000"))
    
    # Create new API entry
    try:
        api_entry = APIList.create_api_entry(
            db=db,
            main_table_user_id=current_user.id,
            api_key=new_api_key,
            instructions=instructions,
            label=label,
            token_limit=token_limit
        )
        
        return GenApiResponse(api_key=new_api_key)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create API key: {str(e)}"
        )

@router.get("/api-keys", response_model=List[ApiKeyInfo])
async def get_user_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Retrieve all API keys associated with the current user.
    
    Returns:
        List of API key information including usage statistics and metadata.
    """
    try:
        api_keys = db.query(APIList).filter(
            APIList.main_table_user_id == current_user.id
        ).all()
        
        return [
            ApiKeyInfo(
                api_key=key.api_key,
                label=key.label,
                instructions=key.instructions,
                total_tokens=key.total_tokens,
                tokens_used=key.tokens_used,
                tokens_remaining=key.tokens_remaining,
                token_limit_per_day=key.token_limit_per_day,
                created_at=key.created_at.isoformat(),
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None
            ) for key in api_keys
        ]
    except Exception as e:
        logger.error(f"Error fetching API keys for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve API keys"
        )

@router.put("/api-keys/{api_key}/instructions")
async def update_api_instructions(
    api_key: str,
    request: UpdateInstructionsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Update the instructions for a specific API key.
    
    Args:
        api_key: The API key to update
        request: New instructions for the API key
        
    Returns:
        Success message if update was successful
    """
    try:
        api_entry = db.query(APIList).filter(
            APIList.api_key == api_key,
            APIList.main_table_user_id == current_user.id
        ).first()
        
        if not api_entry:
            raise HTTPException(
                status_code=404,
                detail="API key not found"
            )
        
        api_entry.instructions = request.instructions
        db.commit()
        
        return {"message": "Instructions updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating instructions for API key {api_key}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update instructions"
        )

@router.put("/api-keys/{api_key}/token-limit")
async def update_token_limit(
    api_key: str,
    request: UpdateTokenLimitRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Update the daily token limit for a specific API key.
    
    Args:
        api_key: The API key to update
        request: New token limit for the API key
        
    Returns:
        Success message if update was successful
    """
    try:
        api_entry = db.query(APIList).filter(
            APIList.api_key == api_key,
            APIList.main_table_user_id == current_user.id
        ).first()
        
        if not api_entry:
            raise HTTPException(
                status_code=404,
                detail="API key not found"
            )
        
        if request.token_limit < api_entry.tokens_used:
            raise HTTPException(
                status_code=400,
                detail="New token limit cannot be less than tokens already used"
            )
        
        api_entry.token_limit_per_day = request.token_limit
        api_entry.tokens_remaining = request.token_limit - api_entry.tokens_used
        db.commit()
        
        return {"message": "Token limit updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating token limit for API key {api_key}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update token limit"
        )

@router.post("/api-keys/{api_key}/documents")
async def add_document(
    api_key: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...)
):
    """
    Add a document to a specific API key. Supports PDF, DOCX, TXT, and image files.
    The document will be processed, extracted, and split into chunks before storage.
    
    Args:
        api_key: The API key to add the document to
        file: The document file to process (PDF, DOCX, TXT, or image)
        
    Returns:
        Success message with number of chunks created
    """
    try:
        # Validate API key ownership
        api_entry = db.query(APIList).filter(
            APIList.api_key == api_key,
            APIList.main_table_user_id == current_user.id
        ).first()
        
        if not api_entry:
            raise HTTPException(
                status_code=404,
                detail="API key not found"
            )
        
        # Extract data from the file
        extracted_data = await extract_document_data(file)
        
        if not extracted_data:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type or failed to extract data"
            )
        
        # Convert extracted data to string if it's not already
        if not isinstance(extracted_data, str):
            extracted_data = str(extracted_data)
        
        # Split the text into chunks
        chunks = chunk_document_text(extracted_data)
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No valid content found in the document"
            )
        
        # Create document entries for each chunk
        documents = []
        for chunk in chunks:
            document = Documents(
                chunk_text=chunk,
                api_id=api_entry.id
            )
            documents.append(document)
        
        # Add all documents to the database
        db.add_all(documents)
        db.commit()
        
        return {
            "message": "Document processed and added successfully",
            "chunks_created": len(chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document for API key {api_key}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process and add document"
        )

@router.delete("/api-keys/{api_key}")
async def delete_api_key(
    api_key: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Delete a specific API key and all associated documents.
    
    Args:
        api_key: The API key to delete
        
    Returns:
        Success message if API key was deleted successfully
    """
    try:
        api_entry = db.query(APIList).filter(
            APIList.api_key == api_key,
            APIList.main_table_user_id == current_user.id
        ).first()
        
        if not api_entry:
            raise HTTPException(
                status_code=404,
                detail="API key not found"
            )
        
        db.delete(api_entry)
        db.commit()
        
        return {"message": "API key deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key {api_key}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete API key"
        )
    
    

