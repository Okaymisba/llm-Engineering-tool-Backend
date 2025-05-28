"""
User Model Module

This module defines the User model with password hashing capabilities and database
interaction. It provides functionality for user authentication and management.

Dependencies:
    - SQLAlchemy for ORM
    - passlib for password hashing
    - python-dotenv for environment variable management
"""

import os

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from models.__init__ import Base

load_dotenv()

# Password hashing context for secure password management
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    Represents a user in the application with attributes for authentication, usage,
    and transaction tracking.

    This class defines a user model with fields such as `username`, `email`,
    `hashed_password`, and various attributes to track tokens, credits, transactions,
    and activity details. Relationships are defined for API keys and chat sessions,
    which are associated entities.

    :ivar id: Unique identifier of the user.
    :type id: int
    :ivar username: The username associated with the user.
    :type username: str
    :ivar email: The email address associated with the user.
    :type email: str
    :ivar hashed_password: The hashed password for authentication.
    :type hashed_password: str
    :ivar is_verified: Indicates if the user has been verified.
    :type is_verified: bool
    :ivar total_tokens: Total token allocation for the user.
    :type total_tokens: int
    :ivar tokens_used: Total number of tokens the user has consumed.
    :type tokens_used: int
    :ivar tokens_remaining: Remaining tokens available to the user.
    :type tokens_remaining: int
    :ivar total_credits: Total credits allocated to the user.
    :type total_credits: int
    :ivar credits_remaining: Credits remaining for the user to utilize.
    :type credits_remaining: int
    :ivar credits_used: Total credits consumed by the user.
    :type credits_used: int
    :ivar no_of_transactions: The number of transactions carried out by the user.
    :type no_of_transactions: int
    :ivar pending_transaction: Indicates whether the user has a pending transaction.
    :type pending_transaction: bool
    :ivar last_transaction: Timestamp of the user's last transaction, or None if no
        transaction has occurred.
    :type last_transaction: datetime.datetime
    :ivar last_active: Timestamp of the user's last activity, or None if not
        available.
    :type last_active: datetime.datetime
    :ivar api_keys: List of API keys associated with the user.
    :type api_keys: list[APIList]
    :ivar chat_sessions: List of chat sessions associated with the user.
    :type chat_sessions: list[ChatSession]
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    total_tokens = Column(Integer, default=os.getenv("FREE_TOKENS"))
    tokens_used = Column(Integer, default=0)
    tokens_remaining = Column(Integer, default=os.getenv("FREE_TOKENS"))
    total_credits = Column(Integer, default=0)
    credits_remaining = Column(Integer, default=0)
    credits_used = Column(Integer, default=0)
    no_of_transactions = Column(Integer, default=0)
    pending_transaction = Column(Boolean, default=False)
    last_transaction = Column(DateTime(timezone=True), nullable=True)
    last_active = Column(DateTime(timezone=True), nullable=True)

    api_keys = relationship("APIList", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

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
