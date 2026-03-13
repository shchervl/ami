from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from models.note import Note
from models.tag import Tag, note_tags


class NoteController:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self, sort_by_tag: str | None = None) -> list[dict]:
        if sort_by_tag is None:
            notes = self.session.query(Note).order_by(Note.updated_at.desc()).all()
            return [self._to_dict(note) for note in notes]

        tag_note_ids = (
            select(note_tags.c.note_id)
            .join(Tag, Tag.id == note_tags.c.tag_id)
            .where(Tag.name == sort_by_tag)
            .subquery()
        )

        matching = (
            self.session.query(Note)
            .filter(Note.id.in_(select(tag_note_ids.c.note_id)))
            .order_by(Note.updated_at.desc())
            .all()
        )
        rest = (
            self.session.query(Note)
            .filter(Note.id.notin_(select(tag_note_ids.c.note_id)))
            .order_by(Note.updated_at.desc())
            .all()
        )
        return [self._to_dict(note) for note in matching + rest]

    def search(self, query: str) -> list[dict]:
        pattern = f"%{query}%"
        notes = (
            self.session.query(Note)
            .filter(or_(Note.title.ilike(pattern), Note.body.ilike(pattern)))
            .order_by(Note.updated_at.desc())
            .all()
        )
        return [self._to_dict(note) for note in notes]

    def search_by_tags(self, tag_names: list[str]) -> list[dict]:
        if not tag_names:
            return []
        subq = (
            select(note_tags.c.note_id)
            .join(Tag, Tag.id == note_tags.c.tag_id)
            .where(Tag.name.in_(tag_names))
            .subquery()
        )
        notes = (
            self.session.query(Note)
            .filter(Note.id.in_(select(subq.c.note_id)))
            .order_by(Note.updated_at.desc())
            .all()
        )
        return [self._to_dict(note) for note in notes]

    def get_all_tags(self) -> list[str]:
        tags = self.session.query(Tag).order_by(Tag.name.asc()).all()
        return [tag.name for tag in tags]

    def get_by_id(self, note_id: int) -> dict | None:
        note = self.session.query(Note).filter(Note.id == note_id).first()
        if note is None:
            return None
        return self._to_dict(note)

    def create(self, title: str, body: str, tag_names: list[str] | None = None) -> dict:
        note = Note(title=title, body=body)
        if tag_names:
            note.tags = [self._get_or_create_tag(name) for name in tag_names]
        self.session.add(note)
        self.session.commit()
        return self._to_dict(note)

    def update(self, note_id: int, title: str, body: str,
               tag_names: list[str] | None = None) -> dict:
        note = self.session.query(Note).filter(Note.id == note_id).first()
        if note is None:
            raise ValueError(f"Note with id {note_id} not found")
        note.title = title
        note.body = body
        note.tags = [self._get_or_create_tag(name) for name in tag_names] if tag_names else []
        self.session.commit()
        return self._to_dict(note)

    def delete(self, note_id: int) -> None:
        note = self.session.query(Note).filter(Note.id == note_id).first()
        if note is None:
            raise ValueError(f"Note with id {note_id} not found")
        self.session.delete(note)
        self.session.commit()

    def _get_or_create_tag(self, name: str) -> Tag:
        tag = self.session.query(Tag).filter(Tag.name == name).first()
        if tag is None:
            tag = Tag(name=name)
            self.session.add(tag)
            self.session.flush()
        return tag

    def _to_dict(self, note: Note) -> dict:
        return {
            "id": note.id,
            "title": note.title,
            "body": note.body,
            "created_at": note.created_at.isoformat() if note.created_at else None,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None,
            "tags": [tag.name for tag in note.tags],
        }

    def validate_tag(self, tag: str) -> None:
        Tag(name=tag)  # triggers @validates on Tag.name
