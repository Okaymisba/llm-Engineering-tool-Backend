"""
User Model Module

This module defines the User model with password hashing capabilities and database
interaction. It provides functionality for user authentication and management.

Dependencies:
    - SQLAlchemy for ORM
    - passlib for password hashing
    - python-dotenv for environment variable management
"""

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from models.__init__ import Base

load_dotenv()

# Password hashing context for secure password management
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    User model for managing user accounts and authentication.

    Attributes:
        id (int): Primary key for user identification
        username (str): Unique username for the user
        email (str): Unique email address
        hashed_password (str): BCrypt hashed password
        api_keys (relationship): One-to-many relationship with APIList model

    The model includes methods for password hashing and verification using BCrypt.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    api_keys = relationship("APIList", back_populates="user")

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Generate a BCrypt hash for a given password.

        Args:
            password: Plain text password to hash

        Returns:
            str: BCrypt hashed password
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        """
        Verify a plain text password against the stored hash.

        Args:
            plain_password: Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, self.hashed_password)
