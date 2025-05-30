import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def query_deepseek_model(model, question, prompt_context=None, instructions=None, image_data=None, document_data=None):
    """
    Executes a query against a DeepSeek model using OpenAI's API and streams the response
    in chunks. The function accommodates additional context, instructions, and data in the query
    to enhance the model's understanding and response accuracy.

    The function begins by creating a client for OpenAI's API, constructing the message payload
    to be sent to the model based on the provided parameters, and then streaming the response
    back from the API in incremental chunks to allow real-time processing.

    :param model: Name of the specific DeepSeek model to query.
    :type model: str
    :param question: The user's query or question to be answered by the model.
    :type question: str
    :param prompt_context: (Optional) Additional context information to be included in the query.
    :type prompt_context: str, optional
    :param instructions: (Optional) Custom instructions provided to enhance or steer the model's behavior.
    :type instructions: str, optional
    :param image_data: (Optional) String representation of image data to assist in answering the query.
    :type image_data: str, optional
    :param document_data: (Optional) String representation of document data to assist in answering the query.
    :type document_data: str, optional
    :return: Generator yielding chunks of the model's textual response as strings.
    :rtype: Iterator[str]
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

    response = client.chat.completions.create(
        model=f"deepseek/{model}",
        messages=messages,
        stream=True,
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
            yield chunk.choices[0].delta.content
