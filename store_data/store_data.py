from store_data.database import Database
from dotenv import load_dotenv
import os

load_dotenv()


def store_user_data(user_id, document_text, instructions):
    """
    Stores user data in the temporary in-memory storage.

    Args:
        user_id (str): The ID of the user.
        document_text (str): The text content of the uploaded documents.
        instructions (str): The instructions for the language model.

    Returns:
        None
    """

    db = Database(dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"))
    db.connect()
    db.execute_query(
        "INSERT INTO user_data (user_id, document_text, instructions) VALUES (%s, %s, %s)",
        (user_id, document_text, instructions)
    )
    db.close()
