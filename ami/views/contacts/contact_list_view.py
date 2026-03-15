import tkinter as tk
from tkinter import ttk, messagebox, font as tk_font

from ami.views.base_list_view import BaseListView
from ami.views.contacts.contact_form_view import ContactFormView


class ContactListView(BaseListView):
    _headers = {
        "last_name": "Last Name",
        "first_name": "First Name",
        "phone": "Phone",
        "email": "Email",
        "birthday": "Birthday",
    }

    def __init__(self, parent, controller, on_contact_saved=None):
        super().__init__(parent)
        self.controller = controller
        self._on_contact_saved = on_contact_saved
        self._sort_col = "last_name"
        self._sort_asc = True
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)

        self._search_var = tk.StringVar()
        ttk.Button(top, text="Search", command=self._on_search, width=9).pack(
            side=tk.RIGHT, padx=(4, 0)
        )
        entry = ttk.Entry(top, textvariable=self._search_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.bind("<Return>", lambda _: self._on_search())

        # Main area
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Side panel
        side = ttk.Frame(main)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        ttk.Button(side, text="New Contact", command=self._on_new).pack(
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
        self._tree = ttk.Treeview(
            main, columns=cols, show="headings",
            selectmode="browse", style="Contacts.Treeview"
        )
        for col in cols:
            self._tree.heading(
                col, text=self._headers[col], command=lambda c=col: self._on_sort(c)
            )
            self._tree.column(col, width=140)

        vsb = ttk.Scrollbar(main, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", lambda _: self._on_edit())

    def refresh(self, contacts=None):
        for row in self._tree.get_children():
            self._tree.delete(row)
        if contacts is None:
            contacts = self._fetch_data()

        max_phones = 1
        for c in contacts:
            phone = "\n".join(self._fmt_phone(p) for p in c["phones"])
            email = "\n".join(self._fmt_email(e) for e in c["emails"])
            self._tree.insert(
                "", tk.END, iid=str(c["id"]),
                values=(c["last_name"], c["first_name"], phone, email,
                        c["birthday"] or "")
            )
            max_phones = max(max_phones, len(c["phones"]) or 1)

        line_h = tk_font.nametofont("TkDefaultFont").metrics("linespace")
        ttk.Style().configure("Contacts.Treeview", rowheight=max_phones * line_h + 4)

        self._edit_btn.config(state=tk.DISABLED)
        self._del_btn.config(state=tk.DISABLED)

    def _fmt_phone(self, p):
        return f'{p["number"]} ({p["type"]})' if p["type"] else p["number"]

    def _fmt_email(self, e):
        return f'{e["address"]} ({e["type"]})' if e["type"] else e["address"]

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

    def _on_save(self, contacts=None):
        self.refresh(contacts)
        if self._on_contact_saved:
            self._on_contact_saved()

    def _on_new(self):
        ContactFormView(self, self.controller, contact_id=None, on_save=self._on_save)

    def _on_edit(self):
        cid = self._selected_id()
        if cid is not None:
            ContactFormView(
                self, self.controller, contact_id=cid, on_save=self._on_save
            )

    def _on_delete(self):
        cid = self._selected_id()
        if cid is not None:
            if messagebox.askyesno("Delete", "Delete this contact?"):
                try:
                    self.controller.delete(cid)
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                self.refresh()
