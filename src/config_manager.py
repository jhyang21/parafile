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
from typing import Any, Dict, Tuple

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"

# Default configuration structure used when creating new config files
# or when repairing corrupted/incomplete configurations
DEFAULT_CONFIG = {
    "watched_folder": "SELECT FOLDER",
    "enable_organization": True,
    "categories": [
        {
            "name": "General",
            "naming_pattern": "{original_name}",
            "description": "Default category when no other rules match.",
        }
    ],
    "variables": [
        {
            "name": "original_name",
            "description": "The original filename without extension.",
        }
    ],
}


def load_config() -> Tuple[str, bool,
                           Dict[str, Dict[str, str]], Dict[str, str]]:
    """
    Load configuration from the JSON file with validation and auto-repair.

    This function implements a robust configuration loading system that:
    1. Creates default config if file doesn't exist
    2. Validates and repairs corrupted files
    3. Ensures required categories and variables are present
    4. Auto-saves repaired configurations

    Returns:
        Tuple containing:
        - watched_folder_location (str): Path to the monitored folder
        - enable_organization (bool): Whether to organize files into category folders
        - categories (Dict[str, Dict[str, str]]): Categories with name as key,
          value contains description and naming_pattern
        - variables (Dict[str, str]): Variables with name as key, description as value

    Note:
        This function never raises exceptions. It will always return valid
        configuration data, creating or repairing files as needed.
    """
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return _transform_config(DEFAULT_CONFIG)

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except (json.JSONDecodeError, OSError):
        # Reset to default configuration for corrupted or unreadable files
        save_config(DEFAULT_CONFIG)
        return _transform_config(DEFAULT_CONFIG)

    # Validate and repair configuration structure
    updated = False

    # Ensure all required top-level keys exist
    for key, default_val in DEFAULT_CONFIG.items():
        if key not in data:
            data[key] = default_val
            updated = True

    # Ensure the required "General" category exists as fallback
    if "categories" in data:
        has_general = any(
            cat.get("name") == "General" for cat in data["categories"])
        if not has_general:
            general_category = {
                "name": "General",
                "naming_pattern": "{original_name}",
                "description": "Default category when no other rules match.",
            }
            data["categories"].append(general_category)
            updated = True

    # Ensure the required "original_name" variable exists for basic filename
    # preservation
    if "variables" in data:
        has_original_name = any(
            var.get("name") == "original_name" for var in data["variables"]
        )
        if not has_original_name:
            original_name_var = {
                "name": "original_name",
                "description": "The original filename without extension.",
            }
            data["variables"].append(original_name_var)
            updated = True

    if updated:
        save_config(data)

    return _transform_config(data)


def _transform_config(
    data: Dict[str, Any],
) -> Tuple[str, bool, Dict[str, Dict[str, str]], Dict[str, str]]:
    """
    Transform the raw configuration data into the desired return format.

    Args:
        data: Raw configuration dictionary from JSON

    Returns:
        Tuple of (watched_folder, enable_organization, categories_dict, variables_dict)
    """
    watched_folder = data.get("watched_folder", "SELECT FOLDER")
    enable_organization = data.get("enable_organization", True)

    # Transform categories list into dict with name as key
    categories = {}
    for cat in data.get("categories", []):
        categories[cat["name"]] = {
            "description": cat["description"],
            "naming_pattern": cat["naming_pattern"],
        }

    # Transform variables list into dict with name as key
    variables = {}
    for var in data.get("variables", []):
        variables[var["name"]] = var["description"]

    return watched_folder, enable_organization, categories, variables


def save_config(config: Dict[str, Any]) -> None:
    """
    Save the given config dictionary to the JSON file in a human-readable format.

    Args:
        config: Complete configuration dictionary to save

    Raises:
        RuntimeError: If the file cannot be written (permissions, disk space, etc.)
    """
    try:
        # Write with formatting for human readability and proper Unicode
        # handling
        with CONFIG_FILE.open("w", encoding="utf-8") as fp:
            json.dump(config, fp, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RuntimeError(f"Failed to write configuration file: {exc}")


def save_config_from_parts(
    watched_folder: str,
    enable_organization: bool,
    categories: Dict[str, Dict[str, str]],
    variables: Dict[str, str],
) -> None:
    """
    Save configuration from the parts format back to JSON file.

    Args:
        watched_folder: Path to the monitored folder
        enable_organization: Whether to organize files into category folders
        categories: Categories dict with name as key
        variables: Variables dict with name as key
    """
    # Convert back to the original format
    config = {
        "watched_folder": watched_folder,
        "enable_organization": enable_organization,
        "categories": [
            {
                "name": name,
                "description": details["description"],
                "naming_pattern": details["naming_pattern"],
            }
            for name, details in categories.items()
        ],
        "variables": [],
    }

    # Build variables list (no type information)
    for name, description in variables.items():
        var_entry = {"name": name, "description": description}
        config["variables"].append(var_entry)

    save_config(config)


__all__ = [
    "load_config",
    "save_config",
    "save_config_from_parts",
    "CONFIG_FILE"]
