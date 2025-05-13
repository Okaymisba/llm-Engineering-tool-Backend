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
    Handles a request to ask a question, retrieves relevant document embeddings,
    searches for the most similar document chunk using FAISS, generates a prompt,
    and queries a local model for an answer.

    :param api_key: API key used for authentication or identification purposes.
    :type api_key: str
    :param question: The question text to be processed and answered by the model.
    :type question: str
    :param db: Dependency-injected database session for database operations.
    :type db: Session
    :return: A dictionary containing the success status and the generated answer.
    :rtype: dict
    """
    # Verify API Key validity
    api_entry = APIList.get_by_api_key(db, api_key)
    if not api_entry:
        raise HTTPException(status_code=403, detail="Invalid or expired API key.")

    # Retrieve Documents linked to this API key
    documents = db.query(Documents).filter(Documents.api_id == api_entry.id).all()
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found for the given API key.")

    # Retrieve Embeddings for these Documents
    embeddings = []
    for document in documents:
        embedding_entry = db.query(Embeddings).filter(Embeddings.document_id == document.api_id).first()
        if embedding_entry:
            embeddings.append((document.document_id, np.frombuffer(embedding_entry.embedding, dtype=np.float32)))

    if not embeddings:
        raise HTTPException(status_code=404, detail="No embeddings found for the associated documents.")

    # Load FAISS index with document data
    try:
        index, id_map = load_faiss_index(embeddings)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Embed the question into the same vector format (stubbed here)
    # (Assume we pass the question through some embedding model to get its vector)
    question_embedding = np.random.rand(len(embeddings[0][1])).astype('float32')  # Placeholder for embedding

    # Perform similarity search (find most similar document)
    top_k = 3  # We only need the top result
    distances, indices = index.search(np.expand_dims(question_embedding, axis=0), top_k)

    # Retrieve the most relevant document info
    most_similar_documents = []
    for idx in indices[0]:
        if idx != -1:  # Check if index is valid
            most_similar_doc_id = id_map.get(idx)
            if most_similar_doc_id:
                document = db.query(Documents).filter(Documents.document_id == most_similar_doc_id).first()
                if document:
                    most_similar_documents.append(document)

    if not most_similar_documents:
        raise HTTPException(status_code=500, detail="Could not retrieve the most similar document.")

    # Generate the prompt using the most similar document chunk
    prompt_context = []
    for document in most_similar_documents:
        prompt_context.append(document.chunk_text)
    instructions = api_entry.instructions
    prompt = generate_prompt(api_key, question, prompt_context, instructions)

    # Query the local model using the prompt
    response = query_local_model(prompt)

    # Return the successful response
    return {
        "success": True,
        "answer": response,
        "context": prompt_context,  # Provide the context used for debugging
    }
