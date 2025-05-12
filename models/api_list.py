"""
APIList Model Module

This module defines the APIList model for managing API keys and associated document data.
It provides functionality for storing and retrieving API keys linked to user documents
and their processing instructions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, Session
from models.__init__ import Base


class APIList(Base):
    """
    API List model for managing document-specific API keys.

    Attributes:
        id (int): Primary key
        main_table_user_id (int): Foreign key to users table
        api_key (str): Unique API key for document access
        document_data (str): Stored document text/content
        instructions (str): Processing instructions for the document
        created_at (datetime): Timestamp of API key creation
        last_used_at (datetime): Timestamp of last API key usage
        user (relationship): Relationship to User model
    """
    __tablename__ = 'api_list'

    id = Column(Integer, primary_key=True)
    main_table_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    document_data = Column(Text)
    instructions = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")

    @classmethod
    def get_by_api_key(cls, db: Session, api_key: str):
        """
        Retrieve an API entry using its API key.

        Args:
            db: SQLAlchemy database session
            api_key: The API key string to search for

        Returns:
            APIList object if found, None otherwise
        """
        return db.query(cls).filter(cls.api_key == api_key).first()

    @classmethod
    def create_api_entry(cls, db: Session, main_table_user_id: int, api_key: str,
                        document_data: str, instructions: str = None):
        """
        Create a new API key entry with associated document data.

        Args:
            db: SQLAlchemy database session
            main_table_user_id: User ID who owns this API key
            api_key: Unique API key string
            document_data: Document text/content to be stored
            instructions: Optional processing instructions

        Returns:
            Newly created APIList object
        """
        api_entry = cls(
            main_table_user_id=main_table_user_id,
            api_key=api_key,
            document_data=document_data,
            instructions=instructions
        )
        db.add(api_entry)
        db.commit()
        db.refresh(api_entry)
        return api_entry