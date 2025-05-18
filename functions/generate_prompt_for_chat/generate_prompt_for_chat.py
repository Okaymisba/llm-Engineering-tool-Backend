def generate_prompt_for_chat(question, image_data=None, document_data=None):
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
    else:
        prompt = f"""
        {question}
        """

    return prompt
