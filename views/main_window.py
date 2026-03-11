import sys
import tkinter as tk
from tkinter import ttk

from views.contacts.contact_list_view import ContactListView
from views.notes.note_list_view import NoteListView


def platform_theme() -> str:
    if sys.platform == "darwin":
        return "aqua"
    elif sys.platform == "win32":
        return "vista"
    else:
        return "clam"


class MainWindow(tk.Tk):
    def __init__(self, contact_ctrl, note_ctrl):
        super().__init__()
        self.title("ami – Personal Assistant")
        self.geometry("900x600")

        style = ttk.Style(self)
        try:
            style.theme_use(platform_theme())
        except tk.TclError:
            pass  # fall back to default if theme unavailable

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        contacts_tab = ContactListView(notebook, contact_ctrl)
        notebook.add(contacts_tab, text="Contacts")

        notes_tab = NoteListView(notebook, note_ctrl)
        notebook.add(notes_tab, text="Notes")
