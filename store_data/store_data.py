from store_data.database import Database


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

    db = Database(dbname="llm_engineering_tool", user="postgres", password="postgres")
    db.connect()
    db.execute_query(
        "INSERT INTO user_data (user_id, document_text, instructions) VALUES (%s, %s, %s)",
        (user_id, document_text, instructions)
    )
    db.close()
