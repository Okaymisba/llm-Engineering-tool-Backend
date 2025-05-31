import logging
import time
from typing import Optional, Annotated, List

from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

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
    """
    Handles a chat request by generating a response based on the given parameters
    and optionally using additional context from uploaded documents or images.

    The function takes in the following parameters:

    - `session_id`: A unique identifier for the chat session to store the
      conversation history.
    - `question`: The main query or input text to be answered or processed
      by the model.
    - `provider`: The provider name for the model to be queried.
    - `model`: The specific model identifier of the provider to be queried.
    - `our_image_processing_algo`: A boolean indicating whether to use our
      image processing algorithm.
    - `document_semantic_search`: A boolean indicating whether to use semantic
      search on the uploaded documents.
    - `current_user`: The authenticated user performing the chat request.
    - `upload_image`: An optional list of image files to be used as context.
    - `upload_document`: An optional list of document files to be used as context.
    - `db`: A database session used to store the conversation history.

    The function returns a StreamingResponse containing the generated response
    as a sequence of text chunks. The response is generated using the
    `generate_response` function, which takes in the same parameters as this
    function, plus a `stream` parameter set to `True`. The response is processed
    in chunks, and each chunk is yielded to the caller as a text string.

    The function also logs any exceptions that occur during response generation
    and stores the conversation history in the database.
    """
    image_data = []
    document_data = []
    document_hits = None
    start_time = time.time() * 1000

    try:
        if upload_image:
            for image in upload_image:
                image_data.append(extract_image_data(image.file))

        if upload_document:
            for document in upload_document:
                doc_data = await extract_document_data(document)
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

            try:
                async for chunk in generate_response_streaming(
                        provider=provider,
                        model=model,
                        question=question,
                        image_data=image_data,
                        document_data=document_data
                ):
                    if first_chunk_time is None:
                        first_chunk_time = time.time() * 1000

                    if isinstance(chunk, str):
                        full_answer += chunk
                        yield chunk

                    elif isinstance(chunk, dict):
                        if "prompt_tokens" in chunk:
                            input_tokens += chunk["prompt_tokens"]
                        if "completion_tokens" in chunk:
                            output_tokens += chunk["completion_tokens"]

                latency = int(first_chunk_time - start_time) if first_chunk_time else 0

                add_chat_in_chat_session(
                    session_id=session_id,
                    belongs_to=current_user.id,
                    document=document_data,
                    image=image_data,
                    question=question,
                    answer=full_answer,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    request_latency_ms=latency,
                    status_code=200,
                    document_hits=document_hits,
                    db=db)

            except Exception as e:
                # Handle any exceptions that occur during response generation
                error = f"Error during response generation: {str(e)}"
                logger.error(error)
                yield error

                add_chat_in_chat_session(
                    session_id=session_id,
                    belongs_to=current_user.id,
                    document=document_data if document_data else None,
                    image=image_data if image_data else None,
                    question=question,
                    answer=error,
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    request_latency_ms=int(time.time() * 1000 - start_time),
                    status_code=500,
                    document_hits=document_hits,
                    db=db)

        return StreamingResponse(stream_response(), media_type="text/plain")

    except Exception as e:
        # Handle any exceptions that occur during request processing
        error_message = f"Error processing request: {str(e)}"
        logger.error(error_message)

        add_chat_in_chat_session(
            session_id=session_id,
            belongs_to=current_user.id,
            document=document_data if document_data else None,
            image=image_data if image_data else None,
            question=question,
            answer=error_message,
            model=model,
            input_tokens=0,
            output_tokens=0,
            request_latency_ms=int(time.time() * 1000 - start_time),
            status_code=500,
            document_hits=document_hits,
            db=db)

        raise HTTPException(status_code=500, detail=error_message)
