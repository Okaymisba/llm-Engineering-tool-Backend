def generate_prompt(question, prompt_context=None, instructions=None, image_data=None, document_data=None):
    """
    Generates a formatted prompt string based on the given question and various optional contextual inputs, such as
    image data, document data, a general prompt context, or specific instructions. The prompt is constructed dynamically
    depending on the provided arguments and follows a predefined structure to include the relevant information for
    responding to the question.

    :param question: The core query that the generated prompt aims to address.
    :type question: str
    :param prompt_context: Optional textual context that provides additional information for interpreting the question.
    :type prompt_context: str, optional
    :param instructions: Optional specific instructions or guidelines that clarify the desired response or behavior.
    :type instructions: str, optional
    :param image_data: Optional data or metadata related to an image that might inform the response.
    :type image_data: str, optional
    :param document_data: Optional data or content of a document that might assist in addressing the question.
    :type document_data: str, optional
    :return: A formatted string containing the prompt assembled based on the provided inputs.
    :rtype: str
    """

    if image_data and document_data:
        prompt = f"""
        Image Data
        {image_data}

        Document Data
        {document_data}

        Based on the provided information above, answer the following question:
        {question}
        """
    elif image_data:
        prompt = f"""
        Image Data
        {image_data}

        Based on the provided information above, answer the following question:
        {question}
        """
    elif document_data:
        prompt = f"""
        Document Data
        {document_data}

        Based on the provided information above, answer the following question:
        {question}
        """
    elif prompt_context:
        prompt = f"""
        Here is the context: {prompt_context}

        Based on the provided information above, answer the following question:
        {question}
        """
    elif instructions:
        prompt = f"""
        {instructions}

        Based on the provided information above, answer the following question:
        {question}
        """
    else:
        prompt = f"""
        Based on the provided information above, answer the following question:
        {question}
        """

    return prompt
