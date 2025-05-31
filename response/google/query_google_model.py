import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")


def query_google_model(model, question, prompt_context=None, instructions=None, image_data=None,
                       document_data=None):
    """
    Queries the Google model using the provided parameters and streams the generated content
    alongside token metadata. The function utilizes a client to communicate with the model
    and accepts various inputs such as the context, question, instructions, and optional
    image or document data to tailor the model's response. The generated response is then
    yielded incrementally as text along with token usage metadata detailing the token count
    information.

    :param model: The model to query.
    :type model: str
    :param question: The question to ask the model.
    :type question: str
    :param prompt_context: Provides additional context for the model (optional).
    :type prompt_context: str or None
    :param instructions: Specific instructions to guide the model (optional).
    :type instructions: str or None
    :param image_data: Image data to include as part of the prompt (optional).
    :type image_data: str or None
    :param document_data: Document data to include as part of the prompt (optional).
    :type document_data: str or None
    :return: A generator yielding the model's textual response or token metadata.
    :rtype: generator
    """
    client = genai.Client(api_key=api_key)

    content = []

    if prompt_context:
        content.append({f"Here is the context: {prompt_context}"})

    if instructions:
        content.append({f"instructions: {instructions}"})

    if image_data:
        content.append({f"Image Data: {image_data}"})

    if document_data:
        content.append({f"Document Data: {document_data}"})

    content.append({f"question: {question}"})

    token_metadata = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

    response = client.models.generate_content_stream(
        model=model,
        contents=content,
    )

    for chunk in response:
        if chunk:
            yield chunk.text

        if hasattr(chunk, "usage_metadata"):
            token_metadata["prompt_tokens"] = chunk.usage_metadata.prompt_token_count
            token_metadata["completion_tokens"] = chunk.usage_metadata.candidates_token_count
            token_metadata["total_tokens"] = chunk.usage_metadata.total_token_count

    yield token_metadata
