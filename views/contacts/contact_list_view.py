import tkinter as tk
from tkinter import ttk, messagebox

from views.contacts.contact_form_view import ContactFormView


class ContactListView(ttk.Frame):
    def __init__(self, parent, controller, on_contact_saved=None):
        super().__init__(parent)
        self.controller = controller
        self._on_contact_saved = on_contact_saved
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)

        self._search_var = tk.StringVar()
        ttk.Entry(top, textvariable=self._search_var, width=30).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="Search", command=self._on_search).pack(side=tk.LEFT)

        # Main area
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Side panel
        side = ttk.Frame(main)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        ttk.Button(side, text="New Contact", command=self._on_new).pack(fill=tk.X, pady=(0, 4))
        self._edit_btn = ttk.Button(side, text="Edit", state=tk.DISABLED, command=self._on_edit)
        self._edit_btn.pack(fill=tk.X, pady=(0, 4))
        self._del_btn = ttk.Button(side, text="Delete", state=tk.DISABLED, command=self._on_delete)
        self._del_btn.pack(fill=tk.X)

        # Treeview
        cols = ("last_name", "first_name", "phone", "email", "birthday")
        self._tree = ttk.Treeview(main, columns=cols, show="headings", selectmode="browse")
        headers = {"last_name": "Last Name", "first_name": "First Name",
                   "phone": "Phone", "email": "Email", "birthday": "Birthday"}
        for col in cols:
            self._tree.heading(col, text=headers[col])
            self._tree.column(col, width=140)

        vsb = ttk.Scrollbar(main, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    def refresh(self, contacts=None):
        for row in self._tree.get_children():
            self._tree.delete(row)
        if contacts is None:
            contacts = self.controller.get_all()
        for c in contacts:
            phone = c["phones"][0]["number"] if c["phones"] else ""
            email = c["emails"][0]["address"] if c["emails"] else ""
            self._tree.insert("", tk.END, iid=str(c["id"]),
                              values=(c["last_name"], c["first_name"], phone, email,
                                      c["birthday"] or ""))
        self._edit_btn.config(state=tk.DISABLED)
        self._del_btn.config(state=tk.DISABLED)

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

    def _on_save(self, contacts=None):
        self.refresh(contacts)
        if self._on_contact_saved:
            self._on_contact_saved()

    def _on_new(self):
        ContactFormView(self, self.controller, contact_id=None, on_save=self._on_save)

    def _on_edit(self):
        cid = self._selected_id()
        if cid is not None:
            ContactFormView(self, self.controller, contact_id=cid, on_save=self._on_save)

    def _on_delete(self):
        cid = self._selected_id()
        if cid is not None:
            if messagebox.askyesno("Delete", "Delete this contact?"):
                try:
                    self.controller.delete(cid)
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                self.refresh()
