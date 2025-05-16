from typing import Optional, Annotated

from fastapi import APIRouter, File, UploadFile, Depends
from pydantic import BaseModel

from functions.extract_image_data.extract_image_data import extract_image_data
from models.user import User
from routers.auth import get_current_user

router = APIRouter()


class Chat(BaseModel):
    question: str
    model: str
    image_processing_algo: str
    document_semantic_search: str


@router.get("/chat")
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
            return document
        return None
    return None
