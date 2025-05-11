from fastapi import APIRouter

from prompt_generation.prompt_generation import generate_prompt
from prompt_generation.query_local_model import query_local_model

router = APIRouter()


@router.get("/ask/")
def ask_question(user_id: str, question: str):
    """
    Handles GET requests to answer a question using stored user data.

    This function generates a prompt from the stored user data and the given question,
    sends the prompt to a local language model, and returns the model's response.

    Args:
        user_id (str): The ID of the user whose data is used to generate the prompt.
        question (str): The question to be answered by the language model.

    Returns:
        dict: A dictionary containing the answer from the language model.
    """

    prompt = generate_prompt(user_id, question)
    response = query_local_model(prompt)
    return {"success": True, "answer": response}
