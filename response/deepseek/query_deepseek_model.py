import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def query_deepseek_model(model, question, prompt_context=None, instructions=None, image_data=None, document_data=None,
                         web_search_results=None):
    """
    Queries the DeepSeek model through OpenAI's API, integrating various forms of input to
    formulate a comprehensive response.

    The function supports additional input data types such as context, instructions, image data,
    documents, and web search results. It utilizes these inputs to construct messages for the model
    and streams back the model's response in chunks. Token utilization data is also provided as part
    of the output.

    :param model: The model to be queried. For example, specific versions or endpoints of a DeepSeek
        model.
    :type model: str

    :param question: The primary question to send to the DeepSeek model.
    :type question: str

    :param prompt_context: Additional context that helps refine the model's response. Defaults to None
        if no context is provided.
    :type prompt_context: Optional[str]

    :param instructions: Specific instructions for the model to guide its reasoning or response.
        Defaults to None if no instructions are provided.
    :type instructions: Optional[str]

    :param image_data: Information about the image to be used as input for the query. Defaults to None
        if no image data is provided.
    :type image_data: Optional[str]

    :param document_data: Information or contents of a document to be used as input for the query.
        Defaults to None if no document data is provided.
    :type document_data: Optional[str]

    :param web_search_results: Results from web searches that can act as supplementary information for
        answering the query. Defaults to None if no web search data is provided.
    :type web_search_results: Optional[str]

    :return: A generator object yielding parts of the model's response including reasoning, content,
        and metadata on token usage. Metadata includes information about prompt tokens, completion
        tokens, and total tokens used during processing.
    :rtype: Generator[Dict[str, Any], None, None]
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

    if web_search_results:
        messages.append({"role": "system", "content": f"Here are the web search results: {web_search_results}"})

    messages.append({"role": "user", "content": question})

    token_metadata = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

    response = client.chat.completions.create(
        model=f"deepseek/{model}",
        messages=messages,
        stream=True,
    )

    for chunk in response:
        if hasattr(chunk.choices[0].delta, "reasoning") and chunk.choices[0].delta.reasoning:
            yield {"reasoning": chunk.choices[0].delta.reasoning}
        if chunk.choices[0].delta.content:
            yield {"content": chunk.choices[0].delta.content}

        if hasattr(chunk, 'usage') and chunk.usage is not None:
            token_metadata.update({
                "prompt_tokens": getattr(chunk.usage, 'prompt_tokens', None),
                "completion_tokens": getattr(chunk.usage, 'completion_tokens', None),
                "total_tokens": getattr(chunk.usage, 'total_tokens', None)
            })

    yield {"metadata": token_metadata}
