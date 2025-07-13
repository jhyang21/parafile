import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, List

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from config_manager import load_config, save_config
from organizer import start_observer


class ConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Organizer Settings")
        self.geometry("600x600")

        self.config_data = load_config()
        self.observer_thread = None
        self.monitoring_active = False

        # Watched folder frame
        folder_frame = tk.Frame(self)
        folder_frame.pack(fill=tk.X, pady=10, padx=10)

        tk.Label(folder_frame, text="Watched Folder:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar(value=self.config_data["watched_folder"])
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT)

        # Monitoring control frame
        monitor_frame = tk.Frame(self)
        monitor_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(monitor_frame, text="Monitoring Status:").pack(side=tk.LEFT)
        self.status_label = tk.Label(monitor_frame, text="Stopped", fg="red")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.monitor_button = tk.Button(monitor_frame, text="Start Monitoring", command=self.toggle_monitoring, bg="green", fg="white")
        self.monitor_button.pack(side=tk.LEFT, padx=10)

        # Main content frame
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Categories list section
        cat_section = tk.Frame(main_frame)
        cat_section.pack(fill=tk.BOTH, expand=True, pady=5)

        tk.Label(cat_section, text="Categories:").pack(anchor=tk.W)
        self.cat_listbox = tk.Listbox(cat_section, height=6)
        self.cat_listbox.pack(fill=tk.BOTH, expand=True)

        # Category buttons
        cat_btn_frame = tk.Frame(cat_section)
        cat_btn_frame.pack(pady=5)
        tk.Button(cat_btn_frame, text="Add", command=self.add_category).pack(side=tk.LEFT, padx=5)
        tk.Button(cat_btn_frame, text="Edit", command=self.edit_category).pack(side=tk.LEFT, padx=5)
        tk.Button(cat_btn_frame, text="Delete", command=self.delete_category).pack(side=tk.LEFT, padx=5)

        # Variables list section
        var_section = tk.Frame(main_frame)
        var_section.pack(fill=tk.BOTH, expand=True, pady=5)

        tk.Label(var_section, text="Variables:").pack(anchor=tk.W)
        self.var_listbox = tk.Listbox(var_section, height=6)
        self.var_listbox.pack(fill=tk.BOTH, expand=True)

        # Variable buttons
        var_btn_frame = tk.Frame(var_section)
        var_btn_frame.pack(pady=5)
        tk.Button(var_btn_frame, text="Add", command=self.add_variable).pack(side=tk.LEFT, padx=5)
        tk.Button(var_btn_frame, text="Edit", command=self.edit_variable).pack(side=tk.LEFT, padx=5)
        tk.Button(var_btn_frame, text="Delete", command=self.delete_variable).pack(side=tk.LEFT, padx=5)

        # Populate listboxes
        self.refresh_categories()
        self.refresh_variables()

        # Save button
        tk.Button(self, text="Save Changes", command=self.save_changes).pack(pady=10)
        
        # Check if folder needs to be selected (after GUI is created)
        if self.config_data["watched_folder"] == "SELECT FOLDER":
            self.prompt_folder_selection()
            
        # Bind window close event to cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handle window closing - stop monitoring if active."""
        if self.monitoring_active:
            self.stop_monitoring()
        self.destroy()

    def toggle_monitoring(self):
        """Toggle the monitoring on/off."""
        if not self.monitoring_active:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """Start the file monitoring in a separate thread."""
        # Check if folder is selected
        if self.config_data["watched_folder"] == "SELECT FOLDER":
            messagebox.showwarning("No Folder Selected", 
                                 "Please select a folder to monitor before starting.")
            return
        
        # Check if folder exists
        folder_path = Path(self.config_data["watched_folder"])
        if not folder_path.exists():
            result = messagebox.askyesno("Folder Not Found", 
                                       f"The folder '{folder_path}' does not exist. Create it?")
            if result:
                folder_path.mkdir(parents=True, exist_ok=True)
            else:
                return
        
        # Start monitoring in a separate thread
        self.observer_thread = threading.Thread(target=self.run_observer, daemon=True)
        self.observer_thread.start()
        
        # Update UI
        self.monitoring_active = True
        self.status_label.config(text="Running", fg="green")
        self.monitor_button.config(text="Stop Monitoring", bg="red")
        
        messagebox.showinfo("Monitoring Started", 
                          f"File monitoring started for folder:\n{self.config_data['watched_folder']}")

    def stop_monitoring(self):
        """Stop the file monitoring."""
        self.monitoring_active = False
        
        # Update UI
        self.status_label.config(text="Stopped", fg="red")
        self.monitor_button.config(text="Start Monitoring", bg="green")
        
        messagebox.showinfo("Monitoring Stopped", "File monitoring has been stopped.")

    def run_observer(self):
        """Run the file observer - this runs in a separate thread."""
        try:
            # Create a modified version of start_observer that can be stopped
            from organizer import DocumentHandler
            from watchdog.observers import Observer
            
            watched_folder = Path(self.config_data["watched_folder"])
            event_handler = DocumentHandler(self.config_data)
            observer = Observer()
            observer.schedule(event_handler, str(watched_folder), recursive=False)
            observer.start()
            
            # Keep running until monitoring is stopped
            while self.monitoring_active:
                observer.join(timeout=1)  # Check every second
                
            observer.stop()
            observer.join()
            
        except Exception as e:
            # Handle any errors and update UI on main thread
            self.after(0, lambda: self.handle_monitoring_error(str(e)))

    def handle_monitoring_error(self, error_message):
        """Handle monitoring errors on the main thread."""
        self.monitoring_active = False
        self.status_label.config(text="Error", fg="red")
        self.monitor_button.config(text="Start Monitoring", bg="green")
        messagebox.showerror("Monitoring Error", f"An error occurred during monitoring:\n{error_message}")

    # Folder browse
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_var.set(folder_selected)
            self.config_data["watched_folder"] = folder_selected
            save_config(self.config_data)
    
    def prompt_folder_selection(self):
        """Prompt user to select a folder if none is selected."""
        result = messagebox.askyesno(
            "Select Folder", 
            "No folder is currently selected for monitoring. Would you like to select a folder now?"
        )
        if result:
            self.browse_folder()

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
            save_config(self.config_data)

    def edit_category(self):
        index = self.cat_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a category to edit.")
            return
        idx = index[0]
        current = self.config_data["categories"][idx]
        
        # Prevent editing the "General" category
        if current["name"] == "General":
            messagebox.showwarning("Protected Item", 
                                 "The 'General' category cannot be edited as it's required for the application to function properly.")
            return
        
        updated = self.category_dialog(current)
        if updated:
            self.config_data["categories"][idx] = updated
            self.refresh_categories()
            save_config(self.config_data)

    def delete_category(self):
        index = self.cat_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a category to delete.")
            return
        idx = index[0]
        current = self.config_data["categories"][idx]
        
        # Prevent deleting the "General" category
        if current["name"] == "General":
            messagebox.showwarning("Protected Item", 
                                 "The 'General' category cannot be deleted as it's required for the application to function properly.")
            return
        
        del self.config_data["categories"][idx]
        self.refresh_categories()
        save_config(self.config_data)

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
            save_config(self.config_data)

    def edit_variable(self):
        index = self.var_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a variable to edit.")
            return
        idx = index[0]
        current = self.config_data["variables"][idx]
        
        # Prevent editing the "original_name" variable
        if current["name"] == "original_name":
            messagebox.showwarning("Protected Item", 
                                 "The 'original_name' variable cannot be edited as it's required for the application to function properly.")
            return
        
        updated = self.variable_dialog(current)
        if updated:
            self.config_data["variables"][idx] = updated
            self.refresh_variables()
            save_config(self.config_data)

    def delete_variable(self):
        index = self.var_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a variable to delete.")
            return
        idx = index[0]
        current = self.config_data["variables"][idx]
        
        # Prevent deleting the "original_name" variable
        if current["name"] == "original_name":
            messagebox.showwarning("Protected Item", 
                                 "The 'original_name' variable cannot be deleted as it's required for the application to function properly.")
            return

        del self.config_data["variables"][idx]
        self.refresh_variables()
        save_config(self.config_data)

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


def main():
    """Main entry point for the GUI application."""
    app = ConfigGUI()
    app.mainloop()


if __name__ == "__main__":
    main() 