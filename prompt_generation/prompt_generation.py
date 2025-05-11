from store_data.database import Database


def generate_prompt(api_key, question):
    """
    Generates a prompt based on user data retrieved from a database, including instructions,
    documents, and the provided question. The prompt is generated using the data associated
    with the provided API key.

    :param api_key: The API key to identify the user in the database.
    :type api_key: str
    :param question: The question to be incorporated into the generated prompt.
    :type question: str
    :return: A string containing the generated prompt based on user data and the given question.
    :rtype: str
    """

    db = Database(dbname="llm_engineering_tool", user="postgres", password="postgres")

    db.connect()
    user_data = db.fetch_one("SELECT * FROM api_list WHERE api_key = %s", (api_key,))
    db.close()

    if not user_data:
        return "User data not found."

    instructions = user_data["instructions"]
    documents = user_data["document_data"]

    prompt = f"""
    Instructions: {instructions}

    Based on the provided information below and the instructions given above, answer the following question:
    {question}
    
    You have the following information from the uploaded documents:
    {documents}
    """
    return prompt
