import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def query_deepseek_model(model, question, prompt_context=None, instructions=None, image_data=None, document_data=None):
    """
    Queries a DeepSeek model using context, instructions, images, or document data,
    passing user-specified questions and retrieving streaming responses token by token.
    This function integrates with the OpenAI API via OpenRouter.

    :param model: The specific model to be used for querying, formatted as "deepseek/<model_name>".
    :type model: str
    :param question: The main question or prompt for the model to respond to.
    :type question: str
    :param prompt_context: Optional contextual information provided to the model to guide its response.
    :type prompt_context: str or None
    :param instructions: Optional guidelines or instructions detailing how the model should behave.
    :type instructions: str or None
    :param image_data: Optional image information given as input to complement the question context.
    :type image_data: str or None
    :param document_data: Optional document information provided to enhance the query context.
    :type document_data: str or None
    :return: Yields pieces of the model's response as they stream in and ends with token metadata,
             which includes `prompt_tokens`, `completion_tokens`, and `total_tokens`, or None if not available.
    :rtype: Generator[str or dict]
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )

    messages = []

    if instructions:
        messages.append({"role": "system", "content": instructions})

    if prompt_context:
        messages.append({"role": "system", "content": f"Here is the context: {prompt_context}"})

    if image_data:
        messages.append({"role": "system", "content": f"Here is the image: {image_data}"})

    if document_data:
        messages.append({"role": "system", "content": f"Here is the document: {document_data}"})

    messages.append({"role": "user", "content": question})

    token_metadata = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

    response = client.chat.completions.create(
        model=f"deepseek/{model}",
        messages=messages,
        stream=True,
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

        if hasattr(chunk, 'usage') and chunk.usage is not None:
            token_metadata.update({
                "prompt_tokens": getattr(chunk.usage, 'prompt_tokens', None),
                "completion_tokens": getattr(chunk.usage, 'completion_tokens', None),
                "total_tokens": getattr(chunk.usage, 'total_tokens', None)
            })

    yield token_metadata
