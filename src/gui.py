import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from config_manager import load_config, save_config


class ConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Organizer Settings")
        self.geometry("600x600")

        self.config_data = load_config()
        self.monitor_process: subprocess.Popen | None = None
        self.current_view = None

        # Main container to switch between views
        self.view_container = tk.Frame(self)
        self.view_container.pack(fill=tk.BOTH, expand=True)

        self.create_list_view()
        self.show_list_view()
            
        # Check if folder needs to be selected (after GUI is created)
        if self.config_data["watched_folder"] == "SELECT FOLDER" or not self.config_data["watched_folder"]:
            self.prompt_folder_selection()
            
        # Bind window close event to cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_list_view(self):
        """Creates the main list view with all the controls."""
        self.list_view_frame = tk.Frame(self.view_container)
        
        # Watched folder frame
        folder_frame = tk.Frame(self.list_view_frame)
        folder_frame.pack(fill=tk.X, pady=10, padx=10)

        tk.Label(folder_frame, text="Watched Folder:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar(value=self.config_data["watched_folder"])
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT)

        # Monitoring control frame
        monitor_frame = tk.Frame(self.list_view_frame)
        monitor_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(monitor_frame, text="Monitoring Status:").pack(side=tk.LEFT)
        self.status_label = tk.Label(monitor_frame, text="Stopped", fg="red")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.monitor_button = tk.Button(monitor_frame, text="Start Monitoring", command=self.toggle_monitoring, bg="green", fg="white")
        self.monitor_button.pack(side=tk.LEFT, padx=10)

        # Main content frame
        main_frame = tk.Frame(self.list_view_frame)
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
        tk.Button(self.list_view_frame, text="Save Watched Folder", command=self.save_changes).pack(pady=10)

    def show_view(self, view_frame: tk.Frame):
        """Switch to a different view frame."""
        if self.current_view:
            self.current_view.pack_forget()
        self.current_view = view_frame
        self.current_view.pack(fill=tk.BOTH, expand=True)

    def show_list_view(self):
        """Switch back to the main list view."""
        if hasattr(self, 'form_view_frame'):
            self.form_view_frame.destroy()
            del self.form_view_frame
        self.show_view(self.list_view_frame)

    def on_closing(self):
        """Handle window closing - stop monitoring if active."""
        if self.monitor_process and self.monitor_process.poll() is None:
            self.stop_monitoring()
        self.destroy()

    def toggle_monitoring(self):
        """Toggle the monitoring on/off."""
        is_running = self.monitor_process and self.monitor_process.poll() is None
        if not is_running:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """Start the file monitoring in a separate process."""
        # Check if folder is selected
        if self.config_data["watched_folder"] == "SELECT FOLDER" or not self.config_data["watched_folder"]:
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
        
        # Start monitoring in a separate process
        try:
            # Using sys.executable ensures we use the same python interpreter
            # that is running the GUI. This is important for virtual envs.
            # We construct the absolute path to main.py to be safe.
            main_script_path = Path(__file__).resolve().parent.parent / "main.py"
            
            self.monitor_process = subprocess.Popen(
                [sys.executable, str(main_script_path), "monitor"]
            )
            
            # Update UI
            self.status_label.config(text="Running", fg="green")
            self.monitor_button.config(text="Stop Monitoring", bg="red")
            
            messagebox.showinfo("Monitoring Started", 
                              f"File monitoring started for folder:\n{self.config_data['watched_folder']}")
        except Exception as e:
            messagebox.showerror("Failed to Start", f"Could not start the monitoring process:\n{e}")
            self.status_label.config(text="Error", fg="red")
            self.monitor_button.config(text="Start Monitoring", bg="green")


    def stop_monitoring(self):
        """Stop the file monitoring process."""
        if self.monitor_process and self.monitor_process.poll() is None:
            self.monitor_process.terminate()
            try:
                # Wait for a short period for the process to terminate
                self.monitor_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If it doesn't terminate, force kill it
                self.monitor_process.kill()
                self.monitor_process.wait()

        self.monitor_process = None
        
        # Update UI
        self.status_label.config(text="Stopped", fg="red")
        self.monitor_button.config(text="Start Monitoring", bg="green")
        
        messagebox.showinfo("Monitoring Stopped", "File monitoring has been stopped.")

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
        """Show the form to add a new category."""
        self.show_category_form()

    def edit_category(self):
        """Show the form to edit a selected category."""
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
        
        self.show_category_form(current, idx)

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

    def show_category_form(self, cat: Dict[str, str] | None = None, index: int | None = None):
        """Display the form for adding or editing a category."""
        self.form_view_frame = tk.Frame(self.view_container, padx=10, pady=10)
        self.show_view(self.form_view_frame)

        title = "Edit Category" if cat else "Add Category"
        tk.Label(self.form_view_frame, text=title, font=("Helvetica", 16)).pack(pady=10)

        # Main container for form and variables list
        editor_frame = tk.Frame(self.form_view_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Form fields on the left
        form_fields_frame = tk.Frame(editor_frame, padx=10)
        form_fields_frame.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.N)
        
        fields = {
            "name": tk.StringVar(value=cat["name"] if cat else ""),
            "description": tk.StringVar(value=cat["description"] if cat else ""),
            "naming_pattern": tk.StringVar(value=cat["naming_pattern"] if cat else ""),
        }

        entry_widgets = {}
        row = 0
        for label, var in fields.items():
            tk.Label(form_fields_frame, text=label.replace("_", " ").capitalize() + ":").grid(row=row, column=0, sticky=tk.W, pady=5)
            entry = tk.Entry(form_fields_frame, textvariable=var, width=40)
            entry.grid(row=row, column=1, pady=5, padx=5)
            entry_widgets[label] = entry
            row += 1

        # Variables list on the right
        variables_list_frame = tk.Frame(editor_frame, padx=10)
        variables_list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(variables_list_frame, text="Available Variables (click to insert)").pack(anchor=tk.W)

        var_listbox = tk.Listbox(variables_list_frame, height=8)
        for variable in self.config_data.get("variables", []):
            var_listbox.insert(tk.END, variable["name"])
        var_listbox.pack(fill=tk.BOTH, expand=True)

        def insert_variable_at_cursor(event):
            selection = var_listbox.curselection()
            if not selection:
                return
            
            variable_name = var_listbox.get(selection[0])
            naming_pattern_entry = entry_widgets["naming_pattern"]
            naming_pattern_entry.insert(tk.INSERT, f"{{{variable_name}}}")
            # Delay focus setting to ensure cursor visibility after the event.
            naming_pattern_entry.after(10, naming_pattern_entry.focus_set)

        var_listbox.bind("<<ListboxSelect>>", insert_variable_at_cursor)

        def on_save():
            vals = {k: v.get().strip() for k, v in fields.items()}
            if not vals["name"]:
                messagebox.showerror("Error", "Name is required.", parent=self.form_view_frame)
                return

            if index is not None:
                self.config_data["categories"][index] = vals
            else:
                self.config_data["categories"].append(vals)
            
            save_config(self.config_data)
            self.refresh_categories()
            self.show_list_view()

        btn_frame = tk.Frame(self.form_view_frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Save", command=on_save).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.show_list_view).pack(side=tk.LEFT, padx=10)

    # Variable CRUD
    def add_variable(self):
        """Show the form to add a new variable."""
        self.show_variable_form()

    def edit_variable(self):
        """Show the form to edit a selected variable."""
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
        
        self.show_variable_form(current, idx)

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

    def show_variable_form(self, var: Dict[str, str] | None = None, index: int | None = None):
        """Display the form for adding or editing a variable."""
        self.form_view_frame = tk.Frame(self.view_container, padx=10, pady=10)
        self.show_view(self.form_view_frame)

        title = "Edit Variable" if var else "Add Variable"
        tk.Label(self.form_view_frame, text=title, font=("Helvetica", 16)).pack(pady=10)

        fields = {
            "name": tk.StringVar(value=var["name"] if var else ""),
            "description": tk.StringVar(value=var["description"] if var else ""),
        }
        
        form_fields_frame = tk.Frame(self.form_view_frame)
        form_fields_frame.pack(pady=10)

        row = 0
        for label, var_str in fields.items():
            tk.Label(form_fields_frame, text=label.capitalize() + ":").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
            tk.Entry(form_fields_frame, textvariable=var_str, width=50).grid(row=row, column=1, pady=5, padx=5)
            row += 1

        def on_save():
            vals = {k: v.get().strip() for k, v in fields.items()}
            if not vals["name"]:
                messagebox.showerror("Error", "Name is required.", parent=self.form_view_frame)
                return

            if index is not None:
                self.config_data["variables"][index] = vals
            else:
                self.config_data.setdefault("variables", []).append(vals)

            save_config(self.config_data)
            self.refresh_variables()
            self.show_list_view()
        
        btn_frame = tk.Frame(self.form_view_frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Save", command=on_save).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.show_list_view).pack(side=tk.LEFT, padx=10)

    def refresh_variables(self):
        self.var_listbox.delete(0, tk.END)
        for var in self.config_data.get("variables", []):
            self.var_listbox.insert(tk.END, var["name"])

    def save_changes(self):
        self.config_data["watched_folder"] = self.folder_var.get().strip()
        save_config(self.config_data)
        messagebox.showinfo("Config Saved", "Watched folder saved successfully.")


def main():
    """Main entry point for the GUI application."""
    app = ConfigGUI()
    app.mainloop()


if __name__ == "__main__":
    main() 