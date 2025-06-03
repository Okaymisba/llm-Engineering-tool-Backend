import json
import logging
import time
from typing import Optional, Annotated, List

from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
# from starlette.exceptions import ClientDisconnect # Good to be aware of this for more specific handling if needed

from functions.extract_document_data.extract_document_data import extract_document_data
from functions.extract_image_data.extract_image_data import extract_image_data
from functions.semantic_search.semantic_search import semantic_search
from models import get_db
from models.model_operations.chat_session.add_chat_in_chat_session import add_chat_in_chat_session
from models.user import User
from response.generate_response_streaming import generate_response_streaming
from routers.auth import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat")
async def chat(
        request: Request, # Added Request
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
    start_time = time.time() * 1000

    # Outer try-except for setup errors before streaming starts
    try:
        if upload_image:
            for image_file_in_loop in upload_image:
                image_data.append(extract_image_data(image_file_in_loop.file))

        if upload_document:
            for document_file_in_loop in upload_document:
                doc_data = await extract_document_data(document_file_in_loop)
                document_data.append(doc_data)

                if document_semantic_search:
                    hits = semantic_search(question, [doc_data])
                    if hits:
                        document_hits = hits

        async def stream_response():
            full_answer = ""
            input_tokens = 0
            output_tokens = 0
            first_chunk_time = None
            response_logged_to_db = False
            client_disconnected_during_streaming = False
            error_during_streaming = None

            try:
                async for chunk in generate_response_streaming(
                        provider=provider,
                        model=model,
                        question=question,
                        image_data=image_data,
                        document_data=document_data
                ):
                    if not client_disconnected_during_streaming and await request.is_disconnected():
                        client_disconnected_during_streaming = True
                        logger.info(f"Client disconnected for session {session_id}. Backend will continue processing and log results.")
                        # Stop yielding, but continue processing loop to get full answer and tokens.

                    if first_chunk_time is None and (chunk["type"] == "content" or chunk["type"] == "reasoning") and chunk.get("data"):
                        first_chunk_time = time.time() * 1000

                    if chunk["type"] == "metadata":
                        if "prompt_tokens" in chunk["data"]:
                            input_tokens += chunk["data"]["prompt_tokens"]
                        if "completion_tokens" in chunk["data"]:
                            output_tokens += chunk["data"]["completion_tokens"]
                        if not client_disconnected_during_streaming:
                            yield json.dumps(chunk) + "\n"
                    else: # "content" or "reasoning"
                        full_answer += chunk["data"]
                        if not client_disconnected_during_streaming:
                            yield json.dumps(chunk) + "\n"

            except Exception as e:
                error_during_streaming = f"Error during response generation stream for session {session_id}: {str(e)}"
                logger.error(error_during_streaming)
                if not full_answer: # Ensure error is part of the answer if no content was generated
                    full_answer = error_during_streaming

                if not client_disconnected_during_streaming and not await request.is_disconnected():
                    try:
                        yield json.dumps({"type": "error", "data": str(e)}) + "\n"
                    except Exception as yield_e:
                        logger.warning(f"Could not yield error to client for session {session_id}: {str(yield_e)}")
                        client_disconnected_during_streaming = True # Assume client is gone

            finally:
                if not response_logged_to_db:
                    response_logged_to_db = True
                    latency_val = int(first_chunk_time - start_time) if first_chunk_time and start_time > 0 else 0

                    current_status_code = 500
                    final_answer_to_log = full_answer

                    if error_during_streaming:
                        final_answer_to_log = error_during_streaming # Prioritize error message
                        current_status_code = 500
                    elif client_disconnected_during_streaming:
                        if full_answer:
                            current_status_code = 200 # Got some answer, client left
                            final_answer_to_log = full_answer
                        else:
                            current_status_code = 503 # Client disconnected before any answer was formed
                            final_answer_to_log = "Response generation was in progress when client disconnected; no primary content was generated."
                    elif full_answer: # Normal completion with an answer
                        current_status_code = 200
                    else: # No error, no disconnect, but also no answer (should be rare)
                        final_answer_to_log = "No content was generated by the model."
                        current_status_code = 204 # No content

                    logger.info(f"Finalizing chat session {session_id} in 'finally' block. Client disconnected: {client_disconnected_during_streaming}, Status: {current_status_code}, Error during stream: {error_during_streaming is not None}")
                    add_chat_in_chat_session(
                        session_id=session_id,
                        belongs_to=current_user.id,
                        document=document_data,
                        image=image_data,
                        question=question,
                        answer=final_answer_to_log,
                        model=model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        request_latency_ms=latency_val,
                        status_code=current_status_code,
                        document_hits=document_hits,
                        db=db
                    )

        return StreamingResponse(stream_response(), media_type="application/x-ndjson")

    except Exception as e:
        # This catches errors in the main /chat endpoint setup, *before* stream_response() is called
        # These are critical setup errors.
        outer_error_message = f"Critical error processing request setup for session {session_id}: {str(e)}"
        logger.error(outer_error_message)

        # Attempt to log this critical setup error to DB
        # Check if essential details like session_id, current_user, db, model are available
        # It's possible they are not if the error is very early (e.g. dependency injection failure for db)
        # but session_id and model are Form parameters, so they should be available if parsing got that far.
        # current_user depends on auth.
        # This is a best-effort logging.
        try:
            if session_id and hasattr(current_user, 'id') and db and model:
                add_chat_in_chat_session(
                    session_id=session_id,
                    belongs_to=current_user.id, # Make sure current_user is resolved
                    document=None,
                    image=None,
                    question=question if 'question' in locals() else "N/A due to early error",
                    answer=outer_error_message,
                    model=model if 'model' in locals() else "N/A due to early error",
                    input_tokens=0,
                    output_tokens=0,
                    request_latency_ms=int(time.time() * 1000 - start_time), # time since request start
                    status_code=500, # Internal server error for setup issues
                    document_hits=None,
                    db=db
                )
            else:
                logger.error(f"Could not log critical setup error to DB for session {session_id} due to missing core data (user, db, or model).")
        except Exception as db_log_err:
            logger.error(f"Failed to log critical setup error to DB for session {session_id}: {str(db_log_err)}")

        raise HTTPException(status_code=500, detail=outer_error_message)
