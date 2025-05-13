import os
import shutil
from typing import Annotated

from fastapi import UploadFile, File, Form, APIRouter, Depends

from document_handling.document_handling import parse_document
from functions.generate_api_key.generate_api_key import generate_api_key
from models.user import User
from routers.auth import get_current_user
from store_data.store_data import store_user_data

router = APIRouter()


@router.post("/upload/")
async def upload_document(
        current_user: Annotated[User, Depends(get_current_user)],
        instructions: str = Form(None),
        file: UploadFile = File(None)
):
    """
    Handles the upload and storage of a document for the authenticated user, processes the document,
    and stores the extracted text alongside additional information.

    :param current_user: Annotated parameter for the authenticated user object,
        fetched using the dependency injection mechanism of `Depends(get_current_user)`.
    :type current_user: User
    :param instructions: Optional textual instructions for processing or storing the document.
    :type instructions: str
    :param file: Uploaded document file whose content is processed and stored.
    :type file: UploadFile
    :return: JSON response with a success status and a message indicating the result of the operation.
    :rtype: dict
    """

    upload_dir = f"./uploads/{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        document_text = parse_document(file_path)

        api_key = generate_api_key()
        store_user_data(current_user.id, api_key, document_text, instructions)
        return {"success": True, "message": "Data uploaded and stored successfully."}

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(upload_dir):
            os.removedirs(upload_dir)
