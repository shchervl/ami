from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from ami.models import Contact, Email, Phone


def test_create_contact_with_all_fields(session):
    contact = Contact(
        first_name="John",
        last_name="Doe",
        address="123 Main St",
        birthday=date(1990, 1, 1),
    )
    session.add(contact)
    session.commit()

    assert contact.id is not None
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.address == "123 Main St"


def test_create_contact_with_minimal_fields(session):
    contact = Contact(first_name="A", last_name="B")
    session.add(contact)
    session.commit()

    assert contact.id is not None
    assert contact.address is None
    assert contact.birthday is None


def test_contact_with_multiple_phones(session):
    contact = Contact(first_name="Jane", last_name="Smith")
    contact.phones = [
        Phone(number="1234567890", type="personal"),
        Phone(number="0987654321", type="work"),
    ]
    session.add(contact)
    session.commit()

    assert len(contact.phones) == 2


def test_contact_with_multiple_emails(session):
    contact = Contact(first_name="Jane", last_name="Smith")
    contact.emails = [
        Email(address="jane@personal.com", type="personal"),
        Email(address="jane@work.com", type="work"),
    ]
    session.add(contact)
    session.commit()

    assert len(contact.emails) == 2


def test_phone_without_type_is_allowed(session):
    contact = Contact(first_name="Jane", last_name="Smith")
    contact.phones = [Phone(number="1234567890")]
    session.add(contact)
    session.commit()

    assert contact.phones[0].type is None


def test_email_without_type_is_allowed(session):
    contact = Contact(first_name="Jane", last_name="Smith")
    contact.emails = [Email(address="jane@example.com")]
    session.add(contact)
    session.commit()

    assert contact.emails[0].type is None


def test_deleting_contact_cascades_phones_and_emails(session):
    contact = Contact(first_name="Jane", last_name="Smith")
    contact.phones = [Phone(number="1234567890")]
    contact.emails = [Email(address="jane@example.com")]
    session.add(contact)
    session.commit()

    session.delete(contact)
    session.commit()

    assert session.query(Phone).count() == 0
    assert session.query(Email).count() == 0


def test_contact_with_single_char_names(session):
    contact = Contact(first_name="A", last_name="B")
    session.add(contact)
    session.commit()

    assert contact.first_name == "A"
    assert contact.last_name == "B"


def test_contact_with_very_long_name(session):
    long_name = "A" * 255
    contact = Contact(first_name=long_name, last_name=long_name)
    session.add(contact)
    session.commit()

    assert contact.first_name == long_name


def test_phone_with_single_digit_number_raises(session):
    contact = Contact(first_name="A", last_name="B")
    with pytest.raises(ValueError):
        contact.phones = [Phone(number="0")]


def test_contact_without_first_name_raises(session):
    contact = Contact(last_name="Doe")
    session.add(contact)
    with pytest.raises(IntegrityError):
        session.commit()


def test_contact_without_last_name_raises(session):
    contact = Contact(first_name="John")
    session.add(contact)
    with pytest.raises(IntegrityError):
        session.commit()


def test_phone_without_number_raises(session):
    contact = Contact(first_name="John", last_name="Doe")
    contact.phones = [Phone()]
    session.add(contact)
    with pytest.raises(IntegrityError):
        session.commit()


def test_email_without_address_raises(session):
    contact = Contact(first_name="John", last_name="Doe")
    contact.emails = [Email()]
    session.add(contact)
    with pytest.raises(IntegrityError):
        session.commit()
