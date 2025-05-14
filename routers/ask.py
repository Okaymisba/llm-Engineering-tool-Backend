import faiss
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from models import get_db
from models.api_list import APIList
from models.documents import Documents
from models.embeddings import Embeddings
from prompt_generation.prompt_generation import generate_prompt
from prompt_generation.query_local_model import query_local_model

router = APIRouter()


def load_faiss_index(embeddings):
    # Initialize FAISS index
    dimension = embeddings[0][1].shape[0]
    index = faiss.IndexFlatL2(dimension)
    id_map = {}

    for idx, (doc_id, embedding) in enumerate(embeddings):
        index.add(np.expand_dims(embedding, axis=0))  # Add embeddings
        id_map[idx] = doc_id  # Map FAISS index to document ID

    return index, id_map


@router.get("/ask/")
def ask_question(api_key: str, question: str, db: Session = Depends(get_db)):
    """
    Handles the `/ask/` endpoint by processing a question based on documents associated
    with a provided API key. It retrieves relevant documents, calculates their embeddings,
    performs similarity matching, and generates a response using a local model.

    :param api_key: The API key used for authentication and to identify associated documents.
    :type api_key: str
    :param question: The user's question to process and answer.
    :type question: str
    :param db: Database session dependency used for querying and processing data.
    :type db: Session
    :return: A dictionary containing the success status, the generated answer, and
        the context used for generating the answer.
    :rtype: dict
    :raises HTTPException:
        - 403 if the API key is invalid or expired.
        - 404 if no documents are found for the given API key.
        - 404 if no embeddings for the associated documents are found.
        - 500 if the FAISS index cannot be built or errors occur during processing.
    """

    api_entry = APIList.get_by_api_key(db, api_key)
    if not api_entry:
        raise HTTPException(status_code=403, detail="Invalid or expired API key.")

    documents = db.query(Documents).filter(Documents.api_id == api_entry.id).all()
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found for the given API key.")

    embeddings = []
    for document in documents:
        embedding_entry = db.query(Embeddings).filter(Embeddings.document_id == document.api_id).first()
        if embedding_entry:
            embeddings.append((document.document_id, np.frombuffer(embedding_entry.embedding, dtype=np.float32)))

    if not embeddings:
        raise HTTPException(status_code=404, detail="No embeddings found for the associated documents.")

    try:
        index, id_map = load_faiss_index(embeddings)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    question_embedding = np.random.rand(len(embeddings[0][1])).astype('float32')  # Placeholder for embedding

    top_k = 3
    distances, indices = index.search(np.expand_dims(question_embedding, axis=0), top_k)

    most_similar_documents = []
    for idx in indices[0]:
        if idx != -1:
            most_similar_doc_id = id_map.get(idx)
            if most_similar_doc_id:
                document = db.query(Documents).filter(Documents.document_id == most_similar_doc_id).first()
                if document:
                    most_similar_documents.append(document)

    if not most_similar_documents:
        raise HTTPException(status_code=500, detail="Could not retrieve the most similar document.")

    prompt_context = []
    for document in most_similar_documents:
        prompt_context.append(document.chunk_text)
    instructions = api_entry.instructions
    prompt = generate_prompt(api_key, question, prompt_context, instructions)

    response = query_local_model(prompt)

    return {
        "success": True,
        "answer": response,
        "context": prompt_context,
    }
