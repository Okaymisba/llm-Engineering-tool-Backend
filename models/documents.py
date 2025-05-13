from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
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
    """
    __tablename__ = 'documents'

    document_id = Column(Integer, primary_key=True)
    chunk_text = Column(Text)
    api_id = Column(Integer, ForeignKey('api_list.id'), unique=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    api = relationship("APIList", back_populates="documents")
