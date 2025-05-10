# Tmp in memory storage
# TODO: Replace with a database or persistent storage solution

user_data = {}


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
    user_data[user_id] = {
        "documents": document_text,
        "instructions": instructions
    }
