from datetime import date, timedelta

import pytest

from ami.controllers.contact_controller import ContactController


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ctrl(session):
    return ContactController(session)


def ids(results):
    return {r["id"] for r in results}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_contact(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Smith")
    all_contacts = ctrl.get_all()
    assert len(all_contacts) == 1
    assert all_contacts[0]["first_name"] == "Alice"
    assert all_contacts[0]["last_name"] == "Smith"


def test_create_with_phones_emails(session):
    ctrl = make_ctrl(session)
    phones = [{"number": "1111111111", "type": "mobile"}, {"number": "2222222222", "type": "work"}]
    emails = [{"address": "alice@example.com", "type": "personal"}]
    result = ctrl.create("Alice", "Smith", phones=phones, emails=emails)
    assert len(result["phones"]) == 2
    assert len(result["emails"]) == 1
    assert {p["number"] for p in result["phones"]} == {"1111111111", "2222222222"}
    assert result["emails"][0]["address"] == "alice@example.com"


def test_create_without_phones_emails_has_empty_lists(session):
    ctrl = make_ctrl(session)
    result = ctrl.create("Alice", "Smith")
    assert result["phones"] == []
    assert result["emails"] == []


def test_create_with_phones_only(session):
    ctrl = make_ctrl(session)
    result = ctrl.create("Alice", "Smith", phones=[{"number": "1234567890"}])
    assert len(result["phones"]) == 1
    assert result["emails"] == []


def test_create_with_emails_only(session):
    ctrl = make_ctrl(session)
    result = ctrl.create("Alice", "Smith", emails=[{"address": "a@b.com"}])
    assert result["phones"] == []
    assert len(result["emails"]) == 1


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def test_get_by_id(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Bob", "Jones", address="123 Main St")
    fetched = ctrl.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["first_name"] == "Bob"
    assert fetched["address"] == "123 Main St"


def test_get_by_id_not_found(session):
    ctrl = make_ctrl(session)
    assert ctrl.get_by_id(999) is None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def test_update_contact(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Carol", "White", phones=[{"number": "0000000000"}])
    updated = ctrl.update(
        created["id"], "Carol", "Black",
        phones=[{"number": "1111111111"}, {"number": "2222222222"}],
    )
    assert updated["last_name"] == "Black"
    assert len(updated["phones"]) == 2
    assert {p["number"] for p in updated["phones"]} == {"1111111111", "2222222222"}


def test_update_replaces_phones_and_emails(session):
    ctrl = make_ctrl(session)
    created = ctrl.create(
        "Dave", "Lee",
        phones=[{"number": "1111111111"}],
        emails=[{"address": "old@old.com"}],
    )
    updated = ctrl.update(
        created["id"], "Dave", "Lee",
        phones=[{"number": "9999999999"}],
        emails=[{"address": "new@new.com"}],
    )
    assert updated["phones"][0]["number"] == "9999999999"
    assert updated["emails"][0]["address"] == "new@new.com"


def test_update_clears_phones_emails_when_none(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Eve", "Fox",
                          phones=[{"number": "1234567890"}],
                          emails=[{"address": "e@e.com"}])
    updated = ctrl.update(created["id"], "Eve", "Fox")
    assert updated["phones"] == []
    assert updated["emails"] == []


def test_update_not_found_raises(session):
    ctrl = make_ctrl(session)
    with pytest.raises(ValueError, match="not found"):
        ctrl.update(999, "X", "Y")


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_contact(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Dave", "Brown")
    ctrl.delete(created["id"])
    assert ctrl.get_all() == []


def test_delete_not_found_raises(session):
    ctrl = make_ctrl(session)
    with pytest.raises(ValueError, match="not found"):
        ctrl.delete(999)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_validate_empty_first_name(session):
    ctrl = make_ctrl(session)
    with pytest.raises(ValueError):
        ctrl.create("", "Smith")


def test_validate_empty_last_name(session):
    ctrl = make_ctrl(session)
    with pytest.raises(ValueError):
        ctrl.create("Alice", "")


# ---------------------------------------------------------------------------
# search (text) — filtering correctness
# ---------------------------------------------------------------------------

def test_search_by_name(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Smith")
    ctrl.create("Bob", "Jones")
    results = ctrl.search("Alice")
    assert len(results) == 1
    assert results[0]["first_name"] == "Alice"


def test_search_by_last_name(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Smith")
    ctrl.create("Bob", "Jones")
    results = ctrl.search("Jones")
    assert len(results) == 1
    assert results[0]["last_name"] == "Jones"


def test_search_by_phone(session):
    ctrl = make_ctrl(session)
    ctrl.create("Eve", "Taylor", phones=[{"number": "5551234567"}])
    ctrl.create("No", "Phone")
    results = ctrl.search("555")
    assert len(results) == 1
    assert results[0]["first_name"] == "Eve"


def test_search_by_email(session):
    ctrl = make_ctrl(session)
    ctrl.create("Frank", "Mill", emails=[{"address": "frank@company.com"}])
    ctrl.create("Other", "Person")
    results = ctrl.search("company")
    assert len(results) == 1
    assert results[0]["first_name"] == "Frank"


def test_search_case_insensitive(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Smith")
    assert len(ctrl.search("alice")) == 1
    assert len(ctrl.search("SMITH")) == 1


def test_search_no_match_returns_empty(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Smith")
    assert ctrl.search("zzznomatch") == []


def test_search_does_not_return_duplicates(session):
    # Contact matches on both first name and phone — should appear once
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Smith", phones=[{"number": "1234567890"}],
                emails=[{"address": "alice@alice.com"}])
    results = ctrl.search("alice")
    assert len(results) == 1


def test_search_sort_does_not_change_result_set(session):
    ctrl = make_ctrl(session)
    ctrl.create("Zara", "Smith")
    ctrl.create("Anna", "Smith")
    ctrl.create("Bob", "Jones")
    asc = ids(ctrl.search("Smith", sort_by="first_name", sort_asc=True))
    desc = ids(ctrl.search("Smith", sort_by="first_name", sort_asc=False))
    assert asc == desc
    assert len(asc) == 2


def test_search_sort_by_first_name(session):
    ctrl = make_ctrl(session)
    ctrl.create("Zara", "Smith")
    ctrl.create("Anna", "Smith")
    results = ctrl.search("Smith", sort_by="first_name", sort_asc=True)
    assert results[0]["first_name"] == "Anna"


# ---------------------------------------------------------------------------
# get_all — sorting
# ---------------------------------------------------------------------------

def test_get_all_sort_by_last_name_asc(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Zebra")
    ctrl.create("Bob", "Apple")
    results = ctrl.get_all(sort_by="last_name", sort_asc=True)
    assert results[0]["last_name"] == "Apple"
    assert results[1]["last_name"] == "Zebra"


def test_get_all_sort_by_last_name_desc(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Zebra")
    ctrl.create("Bob", "Apple")
    results = ctrl.get_all(sort_by="last_name", sort_asc=False)
    assert results[0]["last_name"] == "Zebra"


def test_get_all_sort_by_phone(session):
    ctrl = make_ctrl(session)
    ctrl.create("A", "A", phones=[{"number": "9000000000"}])
    ctrl.create("B", "B", phones=[{"number": "1000000000"}])
    results = ctrl.get_all(sort_by="phone", sort_asc=True)
    assert results[0]["phones"][0]["number"] == "1000000000"


def test_get_all_sort_by_email(session):
    ctrl = make_ctrl(session)
    ctrl.create("A", "A", emails=[{"address": "zzz@example.com"}])
    ctrl.create("B", "B", emails=[{"address": "aaa@example.com"}])
    results = ctrl.get_all(sort_by="email", sort_asc=True)
    assert results[0]["emails"][0]["address"] == "aaa@example.com"


def test_get_all_sort_does_not_change_result_set(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alice", "Zebra")
    ctrl.create("Bob", "Apple")
    ctrl.create("Carol", "Mango")
    asc = ids(ctrl.get_all(sort_by="last_name", sort_asc=True))
    desc = ids(ctrl.get_all(sort_by="last_name", sort_asc=False))
    assert asc == desc


# ---------------------------------------------------------------------------
# Upcoming birthdays
# ---------------------------------------------------------------------------

def test_upcoming_birthdays(session):
    ctrl = make_ctrl(session)
    today = date.today()
    soon = today + timedelta(days=3)
    ctrl.create("Frank", "Miller", birthday=date(1990, soon.month, soon.day))
    results = ctrl.get_upcoming_birthdays(7)
    assert len(results) == 1
    assert results[0]["first_name"] == "Frank"
    assert results[0]["days_until"] == 3


def test_upcoming_birthdays_excludes_past(session):
    ctrl = make_ctrl(session)
    today = date.today()
    yesterday = today - timedelta(days=1)
    ctrl.create("Past", "Birthday", birthday=date(1990, yesterday.month, yesterday.day))
    results = ctrl.get_upcoming_birthdays(7)
    assert results == []


def test_upcoming_birthdays_excludes_beyond_window(session):
    ctrl = make_ctrl(session)
    today = date.today()
    far = today + timedelta(days=30)
    ctrl.create("Far", "Away", birthday=date(1990, far.month, far.day))
    results = ctrl.get_upcoming_birthdays(7)
    assert results == []


def test_upcoming_birthdays_includes_today(session):
    ctrl = make_ctrl(session)
    today = date.today()
    ctrl.create("Born", "Today", birthday=date(1990, today.month, today.day))
    results = ctrl.get_upcoming_birthdays(0)
    assert len(results) == 1
    assert results[0]["days_until"] == 0


def test_upcoming_birthdays_sort_by_days_until(session):
    ctrl = make_ctrl(session)
    today = date.today()
    far = today + timedelta(days=5)
    near = today + timedelta(days=1)
    ctrl.create("Far", "Out", birthday=date(1990, far.month, far.day))
    ctrl.create("Near", "By", birthday=date(1990, near.month, near.day))
    results = ctrl.get_upcoming_birthdays(days=7, sort_by="days_until", sort_asc=True)
    assert results[0]["first_name"] == "Near"


def test_upcoming_birthdays_year_wrap(session):
    ctrl = make_ctrl(session)
    today = date.today()
    upcoming = today + timedelta(days=3)
    ctrl.create("Grace", "Hall", birthday=date(1985, upcoming.month, upcoming.day))
    results = ctrl.get_upcoming_birthdays(7)
    assert len(results) == 1
    assert results[0]["days_until"] == 3
