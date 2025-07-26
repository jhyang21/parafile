"""
GUI module for the Parafile application.

This module provides a comprehensive tkinter-based configuration interface
for setting up and managing the file organization system. The GUI allows users to:

- Configure the watched folder for file monitoring
- Create and manage document categories with custom naming patterns
- Define variables for use in naming patterns
- Start and stop the file monitoring service
- Edit categories and variables with advanced form interfaces

The interface supports both list views for management and detailed form views
for editing, with syntax highlighting for naming patterns and real-time
variable suggestions for improved user experience.

Key Components:
- ConfigGUI: Main application window with integrated views
- Category management: Full CRUD operations with pattern editing
- Variable management: Dynamic placeholder system
- Monitoring control: Start/stop file watching service
- Configuration persistence: Automatic saving and validation
"""

import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import Dict, List

from config_manager import load_config, save_config_from_parts


class ConfigGUI(tk.Tk):
    """
    Main GUI application class for Parafile configuration.

    This class creates and manages the complete configuration interface,
    handling view switching between list and form modes, configuration
    persistence, and integration with the file monitoring service.

    The GUI implements a view-based architecture where different screens
    (list view, form views) are swapped in and out of the main container
    as needed, providing a smooth user experience.

    Attributes:
        watched_folder: Current watched folder path
        categories: Categories dict with name as key
        variables: Variables dict with name as key
        monitor_process: Subprocess handle for the monitoring service
        current_view: Reference to the currently active view frame
        view_container: Main container for swapping views
    """

    def __init__(self):
        """
        Initialize the main GUI window and components.

        Sets up the window properties, loads configuration, creates the
        view system, and prompts for folder selection if needed. Also
        establishes proper cleanup handling for the monitoring process.
        """
        super().__init__()

        self.title("File Organizer Settings")
        self.geometry("600x600")

        # Load configuration as separate objects
        (
            self.watched_folder,
            self.enable_organization,
            self.categories,
            self.variables,
        ) = load_config()
        self.monitor_process: subprocess.Popen | None = None
        self.current_view = None

        # Main container for view switching between list and form views
        self.view_container = tk.Frame(self)
        self.view_container.pack(fill=tk.BOTH, expand=True)

        self.create_list_view()
        self.show_list_view()

        # Prompt for folder selection if none configured
        if self.watched_folder == "SELECT FOLDER" or not self.watched_folder:
            self.prompt_folder_selection()

        # Ensure proper cleanup on window close to prevent orphaned processes
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_list_view(self):
        """
        Create the main list view with all configuration controls.

        This method builds the primary interface containing:
        - Watched folder selection and display
        - Monitoring start/stop controls with status indicator
        - Categories list with add/edit/delete operations
        - Variables list with full management capabilities

        The layout uses frames to organize related controls and provides
        a clean, intuitive interface for all configuration tasks.
        """
        # Create the main list view frame
        self.list_view_frame = tk.Frame(self.view_container)

        # === WATCHED FOLDER SECTION ===
        # Frame for folder selection controls
        folder_frame = tk.Frame(self.list_view_frame)
        folder_frame.pack(fill=tk.X, pady=10, padx=10)

        # Folder selection label and entry
        tk.Label(folder_frame, text="Watched Folder:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar(value=self.watched_folder)
        self.folder_entry = tk.Entry(
            folder_frame, textvariable=self.folder_var, width=50
        )
        self.folder_entry.pack(side=tk.LEFT, padx=5)

        # Browse button for folder selection dialog
        tk.Button(
            folder_frame,
            text="Browse",
            command=self.browse_folder).pack(
            side=tk.LEFT)

        # === ORGANIZATION TOGGLE SECTION ===
        # Frame for organization settings
        org_frame = tk.Frame(self.list_view_frame)
        org_frame.pack(fill=tk.X, pady=10, padx=10)

        # Organization toggle checkbox
        self.org_var = tk.BooleanVar(value=self.enable_organization)
        self.org_checkbox = tk.Checkbutton(
            org_frame,
            text="Organize files into category folders",
            variable=self.org_var,
            command=self.on_organization_toggle,
        )
        self.org_checkbox.pack(side=tk.LEFT)

        # Help text for the organization feature
        help_label = tk.Label(
            org_frame,
            text="(When disabled, files are only renamed, not moved to subfolders)",
            fg="gray",
            font=(
                "Arial",
                8),
        )
        help_label.pack(side=tk.LEFT, padx=10)

        # === MONITORING CONTROL SECTION ===
        # Frame for monitoring status and controls
        monitor_frame = tk.Frame(self.list_view_frame)
        monitor_frame.pack(fill=tk.X, pady=10, padx=10)

        # Monitoring status display
        tk.Label(monitor_frame, text="Monitoring Status:").pack(side=tk.LEFT)
        self.status_label = tk.Label(monitor_frame, text="Stopped", fg="red")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Start/Stop monitoring button with dynamic text and color
        self.monitor_button = tk.Button(
            monitor_frame,
            text="Start Monitoring",
            command=self.toggle_monitoring,
            bg="green",
            fg="white",
        )
        self.monitor_button.pack(side=tk.LEFT, padx=10)

        # === MAIN CONFIGURATION SECTION ===
        # Container for categories and variables lists
        main_frame = tk.Frame(self.list_view_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # === CATEGORIES MANAGEMENT ===
        # Section for category configuration
        cat_section = tk.Frame(main_frame)
        cat_section.pack(fill=tk.BOTH, expand=True, pady=5)

        # Categories list header and listbox
        tk.Label(cat_section, text="Categories:").pack(anchor=tk.W)
        self.cat_listbox = tk.Listbox(cat_section, height=6)
        self.cat_listbox.pack(fill=tk.BOTH, expand=True)

        # Category management buttons
        cat_btn_frame = tk.Frame(cat_section)
        cat_btn_frame.pack(pady=5)
        tk.Button(cat_btn_frame, text="Add", command=self.add_category).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(cat_btn_frame, text="Edit", command=self.edit_category).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(
            cat_btn_frame,
            text="Delete",
            command=self.delete_category).pack(
            side=tk.LEFT,
            padx=5)

        # === VARIABLES MANAGEMENT ===
        # Section for variable configuration
        var_section = tk.Frame(main_frame)
        var_section.pack(fill=tk.BOTH, expand=True, pady=5)

        # Variables list header and listbox
        tk.Label(var_section, text="Variables:").pack(anchor=tk.W)
        self.var_listbox = tk.Listbox(var_section, height=6)
        self.var_listbox.pack(fill=tk.BOTH, expand=True)

        # Variable management buttons
        var_btn_frame = tk.Frame(var_section)
        var_btn_frame.pack(pady=5)
        tk.Button(var_btn_frame, text="Add", command=self.add_variable).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(var_btn_frame, text="Edit", command=self.edit_variable).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(
            var_btn_frame,
            text="Delete",
            command=self.delete_variable).pack(
            side=tk.LEFT,
            padx=5)

        # Populate listboxes with current configuration data
        self.refresh_categories()
        self.refresh_variables()

    def show_view(self, view_frame: tk.Frame):
        """
        Switch to a different view frame.

        This method implements the view switching system by hiding the current
        view and showing the specified view frame. It's the core of the
        navigation system between list and form views.

        Args:
            view_frame: The frame to display as the new current view
        """
        # Hide the currently active view if one exists
        if self.current_view:
            self.current_view.pack_forget()

        # Set and display the new view
        self.current_view = view_frame
        self.current_view.pack(fill=tk.BOTH, expand=True)

    def show_list_view(self):
        """
        Switch back to the main list view.

        This method handles returning to the main configuration screen from
        any form view. It properly cleans up form views by destroying them
        to prevent memory leaks and interface conflicts.
        """
        # Clean up any existing form view to prevent memory leaks
        if hasattr(self, "form_view_frame"):
            self.form_view_frame.destroy()
            del self.form_view_frame

        self.show_view(self.list_view_frame)

    def on_closing(self):
        """
        Handle window closing event with proper cleanup.

        Ensures that any running monitoring process is properly terminated
        before the application exits. This prevents orphaned processes
        that would continue running after the GUI is closed.
        """
        if self.monitor_process and self.monitor_process.poll() is None:
            self.stop_monitoring()

        self.destroy()

    def toggle_monitoring(self):
        """
        Toggle the file monitoring service on/off.

        This method checks the current state of the monitoring process
        and either starts or stops it accordingly. The button text and
        status display are updated to reflect the current state.
        """
        is_running = self.monitor_process and self.monitor_process.poll() is None

        if not is_running:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """
        Start the file monitoring service in a separate process.

        This method validates the configuration, creates the monitored folder
        if needed, and launches the monitoring service as a subprocess. It
        provides user feedback and updates the UI to reflect the new state.

        The monitoring runs as a separate process to avoid blocking the GUI
        and to allow the user to continue configuring while monitoring runs.
        """
        if self.watched_folder == "SELECT FOLDER" or not self.watched_folder:
            messagebox.showwarning(
                "No Folder Selected",
                "Please select a folder to monitor before starting.",
            )
            return

        folder_path = Path(self.watched_folder)
        if not folder_path.exists():
            result = messagebox.askyesno(
                "Folder Not Found",
                f"The folder '{folder_path}' does not exist. Create it?",
            )
            if result:
                folder_path.mkdir(parents=True, exist_ok=True)
            else:
                return

        try:
            # Use sys.executable to ensure compatibility with virtual
            # environments
            main_script_path = Path(
                __file__).resolve().parent.parent / "main.py"

            self.monitor_process = subprocess.Popen(
                [sys.executable, str(main_script_path), "monitor"]
            )

            self.status_label.config(text="Running", fg="green")
            self.monitor_button.config(text="Stop Monitoring", bg="red")

            messagebox.showinfo(
                "Monitoring Started",
                f"File monitoring started for folder:\n"
                f"{self.watched_folder}",
            )

        except Exception as e:
            messagebox.showerror(
                "Failed to Start",
                f"Could not start the monitoring process:\n{e}")
            # Reset UI to stopped state
            self.status_label.config(text="Error", fg="red")
            self.monitor_button.config(text="Start Monitoring", bg="green")

    def stop_monitoring(self):
        """
        Stop the file monitoring service.

        This method gracefully terminates the monitoring process, first
        attempting a normal termination and falling back to force kill
        if necessary. It updates the UI and provides user feedback.
        """
        if self.monitor_process and self.monitor_process.poll() is None:
            # Attempt graceful termination, force kill if needed
            self.monitor_process.terminate()
            try:
                self.monitor_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.monitor_process.kill()
                self.monitor_process.wait()

        self.monitor_process = None
        self.status_label.config(text="Stopped", fg="red")
        self.monitor_button.config(text="Start Monitoring", bg="green")
        messagebox.showinfo(
            "Monitoring Stopped",
            "File monitoring has been stopped.")

    def browse_folder(self):
        """
        Open folder selection dialog and update configuration.

        This method provides a user-friendly way to select the monitored
        folder using the system's native folder browser. It automatically
        saves the configuration after selection.
        """
        folder_selected = filedialog.askdirectory()

        if folder_selected:
            self.folder_var.set(folder_selected)
            self.watched_folder = self.folder_var.get().strip()
            save_config_from_parts(
                self.watched_folder,
                self.enable_organization,
                self.categories,
                self.variables,
            )
            messagebox.showinfo(
                "Config Saved",
                "Watched folder saved successfully.")

    def on_organization_toggle(self):
        """
        Handle changes to the organization toggle checkbox.

        This method updates the enable_organization setting and saves
        the configuration when the user toggles the organization feature.
        It provides immediate feedback about the setting change.
        """
        self.enable_organization = self.org_var.get()
        save_config_from_parts(
            self.watched_folder,
            self.enable_organization,
            self.categories,
            self.variables,
        )

        status = "enabled" if self.enable_organization else "disabled (rename only)"
        messagebox.showinfo(
            "Organization Setting Updated",
            f"File organization is now {status}.")

    def prompt_folder_selection(self):
        """
        Prompt user to select a folder if none is currently configured.

        This method is called during initialization to ensure the user
        has a valid folder configured before they can start monitoring.
        It provides a clear explanation and optional selection process.
        """
        result = messagebox.askyesno(
            "Select Folder",
            "No folder is currently selected for monitoring. "
            "Would you like to select a folder now?",
        )
        if result:
            self.browse_folder()

    def refresh_categories(self):
        """
        Refresh the categories listbox with current configuration data.

        This method updates the categories display to reflect any changes
        made to the configuration. It's called after add/edit/delete
        operations to keep the UI synchronized.
        """
        # Clear the existing list
        self.cat_listbox.delete(0, tk.END)

        # Populate with current categories
        for cat_name in self.categories:
            self.cat_listbox.insert(tk.END, cat_name)

    def add_category(self):
        """
        Show the form to add a new category.

        Switches to the category form view in add mode, allowing the user
        to create a new category with custom naming patterns and descriptions.
        """
        self.show_category_form()

    def edit_category(self):
        """
        Show the form to edit the selected category.

        Validates that a category is selected, prevents editing of the
        protected "General" category, and switches to the category form
        view in edit mode with the current category data pre-filled.
        """
        # Get the selected category index
        index = self.cat_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a category to edit.")
            return

        idx = index[0]
        cat_names = list(self.categories.keys())
        current_name = cat_names[idx]
        current = {"name": current_name, **self.categories[current_name]}

        # Prevent editing the required "General" category
        # This category is essential for the application's fallback behavior
        if current["name"] == "General":
            messagebox.showwarning(
                "Protected Item",
                "The 'General' category cannot be edited as it's required "
                "for the application to function properly.",
            )
            return

        # Show the form with current category data
        self.show_category_form(current, idx)

    def delete_category(self):
        """
        Delete the selected category from the configuration.

        Validates selection, prevents deletion of the protected "General"
        category, and removes the selected category from the configuration.
        Updates the display and saves the configuration automatically.
        """
        # Get the selected category index
        index = self.cat_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a category to delete.")
            return

        idx = index[0]
        cat_names = list(self.categories.keys())
        current_name = cat_names[idx]

        # Prevent deletion of the required "General" category
        if current_name == "General":
            messagebox.showwarning(
                "Protected Item",
                "The 'General' category cannot be deleted as it's required "
                "for the application to function properly.",
            )
            return

        # Remove the category and update the display
        del self.categories[current_name]
        self.refresh_categories()
        save_config_from_parts(
            self.watched_folder,
            self.enable_organization,
            self.categories,
            self.variables,
        )

    def show_category_form(
        self, cat: Dict[str, str] | None = None, index: int | None = None
    ):
        """
        Display the form for adding or editing a category.

        This method creates a comprehensive form interface for category
        management, including syntax highlighting for naming patterns,
        variable insertion helpers, and real-time preview capabilities.

        Args:
            cat: Existing category data for edit mode, None for add mode
            index: Index of category being edited, None for new category

        The form includes:
        - Basic fields (name, description, naming pattern)
        - Syntax highlighting for variables in naming patterns
        - Variable list for easy insertion
        - Keyboard shortcuts and suggestions
        """
        # Create the form view frame
        self.form_view_frame = tk.Frame(self.view_container, padx=10, pady=10)
        self.show_view(self.form_view_frame)

        title = "Edit Category" if cat else "Add Category"
        tk.Label(
            self.form_view_frame,
            text=title,
            font=(
                "Helvetica",
                16)).pack(
            pady=10)

        # Main container for form fields and variable helper
        editor_frame = tk.Frame(self.form_view_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left side: form input fields
        form_fields_frame = tk.Frame(editor_frame, padx=10)
        form_fields_frame.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.N)

        fields = {
            "name": tk.StringVar(
                value=cat["name"] if cat else ""), "description": tk.StringVar(
                value=cat["description"] if cat else ""), "naming_pattern": tk.StringVar(
                value=cat["naming_pattern"] if cat else ""), }

        entry_widgets = {}

        # Create form fields dynamically
        row = 0
        for label, var in fields.items():
            tk.Label(
                form_fields_frame,
                text=label.replace(
                    "_",
                    " ").capitalize() +
                ":").grid(
                row=row,
                column=0,
                sticky=tk.W,
                pady=5)

            # Use Text widget for naming pattern (multi-line), Entry for others
            if label == "naming_pattern":
                entry = tk.Text(form_fields_frame, height=2, width=40)
                entry.insert("1.0", var.get())
            else:
                entry = tk.Entry(form_fields_frame, textvariable=var, width=40)

            entry.grid(row=row, column=1, pady=5, padx=5)
            entry_widgets[label] = entry
            row += 1

        # Configure syntax highlighting for the naming pattern field
        naming_pattern_text = entry_widgets["naming_pattern"]
        naming_pattern_text.tag_configure(
            "variable", background="#e0e0e0", relief="raised"
        )

        def update_tags():
            """
            Update syntax highlighting for variables in naming pattern.

            This function scans the naming pattern text for variable
            placeholders (e.g., {variable_name}) and applies visual
            highlighting to make them easily identifiable.
            """
            naming_pattern_text.tag_remove("variable", "1.0", tk.END)
            text = naming_pattern_text.get("1.0", tk.END)

            # Find and highlight all variable placeholders using regex
            import re

            for match in re.finditer(r"\{(\w+)\}", text):
                start = f"1.0 + {match.start()}c"
                end = f"1.0 + {match.end()}c"
                naming_pattern_text.tag_add("variable", start, end)

        update_tags()

        # Right side: available variables list for easy insertion
        variables_list_frame = tk.Frame(editor_frame, padx=10)
        variables_list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            variables_list_frame, text="Available Variables (click to insert)"
        ).pack(anchor=tk.W)

        var_listbox = tk.Listbox(variables_list_frame, height=8)
        for var_name in self.variables:
            var_listbox.insert(tk.END, var_name)
        var_listbox.pack(fill=tk.BOTH, expand=True)

        def insert_variable_at_cursor(event):
            """
            Insert selected variable at cursor position in naming pattern.

            This function handles clicks on the variables list by inserting
            the selected variable as a placeholder in the naming pattern
            field at the current cursor position.

            Args:
                event: The listbox selection event
            """
            selection = var_listbox.curselection()
            if not selection:
                return

            variable_name = var_listbox.get(selection[0])
            naming_pattern_entry = entry_widgets["naming_pattern"]
            naming_pattern_entry.insert(tk.INSERT, f"/{{{variable_name}}}")
            update_tags()

            # Return focus to the naming pattern field
            naming_pattern_entry.after(10, naming_pattern_entry.focus_set)

        var_listbox.bind("<<ListboxSelect>>", insert_variable_at_cursor)
        naming_pattern_entry = entry_widgets["naming_pattern"]

        def show_variable_suggestions(event):
            """
            Show variable suggestions when '/' is typed in naming pattern.

            This function creates a context menu with available variables
            when the user types '/' in the naming pattern field, providing
            a quick way to insert variables without using the mouse.

            Args:
                event: The key press event containing the typed character
            """
            if event.char == "/":
                cursor_pos = naming_pattern_entry.index(tk.INSERT)

                # Create popup menu with variable options
                menu = tk.Menu(self.form_view_frame, tearoff=0)
                for var_name in self.variables:
                    menu.add_command(
                        label=var_name,
                        command=lambda v=var_name: insert_variable(f"{{{v}}}"),
                    )

                # Calculate menu position relative to cursor
                x, y = (
                    naming_pattern_entry.winfo_rootx(),
                    naming_pattern_entry.winfo_rooty(),
                )
                bbox = naming_pattern_entry.bbox(cursor_pos)
                if bbox:
                    x += bbox[0]
                    y += bbox[1] + bbox[3]

                menu.post(x, y)

        def insert_variable(var_string):
            """
            Insert a variable string at the current cursor position.

            Helper function for inserting variable placeholders and
            updating syntax highlighting afterwards.

            Args:
                var_string: The variable placeholder string to insert
            """
            naming_pattern_entry.insert(tk.INSERT, var_string)
            update_tags()

        naming_pattern_entry.bind("<Key>", show_variable_suggestions)
        naming_pattern_entry.bind("<KeyRelease>", lambda e: update_tags())

        def on_save():
            """
            Save the new or edited category to configuration.

            This function validates the form data, updates the configuration,
            saves it to disk, refreshes the categories list, and returns
            to the main view.
            """
            # Extract form data into category dictionary
            new_cat = {}
            for label, var in fields.items():
                if label == "naming_pattern":
                    new_cat[label] = entry_widgets[label].get(
                        "1.0", tk.END).strip()
                else:
                    new_cat[label] = var.get()

            if not new_cat["name"]:
                messagebox.showerror(
                    "Error", "Name is required.", parent=self.form_view_frame
                )
                return

            # Update configuration based on mode (add vs edit)
            if index is not None:
                # Edit mode: update existing category
                cat_names = list(self.categories.keys())
                old_name = cat_names[index]

                # If name changed, remove old entry and add new one
                if old_name != new_cat["name"]:
                    del self.categories[old_name]

                self.categories[new_cat["name"]] = {
                    "description": new_cat["description"],
                    "naming_pattern": new_cat["naming_pattern"],
                }
            else:
                # Add mode: append new category
                self.categories[new_cat["name"]] = {
                    "description": new_cat["description"],
                    "naming_pattern": new_cat["naming_pattern"],
                }

            # Save configuration and update display
            save_config_from_parts(
                self.watched_folder,
                self.enable_organization,
                self.categories,
                self.variables,
            )
            self.refresh_categories()
            self.show_list_view()

        # === FORM BUTTONS ===
        # Save and Cancel buttons
        btn_frame = tk.Frame(self.form_view_frame)
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="Save",
            command=on_save).pack(
            side=tk.LEFT,
            padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.show_list_view).pack(
            side=tk.LEFT, padx=10
        )

    def add_variable(self):
        """
        Show the form to add a new variable.

        Switches to the variable form view in add mode, allowing the user
        to create a new variable that can be used in naming patterns.
        """
        self.show_variable_form()

    def edit_variable(self):
        """
        Show the form to edit the selected variable.

        Validates that a variable is selected, prevents editing of the
        protected "original_name" variable, and switches to the variable
        form view in edit mode with current data pre-filled.
        """
        # Get the selected variable index
        index = self.var_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a variable to edit.")
            return

        idx = index[0]
        var_names = list(self.variables.keys())
        current_name = var_names[idx]
        current = {
            "name": current_name,
            "description": self.variables[current_name]}

        # Prevent editing the required "original_name" variable
        # This variable is essential for basic filename preservation
        if current["name"] == "original_name":
            messagebox.showwarning(
                "Protected Item",
                "The 'original_name' variable cannot be edited as it's "
                "required for the application to function properly.",
            )
            return

        # Show the form with current variable data
        self.show_variable_form(current, idx)

    def delete_variable(self):
        """
        Delete the selected variable from the configuration.

        Validates selection, prevents deletion of the protected "original_name"
        variable, and removes the selected variable from the configuration.
        Updates the display and saves the configuration automatically.
        """
        # Get the selected variable index
        index = self.var_listbox.curselection()
        if not index:
            messagebox.showinfo("Info", "Select a variable to delete.")
            return

        idx = index[0]
        var_names = list(self.variables.keys())
        current_name = var_names[idx]

        # Prevent deletion of the required "original_name" variable
        if current_name == "original_name":
            messagebox.showwarning(
                "Protected Item",
                "The 'original_name' variable cannot be deleted as it's "
                "required for the application to function properly.",
            )
            return

        # Remove the variable and update the display
        del self.variables[current_name]
        self.refresh_variables()
        save_config_from_parts(
            self.watched_folder,
            self.enable_organization,
            self.categories,
            self.variables,
        )

    def show_variable_form(
        self, var: Dict[str, str] | None = None, index: int | None = None
    ):
        """
        Display the form for adding or editing a variable.

        This method creates a simple form interface for variable management
        with fields for name and description. Variables are used as
        placeholders in category naming patterns.

        Args:
            var: Existing variable data for edit mode, None for add mode
            index: Index of variable being edited, None for new variable
        """
        # Create the form view frame
        self.form_view_frame = tk.Frame(self.view_container, padx=10, pady=10)
        self.show_view(self.form_view_frame)

        # Form title based on mode
        title = "Edit Variable" if var else "Add Variable"
        tk.Label(
            self.form_view_frame,
            text=title,
            font=(
                "Helvetica",
                16)).pack(
            pady=10)

        # Create StringVar objects for form fields
        fields = {
            "name": tk.StringVar(
                value=var["name"] if var else ""), "description": tk.StringVar(
                value=var["description"] if var else ""), }

        # Form fields container
        form_fields_frame = tk.Frame(self.form_view_frame)
        form_fields_frame.pack(pady=10)

        # Create form fields dynamically
        row = 0
        for label, var_str in fields.items():
            # Create label and entry for each field
            tk.Label(form_fields_frame, text=label.capitalize() + ":").grid(
                row=row, column=0, sticky=tk.W, pady=5, padx=5
            )
            tk.Entry(form_fields_frame, textvariable=var_str, width=50).grid(
                row=row, column=1, pady=5, padx=5
            )
            row += 1

        def on_save():
            """
            Save the new or edited variable to configuration.

            This function validates the form data, updates the configuration,
            saves it to disk, refreshes the variables list, and returns
            to the main view.
            """
            # Extract form data into variable dictionary
            vals = {k: v.get().strip() for k, v in fields.items()}

            # Validate required fields
            if not vals["name"]:
                messagebox.showerror(
                    "Error", "Name is required.", parent=self.form_view_frame
                )
                return

            # Update configuration based on mode (add vs edit)
            if index is not None:
                # Edit mode: update existing variable
                var_names = list(self.variables.keys())
                old_name = var_names[index]

                # If name changed, remove old entry
                if old_name != vals["name"]:
                    del self.variables[old_name]

                self.variables[vals["name"]] = vals["description"]
            else:
                # Add mode: append new variable
                self.variables[vals["name"]] = vals["description"]

            # Save configuration and update display
            save_config_from_parts(
                self.watched_folder,
                self.enable_organization,
                self.categories,
                self.variables,
            )
            self.refresh_variables()
            self.show_list_view()

        # === FORM BUTTONS ===
        # Save and Cancel buttons
        btn_frame = tk.Frame(self.form_view_frame)
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="Save",
            command=on_save).pack(
            side=tk.LEFT,
            padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.show_list_view).pack(
            side=tk.LEFT, padx=10
        )

    def refresh_variables(self):
        """
        Refresh the variables listbox with current configuration data.

        This method updates the variables display to reflect any changes
        made to the configuration. It's called after add/edit/delete
        operations to keep the UI synchronized.
        """
        # Clear the existing list
        self.var_listbox.delete(0, tk.END)

        # Populate with current variables
        for var_name in self.variables:
            self.var_listbox.insert(tk.END, var_name)


def main():
    """
    Main entry point for the GUI application.

    Creates and runs the ConfigGUI application. This function is called
    when the GUI is launched either directly or through the main.py
    entry point with the 'gui' command.

    The function starts the tkinter main loop, which handles all GUI
    events and user interactions until the application is closed.
    """
    # Create and start the GUI application
    app = ConfigGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
