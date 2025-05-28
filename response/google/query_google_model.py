import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")


async def query_google_model(model, question, prompt_context=None, instructions=None, image_data=None,
                             document_data=None,
                             stream=True):
    """
    Queries a specified Google model to generate responses to a given question, optionally
    using additional context, instructions, image data, or document data. Supports streaming
    and non-streaming response behaviors.

    :param model: The model to be queried.
    :type model: str
    :param question: The primary question or input to query the model with.
    :type question: str
    :param prompt_context: Optional additional context to provide to the model.
    :type prompt_context: Optional[str]
    :param instructions: Optional instructions for guiding the model's behavior.
    :type instructions: Optional[str]
    :param image_data: Optional image data to augment the model's understanding.
    :type image_data: Optional[str]
    :param document_data: Optional document data to provide additional context.
    :type document_data: Optional[str]
    :param stream: Whether to stream the response from the model. Defaults to True.
    :type stream: bool
    :return: An asynchronous generator yielding chunks of text for streaming responses
             or a complete response text for non-streaming responses.
    :rtype: AsyncGenerator[str, None] or Generator[str, None, None]
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

    if stream:
        response = client.models.generate_content_stream(
            model=model,
            contents=content,
        )

        for chunk in response:
            yield chunk.text
    else:
        response = client.models.generate_content(
            model=model,
            contents=content
        )
        yield response.text
