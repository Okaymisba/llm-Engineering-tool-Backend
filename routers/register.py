from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.user import User, get_db, get_password_hash
from pydantic import BaseModel, EmailStr


router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id:int
    username:str
    email:str

    class Config:
        orm_mode = True

@router.post("/register", response_model=UserResponse)
async def Register(user:UserCreate, db : Session = Depends(get_db)):
    """
    Creates a new user with the given username, email and password.

    Args:
    user (UserCreate): The user information to be registered.

    Returns:
    UserResponse: The registered user information.

    Raises:
    HTTPException: If the user's email is already registered.
    """
    # Check if user already exist
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username = user.username,
        email = user.email,
        hashed_password = hashed_password
    )
    # Adding the user record in database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

