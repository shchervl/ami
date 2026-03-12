import tkinter as tk
from tkinter import ttk, messagebox


class NoteListView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._tag_vars = {}  # tag_name -> BooleanVar
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)

        self._search_var = tk.StringVar()
        ttk.Entry(top, textvariable=self._search_var, width=30).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="Search", command=self._on_search).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="New Note", command=self._on_new).pack(side=tk.LEFT)

        # Tag filter area
        tag_outer = ttk.LabelFrame(self, text="Filter by Tags")
        tag_outer.pack(fill=tk.X, padx=5, pady=(0, 5))

        self._tag_filter_frame = ttk.Frame(tag_outer)
        self._tag_filter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(tag_outer, text="Apply Filter", command=self._on_filter_tags).pack(side=tk.RIGHT, padx=5, pady=2)

        # Treeview
        cols = ("title", "tags", "updated")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("title", text="Title")
        self._tree.heading("tags", text="Tags")
        self._tree.heading("updated", text="Updated")
        self._tree.column("title", width=250)
        self._tree.column("tags", width=200)
        self._tree.column("updated", width=180)

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=(0, 5))
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=(0, 5))

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Bottom bar
        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X, padx=5, pady=(0, 5))
        self._edit_btn = ttk.Button(bottom, text="Edit", state=tk.DISABLED, command=self._on_edit)
        self._edit_btn.pack(side=tk.LEFT, padx=(0, 4))
        self._del_btn = ttk.Button(bottom, text="Delete", state=tk.DISABLED, command=self._on_delete)
        self._del_btn.pack(side=tk.LEFT)

    def refresh(self, notes=None):
        for row in self._tree.get_children():
            self._tree.delete(row)
        if notes is None:
            notes = self.controller.get_all()
        for n in notes:
            tags_str = ", ".join(n.get("tags", []))
            updated = (n.get("updated_at") or "")[:19]  # trim microseconds
            self._tree.insert("", tk.END, iid=str(n["id"]),
                              values=(n["title"], tags_str, updated))
        self._rebuild_tag_filters()
        self._edit_btn.config(state=tk.DISABLED)
        self._del_btn.config(state=tk.DISABLED)

    def _rebuild_tag_filters(self):
        previous = {tag: var.get() for tag, var in self._tag_vars.items()}
        for widget in self._tag_filter_frame.winfo_children():
            widget.destroy()
        self._tag_vars.clear()
        for tag in self.controller.get_all_tags():
            var = tk.BooleanVar(value=previous.get(tag, False))
            self._tag_vars[tag] = var
            ttk.Checkbutton(self._tag_filter_frame, text=tag, variable=var).pack(side=tk.LEFT, padx=2)

    def _selected_id(self):
        sel = self._tree.selection()
        return int(sel[0]) if sel else None

    def _on_select(self, _event=None):
        state = tk.NORMAL if self._tree.selection() else tk.DISABLED
        self._edit_btn.config(state=state)
        self._del_btn.config(state=state)

    def _on_search(self):
        query = self._search_var.get().strip()
        results = self.controller.search(query) if query else self.controller.get_all()
        self.refresh(results)

    def _on_filter_tags(self):
        selected = [tag for tag, var in self._tag_vars.items() if var.get()]
        if selected:
            results = self.controller.search_by_tags(selected)
            self.refresh(results)
        else:
            self.refresh()

    def _on_new(self):
        from views.notes.note_form_view import NoteFormView
        NoteFormView(self, self.controller, note_id=None, on_save=self.refresh)

    def _on_edit(self):
        nid = self._selected_id()
        if nid is not None:
            from views.notes.note_form_view import NoteFormView
            NoteFormView(self, self.controller, note_id=nid, on_save=self.refresh)

    def _on_delete(self):
        nid = self._selected_id()
        if nid is not None:
            if messagebox.askyesno("Delete", "Delete this note?"):
                try:
                    self.controller.delete(nid)
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                self.refresh()
