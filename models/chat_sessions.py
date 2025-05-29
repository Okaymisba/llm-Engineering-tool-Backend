from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from models.__init__ import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False)
    belongs_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    document = Column(Text, nullable=True)
    image = Column(Text, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)

    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    request_latency_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    document_hits = Column(JSON, nullable=True)
    

    created_at = Column(Text, nullable=False, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_sessions")
