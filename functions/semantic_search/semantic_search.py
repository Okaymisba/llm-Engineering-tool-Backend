from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("clips/mfaq")


def semantic_search(question: str, documents: list, top_k: int = 3):
    """
    Performs a semantic search for the given question against a list of documents.
    This function leverages a pre-trained model to encode the question and documents
    into embeddings and retrieves the top `top_k` most similar document chunks
    based on their embeddings.

    :param question: The question or query input to be searched.
    :type question: str
    :param documents: A list of documents, where each document contains information
        including its ID and the chunk of text to be considered for the search.
    :type documents: list
    :param top_k: The number of top similar documents to retrieve. Defaults to 3.
    :type top_k: int
    :return: A list of the most semantically similar documents including document
        IDs, text chunks, and similarity scores.
    :rtype: list
    """

    question_embedding = model.encode(question, normalize_embeddings=True)

    document_texts = [doc.chunk_text for doc in documents]

    embeddings = model.encode(document_texts, normalize_embeddings=True, convert_to_tensor=True)

    similarities = util.semantic_search(question_embedding, embeddings, top_k=top_k)

    most_similar_documents = []
    for hit in similarities[0]:
        corpus_id = hit["corpus_id"]
        most_similar_documents.append({
            "document_id": documents[corpus_id].document_id,
            "chunk_text": documents[corpus_id].chunk_text,
            "score": hit["score"]
        })

    return most_similar_documents
