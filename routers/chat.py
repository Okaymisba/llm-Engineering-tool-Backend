from typing import Optional, Annotated

from fastapi import APIRouter, File, UploadFile, Depends
from pydantic import BaseModel

from models.user import User
from routers.auth import get_current_user

router = APIRouter()


class Chat(BaseModel):
    question: str
    model: str
    image_processing_algo: str
    document_semantic_search: str
    upload_image: Optional[list[UploadFile]] = File(None)
    upload_document: Optional[list[UploadFile]] = File(None)


@router.get("/chat")
async def chat(data: Chat, current_user: Annotated[User, Depends(get_current_user)]):
    image_data = []
    document_data = []

    if data.upload_image:
        for image in data.upload_image:
            return image
    if data.upload_document:
        for document in data.upload_document:
            return document
        return None
    return None
