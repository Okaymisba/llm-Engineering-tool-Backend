import os
from fastapi import FastAPI, UploadFile, File, Form
import shutil

from document_handling.document_handling import parse_document
from prompt_generation.prompt_generation import generate_prompt
from prompt_generation.query_local_model import query_local_model
from store_data.store_data import store_user_data

app = FastAPI()


@app.post("/upload/")
async def upload_document(
        user_id: str = Form(...),
        instructions: str = Form(...),
        file: UploadFile = File(...)
):
    """
    Uploads a document, extracts its content, and stores user data.

    This asynchronous function handles uploading a document file, extracting
    its text content, and storing the data in temporary in-memory storage
    along with provided user instructions.

    The function first saves the uploaded file to a local directory, then
    extracts the text content from the document using the `parse_document`
    function. The extracted text and user instructions are stored using
    the `store_user_data` function.

    Args:
        user_id (str): The ID of the user uploading the document.
        instructions (str): The instructions to be stored alongside the document text.
        file (UploadFile): The uploaded document file.

    Returns:
        dict: A message indicating successful data upload and storage.
    """

    os.makedirs("./uploads", exist_ok=True)
    file_path = f"./uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document_text = parse_document(file_path)

    store_user_data(user_id, document_text, instructions)
    return {"message": "Data uploaded and stored successfully."}


@app.get("/ask/")
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
    return {"answer": response}
