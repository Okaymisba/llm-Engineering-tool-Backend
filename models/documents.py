"""
Documents Model Module

This module defines the Documents model for managing document chunks in
the database. It establishes a foreign key relationship with the APIList
model and contains metadata for each document chunk.

Dependencies:
    - SQLAlchemy for ORM
    - datetime for managing timestamps
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship

from models.__init__ import Base


class Documents(Base):
    """
    Document model for managing document chunks.

    Attributes:
        document_id (int): Primary key
        chunk_text (str): Text content of the chunk
        api_id (int): Foreign key to api_list table
        created_at (datetime): Timestamp of document creation
        filename (str): Name of the uploaded file
        size (int): Size of the file in KB
        hits (int): Number of times the document has been accessed
        last_used (datetime): Timestamp of last access
    """
    __tablename__ = 'documents'

    document_id = Column(Integer, primary_key=True)
    api_id = Column(Integer, ForeignKey('api_list.id'), unique=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    hits = Column(Integer, default=0)
    filename = Column(Text, nullable=False)
    size = Column(Integer, nullable=False)
    last_used = Column(DateTime, default=None)

    api = relationship("APIList", back_populates="documents")
    embeddings = relationship("Embeddings", back_populates="document", cascade="all, delete-orphan")
