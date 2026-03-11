from datetime import date
from sqlalchemy import or_
from sqlalchemy.orm import Session
from models.contact import Contact, Phone, Email


class ContactController:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[dict]:
        contacts = (
            self.session.query(Contact)
            .order_by(Contact.last_name, Contact.first_name)
            .all()
        )
        return [self._to_dict(c) for c in contacts]

    def search(self, query: str) -> list[dict]:
        pattern = f"%{query}%"
        contacts = (
            self.session.query(Contact)
            .outerjoin(Phone)
            .outerjoin(Email)
            .filter(
                or_(
                    Contact.first_name.ilike(pattern),
                    Contact.last_name.ilike(pattern),
                    Phone.number.ilike(pattern),
                    Email.address.ilike(pattern),
                )
            )
            .distinct()
            .all()
        )
        return [self._to_dict(c) for c in contacts]

    def get_upcoming_birthdays(self, days: int = 7) -> list[dict]:
        today = date.today()
        results = []
        contacts = (
            self.session.query(Contact)
            .filter(Contact.birthday.isnot(None))
            .all()
        )
        for contact in contacts:
            bday = contact.birthday
            # Handle Feb 29 in non-leap years
            try:
                this_year_bday = bday.replace(year=today.year)
            except ValueError:
                this_year_bday = date(today.year, 2, 28)

            if this_year_bday < today:
                try:
                    next_year_bday = bday.replace(year=today.year + 1)
                except ValueError:
                    next_year_bday = date(today.year + 1, 2, 28)
                upcoming = next_year_bday
            else:
                upcoming = this_year_bday

            days_until = (upcoming - today).days
            if 0 <= days_until <= days:
                contact_dict = self._to_dict(contact)
                contact_dict["days_until"] = days_until
                results.append(contact_dict)

        return results

    def get_by_id(self, contact_id: int) -> dict | None:
        contact = self.session.query(Contact).filter(Contact.id == contact_id).first()
        if contact is None:
            return None
        return self._to_dict(contact)

    def create(
        self,
        first_name: str,
        last_name: str,
        address: str | None = None,
        birthday=None,
        phones: list[dict] | None = None,
        emails: list[dict] | None = None,
    ) -> dict:
        self._validate(first_name, last_name)
        if isinstance(birthday, str):
            birthday = date.fromisoformat(birthday)
        contact = Contact(
            first_name=first_name,
            last_name=last_name,
            address=address,
            birthday=birthday,
        )
        if phones:
            for p in phones:
                contact.phones.append(Phone(number=p["number"], type=p.get("type")))
        if emails:
            for e in emails:
                contact.emails.append(Email(address=e["address"], type=e.get("type")))
        self.session.add(contact)
        self.session.commit()
        return self._to_dict(contact)

    def update(
        self,
        contact_id: int,
        first_name: str,
        last_name: str,
        address: str | None = None,
        birthday=None,
        phones: list[dict] | None = None,
        emails: list[dict] | None = None,
    ) -> dict:
        self._validate(first_name, last_name)
        contact = self.session.query(Contact).filter(Contact.id == contact_id).first()
        if contact is None:
            raise ValueError(f"Contact with id {contact_id} not found")
        if isinstance(birthday, str):
            birthday = date.fromisoformat(birthday)
        contact.first_name = first_name
        contact.last_name = last_name
        contact.address = address
        contact.birthday = birthday

        contact.phones[:] = []
        contact.emails[:] = []

        if phones:
            for p in phones:
                contact.phones.append(Phone(number=p["number"], type=p.get("type")))
        if emails:
            for e in emails:
                contact.emails.append(Email(address=e["address"], type=e.get("type")))

        self.session.commit()
        return self._to_dict(contact)

    def delete(self, contact_id: int) -> None:
        contact = self.session.query(Contact).filter(Contact.id == contact_id).first()
        if contact is None:
            raise ValueError(f"Contact with id {contact_id} not found")
        self.session.delete(contact)
        self.session.commit()

    def _to_dict(self, contact: Contact) -> dict:
        return {
            "id": contact.id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "address": contact.address,
            "birthday": contact.birthday.isoformat() if contact.birthday else None,
            "phones": [
                {"id": p.id, "number": p.number, "type": p.type}
                for p in contact.phones
            ],
            "emails": [
                {"id": e.id, "address": e.address, "type": e.type}
                for e in contact.emails
            ],
        }

    def _validate(self, first_name: str, last_name: str) -> None:
        if not first_name or not first_name.strip():
            raise ValueError("first_name cannot be empty or whitespace")
        if not last_name or not last_name.strip():
            raise ValueError("last_name cannot be empty or whitespace")
