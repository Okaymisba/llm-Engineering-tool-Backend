from datetime import datetime

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from functions.chunk_text.chunk_text import chunk_document_text
from models.__init__ import engine
from models.api_list import APIList
from models.documents import Documents
from models.embeddings import Embeddings

load_dotenv()


def store_user_data(user_id: int, api_key: str, document_text: str, instructions: str = None) -> APIList:
    """
    Stores user data into several database tables and generates embeddings for the
    provided document text. The function performs the following operations:
    - Splits the input `document_text` into chunks.
    - Inserts user details and document metadata into the 'documents' table.
    - Associates the generated document ID with the API entry.
    - Computes embedding vectors for each chunk of the `document_text` and stores
      them in the 'embeddings' table.

    Also, updates the relevant entries to properly link API and document details.

    :param user_id: The identifier of the user submitting the data.
    :type user_id: int
    :param api_key: The API key provided by the user for authentication.
    :type api_key: str
    :param document_text: The complete text document to be processed and stored.
    :type document_text: str
    :param instructions: Optional instructions or metadata related to `document_text`.
    :type instructions: str, optional
    :return: APIList instance representing the created API entry, including all
        associated data.
    :rtype: APIList
    :raises RuntimeError: If any error occurs during the database interaction or
        data storage process.
    """

    chunk_text = chunk_document_text(document_text)

    with Session(engine) as db:
        try:
            api_entry = APIList.create_api_entry(
                db=db,
                main_table_user_id=user_id,
                api_key=api_key,
                instructions=instructions,
            )

            for chunk in chunk_text:
                document_entry = Documents(
                    chunk_text=chunk,
                    api_id=api_entry.id,
                    created_at=datetime.utcnow()
                )
                db.add(document_entry)
                db.commit()
                db.refresh(document_entry)

            document_id = document_entry.document_id
            api_entry.document_id = document_id

            db.commit()

            model = SentenceTransformer('all-MiniLM-L6-v2')

            for chunk in chunk_text:
                embedding = model.encode(chunk)

                embedding_data = embedding.tobytes()

                embedding_entry = Embeddings(
                    document_id=document_entry.api_id,
                    embedding=embedding_data
                )
                db.add(embedding_entry)

                db.commit()

            return api_entry

        except Exception as e:
            db.rollback()
            raise RuntimeError(f"An error occurred while storing user data: {e}")
