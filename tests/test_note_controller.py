import pytest

from ami.controllers.note_controller import NoteController
from ami.models.tag import Tag


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ctrl(session):
    return NoteController(session)


def ids(results):
    return {r["id"] for r in results}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_note(session):
    ctrl = make_ctrl(session)
    ctrl.create("My Title", "Some body text")
    all_notes = ctrl.get_all()
    assert len(all_notes) == 1
    assert all_notes[0]["title"] == "My Title"
    assert all_notes[0]["body"] == "Some body text"


def test_create_with_tags(session):
    ctrl = make_ctrl(session)
    result = ctrl.create("Tagged Note", "Body here", tag_names=["python", "work"])
    assert set(result["tags"]) == {"python", "work"}


def test_create_without_tags_has_empty_list(session):
    ctrl = make_ctrl(session)
    result = ctrl.create("Plain", "body")
    assert result["tags"] == []


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def test_get_by_id(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Note One", "Body one")
    fetched = ctrl.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["title"] == "Note One"
    assert fetched["body"] == "Body one"
    assert fetched["id"] == created["id"]


def test_get_by_id_not_found(session):
    ctrl = make_ctrl(session)
    assert ctrl.get_by_id(999) is None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def test_update_note(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Old Title", "Some body")
    updated = ctrl.update(created["id"], "New Title", "Some body")
    assert updated["title"] == "New Title"


def test_update_replaces_tags(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Note", "Body", tag_names=["tag1"])
    updated = ctrl.update(created["id"], "Note", "Body", tag_names=["tag2"])
    assert updated["tags"] == ["tag2"]


def test_update_clears_tags_when_none(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Note", "Body", tag_names=["tag1"])
    updated = ctrl.update(created["id"], "Note", "Body", tag_names=None)
    assert updated["tags"] == []


def test_update_not_found_raises(session):
    ctrl = make_ctrl(session)
    with pytest.raises(ValueError, match="not found"):
        ctrl.update(999, "Title", "Body")


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_note(session):
    ctrl = make_ctrl(session)
    created = ctrl.create("Delete Me", "Body text")
    ctrl.delete(created["id"])
    assert ctrl.get_all() == []


def test_delete_not_found_raises(session):
    ctrl = make_ctrl(session)
    with pytest.raises(ValueError, match="not found"):
        ctrl.delete(999)


# ---------------------------------------------------------------------------
# Tag management
# ---------------------------------------------------------------------------

def test_get_all_tags(session):
    ctrl = make_ctrl(session)
    ctrl.create("Note 1", "Body", tag_names=["zebra", "apple"])
    ctrl.create("Note 2", "Body", tag_names=["mango", "apple"])
    tags = ctrl.get_all_tags()
    assert tags == ["apple", "mango", "zebra"]


def test_get_or_create_tag_idempotent(session):
    ctrl = make_ctrl(session)
    ctrl.create("Note 1", "Body", tag_names=["x"])
    ctrl.create("Note 2", "Body", tag_names=["x"])
    assert session.query(Tag).filter(Tag.name == "x").count() == 1


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_validate_empty_title(session):
    ctrl = make_ctrl(session)
    with pytest.raises(ValueError):
        ctrl.create("", "Some body")


def test_validate_empty_body(session):
    ctrl = make_ctrl(session)
    with pytest.raises(ValueError):
        ctrl.create("Title", "")


# ---------------------------------------------------------------------------
# get_all — sorting
# ---------------------------------------------------------------------------

def test_get_all_sort_by_title_asc(session):
    ctrl = make_ctrl(session)
    ctrl.create("Zebra Note", "body")
    ctrl.create("Apple Note", "body")
    results = ctrl.get_all(sort_by="title", sort_asc=True)
    assert results[0]["title"] == "Apple Note"
    assert results[1]["title"] == "Zebra Note"


def test_get_all_sort_by_title_desc(session):
    ctrl = make_ctrl(session)
    ctrl.create("Zebra Note", "body")
    ctrl.create("Apple Note", "body")
    results = ctrl.get_all(sort_by="title", sort_asc=False)
    assert results[0]["title"] == "Zebra Note"


def test_get_all_sort_by_tags(session):
    ctrl = make_ctrl(session)
    ctrl.create("Note Z", "body", tag_names=["zebra"])
    ctrl.create("Note A", "body", tag_names=["apple"])
    results = ctrl.get_all(sort_by="tags", sort_asc=True)
    assert results[0]["title"] == "Note A"


def test_get_all_sort_does_not_change_result_set(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alpha", "body")
    ctrl.create("Beta", "body")
    ctrl.create("Gamma", "body")
    asc = ids(ctrl.get_all(sort_by="title", sort_asc=True))
    desc = ids(ctrl.get_all(sort_by="title", sort_asc=False))
    assert asc == desc


# ---------------------------------------------------------------------------
# search (text) — filtering correctness
# ---------------------------------------------------------------------------

def test_search_by_title(session):
    ctrl = make_ctrl(session)
    ctrl.create("Alpha Note", "Some content")
    ctrl.create("Beta Note", "Other content")
    results = ctrl.search("Alpha")
    assert len(results) == 1
    assert results[0]["title"] == "Alpha Note"


def test_search_by_body(session):
    ctrl = make_ctrl(session)
    ctrl.create("Note One", "unique_keyword in body")
    ctrl.create("Note Two", "completely different")
    results = ctrl.search("unique_keyword")
    assert len(results) == 1
    assert results[0]["title"] == "Note One"


def test_search_case_insensitive(session):
    ctrl = make_ctrl(session)
    ctrl.create("Hello World", "body")
    assert len(ctrl.search("hello")) == 1
    assert len(ctrl.search("WORLD")) == 1


def test_search_no_match_returns_empty(session):
    ctrl = make_ctrl(session)
    ctrl.create("Note", "body")
    assert ctrl.search("zzznomatch") == []


def test_search_sort_by_title(session):
    ctrl = make_ctrl(session)
    ctrl.create("Zorro body search", "body")
    ctrl.create("Alpha body search", "body")
    results = ctrl.search("body search", sort_by="title", sort_asc=True)
    assert results[0]["title"] == "Alpha body search"


def test_search_sort_does_not_change_result_set(session):
    ctrl = make_ctrl(session)
    ctrl.create("Match Alpha", "keyword")
    ctrl.create("Match Beta", "keyword")
    ctrl.create("No match", "other")
    asc = ids(ctrl.search("keyword", sort_by="title", sort_asc=True))
    desc = ids(ctrl.search("keyword", sort_by="title", sort_asc=False))
    assert asc == desc
    assert len(asc) == 2


# ---------------------------------------------------------------------------
# search_by_tags — filtering correctness
# ---------------------------------------------------------------------------

def test_search_by_tags_union(session):
    ctrl = make_ctrl(session)
    note_ab = ctrl.create("Note AB", "Body", tag_names=["a", "b"])
    note_a = ctrl.create("Note A", "Body", tag_names=["a"])
    note_b = ctrl.create("Note B", "Body", tag_names=["b"])
    ctrl.create("Note none", "Body")
    results = ctrl.search_by_tags(["a", "b"])
    assert ids(results) == {note_ab["id"], note_a["id"], note_b["id"]}


def test_search_by_single_tag(session):
    ctrl = make_ctrl(session)
    n1 = ctrl.create("Note 1", "body", tag_names=["work"])
    ctrl.create("Note 2", "body", tag_names=["personal"])
    results = ctrl.search_by_tags(["work"])
    assert ids(results) == {n1["id"]}


def test_search_by_tags_empty_list_returns_empty(session):
    ctrl = make_ctrl(session)
    ctrl.create("Note", "body", tag_names=["work"])
    assert ctrl.search_by_tags([]) == []


def test_search_by_tags_no_match_returns_empty(session):
    ctrl = make_ctrl(session)
    ctrl.create("Note", "body", tag_names=["work"])
    assert ctrl.search_by_tags(["nonexistent"]) == []


def test_search_by_tags_sort_by_title(session):
    ctrl = make_ctrl(session)
    ctrl.create("Zeta", "body", tag_names=["work"])
    ctrl.create("Alpha", "body", tag_names=["work"])
    results = ctrl.search_by_tags(["work"], sort_by="title", sort_asc=True)
    assert results[0]["title"] == "Alpha"


def test_search_by_tags_sort_does_not_change_result_set(session):
    ctrl = make_ctrl(session)
    n1 = ctrl.create("Aaa", "body", tag_names=["work"])
    n2 = ctrl.create("Zzz", "body", tag_names=["work"])
    ctrl.create("Other", "body", tag_names=["personal"])
    asc = ids(ctrl.search_by_tags(["work"], sort_by="title", sort_asc=True))
    desc = ids(ctrl.search_by_tags(["work"], sort_by="title", sort_asc=False))
    assert asc == desc == {n1["id"], n2["id"]}


# ---------------------------------------------------------------------------
# search_by_tags_and_text — combined filtering
# ---------------------------------------------------------------------------

def test_combined_text_and_tag_match(session):
    ctrl = make_ctrl(session)
    target = ctrl.create("Meeting notes", "discussed project", tag_names=["work"])
    ctrl.create("Meeting notes", "discussed project")  # no tag
    ctrl.create("Random note", "unrelated", tag_names=["work"])  # tag but no text match
    results = ctrl.search_by_tags_and_text(["work"], "meeting")
    assert ids(results) == {target["id"]}


def test_combined_requires_both_conditions(session):
    ctrl = make_ctrl(session)
    ctrl.create("Title A", "body", tag_names=["work"])  # tag matches, text doesn't
    ctrl.create("Keyword here", "body")  # text matches, tag doesn't
    results = ctrl.search_by_tags_and_text(["work"], "keyword")
    assert results == []


def test_combined_multiple_tags_and_text(session):
    ctrl = make_ctrl(session)
    n1 = ctrl.create("Alpha meeting", "notes", tag_names=["work", "important"])
    n2 = ctrl.create("Beta meeting", "notes", tag_names=["work"])
    ctrl.create("Alpha meeting", "notes", tag_names=["personal"])  # wrong tag
    results = ctrl.search_by_tags_and_text(["work", "important"], "meeting")
    # union of tags: notes tagged "work" OR "important" AND containing "meeting"
    assert ids(results) == {n1["id"], n2["id"]}


def test_combined_text_in_body(session):
    ctrl = make_ctrl(session)
    target = ctrl.create("Title", "secret keyword in body", tag_names=["work"])
    ctrl.create("Title", "other body", tag_names=["work"])
    results = ctrl.search_by_tags_and_text(["work"], "secret keyword")
    assert ids(results) == {target["id"]}


def test_combined_case_insensitive(session):
    ctrl = make_ctrl(session)
    target = ctrl.create("Hello World", "body", tag_names=["work"])
    results = ctrl.search_by_tags_and_text(["work"], "HELLO")
    assert ids(results) == {target["id"]}


def test_combined_empty_tags_falls_back_to_text_search(session):
    ctrl = make_ctrl(session)
    n1 = ctrl.create("Match this", "body", tag_names=["work"])
    n2 = ctrl.create("Match this too", "body")
    ctrl.create("No match", "body")
    results = ctrl.search_by_tags_and_text([], "Match this")
    assert ids(results) == {n1["id"], n2["id"]}


def test_combined_sort_does_not_change_result_set(session):
    ctrl = make_ctrl(session)
    n1 = ctrl.create("Alpha keyword", "body", tag_names=["work"])
    n2 = ctrl.create("Zeta keyword", "body", tag_names=["work"])
    ctrl.create("Alpha keyword", "body", tag_names=["personal"])
    asc = ids(ctrl.search_by_tags_and_text(["work"], "keyword", sort_by="title", sort_asc=True))
    desc = ids(ctrl.search_by_tags_and_text(["work"], "keyword", sort_by="title", sort_asc=False))
    assert asc == desc == {n1["id"], n2["id"]}


def test_combined_sort_order(session):
    ctrl = make_ctrl(session)
    ctrl.create("Zeta keyword", "body", tag_names=["work"])
    ctrl.create("Alpha keyword", "body", tag_names=["work"])
    asc = ctrl.search_by_tags_and_text(["work"], "keyword", sort_by="title", sort_asc=True)
    assert asc[0]["title"] == "Alpha keyword"
    desc = ctrl.search_by_tags_and_text(["work"], "keyword", sort_by="title", sort_asc=False)
    assert desc[0]["title"] == "Zeta keyword"
