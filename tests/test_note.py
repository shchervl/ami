import pytest
from sqlalchemy.exc import IntegrityError

from models import Note, Tag


def test_create_note_with_all_fields(session):
    note = Note(title="My Note", body="Some content here")
    session.add(note)
    session.commit()

    assert note.id is not None
    assert note.title == "My Note"
    assert note.body == "Some content here"


def test_note_created_at_is_set_automatically(session):
    note = Note(title="Note", body="Body")
    session.add(note)
    session.commit()

    assert note.created_at is not None


def test_note_updated_at_is_set_automatically(session):
    note = Note(title="Note", body="Body")
    session.add(note)
    session.commit()

    assert note.updated_at is not None


def test_note_with_single_tag(session):
    tag = Tag(name="work")
    note = Note(title="Note", body="Body", tags=[tag])
    session.add(note)
    session.commit()

    assert len(note.tags) == 1
    assert note.tags[0].name == "work"


def test_note_with_multiple_tags(session):
    note = Note(
        title="Note",
        body="Body",
        tags=[Tag(name="work"), Tag(name="urgent"), Tag(name="personal")],
    )
    session.add(note)
    session.commit()

    assert len(note.tags) == 3


def test_same_tag_assigned_to_multiple_notes(session):
    tag = Tag(name="shared")
    note1 = Note(title="Note 1", body="Body 1", tags=[tag])
    note2 = Note(title="Note 2", body="Body 2", tags=[tag])
    session.add_all([note1, note2])
    session.commit()

    assert tag in note1.tags
    assert tag in note2.tags


def test_note_without_tags(session):
    note = Note(title="Note", body="Body")
    session.add(note)
    session.commit()

    assert note.tags == []


def test_note_with_single_char_title_and_body(session):
    note = Note(title="A", body="B")
    session.add(note)
    session.commit()

    assert note.title == "A"
    assert note.body == "B"


def test_note_with_very_long_body(session):
    long_body = "x" * 10_000
    note = Note(title="Long Note", body=long_body)
    session.add(note)
    session.commit()

    assert len(note.body) == 10_000


def test_tag_with_single_char_name(session):
    tag = Tag(name="x")
    session.add(tag)
    session.commit()

    assert tag.name == "x"


def test_note_without_title_raises(session):
    note = Note(body="Some body")
    session.add(note)
    with pytest.raises(IntegrityError):
        session.commit()


def test_note_without_body_raises(session):
    note = Note(title="Some title")
    session.add(note)
    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_tag_name_raises(session):
    session.add(Tag(name="duplicate"))
    session.commit()

    session.add(Tag(name="duplicate"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_tag_name_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        Tag(name="")


def test_tag_name_whitespace_raises():
    with pytest.raises(ValueError, match="empty"):
        Tag(name="   ")
