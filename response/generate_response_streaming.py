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
):
    """
    Generates a streaming response from the specified provider's model based on the given question,
    prompt context, and additional inputs. Supports providers such as "deepseek," "google," and
    others with specific implementations for each.

    This is an asynchronous generator function that yields pieces of data as they are processed.
    The response chunks may contain different types of data, including reasoning, content, and
    metadata, depending upon the provider and the model.

    :param provider: The name of the AI provider (e.g., "deepseek," "google"). Determines which model service is used.
    :param model: The specific model to query for generating the response.
    :param question: The main query or question to which the model should generate a response.
    :param prompt_context: A list representing the context or additional information to guide the response.
    :param instructions: Optional instructions passed to the model to influence the response format or content.
    :param image_data: A list of image data to be used by the model, if supported by the provider.
    :param document_data: A list of document data to be used by the model, if supported by the provider.
    :return: An asynchronous generator yielding dictionaries with keys such as "type" and "data" for processed chunks.
    :rtype: AsyncGenerator[dict, None]
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
                    document_data
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
                    document_data
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
