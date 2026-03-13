import tkinter as tk
from tkinter import ttk

from views.base_list_view import BaseListView


class BirthdayListView(BaseListView):
    _headers = {
        "last_name": "Last Name",
        "first_name": "First Name",
        "birthday": "Birthday",
        "days_until": "Days Until",
    }

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._sort_col = "days_until"
        self._sort_asc = True
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(top, text="Show birthdays within next").pack(side=tk.LEFT)
        self._days_var = tk.StringVar(value="365")
        self._days_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(top, textvariable=self._days_var, width=5).pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="days").pack(side=tk.LEFT)

        cols = tuple(self._headers)
        widths = {"last_name": 180, "first_name": 180, "birthday": 120, "days_until": 100}
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="none")
        for col in cols:
            self._tree.heading(
                col, text=self._headers[col], command=lambda c=col: self._on_sort(c)
            )
            self._tree.column(
                col, width=widths[col],
                anchor=tk.CENTER if col == "days_until" else tk.W
            )

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=(0, 5))
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=(0, 5))

    def refresh(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        try:
            days = int(self._days_var.get())
        except (ValueError, AttributeError):
            return
        if days < 1:
            return
        contacts = self.controller.get_upcoming_birthdays(
            days, sort_by=self._sort_col, sort_asc=self._sort_asc
        )
        for c in contacts:
            self._tree.insert(
                "", tk.END,
                values=(c["last_name"], c["first_name"], c["birthday"], c["days_until"]),
            )
