from sqlalchemy.orm import Session
from models.api_list import APIList
from models.__init__ import engine
from dotenv import load_dotenv
import os

load_dotenv()


def store_user_data(user_id: int, api_key: str, document_text: str, instructions: str = None) -> APIList:
    """
    Stores user data, including user ID, API key, document text, and specific instructions,
    in the API list table of the database using SQLAlchemy ORM.

    Args:
        user_id (int): The unique identifier for the user
        api_key (str): The API key associated with the user
        document_text (str): The content of the document associated with the user data
        instructions (str, optional): Specific instructions or metadata related to the document

    Returns:
        APIList: The created API entry
    """
    with Session(engine) as db:
        return APIList.create_api_entry(
            db=db,
            main_table_user_id=user_id,
            api_key=api_key,
            document_data=document_text,
            instructions=instructions
        )
