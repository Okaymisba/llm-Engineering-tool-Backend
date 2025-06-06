"""
Embeddings Model Module

This module defines the Embeddings model for managing and storing
embeddings related to documents in the database. It establishes a foreign key
relationship with the Documents model and stores embeddings as binary data.

Dependencies:
    - SQLAlchemy for ORM
"""

from sqlalchemy import Column, Integer, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import relationship

from models.__init__ import Base


class Embeddings(Base):
    """
    Represents the embeddings stored in the database.

    This class is used to manage and store embeddings related to documents
    in the database. It links an embedding with a specific document using
    a foreign key relationship. The embeddings are stored as binary data.
    It maintains a relationship with the ``Documents`` class to provide access
    to document details associated with the embedding.

    :ivar id: Unique identifier for the embedding record.
    :type id: int
    :ivar document_id: Foreign key linking the embedding to a document in
        the ``Documents`` table.
    :type document_id: int
    :ivar embedding: Binary data representing the embedding.
    :type embedding: bytes
    :ivar document: Relationship providing access to the associated document
        record in the ``Documents`` table.
    :type document: Documents
    """
    __tablename__ = 'embeddings'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.document_id'))
    chunk_text = Column(Text)
    embedding = Column(LargeBinary)

    document = relationship("Documents", back_populates="embeddings")
