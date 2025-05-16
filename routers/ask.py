import faiss
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from functions.semantic_search.semantic_search import semantic_search
from models import get_db
from models.api_list import APIList
from models.documents import Documents
from response.generate_response import generate_response

router = APIRouter()


def load_faiss_index(embeddings):
    dimension = embeddings[0][1].shape[0]
    index = faiss.IndexFlatL2(dimension)
    id_map = {}

    for idx, (doc_id, embedding) in enumerate(embeddings):
        index.add(np.expand_dims(embedding, axis=0))
        id_map[idx] = doc_id

    return index, id_map


@router.get("/ask/")
def ask_question(api_key: str, provider: str, model: str, question: str, db: Session = Depends(get_db)):
    """
    Provides functionality to retrieve related documents using a given API key and
    additional inputs to generate a response for a given question. Ensures the
    validity of the API key, retrieves associated documents, performs semantic
    search, and generates a response based on the processed context.

    :param api_key: A string representing the API key used for authorization.
    :param provider: A string indicating the provider of the language model to use.
    :param model: A string specifying the model's name to use for response generation.
    :param question: A string containing the question or query to be answered.
    :param db: A database session dependency used to perform database interactions.
    :type db: Session
    :return: A dictionary containing keys 'success' (boolean indicating success
        of operation), 'answer' (the generated response as a string), and 'context'
        (a list of relevant context snippets from documents).
    :rtype: dict
    """

    api_entry = APIList.get_by_api_key(db, api_key)
    if not api_entry:
        raise HTTPException(status_code=403, detail="Invalid or expired API key.")

    documents = db.query(Documents).filter(Documents.api_id == api_entry.id).all()
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found for the given API key.")

    prompt_context = []
    most_similar_documents = semantic_search(question, documents)

    for document in most_similar_documents:
        prompt_context.append(document.get("chunk_text"))

    instructions = api_entry.instructions

    response = generate_response(provider, model, question, prompt_context, instructions)

    return {
        "success": True,
        "answer": response,
        "context": prompt_context,
    }
