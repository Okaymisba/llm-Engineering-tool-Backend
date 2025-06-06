import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from models.__init__ import get_db
from models.user import User
from utilities.email_service import generate_OTP, send_email
from utilities.email_templates import create_login_opt_msg, forgot_password_otp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
MAX_OTP_ATTEMPTS = int(os.getenv("MAX_OTP_ATTEMPTS", "3"))

PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$")

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class OTPData:
    """
    Class to store OTP data with expiration and attempt tracking.
    
    Attributes:
        otp (str): The one-time password
        expiry (datetime): When the OTP expires
        attempts (int): Number of failed attempts to use this OTP
    """

    def __init__(self, otp: str, expiry: datetime, attempts: int = 0):
        self.otp = otp
        self.expiry = expiry
        self.attempts = attempts


CURRENT_OTPS: dict[str, OTPData] = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class Token(BaseModel):
    """
    Token response model for authentication.
    
    Attributes:
        access_token (str): JWT access token
        token_type (str): Type of token (bearer)
        expires_in (int): Token expiration time in seconds
    """
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """
    Token data model for JWT payload.
    
    Attributes:
        email (str): User's email address
    """
    email: str | None = None


class UserCreate(BaseModel):
    """
    User creation request model.
    
    Attributes:
        username (str): Username (3-50 characters)
        email (EmailStr): Valid email address
        password (str): Password (min 8 characters)
    """
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=8)

    @classmethod
    def validate_password(cls, password: str) -> bool:
        """
        Validates password strength.
        
        Args:
            password (str): Password to validate
            
        Returns:
            bool: True if password meets requirements, False otherwise
        """
        return bool(PASSWORD_REGEX.match(password))


class UserResponse(BaseModel):
    """
    User response model.
    
    Attributes:
        id (int): User ID
        username (str): Username
        email (str): Email address
        is_verified (bool): Email verification status
    """
    id: int
    username: str
    email: str
    is_verified: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """
    Login request model.
    
    Attributes:
        email (EmailStr): User's email
        password (str): User's password
    """
    email: EmailStr
    password: str


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a JWT access token.
    
    Args:
        data (dict): Data to encode in the token
        expires_delta (timedelta, optional): Token expiration time. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.
        
    Returns:
        str: Encoded JWT token
        
    Raises:
        JWTError: If token encoding fails
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class TokenRefreshMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Check if the response has a new token in headers
        if "X-New-Access-Token" in response.headers:
            # Set the new token in Authorization header
            response.headers["Authorization"] = f"Bearer {response.headers['X-New-Access-Token']}"
            # Remove the temporary header
            del response.headers["X-New-Access-Token"]
            
        return response


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Session = Depends(get_db),
        response: Response = None
) -> User:
    """
    Validates JWT token and returns the current user.
    Also creates a new token for the next request.
    
    Args:
        token (str): JWT token from Authorization header
        db (Session): Database session
        response (Response): FastAPI response object
        
    Returns:
        User: Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if not user:
        raise credentials_exception
        
    # Update last_active time
    user.last_active = datetime.now(timezone.utc)
    db.commit()
    
    # Create new token for next request
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Set new token in response headers
    if response:
        response.headers["X-New-Access-Token"] = new_token
    
    return user


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user.
    
    Args:
        user (UserCreate): User registration data
        db (Session): Database session
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: If email/username exists or password invalid
    """
    if not UserCreate.validate_password(user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain letters, numbers, and special characters"
        )

    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()

    if existing_user:
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    try:
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=User.get_password_hash(user.password)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"New user registered: {user.email}")
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    Authenticates user and returns JWT token.
    
    Args:
        form_data (LoginRequest): Login credentials
        db (Session): Database session
        
    Returns:
        Token: JWT token data
        
    Raises:
        HTTPException: If credentials invalid or user not verified
    """
    user = db.query(User).filter(User.email == form_data.email).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    logger.info(f"User logged in: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/get-otp")
async def get_otp(
        email: str = None,
        username: str = None,
):
    """
    Generates and sends OTP to user's email.
    
    Args:
        email (str): User's email address
        username (str): User's username
        request (Request): FastAPI request object
        
    Returns:
        dict: Success status and message
        
    Raises:
        HTTPException: If rate limit exceeded or email sending fails
    """
    # Check if OTP already exists and is not expired
    if email in CURRENT_OTPS:
        otp_data = CURRENT_OTPS[email]
        if datetime.now(timezone.utc) < otp_data.expiry:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {OTP_EXPIRY_MINUTES} minutes before requesting a new OTP"
            )

    otp = generate_OTP()
    msg = create_login_opt_msg(username, otp)

    try:
        await send_email(email, "Your One-Time Password (OTP) for Account Registration", msg)
        CURRENT_OTPS[email] = OTPData(
            otp=otp,
            expiry=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
        )
        logger.info(f"OTP sent to: {email}")
        return {"success": True, "message": "OTP sent successfully"}
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending OTP"
        )


@router.post("/verify-otp")
async def verify_otp(
        email: str,
        otp: int,
        db: Session = Depends(get_db)
):
    """
    Verifies OTP and marks user as verified.
    
    Args:
        email (str): User's email address
        otp (int): OTP to verify
        db (Session): Database session
        
    Returns:
        dict: Success status and message
        
    Raises:
        HTTPException: If OTP invalid, expired, or max attempts exceeded
    """
    if email not in CURRENT_OTPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found for this email"
        )

    otp_data = CURRENT_OTPS[email]

    if datetime.now(timezone.utc) > otp_data.expiry:
        del CURRENT_OTPS[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )

    if otp_data.attempts >= MAX_OTP_ATTEMPTS:
        del CURRENT_OTPS[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP attempts exceeded"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if str(otp_data.otp) == str(otp):
        user.is_verified = True
        db.commit()
        del CURRENT_OTPS[email]
        logger.info(f"User verified: {email}")
        return {"success": True, "message": "User verified successfully"}

    otp_data.attempts += 1
    return {"success": False, "message": "Incorrect OTP"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Returns current user's information.
    
    Args:
        current_user (User): Current authenticated user
        
    Returns:
        UserResponse: User information
    """
    return current_user

