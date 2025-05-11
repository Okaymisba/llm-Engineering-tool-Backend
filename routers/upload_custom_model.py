import os
import shutil

from document_handling.document_handling import parse_document
from fastapi import FastAPI, UploadFile, File, Form, APIRouter

from functions.generate_api_key.generate_api_key import generate_api_key
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

    # TODO: Add a method for extracting the user id from the table user_data for now the user id is provided through
    #  the form but its not right so after wasay finishes the authentications then it will be done

    upload_dir = f"./uploads/{user_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        document_text = parse_document(file_path)

        api_key = generate_api_key()
        store_user_data(user_id, api_key, document_text, instructions)
        return {"success": True, "message": "Data uploaded and stored successfully."}

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(upload_dir):
            os.removedirs(upload_dir)
