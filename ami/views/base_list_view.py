import tkinter as tk
from tkinter import ttk


class BaseListView(ttk.Frame):
    """Shared Treeview boilerplate for list views.

    Subclasses must set before _build_ui returns:
      self._tree    — ttk.Treeview
      self._headers — dict[col_id, display_label]
      self._sort_col — str, default sort column
      self._sort_asc — bool, default sort direction

    Subclasses with Edit/Delete buttons must also set:
      self._edit_btn, self._del_btn — ttk.Button

    Subclasses must implement:
      refresh() — fetch data from controller and repopulate self._tree
    """

    def _fetch_data(self):
        query = self._search_var.get().strip()
        if query:
            return self.controller.search(
                query, sort_by=self._sort_col, sort_asc=self._sort_asc
            )
        return self.controller.get_all(
            sort_by=self._sort_col, sort_asc=self._sort_asc
        )

    def _selected_id(self) -> int | None:
        sel = self._tree.selection()
        return int(sel[0]) if sel else None

    def _on_select(self, _event=None):
        state = tk.NORMAL if self._tree.selection() else tk.DISABLED
        self._edit_btn.config(state=state)
        self._del_btn.config(state=state)

    def _fetch_data(self):
        query = self._search_var.get().strip()
        if query:
            return self.controller.search(
                query, sort_by=self._sort_col, sort_asc=self._sort_asc
            )
        return self.controller.get_all(
            sort_by=self._sort_col, sort_asc=self._sort_asc
        )

    def _on_sort(self, col: str):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        for c, label in self._headers.items():
            indicator = (" ▲" if self._sort_asc else " ▼") if c == self._sort_col else ""
            self._tree.heading(c, text=label + indicator)
        self.refresh()
