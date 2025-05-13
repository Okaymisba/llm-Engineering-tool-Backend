def generate_prompt(api_key, question, prompt_context=None, instructions=None):
    """
    Generates a prompt string formatted using given instructions, question, and
    contextual prompt information.

    The function combines provided instructions, a given question, and a context
    string into a single formatted prompt. This prompt is suitable for scenarios
    where a language model requires structured input to deliver accurate and
    context-aware responses. The instructions and context are optional, offering
    flexibility in composing the input prompt. If no context or instructions are
    provided, the output string will primarily focus on the question.

    :param api_key: The API key used for external service authorization.
    :type api_key: str
    :param question: The specific question the generated prompt should address.
    :type question: str
    :param prompt_context: Optional contextual information to help the
        recipient of the prompt better answer the question.
        Defaults to None.
    :type prompt_context: Optional[str]
    :param instructions: Optional instructions that guide the recipient on
        how to formulate the response. Defaults to None.
    :type instructions: Optional[str]

    :return: A formatted prompt string combining the provided instructions,
        question, and optional context in a structured manner.
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
