import re
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from models.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    birthday: Mapped[Date | None] = mapped_column(Date, nullable=True)

    phones: Mapped[list["Phone"]] = relationship(
        "Phone", back_populates="contact", cascade="all, delete-orphan"
    )
    emails: Mapped[list["Email"]] = relationship(
        "Email", back_populates="contact", cascade="all, delete-orphan"
    )

    @validates("first_name", "last_name")
    def validate_name(self, key, value):
        if not value or not str(value).strip():
            raise ValueError(f"{key.replace('_', ' ').title()} cannot be empty")
        return value

    @validates("birthday")
    def validate_birthday(self, key, value):
        if value is None:
            return value
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)  # YYYY-MM-DD format
            except ValueError:
                raise ValueError("Invalid birthday format. It must be YYYY-MM-DD")
        raise ValueError("Birthday must be a date object or string")


class Phone(Base):
    __tablename__ = "phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    number: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str | None] = mapped_column(String, nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="phones")

    @validates("number")
    def validate_number(self, key, value):
        value = str(value).strip()
        if not (len(value) == 10 and value.isdigit()):
            raise ValueError("Invalid phone number. It must be exactly 10 digits.")
        return value


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str | None] = mapped_column(String, nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="emails")

    @validates("address")
    def validate_email(self, key, value):
        value = str(value).strip()
        # Basic regex for "something@something.com"
        if not re.match(r"^[^@\s]+@[^@\s]+$", value):
            raise ValueError(
                "Invalid email format. It must be 'something@something.com'"
            )
        return value
