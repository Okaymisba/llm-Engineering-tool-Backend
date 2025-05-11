from fastapi import APIRouter

from prompt_generation.prompt_generation import generate_prompt
from prompt_generation.query_local_model import query_local_model

router = APIRouter()


@router.get("/ask/")
def ask_question(api_key: str, question: str):
    """
    Handles a request to ask a question, generates a prompt from the input, queries a local model for an
    answer, and returns the result.

    :param api_key: API key used for authentication or identification purposes.
    :type api_key: str
    :param question: The question text to be processed and answered by the model.
    :type question: str
    :return: A dictionary containing the success status and the generated answer.
    :rtype: dict
    """

    prompt = generate_prompt(api_key, question)
    response = query_local_model(prompt)
    return {"success": True, "answer": response}
