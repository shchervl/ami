import tkinter as tk
from tkinter import ttk, messagebox


class NoteFormView(tk.Toplevel):
    def __init__(self, parent, controller, note_id=None, on_save=None):
        super().__init__(parent)
        self.controller = controller
        self.note_id = note_id
        self.on_save = on_save
        self._current_tags = []  # list of tag name strings

        self.title("Edit Note" if note_id else "New Note")
        self.grab_set()  # modal

        self._build_ui()

        if note_id is not None:
            self._populate(controller.get_by_id(note_id))

        self.transient(parent)
        self.wait_visibility()
        self.focus_set()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}
        form = ttk.Frame(self, padding=10)
        form.pack(fill=tk.BOTH, expand=True)
        form.columnconfigure(1, weight=1)
        form.rowconfigure(1, weight=1)

        # Title
        ttk.Label(form, text="Title*").grid(row=0, column=0, sticky=tk.W, **pad)
        self._title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._title_var, width=50).grid(row=0, column=1, sticky=tk.EW, **pad)

        # Body
        ttk.Label(form, text="Body*").grid(row=1, column=0, sticky=tk.NW, **pad)
        body_frame = ttk.Frame(form)
        body_frame.grid(row=1, column=1, sticky=tk.NSEW, **pad)
        body_frame.rowconfigure(0, weight=1)
        body_frame.columnconfigure(0, weight=1)
        self._body_text = tk.Text(body_frame, width=50, height=12, wrap=tk.WORD)
        body_vsb = ttk.Scrollbar(body_frame, orient=tk.VERTICAL, command=self._body_text.yview)
        self._body_text.configure(yscrollcommand=body_vsb.set)
        self._body_text.grid(row=0, column=0, sticky=tk.NSEW)
        body_vsb.grid(row=0, column=1, sticky=tk.NS)

        # Tags section
        tags_frame = ttk.LabelFrame(form, text="Tags", padding=5)
        tags_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, **pad)

        # Combobox + Add button
        input_row = ttk.Frame(tags_frame)
        input_row.pack(fill=tk.X)
        self._tag_combo = ttk.Combobox(input_row, width=20, state="normal")
        self._tag_combo["values"] = self.controller.get_all_tags()
        self._tag_combo.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(input_row, text="Add Tag", command=self._add_tag).pack(side=tk.LEFT)

        # Badge row for current tags
        self._badges_frame = ttk.Frame(tags_frame)
        self._badges_frame.pack(fill=tk.X, pady=(4, 0))

        # Buttons
        btns = ttk.Frame(form)
        btns.grid(row=3, column=0, columnspan=2, **pad)
        ttk.Button(btns, text="Save", command=self._on_save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

    def _add_tag(self):
        tag = self._tag_combo.get().strip()
        if tag and tag not in self._current_tags:
            self._current_tags.append(tag)
            self._refresh_badges()
        self._tag_combo.set("")

    def _remove_tag(self, tag):
        if tag in self._current_tags:
            self._current_tags.remove(tag)
            self._refresh_badges()

    def _refresh_badges(self):
        for w in self._badges_frame.winfo_children():
            w.destroy()
        for tag in self._current_tags:
            badge = ttk.Frame(self._badges_frame)
            badge.pack(side=tk.LEFT, padx=2)
            ttk.Label(badge, text=tag).pack(side=tk.LEFT)
            ttk.Button(badge, text="✕", width=2,
                       command=lambda t=tag: self._remove_tag(t)).pack(side=tk.LEFT)

    def _populate(self, note: dict):
        if not note:
            return
        self._title_var.set(note.get("title", ""))
        self._body_text.insert("1.0", note.get("body", ""))
        self._current_tags = list(note.get("tags", []))
        self._refresh_badges()

    def _on_save(self):
        title = self._title_var.get().strip()
        body = self._body_text.get("1.0", tk.END).strip()
        try:
            if self.note_id is None:
                self.controller.create(title, body, self._current_tags or None)
            else:
                self.controller.update(self.note_id, title, body, self._current_tags or None)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self)
            return
        if self.on_save:
            self.on_save()
        self.destroy()
