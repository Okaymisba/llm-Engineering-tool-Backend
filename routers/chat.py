import json
import logging
import time
from typing import Optional, Annotated, List, Any

from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse

from functions.extract_document_data.extract_document_data import extract_document_data
from functions.extract_image_data.extract_image_data import extract_image_data
from functions.semantic_search.semantic_search import semantic_search
from response.generate_response_streaming import generate_response_streaming
from services.chat_session_operations import add_chat_session
from services.get_current_user import get_current_user
from utilities.count_tokens import count_tokens
from utilities.search_web.search_web import search_web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


async def _log_chat_session_bg_task(
        session_id_val: str,
        belongs_to_val: str,
        document_list_val: Optional[List[Any]],
        image_list_val: Optional[List[Any]],
        question_val: str,
        answer_val: str,
        model_val: str,
        input_tokens_val: int,
        output_tokens_val: int,
        request_latency_ms_val: int,
        status_code_val: int,
):
    """
    Logs the chat session details to Supabase asynchronously.
    """
    try:
        await add_chat_session(
            session_id=session_id_val,
            belongs_to=belongs_to_val,
            document=document_list_val,
            image=image_list_val,
            question=question_val,
            answer=answer_val,
            model=model_val,
            input_tokens=input_tokens_val,
            output_tokens=output_tokens_val,
            latency_ms=request_latency_ms_val,
            status=status_code_val
        )
        logger.info(f"Background task: Successfully logged chat session {session_id_val} to Supabase.")
    except Exception as e:
        logger.error(f"Background task: Error logging chat session {session_id_val} to Supabase: {str(e)}")


