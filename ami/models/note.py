from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    @validates("title", "body")
    def validate_not_empty(self, key, value):
        if not value or not str(value).strip():
            raise ValueError(f"{key.title()} cannot be empty")
        return value

    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary="note_tags", back_populates="notes"
    )
