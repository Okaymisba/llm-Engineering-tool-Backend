from sqlalchemy import Column, Integer, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from models.__init__ import Base


class Embeddings(Base):
    __tablename__ = 'embeddings'

    document_id = Column(Integer, ForeignKey('documents.document_id'), primary_key=True)
    embedding = Column(LargeBinary)

    document = relationship("Documents", back_populates="embeddings", cascade="all, delete-orphan")
