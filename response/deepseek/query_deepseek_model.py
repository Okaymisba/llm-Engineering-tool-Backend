import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def query_deepseek_model(model, question, prompt_context=None, instructions=None, image_data=None, document_data=None):
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
