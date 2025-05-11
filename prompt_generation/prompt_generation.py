from store_data.database import Database


def generate_prompt(user_id, question):
    """
    Generates a prompt to answer a question based on user-specific data and uploaded text
    documents.

    The function connects to a database to fetch user details and their associated
    data, including instructions and relevant document text. It utilizes this
    data to construct a comprehensive prompt, incorporating the provided question.

    :param user_id: The unique identifier of the user.
    :type user_id: int
    :param question: The question that needs to be addressed based on the user's data.
    :type question: str
    :return: A constructed prompt string containing instructions, user-uploaded
             documents, and the specified question, or an error message if the
             user data is not found.
    :rtype: str
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
