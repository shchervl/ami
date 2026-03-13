from datetime import date, timedelta

import pytest

from ami.controllers.contact_controller import ContactController


def test_create_contact(session):
    ctrl = ContactController(session)
    ctrl.create("Alice", "Smith")
    all_contacts = ctrl.get_all()
    assert len(all_contacts) == 1
    assert all_contacts[0]["first_name"] == "Alice"
    assert all_contacts[0]["last_name"] == "Smith"


def test_create_with_phones_emails(session):
    ctrl = ContactController(session)
    phones = [{"number": "1111111111", "type": "mobile"}, {"number": "2222222222", "type": "work"}]
    emails = [{"address": "alice@example.com", "type": "personal"}]
    result = ctrl.create("Alice", "Smith", phones=phones, emails=emails)
    assert len(result["phones"]) == 2
    assert len(result["emails"]) == 1
    phone_numbers = {p["number"] for p in result["phones"]}
    assert "1111111111" in phone_numbers
    assert "2222222222" in phone_numbers
    assert result["emails"][0]["address"] == "alice@example.com"


def test_get_by_id(session):
    ctrl = ContactController(session)
    created = ctrl.create("Bob", "Jones", address="123 Main St")
    fetched = ctrl.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["first_name"] == "Bob"
    assert fetched["last_name"] == "Jones"
    assert fetched["address"] == "123 Main St"


def test_get_by_id_not_found(session):
    ctrl = ContactController(session)
    result = ctrl.get_by_id(999)
    assert result is None


def test_update_contact(session):
    ctrl = ContactController(session)
    created = ctrl.create("Carol", "White", phones=[{"number": "0000000000"}])
    updated = ctrl.update(
        created["id"],
        "Carol",
        "Black",
        phones=[{"number": "1111111111"}, {"number": "2222222222"}],
    )
    assert updated["last_name"] == "Black"
    assert len(updated["phones"]) == 2
    phone_numbers = {p["number"] for p in updated["phones"]}
    assert "0000000000" not in phone_numbers
    assert "1111111111" in phone_numbers
    assert "2222222222" in phone_numbers


def test_delete_contact(session):
    ctrl = ContactController(session)
    created = ctrl.create("Dave", "Brown")
    ctrl.delete(created["id"])
    assert ctrl.get_all() == []


def test_search_by_name(session):
    ctrl = ContactController(session)
    ctrl.create("Alice", "Smith")
    ctrl.create("Bob", "Jones")
    results = ctrl.search("Alice")
    assert len(results) == 1
    assert results[0]["first_name"] == "Alice"


def test_search_by_phone(session):
    ctrl = ContactController(session)
    ctrl.create("Eve", "Taylor", phones=[{"number": "5551234567"}])
    results = ctrl.search("555")
    assert len(results) == 1
    assert results[0]["first_name"] == "Eve"


def test_validate_empty_name(session):
    ctrl = ContactController(session)
    with pytest.raises(ValueError):
        ctrl.create("", "Smith")


def test_upcoming_birthdays(session):
    ctrl = ContactController(session)
    today = date.today()
    birthday_soon = today + timedelta(days=3)
    # Store birthday with an arbitrary year; the controller uses month/day only
    birthday_stored = date(1990, birthday_soon.month, birthday_soon.day)
    ctrl.create("Frank", "Miller", birthday=birthday_stored)
    results = ctrl.get_upcoming_birthdays(7)
    assert len(results) == 1
    assert results[0]["first_name"] == "Frank"
    assert results[0]["days_until"] == 3


def test_upcoming_birthdays_year_wrap(session):
    ctrl = ContactController(session)
    # Simulate the year-wrap case: a birthday that is 3 days from today but
    # falls in the next calendar year relative to an end-of-year reference.
    # We use Dec 29 as a synthetic "today" and Jan 1 as the birthday (3 days later).
    # Rather than mocking date.today(), we verify the controller logic directly
    # by choosing a real date 3 days away that we know is in the next year when
    # today is near year-end.
    today = date.today()
    # Find a birthday date that is 3 days ahead, wrapping the year if necessary
    upcoming = today + timedelta(days=3)

    # Build a birthday stored with an old year so the stored year is clearly different
    stored_birthday = date(1985, upcoming.month, upcoming.day)
    ctrl.create("Grace", "Hall", birthday=stored_birthday)

    results = ctrl.get_upcoming_birthdays(7)
    assert len(results) == 1
    assert results[0]["days_until"] == 3

    # Now test the explicit year-wrap branch: if the birthday's this-year date is
    # already past, the controller should look to next year. We verify this by
    # creating a contact whose birthday was yesterday (this_year_bday < today),
    # expecting it NOT to appear in upcoming 7-day window but to be scheduled
    # for next year.
    yesterday = today - timedelta(days=1)
    stored_past = date(1990, yesterday.month, yesterday.day)
    ctrl.create("Past", "Birthday", birthday=stored_past)

    results_all = ctrl.get_upcoming_birthdays(7)
    names_in_results = {r["first_name"] for r in results_all}
    # "Past" birthday is 364 or 365 days away — should NOT appear in 7-day window
    assert "Past" not in names_in_results
    # "Grace" is still 3 days away
    assert "Grace" in names_in_results


def test_get_all_sort_by_last_name_asc(session):
    ctrl = ContactController(session)
    ctrl.create("Alice", "Zebra")
    ctrl.create("Bob", "Apple")
    results = ctrl.get_all(sort_by="last_name", sort_asc=True)
    assert results[0]["last_name"] == "Apple"
    assert results[1]["last_name"] == "Zebra"


def test_get_all_sort_by_last_name_desc(session):
    ctrl = ContactController(session)
    ctrl.create("Alice", "Zebra")
    ctrl.create("Bob", "Apple")
    results = ctrl.get_all(sort_by="last_name", sort_asc=False)
    assert results[0]["last_name"] == "Zebra"


def test_get_all_sort_by_phone(session):
    ctrl = ContactController(session)
    ctrl.create("A", "A", phones=[{"number": "9000000000"}])
    ctrl.create("B", "B", phones=[{"number": "1000000000"}])
    results = ctrl.get_all(sort_by="phone", sort_asc=True)
    assert results[0]["phones"][0]["number"] == "1000000000"


def test_search_sort_by_first_name(session):
    ctrl = ContactController(session)
    ctrl.create("Zara", "Smith")
    ctrl.create("Anna", "Smith")
    results = ctrl.search("Smith", sort_by="first_name", sort_asc=True)
    assert results[0]["first_name"] == "Anna"


def test_get_upcoming_birthdays_sort_by_days_until(session):
    from datetime import date, timedelta
    ctrl = ContactController(session)
    today = date.today()
    ctrl.create("Far", "Out", birthday=date(1990, (today + timedelta(days=5)).month, (today + timedelta(days=5)).day))
    ctrl.create("Near", "By", birthday=date(1990, (today + timedelta(days=1)).month, (today + timedelta(days=1)).day))
    results = ctrl.get_upcoming_birthdays(days=7, sort_by="days_until", sort_asc=True)
    assert results[0]["first_name"] == "Near"
