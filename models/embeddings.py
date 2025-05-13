from sqlalchemy import Column, Integer, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from models.__init__ import Base


class Embeddings(Base):
    __tablename__ = 'embeddings'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('api_list.id'))
    embedding = Column(LargeBinary)

    document = relationship("APIList", back_populates="embeddings")
