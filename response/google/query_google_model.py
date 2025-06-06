import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")


def query_google_model(model, question, prompt_context=None, instructions=None, image_data=None,
                       document_data=None, web_search_results=None):
    """
    Queries a Google AI model with the specified question and additional optional
    contextual information. This function allows for the inclusion of various
    data types, such as prompt context, instructions, image data, document data,
    and web search results. It streams the generated content response, as well as
    associated token metadata, in chunks.

    :param model: The identifier of the model to query.
    :param question: The question or prompt to send to the AI model.
    :param prompt_context: Additional context or background information to
        guide the AI model in generating the response.
    :param instructions: Specific instructions or guidelines for the AI model
        regarding how the response should be generated.
    :param image_data: Relevant image data that might aid the AI model in
        forming the response.
    :param document_data: Specific document data for additional context or
        reference during the AI model's processing.
    :param web_search_results: Supplementary web search result data to provide
        further context to the AI model.
    :return: Yields individual chunks of generated content and token metadata
        as a dictionary.
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

    if web_search_results:
        content.append({f"Web Search Results: {web_search_results}"})

    content.append({f"question: {question}"})

    token_metadata = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

    response = client.models.generate_content_stream(
        model=model,
        contents=content,
    )

    for chunk in response:
        if chunk:
            yield {"content": chunk.text}

        if hasattr(chunk, "usage_metadata"):
            token_metadata["prompt_tokens"] = chunk.usage_metadata.prompt_token_count
            token_metadata["completion_tokens"] = chunk.usage_metadata.candidates_token_count
            token_metadata["total_tokens"] = chunk.usage_metadata.total_token_count

    yield {"metadata": token_metadata}
