from typing import Optional, Annotated

from fastapi import APIRouter, File, UploadFile, Depends
from pydantic import BaseModel

from functions.extract_document_data.extract_document_data import extract_document_data
from functions.extract_image_data.extract_image_data import extract_image_data
from functions.generate_prompt_for_chat.generate_prompt_for_chat import generate_prompt_for_chat
from models.user import User
from routers.auth import get_current_user

router = APIRouter()


class Chat(BaseModel):
    question: str
    model: str
    image_processing_algo: str
    document_semantic_search: str


@router.post("/chat")
async def chat(data: Chat,
               current_user: Annotated[User, Depends(get_current_user)],
               upload_image: Optional[list[UploadFile]] = File(None),
               upload_document: Optional[list[UploadFile]] = File(None),
               ):
    image_data = []
    document_data = []

    if data.upload_image:
        for image in data.upload_image:
            image_data.append(extract_image_data(image.file))
    if data.upload_document:
        for document in data.upload_document:
            document_data.append(extract_document_data(document.file))

    if image_data and document_data:
        return generate_prompt_for_chat(data.question, image_data, document_data)
    elif image_data:
        return generate_prompt_for_chat(data.question, image_data, None)
    elif document_data:
        return generate_prompt_for_chat(data.question, None, document_data)

    return None