@router.post("/chat")
async def chat(
        request: Request,
        background_tasks: BackgroundTasks,  # Added BackgroundTasks
        session_id: Annotated[str, Form()],
        question: Annotated[str, Form()],
        provider: Annotated[str, Form()],
        model: Annotated[str, Form()],
        web_search: Annotated[bool, Form()],
        our_image_processing_algo: Annotated[bool, Form()],
        document_semantic_search: Annotated[bool, Form()],
        current_user: dict = Depends(get_current_user),
        upload_image: Optional[List[UploadFile]] = File(None),
        upload_document: Optional[List[UploadFile]] = File(None)
):
    """
    Handles the main chat endpoint which processes user input and performs various operations such as
    handling uploaded images or documents, performing web searches, and returning a streamed response
    with the generated content.

    This function integrates multiple asynchronous tasks including extracting data from images and
    documents, conducting web searches if enabled, and generating responses based on the provided or
    uploaded data. It supports streaming results back to the user in real-time.

    :param request: The HTTP request object representing the client's request.
    :type request: Request
    :param background_tasks: A container for background task operations to log chat sessions.
    :type background_tasks: BackgroundTasks
    :param session_id: A unique identifier for the ongoing session provided by the user.
    :type session_id: str
    :param question: The main question or query posed by the user.
    :type question: str
    :param provider: The provider service for model-based response generation.
    :type provider: str
    :param model: The specific AI model to use for generating responses.
    :type model: str
    :param web_search: A flag indicating whether a web search should be conducted.
    :type web_search: bool
    :param our_image_processing_algo: A flag indicating whether the image processing algorithm should
        be applied.
    :type our_image_processing_algo: bool
    :param document_semantic_search: A flag indicating whether semantic search should be conducted on
        the uploaded documents.
    :type document_semantic_search: bool
    :param current_user: A dictionary containing information about the currently authenticated user.
    :type current_user: dict
    :param upload_image: An optional list of image files uploaded by the user.
    :type upload_image: List[UploadFile] or None
    :param upload_document: An optional list of document files uploaded by the user.
    :type upload_document: List[UploadFile] or None
    :return: A streaming response object sending chunks of data in the NDJSON format.
    :rtype: StreamingResponse
    """
    image_data_list = []
    document_data_list = []
    web_search_results = []
    document_hits = None
    start_time = time.time() * 1000

    try:
        if upload_image:
            for image_file_in_loop in upload_image:
                image_data_list.append(extract_image_data(image_file_in_loop.file))

        if upload_document:
            for document_file_in_loop in upload_document:
                doc_data_content = await extract_document_data(document_file_in_loop)
                document_data_list.append(doc_data_content)

                if document_semantic_search:
                    hits = semantic_search(question, [doc_data_content])
                    if hits:
                        document_hits = hits

        async def stream_response():
            full_answer = ""
            input_tokens = 0
            output_tokens = 0
            first_chunk_time = None
            client_disconnected_during_streaming = False
            error_during_streaming_msg = None

            try:
                if web_search:
                    yield json.dumps({"type": "web_search", "data": "searching..."})
                    web_search_results.append(await search_web(question))
                    yield json.dumps({"type": "web_search", "data": web_search_results})

                async for chunk in generate_response_streaming(
                        provider=provider,
                        model=model,
                        question=question,
                        image_data=image_data_list,
                        document_data=document_data_list,
                        web_search_results=web_search_results
                ):
                    if not client_disconnected_during_streaming and await request.is_disconnected():
                        client_disconnected_during_streaming = True
                        logger.info(
                            f"Client disconnected for session {session_id} during generate_response_streaming. Backend will continue processing.")

                    if first_chunk_time is None and (
                            chunk["type"] == "content" or chunk["type"] == "reasoning") and chunk.get("data"):
                        first_chunk_time = time.time() * 1000

                    if chunk["type"] == "metadata":
                        if "prompt_tokens" in chunk["data"]:
                            input_tokens += chunk["data"]["prompt_tokens"]
                        if "completion_tokens" in chunk["data"]:
                            output_tokens += chunk["data"]["completion_tokens"]
                        if not client_disconnected_during_streaming:
                            if await request.is_disconnected():
                                client_disconnected_during_streaming = True
                                logger.info(
                                    f"Client disconnected for session {session_id} just before yielding metadata. Backend will continue processing.")
                            else:
                                yield json.dumps(chunk) + "\n"
                    else:
                        full_answer += chunk["data"]
                        if not client_disconnected_during_streaming:
                            if await request.is_disconnected():
                                client_disconnected_during_streaming = True
                                logger.info(
                                    f"Client disconnected for session {session_id} just before yielding content. Backend will continue processing.")
                            else:
                                yield json.dumps(chunk) + "\n"

            except Exception as error:
                error_during_streaming_msg = f"Error during response generation stream for session {session_id}: {str(error)}"
                logger.error(error_during_streaming_msg)
                if not full_answer:
                    full_answer = error_during_streaming_msg

                if not client_disconnected_during_streaming:
                    is_disconnected_after_error = await request.is_disconnected()
                    if is_disconnected_after_error:
                        client_disconnected_during_streaming = True
                        logger.info(
                            f"Client disconnected for session {session_id} during exception handling. Backend will continue processing.")

                if not client_disconnected_during_streaming:
                    try:
                        if await request.is_disconnected():
                            client_disconnected_during_streaming = True
                            logger.info(f"Client disconnected for session {session_id} before error could be yielded.")
                        else:
                            yield json.dumps({"type": "error", "data": str(e)}) + "\n"
                    except Exception as yield_e:
                        logger.warning(
                            f"Could not yield error to client for session {session_id} (client likely disconnected): {str(yield_e)}")
                        client_disconnected_during_streaming = True

            finally:
                latency_val = int(first_chunk_time - start_time) if first_chunk_time and start_time > 0 else 0
                final_answer_to_log = full_answer

                if error_during_streaming_msg:
                    final_answer_to_log = error_during_streaming_msg
                    current_status_code = 500
                elif client_disconnected_during_streaming:
                    if full_answer:
                        current_status_code = 200
                    else:
                        current_status_code = 503
                        final_answer_to_log = "Response generation was in progress when client disconnected; no primary content was generated."
                elif full_answer:
                    current_status_code = 200
                else:
                    final_answer_to_log = "No content was generated by the model."
                    current_status_code = 204

                logger.info(
                    f"Scheduling background task for chat session {session_id}. Client disconnected: {client_disconnected_during_streaming}, Status: {current_status_code}, Error: {error_during_streaming_msg is not None}")

                doc_list_for_log = document_data_list if document_data_list else None
                img_list_for_log = image_data_list if image_data_list else None

                background_tasks.add_task(
                    _log_chat_session_bg_task,
                    session_id_val=session_id,
                    belongs_to_val=current_user.get("id"),
                    document_list_val=doc_list_for_log,
                    image_list_val=img_list_for_log,
                    question_val=question,
                    answer_val=final_answer_to_log,
                    model_val=model,
                    input_tokens_val=input_tokens if input_tokens else count_tokens(question),
                    output_tokens_val=count_tokens(
                        full_answer) + 300 if current_status_code == 200 and output_tokens == 0 else output_tokens,
                    request_latency_ms_val=latency_val,
                    status_code_val=current_status_code
                )

        return StreamingResponse(stream_response(), media_type="application/x-ndjson")

    except Exception as e:
        outer_error_message = f"Critical error processing request setup for session {session_id}: {str(e)}"
        logger.error(outer_error_message)
        request_time_ms = int(time.time() * 1000 - start_time) if 'start_time' in locals() else 0

        doc_list_for_log_outer = document_data_list if 'document_data_list' in locals() and document_data_list else None
        img_list_for_log_outer = image_data_list if 'image_data_list' in locals() and image_data_list else None

        if session_id and hasattr(current_user, 'id') and model:
            background_tasks.add_task(
                _log_chat_session_bg_task,
                session_id_val=session_id,
                belongs_to_val=current_user.id,
                document_list_val=doc_list_for_log_outer,
                image_list_val=img_list_for_log_outer,
                question_val=question if 'question' in locals() else "N/A due to early error",
                answer_val=outer_error_message,
                model_val=model,
                input_tokens_val=0,
                output_tokens_val=0,
                request_latency_ms_val=request_time_ms,
                status_code_val=500
            )
        else:
            logger.error(
                f"Could not schedule background task for critical setup error for session {session_id} due to missing core data (session_id, user, or model).")

        raise HTTPException(status_code=500, detail=outer_error_message)
