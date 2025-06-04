# tests/routers/test_chat.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, call # Import call for checking calls with args
from fastapi import BackgroundTasks # To mock BackgroundTasks.add_task

# Import the actual function to check its signature if needed, or just its name as a string
from routers.chat import _log_chat_session_bg_task

# Mock data for generate_response_streaming
MOCK_STREAM_CHUNKS = [
    {"type": "content", "data": "Hello "},
    {"type": "content", "data": "World"},
    {"type": "metadata", "data": {"prompt_tokens": 10, "completion_tokens": 2}},
]

async def mock_generate_response_streaming_func(*args, **kwargs):
    for chunk in MOCK_STREAM_CHUNKS:
        yield chunk

def test_chat_unauthenticated(client: TestClient):
    response = client.post(
        "/chat",
        data={ # Form data
            "session_id": "testsession",
            "question": "Hello?",
            "provider": "testprovider",
            "model": "testmodel",
            "our_image_processing_algo": False,
            "document_semantic_search": False,
        },
    )
    assert response.status_code == 401 # Expecting 401 due to missing auth

@patch("routers.chat.generate_response_streaming", new_callable=lambda: mock_generate_response_streaming_func)
@patch("fastapi.BackgroundTasks.add_task") # Patch add_task directly on the class
def test_chat_successful_no_uploads(
    mock_add_task: MagicMock,
    mock_gen_response: MagicMock, # Name must match a parameter in the test function
    authenticated_client: TestClient
):
    form_data = {
        "session_id": "chatsession123",
        "question": "What is FastAPI?",
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "our_image_processing_algo": "False", # Form data sends strings
        "document_semantic_search": "False", # Form data sends strings
    }

    response = authenticated_client.post("/chat", data=form_data)

    assert response.status_code == 200
    # Verify streamed content
    # expected_streamed_json = "".join([json.dumps(chunk) + "\n" for chunk in MOCK_STREAM_CHUNKS])
    # TestClient.text accumulates the streamed response if not iterated.
    # However, for ndjson, direct comparison might be tricky if chunk order or exact text is an issue.
    # A more robust way is to read line by line.
    # For now, let's check if the content contains parts of our expected data.
    # This part might need adjustment based on how TestClient handles ndjson streams.
    # raw_response_content = response.content.decode() # response.text might try to decode as utf-8 by default

    # Reconstruct expected full answer from content chunks
    expected_full_answer = "".join(c["data"] for c in MOCK_STREAM_CHUNKS if c["type"] == "content")
    expected_input_tokens = MOCK_STREAM_CHUNKS[2]["data"]["prompt_tokens"]
    expected_output_tokens = MOCK_STREAM_CHUNKS[2]["data"]["completion_tokens"]

    # Check if the mock for generate_response_streaming was called correctly
    mock_gen_response.assert_called_once()
    call_args = mock_gen_response.call_args
    assert call_args.kwargs["provider"] == form_data["provider"]
    assert call_args.kwargs["model"] == form_data["model"]
    assert call_args.kwargs["question"] == form_data["question"]
    assert call_args.kwargs["image_data"] == [] # No uploads
    assert call_args.kwargs["document_data"] == [] # No uploads

    # Check if background task was scheduled correctly
    # We expect _log_chat_session_bg_task to be called via add_task
    # The first argument to add_task is the callable, subsequent are its args.
    mock_add_task.assert_called_once()

    # Get the arguments passed to the actual _log_chat_session_bg_task
    # The first argument to add_task is the task function itself.
    # The subsequent arguments are what the task function will receive.
    args_to_bg_task_call_tuple = mock_add_task.call_args[0] # This is a tuple: (task_func, *args_for_task_func)

    assert args_to_bg_task_call_tuple[0] == _log_chat_session_bg_task

    # Extract keyword arguments if add_task was called like: add_task(func, arg1=val1, arg2=val2)
    # If add_task was called like: add_task(func, val1, val2), then they are in args_to_bg_task_call[1:]
    # Based on chat.py, it's called with positional args for _log_chat_session_bg_task

    # The arguments passed to the background task are positional
    # We need to map them to the expected parameter names of _log_chat_session_bg_task
    bg_task_param_names = [
        "session_id_val", "belongs_to_val", "document_list_val", "image_list_val",
        "question_val", "answer_val", "model_val", "input_tokens_val",
        "output_tokens_val", "request_latency_ms_val", "status_code_val", "document_hits_val"
    ]

    actual_bg_task_args = {}
    for i, arg_name in enumerate(bg_task_param_names):
        # args_to_bg_task_call_tuple[0] is the function itself
        # args_to_bg_task_call_tuple[1:] are the arguments to that function
        if (i + 1) < len(args_to_bg_task_call_tuple):
             actual_bg_task_args[arg_name] = args_to_bg_task_call_tuple[i+1]
        else:
            # Handle cases where not all args might be passed (e.g. if some have defaults in the real func)
            # or if the number of args passed is less than defined in bg_task_param_names
             actual_bg_task_args[arg_name] = None # Or some other default placeholder

    assert actual_bg_task_args["session_id_val"] == form_data["session_id"]
    assert actual_bg_task_args["question_val"] == form_data["question"]
    assert actual_bg_task_args["answer_val"] == expected_full_answer
    assert actual_bg_task_args["model_val"] == form_data["model"]
    assert actual_bg_task_args["input_tokens_val"] == expected_input_tokens
    assert actual_bg_task_args["output_tokens_val"] == expected_output_tokens
    assert actual_bg_task_args["status_code_val"] == 200
    assert actual_bg_task_args["document_list_val"] is None # No uploads
    assert actual_bg_task_args["image_list_val"] is None # No uploads
    assert actual_bg_task_args["document_hits_val"] is None # No semantic search

# Need to import json for the streaming response check, if done more thoroughly
import json
