import logging

from response.deepseek.query_deepseek_model import query_deepseek_model
from response.google.query_google_model import query_google_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_response_streaming(
        provider: str,
        model: str,
        question: str,
        prompt_context: list = None,
        instructions: str = None,
        image_data: list = None,
        document_data: list = None,
        web_search_results: list = None
):
    """
    Generate a streaming response asynchronously for the specified provider and model based on
    the given question and additional contextual input, using deep learning APIs or models.

    The function processes input data, streams responses in chunks, and categorizes
    each chunk as reasoning, content, or metadata. Each chunk is yielded in a structured
    format for further processing or use.

    :param provider: The AI service provider to use for generating the response.
        Supported providers include "deepseek", "openai", "anthropic", and "google".
    :param model: The specific model identifier of the AI service provider.
    :param question: The main prompt or question for which a response is to be generated.
    :param prompt_context: Optional list of additional contextual input to
        enhance the relevance of the generated response.
    :param instructions: Optional instructions or directives provided
        to guide the response generation.
    :param image_data: Optional list of image data or references provided
        for context or analysis by the AI model.
    :param document_data: Optional list of textual documents for the AI
        model to consider while generating a response.
    :param web_search_results: Optional list of web search results
        to incorporate into the context for the response generation.
    :return: Structured chunks of the response as they become available,
        categorized into reasoning, content, or metadata.
        The function yields dictionaries with `type` and `data` keys
        for each chunk.
    """
    try:
        if provider == "deepseek":
            # The last chunk will contain the metadata of the tokens which will be a dictionary containing the following agrs:
            # prompt_tokens,
            # completion_tokens,
            # total_tokens
            for chunk in query_deepseek_model(
                    model,
                    question,
                    prompt_context,
                    instructions,
                    image_data,
                    document_data,
                    web_search_results
            ):
                data = chunk
                if chunk.get("reasoning"):
                    yield {"type": "reasoning", "data": data["reasoning"]}
                if chunk.get("content"):
                    yield {"type": "content", "data": data["content"]}
                if chunk.get("metadata"):
                    yield {"type": "metadata", "data": data["metadata"]}

        elif provider == "openai":
            pass
        elif provider == "anthropic":
            pass
        elif provider == "google":
            # Its the same as deepseek
            for chunk in query_google_model(
                    model,
                    question,
                    prompt_context,
                    instructions,
                    image_data,
                    document_data,
                    web_search_results
            ):
                data = chunk
                if chunk.get("reasoning"):
                    yield {"type": "reasoning", "data": data["reasoning"]}
                if chunk.get("content"):
                    yield {"type": "content", "data": data["content"]}
                if chunk.get("metadata"):
                    yield {"type": "metadata", "data": data["metadata"]}

    except Exception as e:
        logger.error(f"Error in generate_response: {str(e)}")
        status_code = 500
        yield f"Error: {str(e)}", {"input_tokens": 0, "output_tokens": 0, "status_code": status_code}
        raise
