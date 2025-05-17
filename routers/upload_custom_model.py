from typing import Annotated

from fastapi import UploadFile, File, Form, APIRouter, Depends

from functions.extract_document_data.extract_document_data import extract_document_data
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
    Uploads a document, processes its contents, and stores it alongside user data.

    This operation extracts textual data from an uploaded file, associates it with
    the currently authenticated user, generates an API key for storing the data,
    and saves the data with optional user-provided instructions.

    :param current_user: The authenticated user performing the document upload.
    :type current_user: User
    :param instructions: Additional guidelines or notes for processing the
        document. Default is None.
    :type instructions: str
    :param file: The document file to be uploaded and processed. Default is None.
    :type file: UploadFile
    :return: A dictionary containing the success status and a message indicating
        that the data has been successfully uploaded and stored.
    :rtype: dict
    """

    document_text = await extract_document_data(file)

    api_key = generate_api_key()
    store_user_data(current_user.id, api_key, document_text, instructions)
    return {"success": True, "message": "Data uploaded and stored successfully."}
