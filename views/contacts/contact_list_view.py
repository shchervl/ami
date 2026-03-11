import tkinter as tk
from tkinter import ttk, messagebox


class ContactListView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)

        self._search_var = tk.StringVar()
        ttk.Entry(top, textvariable=self._search_var, width=30).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="Search", command=self._on_search).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="Upcoming Birthdays", command=self._on_birthdays).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="New Contact", command=self._on_new).pack(side=tk.LEFT)

        # Treeview
        cols = ("last_name", "first_name", "phone", "email", "birthday")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        headers = {"last_name": "Last Name", "first_name": "First Name",
                   "phone": "Phone", "email": "Email", "birthday": "Birthday"}
        for col in cols:
            self._tree.heading(col, text=headers[col])
            self._tree.column(col, width=140)

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

    def _on_birthdays(self):
        results = self.controller.get_upcoming_birthdays()
        self.refresh(results)

    def _on_new(self):
        from views.contacts.contact_form_view import ContactFormView
        ContactFormView(self, self.controller, contact_id=None, on_save=self.refresh)

    def _on_edit(self):
        cid = self._selected_id()
        if cid is not None:
            from views.contacts.contact_form_view import ContactFormView
            ContactFormView(self, self.controller, contact_id=cid, on_save=self.refresh)

    def _on_delete(self):
        cid = self._selected_id()
        if cid is not None:
            if messagebox.askyesno("Delete", "Delete this contact?"):
                try:
                    self.controller.delete(cid)
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                self.refresh()
