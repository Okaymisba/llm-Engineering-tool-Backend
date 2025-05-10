from store_data.database import Database


def generate_prompt(user_id, question):
    """
    Generate a prompt for the language model from the user data.

    Given a user_id and a question, generate a prompt for the language model
    that includes the instructions and text from the uploaded documents.

    Args:
        user_id (str): The ID of the user.
        question (str): The question to be answered.

    Returns:
        str: The generated prompt.
    """
    db = Database(dbname="llm_engineering_tool", user="postgres", password="postgres")

    db.connect()
    user_data = db.fetch_one("SELECT * FROM user_data WHERE user_id = %s", (user_id,))
    db.close()

    if not user_data:
        return "User data not found."

    instructions = user_data["instructions"]
    documents = user_data["document_text"]

    prompt = f"""
    Instructions: {instructions}

    You have the following information from the uploaded documents:
    {documents}

    Based on the above information and the instructions given, answer the following question:
    {question}
    """
    return prompt
