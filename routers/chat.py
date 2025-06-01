import json
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
    Handles a chat request using various input sources such as images, documents, and questions. The endpoint supports
    streaming the response back to the client while processing the input data. Additionally, it handles events like token
    calculations, semantic search for documents, and error reporting. All interactions are logged and saved into the
    database for record-keeping and diagnostics.

    :param session_id: The unique identifier for an ongoing chat session. Used to track and log chats.
    :type session_id: str

    :param question: The primary input to the chat system, which determines the knowledge or reasoning process.
    :type question: str

    :param provider: The service provider which will handle AI/LLM query (e.g., OpenAI, Hugging Face, etc.).
    :type provider: str

    :param model: The AI/LLM model to be used for generating the response.
    :type model: str

    :param our_image_processing_algo: A flag indicating whether to use the internal image processing algorithm.
    :type our_image_processing_algo: bool

    :param document_semantic_search: A flag that, if enabled, allows performing a semantic search based on the provided question.
    :type document_semantic_search: bool

    :param current_user: The current user authenticated in the session. Contains user-specific metadata.
    :type current_user: User

    :param upload_image: A list of uploaded image files to be processed for the chat session. Defaults to None if not provided.
    :type upload_image: Optional[List[UploadFile]]

    :param upload_document: A list of uploaded document files to be processed for the chat session. Defaults to None if not provided.
    :type upload_document: Optional[List[UploadFile]]

    :param db: The database session dependency for performing operations like storing session details or logs.
    :type db: Session

    :return: A streaming HTTP response containing the chat results in real time. Includes metadata such as tokens used,
            first response latency, and other metrics.
    :rtype: StreamingResponse
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
                    # if the model is reasoning model, then first the streaming will be like this
                    # {"type": "reasoning", "data": content}
                    # then it will stream normally like this
                    # {"type": "content", "data": content}
                    # else it will stream normally like above
                    # and the last chunk will be the metadata of the tokens like this
                    # {"type": "metadata", "data": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": total_tokens}}

                    if chunk["type"] == "metadata":
                        if "prompt_tokens" in chunk["data"]:
                            input_tokens += chunk["data"]["prompt_tokens"]
                        if "completion_tokens" in chunk["data"]:
                            output_tokens += chunk["data"]["completion_tokens"]
                        print(chunk)
                        yield json.dumps(chunk)
                    else:
                        full_answer += chunk["data"]
                        print(chunk)
                        yield json.dumps(chunk)

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
