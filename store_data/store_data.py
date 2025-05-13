from datetime import datetime
from sqlalchemy.orm import Session
from models.api_list import APIList
from models.documents import Documents
from models.embeddings import Embeddings
from models.__init__ import engine
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv()


def store_user_data(user_id: int, api_key: str, document_text: str, instructions: str = None) -> APIList:
    """
    Stores user data by:
    1. Inserting into the 'documents' table.
    2. Using the document_id to create an entry in the 'api_list' table.
    3. Using the document_id to create an entry in the 'embeddings' table.

    Args:
        user_id (int): The unique identifier for the user
        api_key (str): The API key associated with the user
        document_text (str): The content of the document associated with the user data
        embedding_data (bytes): The embedding data to be stored for the document
        instructions (str, optional): Specific instructions or metadata related to the document

    Returns:
        APIList: The created API entry
    """
    with Session(engine) as db:
        try:
            # Step 1: Insert into the 'documents' table
            document_entry = Documents(
                chunk_text=document_text,
                created_at=datetime.utcnow()
            )
            db.add(document_entry)
            db.commit()
            db.refresh(document_entry)

            # Get the generated document_id
            document_id = document_entry.document_id

            # Step 2: Insert into the 'api_list' table using the document_id
            api_entry = APIList.create_api_entry(
                db=db,
                main_table_user_id=user_id,
                api_key=api_key,
                instructions=instructions,
                document_id=document_id
            )

            # Link the document to the API entry
            document_entry.api_id = api_entry.id
            db.commit()

            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(document_text)

            embedding_data = embedding.tobytes()

            # Step 3: Insert into the 'embeddings' table using document_id
            embedding_entry = Embeddings(
                document_id=document_id,
                embedding=embedding_data
            )
            db.add(embedding_entry)
            db.commit()

            return api_entry

        except Exception as e:
            db.rollback()
            raise RuntimeError(f"An error occurred while storing user data: {e}")
