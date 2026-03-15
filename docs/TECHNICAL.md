# Ami — Technical Documentation

## Overview

Ami is a desktop Personal Assistant application built with Python and Tkinter. It provides contact management and
note-taking functionality with persistent SQLite storage. The app is distributed as an installable Python package (
`pip install` / `pipx install`) and launched via the `ami` shell command.

---

## Architecture

The project follows a strict **MVC (Model-View-Controller)** pattern with a dedicated database layer:

```
ami/
├── app.py                        # Entry point: wires DB, controllers, and MainWindow
├── database/
│   └── session.py                # SQLite engine setup, singleton session management
├── models/
│   ├── base.py                   # SQLAlchemy declarative Base
│   ├── contact.py                # Contact, Phone, Email ORM models + validators
│   ├── note.py                   # Note ORM model + validators
│   └── tag.py                    # Tag model + note_tags join table
├── controllers/
│   ├── contact_controller.py     # Contact business logic, search, birthday queries
│   └── note_controller.py        # Note business logic, tag management, search
└── views/
    ├── main_window.py            # Root Tk window, ttk.Notebook tab container
    ├── base_list_view.py         # Shared Treeview base class
    ├── contacts/
    │   ├── contact_list_view.py  # Contacts tab: search, list, CRUD actions
    │   ├── contact_form_view.py  # Modal form for create/edit contact
    │   └── birthday_list_view.py # Upcoming Birthdays tab
    └── notes/
        ├── note_list_view.py     # Notes tab: search, tag filter, list, CRUD
        └── note_form_view.py     # Modal form for create/edit note
```

### Layer Responsibilities

| Layer       | Responsibility                                                                                                                       |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------|
| Models      | ORM schema definitions and field-level validation via `@validates`                                                                   |
| Controllers | Business logic, database queries; always return plain `dict` objects — never ORM instances — to keep views decoupled from SQLAlchemy |
| Views       | Tkinter widgets only; call controllers and display results; no direct DB access                                                      |
| Database    | Creates `~/.ami/ami.sqlite`, manages SQLAlchemy engine and singleton `Session`                                                       |

---

## Tech Stack

| Component    | Technology                                |
|--------------|-------------------------------------------|
| Language     | Python 3.10+                              |
| GUI          | Tkinter + ttk (stdlib)                    |
| ORM          | SQLAlchemy 2.0                            |
| Database     | SQLite (via SQLAlchemy)                   |
| Packaging    | setuptools / pyproject.toml (PEP 517)     |
| Distribution | pipx (global install), pip (venv install) |
| Testing      | pytest                                    |
| Linting      | flake8                                    |

---

## Data Model

```
Contact (1) ──< Phone (many)
Contact (1) ──< Email (many)
Note    (many) >──< Tag (many)   [via note_tags join table]
```

- `Contact` stores `first_name`, `last_name`, `address`, `birthday` (nullable)
- `Phone` / `Email` are child records with cascade delete
- `Note` stores `title`, `body`, `created_at`, `updated_at`
- `Tag` is shared across notes (unique name, max 10 chars); association via `note_tags` join table

---

## Challenges and Applied Solutions

### 1. Package Installability — Flat Structure vs. Namespace Pollution

**Challenge:** The project originally had a flat structure with `controllers/`, `models/`, `views/`, `database/` all at
the project root. Installing with `pip install .` would register these as top-level Python packages, risking name
collisions with other installed packages (e.g. a package named `models` or `controllers`).

**Solution:** Wrapped all source files inside an `ami/` sub-package. All internal imports were updated to use the `ami.`
namespace (e.g. `from ami.models import Contact`). Intra-package imports within `models/` and `database/` use relative
imports (e.g. `from .base import Base`). A `pyproject.toml` with `[tool.setuptools.packages.find]` restricted to `ami*`
ensures only the `ami` package is installed.

---

### 2. Asset Path Resolution After Installation

**Challenge:** The app loads an icon image using a relative path. After `pip install`, source files live inside
`site-packages/` rather than the project directory, so naive relative paths break.

**Solution:** The path is computed relative to `__file__`:

```python
icon_path = Path(__file__).parent.parent / "assets" / "amigos.png"
```

After moving `views/main_window.py` into `ami/views/`, `.parent.parent` resolves to `ami/` in both development layout
and after installation into `site-packages/ami/`. The `assets/` directory is declared as package data in
`pyproject.toml`:

```toml
[tool.setuptools.package-data]
ami = ["assets/*"]
```

---

### 3. Tkinter Font Submodule Not Auto-Imported

