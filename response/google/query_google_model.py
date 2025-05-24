import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")


def query_google_model(model, question, prompt_context=None, instructions=None, image_data=None, document_data=None):
    """
    Executes a query using Google's AI model, integrating optional context, instructions,
    image data, and document data to generate a response. This function interacts with a
    client to process and structure the inputs before sending them for generation by the
    specified model. The response is returned as text.

    :param model: Specifies the AI model to be used for the content generation.
    :type model: str
    :param question: The main question or query to be addressed by the AI model.
    :type question: str
    :param prompt_context: Additional context or background information provided to
        enhance the AI model's understanding of the query. This is optional.
    :type prompt_context: Optional[str]
    :param instructions: Specific instructions or guidelines for the AI model to follow
        during content generation. This is optional.
    :type instructions: Optional[str]
    :param image_data: Associated image data relevant to the query, included to provide
        additional context during content generation. This is optional.
    :type image_data: Optional[Any]
    :param document_data: Document data relevant to the query for additional context
        during content generation. This is optional.
    :type document_data: Optional[Any]
    :return: The generated content as a string response from the AI model.
    :rtype: str
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

    response = client.models.generate_content(
        model=model,
        contents=content,
    )

    return response.text
