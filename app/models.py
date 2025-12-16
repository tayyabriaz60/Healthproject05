from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ChatSession(Base):
    """A logical chat session that groups messages for a (future) user."""
    __tablename__ = "chat_sessions"

    # We reuse the existing chat_id (UUID string) as primary key so API doesn’t change.
    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)

    # Placeholder for future auth integration; nullable for now.
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(default=None, nullable=True)

    # Optional field if we ever separate internal Gemini session ID from public chat_id.
    gemini_session_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat_session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    """Individual messages in a chat session."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    chat_session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # 'user' or 'assistant'
    text: Mapped[str] = mapped_column(Text())
    # Optional relative path to an image file stored on disk (e.g. media/chat_images/...)
    image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    chat_session: Mapped[ChatSession] = relationship(back_populates="messages")


