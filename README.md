# GoIT Python Core Homework 08

Python homework project covering closures, decorators, and functional programming patterns.

## Setup Instructions

### 1. Create Virtual Environment

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

**On macOS/Linux:**

```bash
source venv/bin/activate
```

**On Windows:**

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Deactivate Virtual Environment (when done)

```bash
deactivate
```

## Development

To add new dependencies:

```bash
pip install package-name
pip freeze > requirements.txt
```

# Start app from local virtual env
````
python app.py
````

## Architecture

The app follows an **MVC** pattern with a dedicated database layer.

```
app.py
├── database/session.py   (SQLite setup via SQLAlchemy)
├── controllers/
│   ├── ContactController
│   └── NoteController
├── models/
│   ├── Contact (+ Phone, Email)
│   ├── Note
│   └── Tag  (many-to-many with Note via note_tags)
└── views/
    ├── MainWindow          (tkinter Notebook)
    ├── ContactListView
    ├── ContactFormView
    └── NoteListView
```

### Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Entry point | `app.py` | Initialises DB, creates controllers, launches `MainWindow` |
| Database | `database/session.py` | `init_db()` creates `~/.ami/ami.sqlite` and returns a singleton SQLAlchemy `Session` |
| Models | `models/` | SQLAlchemy ORM models: `Contact` (has many `Phone`/`Email`), `Note`, `Tag` (linked to notes via `note_tags` join table) |
| Controllers | `controllers/` | Business logic and DB queries; always return plain `dict` objects to keep views decoupled from ORM |
| Views | `views/` | tkinter widgets; `MainWindow` is a tabbed notebook holding a contacts tab and a notes tab |