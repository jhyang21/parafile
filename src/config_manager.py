import json
from pathlib import Path
from typing import Any, Dict


CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"

# Default structure used when config.json does not yet exist.
DEFAULT_CONFIG = {
    "watched_folder": "SELECT FOLDER",
    "categories": [
        {
            "name": "General",
            "naming_pattern": "{original_name}",
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
    """Load configuration from the JSON file.

    Returns a dictionary with the configuration. If the file does not exist
    or is malformed, it will be created/reset with the default structure.
    """
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except (json.JSONDecodeError, OSError):
        # Reset corrupted config file to default
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    # Ensure both categories and variables keys exist
    updated = False
    for key, default_val in DEFAULT_CONFIG.items():
        if key not in data:
            data[key] = default_val
            updated = True
    
    # Ensure required "General" category exists
    if "categories" in data:
        has_general = any(cat.get("name") == "General" for cat in data["categories"])
        if not has_general:
            general_category = {
                "name": "General",
                "naming_pattern": "{original_name}",
                "description": "Default category when no other rules match."
            }
            data["categories"].append(general_category)
            updated = True
    
    # Ensure required "original_name" variable exists
    if "variables" in data:
        has_original_name = any(var.get("name") == "original_name" for var in data["variables"])
        if not has_original_name:
            original_name_var = {
                "name": "original_name",
                "description": "The original filename without extension."
            }
            data["variables"].append(original_name_var)
            updated = True
    
    if updated:
        save_config(data)
    return data


def save_config(config: Dict[str, Any]) -> None:
    """Save the given config dictionary to the JSON file in a human-readable format."""
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as fp:
            json.dump(config, fp, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RuntimeError(f"Failed to write configuration file: {exc}")


__all__ = ["load_config", "save_config", "CONFIG_FILE"] 