import os
import shutil

from document_handling.document_handling import parse_document
from fastapi import FastAPI, UploadFile, File, Form, APIRouter

from store_data.store_data import store_user_data

router = APIRouter()


@router.post("/upload/")
async def upload_document(
        user_id: int = Form(...),
        instructions: str = Form(None),
        file: UploadFile = File(None)
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
