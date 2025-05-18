from typing import Optional, Annotated, List

from fastapi import APIRouter, File, UploadFile, Depends, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from functions.extract_document_data.extract_document_data import extract_document_data
from functions.extract_image_data.extract_image_data import extract_image_data
from models import get_db
from models.chat_sessions import ChatSession
from models.user import User
from routers.auth import get_current_user

router = APIRouter()


class Chat(BaseModel):
    session_id: str
    question: str
    model: str
    our_image_processing_algo: bool
    document_semantic_search: bool


@router.post("/chat")
async def chat(
        session_id: Annotated[str, Form()],
        question: Annotated[str, Form()],
        model: Annotated[str, Form()],
        our_image_processing_algo: Annotated[bool, Form()],
        document_semantic_search: Annotated[bool, Form()],
        current_user: Annotated[User, Depends(get_current_user)],
        upload_image: Optional[List[UploadFile]] = File(None),
        upload_document: Optional[List[UploadFile]] = File(None),

        db: Session = Depends(get_db)
):
    image_data = []
    document_data = []

    if upload_image:
        for image in upload_image:
            image_data.append(extract_image_data(image.file))

    if upload_document:
        for document in upload_document:
            document_data.append(await extract_document_data(document))

    chat_session = ChatSession(
        session_id=session_id,
        belongs_to=current_user.id,
        document=str(document_data),
        image=str(image_data),
        question=question,
    )

    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)

    print(f"Chat Session Created: {chat_session.id}")

    return None
