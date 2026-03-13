import tkinter as tk
from tkinter import ttk, messagebox

from ami.views.base_list_view import BaseListView
from ami.views.notes.note_form_view import NoteFormView


class NoteListView(BaseListView):
    _headers = {"title": "Title", "tags": "Tags", "updated": "Updated"}

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._tag_vars = {}  # tag_name -> BooleanVar
        self._sort_col = "updated"
        self._sort_asc = False
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Search group
        search_outer = ttk.LabelFrame(self, text="Search")
        search_outer.pack(fill=tk.X, padx=5, pady=5)

        self._search_var = tk.StringVar()
        ttk.Button(search_outer, text="Search", command=self._on_search).pack(
            side=tk.RIGHT, padx=5, pady=2
        )
        ttk.Entry(search_outer, textvariable=self._search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2
        )

        # Tag filter area
        tag_outer = ttk.LabelFrame(self, text="Filter by Tags")
        tag_outer.pack(fill=tk.X, padx=5, pady=(0, 5))

        self._tag_filter_frame = ttk.Frame(tag_outer)
        self._tag_filter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Main area
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Side panel
        side = ttk.Frame(main)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        ttk.Button(side, text="New Note", command=self._on_new).pack(
            fill=tk.X, pady=(0, 4)
        )
        self._edit_btn = ttk.Button(
            side, text="Edit", state=tk.DISABLED, command=self._on_edit
        )
        self._edit_btn.pack(fill=tk.X, pady=(0, 4))
        self._del_btn = ttk.Button(
            side, text="Delete", state=tk.DISABLED, command=self._on_delete
        )
        self._del_btn.pack(fill=tk.X)

        # Treeview
        cols = tuple(self._headers)
        self._tree = ttk.Treeview(main, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self._tree.heading(
                col, text=self._headers[col], command=lambda c=col: self._on_sort(c)
            )
        self._tree.column("title", width=250)
        self._tree.column("tags", width=200)
        self._tree.column("updated", width=180)

        vsb = ttk.Scrollbar(main, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    def refresh(self, notes=None):
        for row in self._tree.get_children():
            self._tree.delete(row)
        if notes is None:
            notes = self.controller.get_all(
                sort_by=self._sort_col, sort_asc=self._sort_asc
            )
        for n in notes:
            tags_str = ", ".join(sorted(n.get("tags", [])))
            updated = (n.get("updated_at") or "")[:19]  # trim microseconds
            self._tree.insert(
                "", tk.END, iid=str(n["id"]),
                values=(n["title"], tags_str, updated)
            )
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
            ttk.Checkbutton(
                self._tag_filter_frame, text=tag, variable=var,
                command=self._on_filter_tags
            ).pack(side=tk.LEFT, padx=2)

    def _on_search(self):
        query = self._search_var.get().strip()
        if query:
            results = self.controller.search(
                query, sort_by=self._sort_col, sort_asc=self._sort_asc
            )
        else:
            results = self.controller.get_all(
                sort_by=self._sort_col, sort_asc=self._sort_asc
            )
        self.refresh(results)

    def _on_filter_tags(self):
        selected = [tag for tag, var in self._tag_vars.items() if var.get()]
        if selected:
            results = self.controller.search_by_tags(
                selected, sort_by=self._sort_col, sort_asc=self._sort_asc
            )
            self.refresh(results)
        else:
            self.refresh()

    def _on_new(self):
        NoteFormView(self, self.controller, note_id=None, on_save=self.refresh)

    def _on_edit(self):
        nid = self._selected_id()
        if nid is not None:
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
