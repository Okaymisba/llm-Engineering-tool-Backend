def generate_prompt(question, prompt_context=None, instructions=None):
    """
    Generate a prompt by combining provided question, context, and instructions.

    :param question: The question to be answered.
    :type question: str

    :param prompt_context: Additional relevant information or context related to the question.
    :type prompt_context: Optional[str]

    :param instructions: Guidelines or directives to follow for answering the question.
    :type instructions: Optional[str]

    :return: A formatted prompt combining the question, context, and instructions.
    :rtype: str
    """

    prompt = f"""
    Instructions: {instructions}

    Based on the provided information below and the instructions given above, answer the following question:
    {question}
    
    You have the following information from the uploaded documents:
    {prompt_context}
    """

    return prompt
