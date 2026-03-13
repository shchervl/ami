import tkinter as tk
from tkinter import ttk, messagebox


class ContactFormView(tk.Toplevel):
    def __init__(self, parent, controller, contact_id=None, on_save=None):
        super().__init__(parent)
        self.controller = controller
        self.contact_id = contact_id
        self.on_save = on_save
        self._phone_rows = []  # list of (frame, number_var, type_var)
        self._email_rows = []  # list of (frame, address_var, type_var)

        self.title("Edit Contact" if contact_id else "New Contact")
        self.resizable(False, False)
        self.grab_set()  # modal

        self._build_ui()

        if contact_id is not None:
            self._populate(controller.get_by_id(contact_id))

        self.transient(parent)
        self.wait_visibility()
        self.focus_set()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}
        form = ttk.Frame(self, padding=10)
        form.pack(fill=tk.BOTH, expand=True)

        # Basic fields
        fields = [("First Name*", "first_name"), ("Last Name*", "last_name"),
                  ("Address", "address"), ("Birthday (YYYY-MM-DD)", "birthday")]
        self._vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky=tk.W, **pad)
            var = tk.StringVar()
            self._vars[key] = var
            ttk.Entry(form, textvariable=var, width=35).grid(row=i, column=1, sticky=tk.EW, **pad)

        # Phones section
        self._phones_frame = ttk.LabelFrame(form, text="Phones", padding=5)
        self._phones_frame.grid(row=len(fields), column=0, columnspan=2, sticky=tk.EW, **pad)
        header = ttk.Frame(self._phones_frame)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Phone", width=20).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(header, text="Type", width=12).pack(side=tk.LEFT)
        ttk.Button(form, text="+ Add Phone", command=self._add_phone_row).grid(
            row=len(fields)+1, column=0, columnspan=2, **pad)

        # Emails section
        self._emails_frame = ttk.LabelFrame(form, text="Emails", padding=5)
        self._emails_frame.grid(row=len(fields)+2, column=0, columnspan=2, sticky=tk.EW, **pad)
        email_header = ttk.Frame(self._emails_frame)
        email_header.pack(fill=tk.X)
        ttk.Label(email_header, text="Email", width=25).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(email_header, text="Type", width=12).pack(side=tk.LEFT)
        ttk.Button(form, text="+ Add Email", command=self._add_email_row).grid(
            row=len(fields)+3, column=0, columnspan=2, **pad)

        # Save/Cancel
        btns = ttk.Frame(form)
        btns.grid(row=len(fields)+4, column=0, columnspan=2, **pad)
        ttk.Button(btns, text="Save", command=self._on_save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

        form.columnconfigure(1, weight=1)

    def _add_phone_row(self, number="", phone_type=""):
        row_frame = ttk.Frame(self._phones_frame)
        row_frame.pack(fill=tk.X, pady=2)
        num_var = tk.StringVar(value=number)
        type_var = tk.StringVar(value=phone_type)
        ttk.Entry(row_frame, textvariable=num_var, width=20).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Entry(row_frame, textvariable=type_var, width=12).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            row_frame, text="✕", width=2,
            command=lambda f=row_frame, r=(row_frame, num_var, type_var):
                self._remove_row(f, self._phone_rows, r),
        ).pack(side=tk.LEFT)
        self._phone_rows.append((row_frame, num_var, type_var))

    def _add_email_row(self, address="", email_type=""):
        row_frame = ttk.Frame(self._emails_frame)
        row_frame.pack(fill=tk.X, pady=2)
        addr_var = tk.StringVar(value=address)
        type_var = tk.StringVar(value=email_type)
        ttk.Entry(row_frame, textvariable=addr_var, width=25).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Entry(row_frame, textvariable=type_var, width=12).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            row_frame, text="✕", width=2,
            command=lambda f=row_frame, r=(row_frame, addr_var, type_var):
                self._remove_row(f, self._email_rows, r),
        ).pack(side=tk.LEFT)
        self._email_rows.append((row_frame, addr_var, type_var))

    def _remove_row(self, frame, rows_list, row_tuple):
        frame.destroy()
        if row_tuple in rows_list:
            rows_list.remove(row_tuple)

    def _populate(self, contact: dict):
        if not contact:
            return
        self._vars["first_name"].set(contact.get("first_name", ""))
        self._vars["last_name"].set(contact.get("last_name", ""))
        self._vars["address"].set(contact.get("address") or "")
        self._vars["birthday"].set(contact.get("birthday") or "")
        for p in contact.get("", []):
            self._add_phone_row(p.get("number", ""), p.get("type") or "")
        for e in contact.get("emails", []):
            self._add_email_row(e.get("address", ""), e.get("type") or "")

    def _on_save(self):
        first_name = self._vars["first_name"].get().strip()
        last_name = self._vars["last_name"].get().strip()
        address = self._vars["address"].get().strip() or None
        birthday = self._vars["birthday"].get().strip() or None

        phones = [{"number": nv.get().strip(), "type": tv.get().strip() or None}
                  for _, nv, tv in self._phone_rows if nv.get().strip()]
        emails = [{"address": av.get().strip(), "type": tv.get().strip() or None}
                  for _, av, tv in self._email_rows if av.get().strip()]

        try:
            if self.contact_id is None:
                self.controller.create(first_name, last_name, address, birthday, phones, emails)
            else:
                self.controller.update(self.contact_id, first_name, last_name, address, birthday, phones, emails)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()
