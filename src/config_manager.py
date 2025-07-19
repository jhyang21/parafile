"""
Configuration management module for the Parafile application.

This module handles all aspects of configuration management including:
- Loading configuration from JSON file
- Saving configuration with proper formatting
- Validating configuration structure
- Ensuring required default items exist
- Creating default configuration when needed

The configuration includes:
- watched_folder: Directory path to monitor for new files
- categories: User-defined document categories with naming patterns
- variables: Placeholder variables for use in naming patterns

The module ensures data integrity by validating and auto-repairing
configuration files that may be missing required elements.
"""
import json
from pathlib import Path
from typing import Any, Dict

# Configuration file location relative to the project root
# Using pathlib for cross-platform path handling
CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"

# Default configuration structure used when creating new config files
# or when repairing corrupted/incomplete configurations
DEFAULT_CONFIG = {
    "watched_folder": "SELECT FOLDER",  # Placeholder indicating no folder selected
    "categories": [
        {
            "name": "General",
            "naming_pattern": "{original_name}",  # Preserves original filename
            "description": "Default category when no other rules match."
        }
    ],
    "variables": [
        {
            "name": "original_name",
            "description": "The original filename without extension."
        }
    ]
}


def load_config() -> Dict[str, Any]:
    """
    Load configuration from the JSON file with validation and auto-repair.

    This function implements a robust configuration loading system that:
    1. Creates default config if file doesn't exist
    2. Validates and repairs corrupted files
    3. Ensures required categories and variables are present
    4. Auto-saves repaired configurations
    
    Returns:
        Dict[str, Any]: Complete configuration dictionary with all required fields
        
    Note:
        This function never raises exceptions. It will always return a valid
        configuration, creating or repairing files as needed. This ensures
        the application can always start successfully.
    """
    # Check if configuration file exists
    if not CONFIG_FILE.exists():
        # Create new configuration with default values
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        # Attempt to load and parse the configuration file
        with CONFIG_FILE.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except (json.JSONDecodeError, OSError):
        # Handle corrupted or unreadable configuration files
        # Reset to default configuration to ensure application stability
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    # Validate and repair configuration structure
    # Track if any repairs were made to determine if we need to save
    updated = False
    
    # Ensure all required top-level keys exist
    for key, default_val in DEFAULT_CONFIG.items():
        if key not in data:
            data[key] = default_val
            updated = True
    
    # Validate categories section
    if "categories" in data:
        # Ensure the required "General" category exists
        # This category serves as a fallback when AI can't categorize documents
        has_general = any(cat.get("name") == "General" 
                         for cat in data["categories"])
        if not has_general:
            # Create the General category with safe defaults
            general_category = {
                "name": "General",
                "naming_pattern": "{original_name}",
                "description": "Default category when no other rules match."
            }
            data["categories"].append(general_category)
            updated = True
    
    # Validate variables section
    if "variables" in data:
        # Ensure the required "original_name" variable exists
        # This variable is essential for basic filename preservation
        has_original_name = any(var.get("name") == "original_name" 
                               for var in data["variables"])
        if not has_original_name:
            # Create the original_name variable
            original_name_var = {
                "name": "original_name",
                "description": "The original filename without extension."
            }
            data["variables"].append(original_name_var)
            updated = True
    
    # Save the configuration if any repairs were made
    if updated:
        save_config(data)
        
    return data


def save_config(config: Dict[str, Any]) -> None:
    """
    Save the given config dictionary to the JSON file in a human-readable format.
    
    The configuration is saved with proper indentation and UTF-8 encoding
    to ensure it's readable by both the application and human collaborators
    who may need to manually edit the configuration.
    
    Args:
        config: Complete configuration dictionary to save
        
    Raises:
        RuntimeError: If the file cannot be written (permissions, disk space, etc.)
        
    Note:
        The function uses ensure_ascii=False to properly handle international
        characters in folder paths and category names.
    """
    try:
        # Write configuration with human-readable formatting
        # indent=2 provides good readability without excessive spacing
        # ensure_ascii=False allows proper Unicode character handling
        with CONFIG_FILE.open("w", encoding="utf-8") as fp:
            json.dump(config, fp, indent=2, ensure_ascii=False)
    except OSError as exc:
        # Provide a more descriptive error message for troubleshooting
        raise RuntimeError(f"Failed to write configuration file: {exc}")


# Define the public API of this module
# These are the main functions and constants that other modules should use
__all__ = ["load_config", "save_config", "CONFIG_FILE"] 