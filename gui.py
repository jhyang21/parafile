import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, List

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from config_manager import load_config, save_config


class ConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Organizer Settings")
        self.geometry("600x400")

        self.config_data = load_config()

        # Watched folder frame
        folder_frame = tk.Frame(self)
        folder_frame.pack(fill=tk.X, pady=10, padx=10)

        tk.Label(folder_frame, text="Watched Folder:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar(value=self.config_data["watched_folder"])
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT)

        # Categories list section
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(list_frame, text="Categories:").pack(anchor=tk.W)
        self.cat_listbox = tk.Listbox(list_frame, height=8)
        self.cat_listbox.pack(fill=tk.BOTH, expand=True)

        # Category buttons
        cat_btn_frame = tk.Frame(self)
        cat_btn_frame.pack(pady=5)
        tk.Button(cat_btn_frame, text="Add", command=self.add_category).pack(side=tk.LEFT, padx=5)
        tk.Button(cat_btn_frame, text="Edit", command=self.edit_category).pack(side=tk.LEFT, padx=5)
        tk.Button(cat_btn_frame, text="Delete", command=self.delete_category).pack(side=tk.LEFT, padx=5)

        # Variables list section
        var_frame = tk.Frame(self)
        var_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(var_frame, text="Variables:").pack(anchor=tk.W)
        self.var_listbox = tk.Listbox(var_frame, height=8)
        self.var_listbox.pack(fill=tk.BOTH, expand=True)

        var_btn_frame = tk.Frame(self)
        var_btn_frame.pack(pady=5)
        tk.Button(var_btn_frame, text="Add", command=self.add_variable).pack(side=tk.LEFT, padx=5)
        tk.Button(var_btn_frame, text="Edit", command=self.edit_variable).pack(side=tk.LEFT, padx=5)
        tk.Button(var_btn_frame, text="Delete", command=self.delete_variable).pack(side=tk.LEFT, padx=5)

        # Populate listboxes
        self.refresh_categories()
        self.refresh_variables()

        # Save button
        tk.Button(self, text="Save Changes", command=self.save_changes).pack(pady=10)

    # Folder browse
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_var.set(folder_selected)

    # Category operations
    def refresh_categories(self):
        self.cat_listbox.delete(0, tk.END)
        for cat in self.config_data["categories"]:
            self.cat_listbox.insert(tk.END, cat["name"])

    def add_category(self):
        cat = self.category_dialog()
        if cat:
            self.config_data["categories"].append(cat)
            self.refresh_categories()

    def edit_category(self):
        index = self.cat_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a category to edit.")
            return
        idx = index[0]
        current = self.config_data["categories"][idx]
        updated = self.category_dialog(current)
        if updated:
            self.config_data["categories"][idx] = updated
            self.refresh_categories()

    def delete_category(self):
        index = self.cat_listbox.curselection()
        if not index:
            return
        idx = index[0]
        del self.config_data["categories"][idx]
        self.refresh_categories()

    def category_dialog(self, cat: Dict[str, str] | None = None) -> Dict[str, str] | None:
        dialog = tk.Toplevel(self)
        dialog.transient(self)
        dialog.grab_set()
        dialog.title("Category" if cat else "Add Category")

        fields = {
            "name": tk.StringVar(value=cat["name"] if cat else ""),
            "description": tk.StringVar(value=cat["description"] if cat else ""),
            "naming_pattern": tk.StringVar(value=cat["naming_pattern"] if cat else ""),
        }

        row = 0
        for label, var in fields.items():
            tk.Label(dialog, text=label.capitalize() + ":").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
            tk.Entry(dialog, textvariable=var, width=50).grid(row=row, column=1, pady=5, padx=5)
            row += 1

        result: Dict[str, str] | None = None

        def on_ok():
            nonlocal result
            vals = {k: v.get().strip() for k, v in fields.items()}
            if not vals["name"]:
                messagebox.showerror("Error", "Name is required.")
                return
            result = vals
            dialog.destroy()

        tk.Button(dialog, text="OK", command=on_ok).grid(row=row, column=0, pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=row, column=1, pady=10)

        self.wait_window(dialog)
        return result

    # Variable CRUD

    def add_variable(self):
        var = self.variable_dialog()
        if var:
            self.config_data.setdefault("variables", []).append(var)
            self.refresh_variables()

    def edit_variable(self):
        index = self.var_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a variable to edit.")
            return
        idx = index[0]
        current = self.config_data["variables"][idx]
        updated = self.variable_dialog(current)
        if updated:
            self.config_data["variables"][idx] = updated
            self.refresh_variables()

    def delete_variable(self):
        index = self.var_listbox.curselection()
        if not index:
            return
        idx = index[0]
        del self.config_data["variables"][idx]
        self.refresh_variables()

    def variable_dialog(self, var: Dict[str, str] | None = None) -> Dict[str, str] | None:
        dialog = tk.Toplevel(self)
        dialog.transient(self)
        dialog.grab_set()
        dialog.title("Variable" if var else "Add Variable")

        fields = {
            "name": tk.StringVar(value=var["name"] if var else ""),
            "description": tk.StringVar(value=var["description"] if var else ""),
        }

        row = 0
        for label, var_str in fields.items():
            tk.Label(dialog, text=label.capitalize() + ":").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
            tk.Entry(dialog, textvariable=var_str, width=50).grid(row=row, column=1, pady=5, padx=5)
            row += 1

        result: Dict[str, str] | None = None

        def on_ok():
            nonlocal result
            vals = {k: v.get().strip() for k, v in fields.items()}
            if not vals["name"]:
                messagebox.showerror("Error", "Name is required.")
                return
            result = vals
            dialog.destroy()

        tk.Button(dialog, text="OK", command=on_ok).grid(row=row, column=0, pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=row, column=1, pady=10)

        self.wait_window(dialog)
        return result

    def refresh_variables(self):
        self.var_listbox.delete(0, tk.END)
        for var in self.config_data.get("variables", []):
            self.var_listbox.insert(tk.END, var["name"])

    def save_changes(self):
        self.config_data["watched_folder"] = self.folder_var.get().strip()
        save_config(self.config_data)
        messagebox.showinfo("Config Saved", "Configuration saved successfully.")


if __name__ == "__main__":
    app = ConfigGUI()
    app.mainloop() 