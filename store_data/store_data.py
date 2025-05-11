from store_data.database import Database
from dotenv import load_dotenv
import os

load_dotenv()


def store_user_data(user_id, api_key, document_text, instructions):
    """
    Stores user data, including user ID, API key, document text, and specific instructions,
    in the API list table of the database.

    :param user_id: The unique identifier for the user.
    :type user_id: int
    :param api_key: The API key associated with the user.
    :type api_key: str
    :param document_text: The content of the document associated with the user data.
    :type document_text: str
    :param instructions: Specific instructions or metadata related to the document.
    :type instructions: str
    :return: None
    """

    db = Database(dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"))
    db.connect()
    db.execute_query(
        "INSERT INTO api_list (main_table_user_id, api_key, document_data, instructions) VALUES (%s, %s, %s, %s)",
        (user_id, api_key, document_text, instructions)
    )
    db.close()
