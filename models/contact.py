from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class Phone(Base):
    __tablename__ = "phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    number: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str | None] = mapped_column(String, nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="phones")


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str | None] = mapped_column(String, nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="emails")
