# chat_session_operations.py
from typing import Optional, List, Any

from services.supabase_client import get_supabase_client


async def add_chat_session(
        session_id: str,
        belongs_to: str,
        document: Optional[List[Any]],
        image: Optional[List[Any]],
        question: str,
        answer: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        status: int,
) -> None:
    """
    Adds a chat session to the database.

    This asynchronous function logs details of a chatbot session to a database table.
    The logged details may include session-related metadata such as the session ID,
    user information, documents, images, the question asked, the answer provided,
    model utilized, token counts, processing latency, and session's status code.

    :param session_id: Unique identifier for the chat session.
    :type session_id: str
    :param belongs_to: Identifier for the user to whom the session belongs.
    :type belongs_to: str
    :param document: Optional list of documents associated with the session.
    :type document: Optional[List[Any]]
    :param image: Optional list of images associated with the session.
    :type image: Optional[List[Any]]
    :param question: Question posed during the session.
    :type question: str
    :param answer: Response generated for the question.
    :type answer: str
    :param model: Name of the language model used for answering the question.
    :type model: str
    :param input_tokens: Number of tokens in the input data.
    :type input_tokens: int
    :param output_tokens: Number of tokens in the output data.
    :type output_tokens: int
    :param latency_ms: Latency of the session processing in milliseconds.
    :type latency_ms: float
    :param status: Status code reflecting the session's state.
    :type status: int
    :return: None
    """
    supabase = get_supabase_client()

    chat_data = {
        "session_id": session_id,
        "belongs_to": belongs_to,
        "document": document,
        "image": image,
        "question": question,
        "answer": answer,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "latency_ms": latency_ms,
        "status": status,
    }

    supabase.table("chats").insert(chat_data).execute()
