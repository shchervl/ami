import tkinter as tk
from tkinter import ttk


class BirthdayListView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(top, text="Show birthdays within next").pack(side=tk.LEFT)
        self._days_var = tk.StringVar(value="365")
        self._days_var.trace_add("write", lambda *_: self._refresh())
        ttk.Entry(top, textvariable=self._days_var, width=5).pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="days").pack(side=tk.LEFT)

        cols = ("last_name", "first_name", "birthday", "days_until")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="none")
        headers = {
            "last_name": "Last Name",
            "first_name": "First Name",
            "birthday": "Birthday",
            "days_until": "Days Until",
        }
        widths = {"last_name": 180, "first_name": 180, "birthday": 120, "days_until": 100}
        for col in cols:
            self._tree.heading(col, text=headers[col])
            self._tree.column(col, width=widths[col], anchor=tk.CENTER if col == "days_until" else tk.W)

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=(0, 5))
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=(0, 5))

    def _refresh(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        try:
            days = int(self._days_var.get())
        except ValueError:
            return
        if days < 1:
            return
        contacts = sorted(self.controller.get_upcoming_birthdays(days), key=lambda c: c["days_until"])
        for c in contacts:
            self._tree.insert(
                "", tk.END,
                values=(c["last_name"], c["first_name"], c["birthday"], c["days_until"]),
            )