class ForgotPasswordRequest(BaseModel):
    """
    Forgot password request model.
    
    Attributes:
        email (EmailStr): User's email
        username (str): User's username
    """
    email: EmailStr
    username: str

class ResetPasswordRequest(BaseModel):
    """
    Reset password request model.
    
    Attributes:
        email (EmailStr): User's email
        new_password (str): New password to set
    """
    email: EmailStr
    new_password: constr(min_length=8)

    @classmethod
    def validate_password(cls, password: str) -> bool:
        """
        Validates password strength.
        
        Args:
            password (str): Password to validate
            
        Returns:
            bool: True if password meets requirements, False otherwise
        """
        return bool(PASSWORD_REGEX.match(password))

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates password reset process by verifying email and username.
    
    Args:
        request (ForgotPasswordRequest): Email and username
        db (Session): Database session
        
    Returns:
        dict: Success status and message
        
    Raises:
        HTTPException: If user not found or invalid credentials
    """
    user = db.query(User).filter(
        User.email == request.email,
        User.username == request.username
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with provided email and username"
        )
    
    # Generate and send OTP
    otp = generate_OTP()
    msg = forgot_password_otp.format(username=request.username, otp=otp)
    
    try:
        await send_email(request.email, "Password Reset OTP", msg)
        CURRENT_OTPS[request.email] = OTPData(
            otp=otp,
            expiry=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
        )
        logger.info(f"Password reset OTP sent to: {request.email}")
        return {"success": True, "message": "OTP sent successfully"}
    except Exception as e:
        logger.error(f"Error sending password reset OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending OTP"
        )

@router.post("/verify-reset-otp")
async def verify_reset_otp(
    email: str,
    otp: int,
    db: Session = Depends(get_db)
):
    """
    Verifies OTP for password reset.
    
    Args:
        email (str): User's email
        otp (int): OTP to verify
        db (Session): Database session
        
    Returns:
        dict: Success status and message
        
    Raises:
        HTTPException: If OTP invalid, expired, or max attempts exceeded
    """
    if email not in CURRENT_OTPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found for this email"
        )

    otp_data = CURRENT_OTPS[email]

    if datetime.now(timezone.utc) > otp_data.expiry:
        del CURRENT_OTPS[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )

    if otp_data.attempts >= MAX_OTP_ATTEMPTS:
        del CURRENT_OTPS[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP attempts exceeded"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if str(otp_data.otp) == str(otp):
        # Generate a temporary token for password reset
        access_token_expires = timedelta(minutes=15)  # Short expiry for security
        reset_token = create_access_token(
            data={"sub": user.email, "purpose": "password_reset"},
            expires_delta=access_token_expires
        )
        del CURRENT_OTPS[email]
        logger.info(f"Password reset OTP verified for: {email}")
        return {
            "success": True,
            "message": "OTP verified successfully",
            "reset_token": reset_token
        }

    otp_data.attempts += 1
    return {"success": False, "message": "Incorrect OTP"}

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    reset_token: str,
    db: Session = Depends(get_db)
):
    """
    Resets user's password after OTP verification.
    
    Args:
        request (ResetPasswordRequest): New password request
        reset_token (str): JWT token from OTP verification
        db (Session): Database session
        
    Returns:
        dict: Success status and message
        
    Raises:
        HTTPException: If token invalid or password requirements not met
    """
    try:
        # Verify reset token
        payload = jwt.decode(reset_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        purpose: str = payload.get("purpose")
        
        if not email or purpose != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid reset token"
            )
            
        if email != request.email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email mismatch"
            )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token"
        )
    
    # Validate password strength
    if not ResetPasswordRequest.validate_password(request.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain letters, numbers, and special characters"
        )
    
    # Update password
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        user.hashed_password = User.get_password_hash(request.new_password)
        db.commit()
        logger.info(f"Password reset successful for: {request.email}")
        return {"success": True, "message": "Password reset successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting password"
        )
    
    