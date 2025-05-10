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

    data = user_data.get(user_id)
    if not data:
        return "User data not found."

    instructions = data["instructions"]
    documents = data["documents"]

    prompt = f"""
    Instructions: {instructions}

    You have the following information from the uploaded documents:
    {documents}

    Based on the above information and the instructions given, answer the following question:
    {question}
    """
    return prompt
