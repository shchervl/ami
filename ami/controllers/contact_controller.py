from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from ami.models.contact import Contact, Email, Phone

_CONTACT_DB_SORT = {
    "last_name": Contact.last_name,
    "first_name": Contact.first_name,
    "birthday": Contact.birthday,
}

_CONTACT_PY_KEYS = {
    "phone": lambda c: c["phones"][0]["number"] if c["phones"] else "",
    "email": lambda c: (c["emails"][0]["address"] or "").lower() if c["emails"] else "",
    "last_name": lambda c: c["last_name"].lower(),
    "first_name": lambda c: c["first_name"].lower(),
    "birthday": lambda c: c["birthday"] or "",
    "days_until": lambda c: c.get("days_until", 0),
}


class ContactController:
    def __init__(self, session: Session):
        self.session = session

    def _base_query(self):
        return self.session.query(Contact).options(
            selectinload(Contact.phones),
            selectinload(Contact.emails),
        )

    def get_all(self, sort_by: str = "last_name", sort_asc: bool = True) -> list[dict]:
        q = self._base_query()
        if sort_by in _CONTACT_DB_SORT:
            col = _CONTACT_DB_SORT[sort_by]
            q = q.order_by(col.asc() if sort_asc else col.desc())
        else:
            q = q.order_by(Contact.last_name)
        result = [self._to_dict(c) for c in q.all()]
        if sort_by not in _CONTACT_DB_SORT:
            key = _CONTACT_PY_KEYS.get(sort_by)
            if key:
                result = sorted(result, key=key, reverse=not sort_asc)
        return result

    def search(self, query: str, sort_by: str = "last_name", sort_asc: bool = True) -> list[dict]:
        pattern = f"%{query}%"
        q = (
            self._base_query()
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
        )
        if sort_by in _CONTACT_DB_SORT:
            col = _CONTACT_DB_SORT[sort_by]
            q = q.order_by(col.asc() if sort_asc else col.desc())
        else:
            q = q.order_by(Contact.last_name)
        result = [self._to_dict(c) for c in q.all()]
        if sort_by not in _CONTACT_DB_SORT:
            key = _CONTACT_PY_KEYS.get(sort_by)
            if key:
                result = sorted(result, key=key, reverse=not sort_asc)
        return result

    def get_upcoming_birthdays(
        self, days: int = 7, sort_by: str = "days_until", sort_asc: bool = True
    ) -> list[dict]:
        today = date.today()
        results = []
        contacts = (
            self._base_query().filter(Contact.birthday.isnot(None)).all()
        )
        for contact in contacts:
            bday = contact.birthday
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

        key = _CONTACT_PY_KEYS.get(sort_by)
        if key:
            results = sorted(results, key=key, reverse=not sort_asc)
        return results

    def get_by_id(self, contact_id: int) -> dict | None:
        contact = self._base_query().filter(Contact.id == contact_id).first()
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
        contact = self.session.query(Contact).filter(Contact.id == contact_id).first()
        if contact is None:
            raise ValueError(f"Contact with id {contact_id} not found")
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
                {"id": p.id, "number": p.number, "type": p.type} for p in contact.phones
            ],
            "emails": [
                {"id": e.id, "address": e.address, "type": e.type}
                for e in contact.emails
            ],
        }
