import time
import logging
from typing import Optional, Annotated, List

from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from functions.extract_document_data.extract_document_data import extract_document_data
from functions.extract_image_data.extract_image_data import extract_image_data
from functions.semantic_search.semantic_search import semantic_search
from models import get_db
from models.chat_sessions import ChatSession
from models.user import User
from response.generate_response import generate_response
from routers.auth import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat")
async def chat(
        session_id: Annotated[str, Form()],
        question: Annotated[str, Form()],
        provider: Annotated[str, Form()],
        model: Annotated[str, Form()],
        our_image_processing_algo: Annotated[bool, Form()],
        document_semantic_search: Annotated[bool, Form()],
        current_user: Annotated[User, Depends(get_current_user)],
        upload_image: Optional[List[UploadFile]] = File(None),
        upload_document: Optional[List[UploadFile]] = File(None),
        db: Session = Depends(get_db)
):
    image_data = []
    document_data = []
    document_hits = None
    start_time = time.time() * 1000  # Start time in milliseconds

    try:
        if upload_image:
            for image in upload_image:
                image_data.append(extract_image_data(image.file))

        if upload_document:
            for document in upload_document:
                doc_data = await extract_document_data(document)
                document_data.append(doc_data)
                
                # If semantic search is enabled, find relevant document chunks
                if document_semantic_search:
                    hits = semantic_search(question, [doc_data])
                    if hits:
                        document_hits = hits

        async def stream_response():
            full_answer = ""
            input_tokens = 0
            output_tokens = 0
            status_code = 200
            first_chunk_time = None
            
            try:
                async for chunk, metadata in generate_response(
                        provider=provider,
                        model=model,
                        question=question,
                        image_data=image_data,
                        document_data=document_data,
                        user_id=current_user.id,
                        stream=True
                ):
                    if first_chunk_time is None:
                        first_chunk_time = time.time() * 1000  # Time of first chunk in milliseconds
                    
                    full_answer += chunk
                    input_tokens = metadata.get("input_tokens", 0)
                    output_tokens = metadata.get("output_tokens", 0)
                    status_code = metadata.get("status_code", 200)
                    yield chunk

                # Calculate latency (time between request and first chunk)
                latency = int(first_chunk_time - start_time) if first_chunk_time else 0

                # Save the full response and metadata to DB after streaming is done
                chat_session = ChatSession(
                    session_id=session_id,
                    belongs_to=current_user.id,
                    document=str(document_data),
                    image=str(image_data),
                    question=question,
                    answer=full_answer,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    request_latency_ms=latency,
                    status_code=status_code,
                    document_hits=document_hits
                )
                db.add(chat_session)
                db.commit()
                db.refresh(chat_session)

            except Exception as e:
                # Handle any errors during streaming
                error_message = f"Error during response generation: {str(e)}"
                logger.error(error_message)
                yield error_message
                
                # Save error state to database
                chat_session = ChatSession(
                    session_id=session_id,
                    belongs_to=current_user.id,
                    document=str(document_data),
                    image=str(image_data),
                    question=question,
                    answer=error_message,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    request_latency_ms=int(time.time() * 1000 - start_time),
                    status_code=500,
                    document_hits=document_hits
                )
                db.add(chat_session)
                db.commit()
                db.refresh(chat_session)

        return StreamingResponse(stream_response(), media_type="text/plain")

    except Exception as e:
        # Handle any errors before streaming starts
        error_message = f"Error processing request: {str(e)}"
        logger.error(error_message)
        
        # Save error state to database
        chat_session = ChatSession(
            session_id=session_id,
            belongs_to=current_user.id,
            document=str(document_data),
            image=str(image_data),
            question=question,
            answer=error_message,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            request_latency_ms=int(time.time() * 1000 - start_time),
            status_code=500,
            document_hits=document_hits
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
        raise HTTPException(status_code=500, detail=error_message)
