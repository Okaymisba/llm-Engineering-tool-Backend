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
    Generate a streaming response by querying the specified model provider using the given parameters.

    This asynchronous generator function streams chunks of the generated response from the specified
    provider. Supported providers include "deepseek", "openai", "anthropic", and "google". Depending
    on the provider, certain underlying querying functions will be invoked to process the input parameters,
    generate a response, and return the result in chunks. Each chunk can represent a part of the model's
    response or terminal metadata such as token usage statistics for the interaction. Errors during the
    process are logged, and an error message along with relevant metadata is yielded.

    :param provider: The name of the provider used for querying the model. Supported providers
        include options like "deepseek", "openai", "anthropic", and "google".
    :param model: The name or identifier of the model being queried, provided by the specified
        provider.
    :param question: The question or main query string to be provided as input to the model.
    :param prompt_context: Optional list of contextual information to guide the model's output.
        Typically used to provide supplementary information or dialogue context.
    :param instructions: Optional additional instructions or system-level guidelines to shape
        the behavior of the model's response.
    :param image_data: Optional list of image data to be processed or referenced by the model,
        if the model supports multimodal input.
    :param document_data: Optional list of document data to be used by the model in generating
        its response or providing insights.
    :return: An asynchronous generator yielding individual chunks of data as streaming parts
        of the response from the given provider.

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
                yield chunk
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
                yield chunk

    except Exception as e:
        logger.error(f"Error in generate_response: {str(e)}")
        status_code = 500
        yield f"Error: {str(e)}", {"input_tokens": 0, "output_tokens": 0, "status_code": status_code}
        raise
