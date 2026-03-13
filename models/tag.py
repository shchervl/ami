from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from models.base import Base

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", ForeignKey("notes.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    @validates("name")
    def validate_name(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("Tag name cannot be empty")
        if len(value) > 10:
            raise ValueError(f"Tag '{value}' exceeds 10 character limit")
        return value

    notes: Mapped[list["Note"]] = relationship(  # noqa: F821
        "Note", secondary=note_tags, back_populates="tags"
    )
