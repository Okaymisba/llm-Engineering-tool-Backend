from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.user import User, User as UserModel
from models.__init__ import get_db
from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Creates a new user with the given username, email and password.

    Args:
        user (UserCreate): The user information to be registered.

    Returns:
        UserResponse: The registered user information.

    Raises:
        HTTPException: If the user's email is already registered.
    """
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user with hashed password
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=User.get_password_hash(user.password)
    )

    # Adding the user record in database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login")
async def login_user(
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    Authenticates a user with their email and password.

    Args:
        login_data (LoginRequest): The login credentials (email and password).
        db (Session): Database session.

    Returns:
        Success message

    Raises:
        HTTPException: If the email is not found or password is incorrect.
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not found"
        )
    if not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    return {"success": True}