**Challenge:** The contacts list view dynamically calculates row height based on the default font metrics using
`tk.font.nametofont(...)`. This raised `AttributeError: module 'tkinter' has no attribute 'font'` because `tkinter.font`
is a separate submodule that is not imported automatically when you `import tkinter as tk`.

**Solution:** Added an explicit import:

```python
from tkinter import ttk, messagebox, font as tk_font
```

And updated the usage to `tk_font.nametofont(...)`.

---

### 4. Missing Tk Support in Homebrew Python

**Challenge:** When installing globally via `pipx`, pipx uses the system Python from Homebrew (Python 3.14). Homebrew's
Python does not include the `_tkinter` C extension by default, causing `ModuleNotFoundError: No module named '_tkinter'`
on launch.

**Solution:** Install the matching Homebrew Tk bridge package:

```bash
brew install python-tk@3.14
```

This installs the `_tkinter` extension for the specific Python version pipx is using.

---

### 5. Search State / Tab Switch Inconsistency

**Challenge:** When a user searched contacts (filtering the list), then cleared the search field without clicking Search
again, then switched tabs and came back — the list still showed the old filtered results while the search field appeared
empty. This created a confusing mismatch between the UI state and the displayed data.

**Root cause:** Two compounding issues:

1. `refresh()` when called with no arguments always called `controller.get_all()`, ignoring the current value of
   `_search_var`
2. No `<<NotebookTabChanged>>` binding existed, so `refresh()` was never triggered on tab switch

**Solution:**

Extracted shared fetch logic into `BaseListView._fetch_data()`, which reads `_search_var` to decide between
`controller.search()` and `controller.get_all()`:

```python
def _fetch_data(self):
    query = self._search_var.get().strip()
    if query:
        return self.controller.search(query, sort_by=self._sort_col, sort_asc=self._sort_asc)
    return self.controller.get_all(sort_by=self._sort_col, sort_asc=self._sort_asc)
```

Both `ContactListView.refresh()` and `NoteListView.refresh()` call `self._fetch_data()` when no explicit data is passed.
Additionally, `MainWindow` binds `<<NotebookTabChanged>>` to call `refresh()` on the newly active tab, keeping displayed
data always consistent with the search field.

---

### 6. Validation Error Messages Lacking Context

**Challenge:** When a phone number or email failed validation, the error dialog showed a generic message (e.g. "Invalid
phone number. It must be exactly 10 digits.") with no indication of which value triggered the error — unhelpful when a
contact has multiple phones or emails.

**Solution:** Included the offending value in the exception message at the model validator level:

```python
raise ValueError(f"Invalid phone number '{value}'. It must be exactly 10 digits.")
raise ValueError(f"Invalid email '{value}'. It must be 'something@something.com'")
```

Since the `ValueError` propagates unchanged through the controller to the view's `messagebox.showerror()`, no changes
were needed in the view layer.

---

### 7. Controllers Returning ORM Objects to Views

**Challenge:** Returning SQLAlchemy ORM instances directly to views would create implicit coupling between the view
layer and the database session lifecycle — views could accidentally trigger lazy loads, or objects could become detached
after session operations.

**Solution:** All controller methods return plain Python `dict` objects via a `_to_dict()` helper. Views only ever
receive and render dicts, making them completely independent of SQLAlchemy internals.

---

### 8. Birthday Calculation Across Year Boundaries

**Challenge:** Computing "days until birthday" requires correctly handling the case where a contact's birthday has
already passed this year (so the next occurrence is next year), and the edge case of February 29 birthdays in non-leap
years.

**Solution:** In `ContactController.get_upcoming_birthdays()`, the birthday is first projected to the current year. If
that date has passed, it is projected to next year. February 29 birthdays in non-leap years are mapped to February 28:

```python
try:
    this_year_bday = bday.replace(year=today.year)
except ValueError:
    this_year_bday = date(today.year, 2, 28)  # Feb 29 in non-leap year
```

---

## Testing

Tests cover models and controllers exclusively — views are not unit-tested (Tkinter requires a display). The test suite
uses an in-memory SQLite database via a pytest fixture in `conftest.py`.

```bash
venv/bin/pytest tests/ -v   # 63 tests, all passing
venv/bin/flake8 ami/         # zero violations
```

---

## Installation

```bash
# Global install (recommended)
brew install pipx
pipx install .
ami

# Virtualenv install
pip install -e .
ami

# Run without installing
python -m ami.app
```

> **macOS note:** Homebrew Python requires `brew install python-tk@<version>` to enable Tkinter support when installing
> globally via pipx.

---

## Data Storage

All data is stored in `~/.ami/ami.sqlite`. The database is created automatically on first launch. Restarting the
application preserves all contacts and notes.
