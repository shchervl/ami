from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload

from ami.models.note import Note
from ami.models.tag import Tag, note_tags

_NOTE_DB_SORT = {
    "title": Note.title,
    "updated": Note.updated_at,
}

_NOTE_PY_KEYS = {
    "tags": lambda n: sorted(t.lower() for t in n.get("tags", []))[0]
    if n.get("tags") else "",
}


class NoteController:
    def __init__(self, session: Session):
        self.session = session

    def _base_query(self):
        return self.session.query(Note).options(selectinload(Note.tags))

    def get_all(self, sort_by: str = "updated", sort_asc: bool = False) -> list[dict]:
        q = self._base_query()
        if sort_by in _NOTE_DB_SORT:
            col = _NOTE_DB_SORT[sort_by]
            q = q.order_by(col.asc() if sort_asc else col.desc())
        else:
            q = q.order_by(Note.updated_at.desc())
        result = [self._to_dict(n) for n in q.all()]
        if sort_by in _NOTE_PY_KEYS:
            result = sorted(result, key=_NOTE_PY_KEYS[sort_by], reverse=not sort_asc)
        return result

    def search(self, query: str, sort_by: str = "updated", sort_asc: bool = False) -> list[dict]:
        pattern = f"%{query}%"
        q = (
            self._base_query()
            .filter(or_(Note.title.ilike(pattern), Note.body.ilike(pattern)))
        )
        if sort_by in _NOTE_DB_SORT:
            col = _NOTE_DB_SORT[sort_by]
            q = q.order_by(col.asc() if sort_asc else col.desc())
        else:
            q = q.order_by(Note.updated_at.desc())
        result = [self._to_dict(n) for n in q.all()]
        if sort_by in _NOTE_PY_KEYS:
            result = sorted(result, key=_NOTE_PY_KEYS[sort_by], reverse=not sort_asc)
        return result

    def search_by_tags(
        self, tag_names: list[str], sort_by: str = "updated", sort_asc: bool = False
    ) -> list[dict]:
        if not tag_names:
            return []
        subq = (
            select(note_tags.c.note_id)
            .join(Tag, Tag.id == note_tags.c.tag_id)
            .where(Tag.name.in_(tag_names))
            .subquery()
        )
        q = self._base_query().filter(Note.id.in_(select(subq.c.note_id)))
        if sort_by in _NOTE_DB_SORT:
            col = _NOTE_DB_SORT[sort_by]
            q = q.order_by(col.asc() if sort_asc else col.desc())
        else:
            q = q.order_by(Note.updated_at.desc())
        result = [self._to_dict(n) for n in q.all()]
        if sort_by in _NOTE_PY_KEYS:
            result = sorted(result, key=_NOTE_PY_KEYS[sort_by], reverse=not sort_asc)
        return result

    def get_all_tags(self) -> list[str]:
        tags = self.session.query(Tag).order_by(Tag.name.asc()).all()
        return [tag.name for tag in tags]

    def get_by_id(self, note_id: int) -> dict | None:
        note = self._base_query().filter(Note.id == note_id).first()
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
