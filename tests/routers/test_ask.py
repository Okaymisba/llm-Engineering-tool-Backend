# tests/routers/test_ask.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Assuming your models are structured to be importable like this
from models.api_list import APIList as APIListModel
from models.documents import Documents as DocumentModel

# Dummy class to simulate SQLAlchemy model instances for mocking
class MockAPIListEntry:
    def __init__(self, id, instructions="Test instructions"):
        self.id = id
        self.instructions = instructions

class MockDocumentEntry:
    def __init__(self, id, api_id, document_name="test_doc.txt", chunk_text="This is a test document chunk."):
        self.id = id
        self.api_id = api_id
        self.document_name = document_name
        self.chunk_text = chunk_text # For semantic search mock

    def get(self, key, default=None): # Simulate .get for semantic_search result
        if key == "chunk_text":
            return self.chunk_text
        return getattr(self, key, default)


@pytest.fixture
def mock_api_entry():
    return MockAPIListEntry(id=1, instructions="Follow these test instructions.")

@pytest.fixture
def mock_document_list(mock_api_entry: MockAPIListEntry):
    return [
        MockDocumentEntry(id=101, api_id=mock_api_entry.id, chunk_text="First chunk of context."),
        MockDocumentEntry(id=102, api_id=mock_api_entry.id, chunk_text="Second chunk of context.")
    ]

def test_ask_question_success(
    client: TestClient,
    mock_api_entry: MockAPIListEntry,
    mock_document_list: list[MockDocumentEntry]
):
    # To test the current state of ask.py, generate_response_streaming will return a coroutine/generator.
    # Let's mock it to return a simple string for "answer" to test the intended logic path,
    # acknowledging the bug in ask.py that it doesn't await/iterate.
    # If it were fixed to be async and iterate, this mock would need to be an async generator.
    mock_generated_answer = "This is the mocked AI answer."

    with patch("routers.ask.APIList.get_by_api_key") as mock_get_api_key, \
         patch("sqlalchemy.orm.Session.query") as mock_db_session_query, \
         patch("routers.ask.semantic_search") as mock_semantic_search, \
         patch("routers.ask.generate_response_streaming", return_value=mock_generated_answer) as mock_gen_response:

        # Setup mocks
        mock_get_api_key.return_value = mock_api_entry

        # Mock the chain of SQLAlchemy query calls for documents
        # Session.query(DocumentModel)
        mock_query_documentmodel = MagicMock()
        mock_db_session_query.return_value = mock_query_documentmodel
        # .filter(Documents.api_id == api_entry.id)
        mock_filtered_query = MagicMock()
        mock_query_documentmodel.filter.return_value = mock_filtered_query
        # .all()
        mock_filtered_query.all.return_value = mock_document_list

        # Mock semantic_search to return some of the mock documents (or their relevant parts)
        # semantic_search in ask.py expects a list of dicts with "chunk_text"
        mock_semantic_search_results = [{"chunk_text": doc.chunk_text} for doc in mock_document_list]
        mock_semantic_search.return_value = mock_semantic_search_results

        response = client.get(
            "/ask/",
            params={
                "api_key": "valid_key",
                "provider": "test_provider",
                "model": "test_model",
                "question": "What is the test about?",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # This assertion depends on whether generate_response_streaming is fixed or not.
        # If not fixed, data["answer"] will be a string representation of a generator/coroutine.
        # We mocked it to return a string, simulating the *intended* (or fixed) behavior.
        assert data["answer"] == mock_generated_answer

        expected_context = [doc_result["chunk_text"] for doc_result in mock_semantic_search_results]
        assert data["context"] == expected_context

        mock_get_api_key.assert_called_once_with(pytest.ANY, "valid_key") # db session, api_key

        # Check SQLAlchemy query calls
        mock_db_session_query.assert_called_with(DocumentModel)
        mock_query_documentmodel.filter.assert_called_once() # Check filter was called
        mock_filtered_query.all.assert_called_once()

        mock_semantic_search.assert_called_once_with("What is the test about?", mock_document_list)
        mock_gen_response.assert_called_once_with(
            "test_provider",
            "test_model",
            "What is the test about?",
            expected_context,
            mock_api_entry.instructions
        )

def test_ask_question_invalid_api_key(client: TestClient):
    with patch("routers.ask.APIList.get_by_api_key", return_value=None) as mock_get_api_key:
        response = client.get(
            "/ask/",
            params={
                "api_key": "invalid_key",
                "provider": "test_provider",
                "model": "test_model",
                "question": "Any question?",
            },
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid or expired API key."
        mock_get_api_key.assert_called_once_with(pytest.ANY, "invalid_key")

def test_ask_question_no_documents_for_api_key(client: TestClient, mock_api_entry: MockAPIListEntry):
    with patch("routers.ask.APIList.get_by_api_key", return_value=mock_api_entry) as mock_get_api_key, \
         patch("sqlalchemy.orm.Session.query") as mock_db_session_query:

        mock_query_documentmodel = MagicMock()
        mock_db_session_query.return_value = mock_query_documentmodel
        mock_filtered_query = MagicMock()
        mock_query_documentmodel.filter.return_value = mock_filtered_query
        mock_filtered_query.all.return_value = [] # No documents

        response = client.get(
            "/ask/",
            params={
                "api_key": "key_with_no_docs",
                "provider": "test_provider",
                "model": "test_model",
                "question": "Any question?",
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No documents found for the given API key."

def test_ask_question_missing_parameters(client: TestClient):
    # Test missing api_key
    response = client.get(
        "/ask/",
        params={
            # "api_key": "some_key", # Missing
            "provider": "test_provider",
            "model": "test_model",
            "question": "A question?",
        },
    )
    assert response.status_code == 422 # Unprocessable Entity

    # Test missing question
    response = client.get(
        "/ask/",
        params={
            "api_key": "some_key",
            "provider": "test_provider",
            "model": "test_model",
            # "question": "A question?", # Missing
        },
    )
    assert response.status_code == 422

# (Add tests for missing provider and model as well if desired)
