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

    # TODO For Wasay: For now this stores the uploaded documents in ./uploads directory which for many users will
    #  be messy. So I think we should save it in the way that the documents will be stored with the user_id as the
    #  directory name and the file name will be the document name and after extracting the contents the file should
    #  be deleted cuz we dont need that. its my opinion, if u think of a better way please let me know

    upload_dir = f"./uploads/{user_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        document_text = parse_document(file_path)

        store_user_data(user_id, document_text, instructions)
        return {"message": "Data uploaded and stored successfully."}

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(upload_dir):
            os.removedirs(upload_dir)


    
    
