from store_data.database import Database
from dotenv import load_dotenv
import os

load_dotenv()


def store_user_data(user_id, document_text, instructions):
    """
    Stores user-provided data into a database. The function connects to the database,
    executes an SQL query to insert the provided data, and then closes the database connection.
    This function requires the existence of a database and appropriate environment variable
    configuration: `DB_NAME`, `DB_USER`, and `DB_PASSWORD`.

    :param user_id: The unique identifier for the user
    :type user_id: int
    :param document_text: The text document provided by the user
    :type document_text: str
    :param instructions: Additional instructions associated with the document
    :type instructions: str
    :return: None
    :rtype: NoneType
    """

    db = Database(dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"))
    db.connect()
    db.execute_query(
        "INSERT INTO user_data (user_id, document_text, instructions) VALUES (%s, %s, %s)",
        (user_id, document_text, instructions)
    )
    db.close()
