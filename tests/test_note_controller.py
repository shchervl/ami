import pytest

from controllers.note_controller import NoteController
from models.tag import Tag


def test_create_note(session):
    ctrl = NoteController(session)
    ctrl.create("My Title", "Some body text")
    all_notes = ctrl.get_all()
    assert len(all_notes) == 1
    assert all_notes[0]["title"] == "My Title"
    assert all_notes[0]["body"] == "Some body text"


def test_create_with_tags(session):
    ctrl = NoteController(session)
    result = ctrl.create("Tagged Note", "Body here", tag_names=["python", "work"])
    assert set(result["tags"]) == {"python", "work"}


def test_get_by_id(session):
    ctrl = NoteController(session)
    created = ctrl.create("Note One", "Body one")
    fetched = ctrl.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["title"] == "Note One"
    assert fetched["body"] == "Body one"
    assert fetched["id"] == created["id"]


def test_get_by_id_not_found(session):
    ctrl = NoteController(session)
    result = ctrl.get_by_id(999)
    assert result is None


def test_update_note(session):
    ctrl = NoteController(session)
    created = ctrl.create("Old Title", "Some body")
    updated = ctrl.update(created["id"], "New Title", "Some body")
    assert updated["title"] == "New Title"


def test_update_replaces_tags(session):
    ctrl = NoteController(session)
    created = ctrl.create("Note", "Body", tag_names=["tag1"])
    updated = ctrl.update(created["id"], "Note", "Body", tag_names=["tag2"])
    assert updated["tags"] == ["tag2"]


def test_delete_note(session):
    ctrl = NoteController(session)
    created = ctrl.create("Delete Me", "Body text")
    ctrl.delete(created["id"])
    assert ctrl.get_all() == []


def test_search_by_title(session):
    ctrl = NoteController(session)
    ctrl.create("Alpha Note", "Some content")
    ctrl.create("Beta Note", "Other content")
    results = ctrl.search("Alpha")
    assert len(results) == 1
    assert results[0]["title"] == "Alpha Note"


def test_search_by_body(session):
    ctrl = NoteController(session)
    ctrl.create("Note One", "unique_keyword in body")
    ctrl.create("Note Two", "completely different")
    results = ctrl.search("unique_keyword")
    assert len(results) == 1
    assert results[0]["title"] == "Note One"


def test_search_by_tags_union(session):
    ctrl = NoteController(session)
    note_ab = ctrl.create("Note AB", "Body", tag_names=["a", "b"])
    note_a = ctrl.create("Note A", "Body", tag_names=["a"])
    note_b = ctrl.create("Note B", "Body", tag_names=["b"])
    results = ctrl.search_by_tags(["a", "b"])
    result_ids = {r["id"] for r in results}
    assert result_ids == {note_ab["id"], note_a["id"], note_b["id"]}


def test_get_all_tags(session):
    ctrl = NoteController(session)
    ctrl.create("Note 1", "Body", tag_names=["zebra", "apple"])
    ctrl.create("Note 2", "Body", tag_names=["mango", "apple"])
    tags = ctrl.get_all_tags()
    # Should be sorted and unique
    assert tags == sorted(set(tags))
    assert tags == ["apple", "mango", "zebra"]


def test_get_or_create_tag_idempotent(session):
    ctrl = NoteController(session)
    ctrl.create("Note 1", "Body", tag_names=["x"])
    ctrl.create("Note 2", "Body", tag_names=["x"])
    # Only one Tag row with name "x" should exist in the DB
    tag_count = session.query(Tag).filter(Tag.name == "x").count()
    assert tag_count == 1


def test_validate_empty_title(session):
    ctrl = NoteController(session)
    with pytest.raises(ValueError):
        ctrl.create("", "Some body")


def test_get_all_sort_by_title_asc(session):
    ctrl = NoteController(session)
    ctrl.create("Zebra Note", "body")
    ctrl.create("Apple Note", "body")
    results = ctrl.get_all(sort_by="title", sort_asc=True)
    assert results[0]["title"] == "Apple Note"
    assert results[1]["title"] == "Zebra Note"


def test_get_all_sort_by_title_desc(session):
    ctrl = NoteController(session)
    ctrl.create("Zebra Note", "body")
    ctrl.create("Apple Note", "body")
    results = ctrl.get_all(sort_by="title", sort_asc=False)
    assert results[0]["title"] == "Zebra Note"


def test_get_all_sort_by_tags(session):
    ctrl = NoteController(session)
    ctrl.create("Note Z", "body", tag_names=["zebra"])
    ctrl.create("Note A", "body", tag_names=["apple"])
    results = ctrl.get_all(sort_by="tags", sort_asc=True)
    assert results[0]["title"] == "Note A"


def test_search_sort_by_title(session):
    ctrl = NoteController(session)
    ctrl.create("Zorro body search", "body")
    ctrl.create("Alpha body search", "body")
    results = ctrl.search("body search", sort_by="title", sort_asc=True)
    assert results[0]["title"] == "Alpha body search"


def test_search_by_tags_sort_by_title(session):
    ctrl = NoteController(session)
    ctrl.create("Zeta", "body", tag_names=["work"])
    ctrl.create("Alpha", "body", tag_names=["work"])
    results = ctrl.search_by_tags(["work"], sort_by="title", sort_asc=True)
    assert results[0]["title"] == "Alpha"
