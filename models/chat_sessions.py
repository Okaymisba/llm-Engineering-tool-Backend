from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from models.__init__ import Base


class ChatSession(Base):
    """
    Represents a chat session record in the database.

    This class serves as a representation of a chat session entity within a database
    for tracking interactions between a user and a conversational model. It includes
    details about the session such as input/output tokens, latency, associated
    documents, etc. Additionally, it maintains relationships with other entities
    like the user to whom the session belongs.

    :ivar id: The primary key identifying the chat session.
    :type id: int
    :ivar session_id: A unique identifier for the session.
    :type session_id: str
    :ivar belongs_to: Foreign key linking the session to a specific user.
    :type belongs_to: int
    :ivar document: The document associated with the session, if any.
    :type document: str or None
    :ivar image: Image data associated with the session, if any.
    :type image: str or None
    :ivar question: The user's input question during the session.
    :type question: str
    :ivar answer: The model-generated response for the session, if any.
    :type answer: str or None
    :ivar model: The conversational model used in the session.
    :type model: str
    :ivar input_tokens: Number of tokens in the user input, if tracked.
    :type input_tokens: int or None
    :ivar output_tokens: Number of tokens in the model output, if tracked.
    :type output_tokens: int or None
    :ivar total_tokens: Total tokens involved in the session, input and output combined.
    :type total_tokens: int or None
    :ivar request_latency_ms: Request-response latency in milliseconds, if tracked.
    :type request_latency_ms: int or None
    :ivar status_code: HTTP status code of the API response, if applicable.
    :type status_code: int or None
    :ivar document_hits: Metadata about documents accessed or returned for the session.
    :type document_hits: dict or None
    :ivar created_at: A timestamp of when the session was created.
    :type created_at: str
    :ivar user: Relationship representing the user to whom this session belongs.
    :type user: User
    """
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False)
    belongs_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    document = Column(Text, nullable=True)
    image = Column(Text, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    model = Column(Text, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    request_latency_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    document_hits = Column(JSON, nullable=True)

    created_at = Column(Text, nullable=False, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_sessions")
