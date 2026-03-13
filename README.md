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

**Option A — install globally with pipx (recommended):**

```bash
brew install pipx   # if not already installed
pipx install .
ami
```

`pipx` manages an isolated environment automatically — no need to activate a venv.

**Option B — install into active virtualenv:**

```bash
pip install -e .
ami
```

**Option C — run directly without installing:**

```bash
python -m ami.app
```

## Contributing (Git Workflow)

### 1. Make sure you have the latest `main`

```bash
git checkout main
git pull origin main
```

### 2. Create a new branch

Name it after what you're working on:

```bash
git checkout -b feat/your-feature-name
```

### 3. Make your changes, then stage and commit

```bash
git add path/to/changed/file.py
git commit -m "Short description of what you did"
```

### 4. Push your branch to GitHub

```bash
git push origin feat/your-feature-name
```

### 5. Open a Pull Request

Go to the repo on GitHub — you'll see a prompt to open a PR for your recently pushed branch. Click it, fill in a title and description, and submit.

---

## Architecture

The app follows an **MVC** pattern with a dedicated database layer.

```
ami/
├── app.py                (entry point: main())
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

| Layer       | Location                  | Responsibility                                                                                                          |
|-------------|---------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Entry point | `ami/app.py`              | Initialises DB, creates controllers, launches `MainWindow`                                                              |
| Database    | `ami/database/session.py` | `init_db()` creates `~/.ami/ami.sqlite` and returns a singleton SQLAlchemy `Session`                                    |
| Models      | `ami/models/`             | SQLAlchemy ORM models: `Contact` (has many `Phone`/`Email`), `Note`, `Tag` (linked to notes via `note_tags` join table) |
| Controllers | `ami/controllers/`        | Business logic and DB queries; always return plain `dict` objects to keep views decoupled from ORM                      |
| Views       | `ami/views/`              | tkinter widgets; `MainWindow` is a tabbed notebook holding a contacts tab and a notes tab                               |