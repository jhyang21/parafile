"""
File organization module for the Parafile application.

This module handles the core file monitoring and organization functionality:
- Monitors specified directories for new files using watchdog
- Extracts text content from supported document formats
- Uses AI processing to categorize and rename files
- Organizes files into category-based folder structures
- Implements robust error handling and retry mechanisms

The module runs as a background service, continuously monitoring for new
files and automatically processing them according to user configuration.
Supports both file creation and move events to handle various file
delivery scenarios.
"""

import logging
import shutil
import time
from pathlib import Path
from typing import Dict, List

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ai_processor import categorize_document, generate_ai_filename, get_naming_pattern
from config_manager import load_config
from text_extractor import extract_text_from_docx, extract_text_from_pdf

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: List[str] = [".pdf", ".docx"]


def ensure_category_folder(base_folder: Path, category_name: str) -> Path:
    """
    Create (if necessary) and return the path to the category subfolder.

    Args:
        base_folder: The root monitored directory
        category_name: Name of the category (used as folder name)

    Returns:
        Path: Full path to the category folder
    """
    category_folder = base_folder / category_name
    category_folder.mkdir(parents=True, exist_ok=True)
    return category_folder


class DocumentHandler(FileSystemEventHandler):
    """
    Watchdog event handler that processes new files in the monitored directory.

    This class extends FileSystemEventHandler to respond to file system events.
    It specifically handles file creation and move events, filtering for
    supported document types and processing them through the AI pipeline.

    The handler implements robust error handling and retry logic to deal with
    common file access issues like temporary locks or permission problems.
    """

    def __init__(
        self,
        watched_folder: str,
        enable_organization: bool,
        categories: Dict[str, Dict[str, str]],
        variables: Dict[str, str],
    ):
        """
        Initialize the document handler with configuration.

        Args:
            watched_folder: Path to the monitored folder
            enable_organization: Whether to organize files into category folders
            categories: Categories dict with name as key
            variables: Variables dict with name as key
        """
        super().__init__()
        self.watched_folder = watched_folder
        self.enable_organization = enable_organization
        self.categories = categories
        self.variables = variables

    def on_created(self, event: FileCreatedEvent):
        """
        Handle file creation events in the monitored directory.

        Args:
            event: File creation event from watchdog
        """
        # Skip directory events and unsupported file types
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        logger.info(f"New file detected: {filepath.name}")
        self.process_file(filepath)

    def on_moved(self, event):
        """
        Handle file move events (common with downloads and email attachments).

        Args:
            event: File move event from watchdog
        """
        # Skip directory events and unsupported file types
        if event.is_directory:
            return

        filepath = Path(event.dest_path)
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        logger.info(f"File moved into folder: {filepath.name}")
        self.process_file(filepath)

    def process_file(self, filepath: Path):
        """
        Process a new file by extracting text and organizing it.

        This method orchestrates the complete file processing pipeline:
        1. Extracts text content using appropriate extractor
        2. Sends text to AI for categorization and naming
        3. Creates category folder if needed
        4. Moves file to appropriate location with new name
        5. Handles naming conflicts by appending counters

        Args:
            filepath: Path to the file to be processed

        Note:
            Implements retry logic for file access issues and comprehensive
            error handling to prevent crashes from corrupted files or
            temporary access problems.
        """
        # Retry configuration - files may be temporarily locked after
        # creation/download
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Extract text based on file type
                if filepath.suffix.lower() == ".pdf":
                    document_text = extract_text_from_pdf(filepath)
                else:  # .docx
                    document_text = extract_text_from_docx(filepath)

                # Step 1: Categorize the document using AI
                categorization_result = categorize_document(
                    document_text, self.categories
                )
                category = categorization_result["category"]

                logger.info(
                    f"AI categorization: category='{category}', "
                    f"confidence={categorization_result['confidence']}%"
                )

                # Step 2: Get the naming pattern for this category
                naming_pattern = get_naming_pattern(category, self.categories)
                if not naming_pattern:
                    logger.warning(
                        f"No naming pattern found for category '{category}', "
                        f"using default"
                    )
                    suggested_name = "unnamed_file"
                else:
                    # Step 3: Generate the AI-powered filename using the naming
                    # pattern
                    category_description = self.categories[category]["description"]
                    suggested_name = generate_ai_filename(
                        document_text=document_text,
                        category=category,
                        category_description=category_description,
                        naming_pattern=naming_pattern,
                        variables=self.variables,
                    )

                logger.info(f"AI filename generation: name='{suggested_name}'")

                # Prepare target location for the organized file
                base_folder = Path(self.watched_folder)

                # Determine destination folder based on organization setting
                if self.enable_organization:
                    # Organize into category-specific subfolder
                    destination_folder = ensure_category_folder(
                        base_folder, category)
                    logger.info(
                        f"Organization enabled: placing in '{category}' folder")
                else:
                    # Keep in the watched folder, just rename
                    destination_folder = base_folder
                    logger.info(
                        "Organization disabled: keeping in watched folder")

                # Construct new filename, preserving original extension
                suggested_filename = f"{suggested_name}{filepath.suffix.lower()}"
                dest_path = destination_folder / suggested_filename

                # Handle naming conflicts by appending sequential numbers
                counter = 1
                while dest_path.exists():
                    dest_path = destination_folder / (
                        f"{suggested_name}_{counter}{filepath.suffix.lower()}"
                    )
                    counter += 1

                shutil.move(str(filepath), dest_path)
                logger.info(
                    f"Moved '{filepath.name}' to "
                    f"'{dest_path.relative_to(base_folder)}'"
                )

                return  # Success - exit retry loop

            except PermissionError as exc:
                # Handle permission/access errors with retry logic
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Permission denied for '{filepath.name}' "
                        f"(attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(
                        f"Failed to process file '{filepath}' "
                        f"after {max_retries} attempts: {exc}"
                    )

            except Exception as exc:
                # Handle all other errors - don't retry as they're unlikely to
                # resolve
                logger.error(f"Failed to process file '{filepath}': {exc}")
                break


def start_observer(
    watched_folder: str = None,
    enable_organization: bool = None,
    categories: Dict[str, Dict[str, str]] = None,
    variables: Dict[str, str] = None,
):
    """
    Start the file system observer for monitoring the configured folder.

    This function sets up and starts the watchdog observer that monitors
    the specified directory for file changes. It validates the configuration
    and creates the watch folder if needed.

    Args:
        watched_folder: Path to the monitored folder (optional, loads from config if None)
        enable_organization: Whether to organize files into category folders (optional, loads from config if None)
        categories: Categories dict with name as key (optional, loads from config if None)
        variables: Variables dict with name as key (optional, loads from config if None)

    Returns:
        Observer: The started watchdog observer instance

    Raises:
        ValueError: If watched_folder is not configured or doesn't exist
    """
    # Load configuration if not provided
    if (
        watched_folder is None
        or enable_organization is None
        or categories is None
        or variables is None
    ):
        watched_folder, enable_organization, categories, variables = load_config()

    if not watched_folder or watched_folder == "SELECT FOLDER":
        raise ValueError(
            "No watched folder configured. Please set up configuration first."
        )

    folder_path = Path(watched_folder)
    if not folder_path.exists():
        # Create the folder if it doesn't exist
        folder_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created watched folder: {folder_path}")

    # Set up and start the file system observer
    event_handler = DocumentHandler(
        watched_folder, enable_organization, categories, variables
    )
    observer = Observer()
    observer.schedule(event_handler, str(folder_path), recursive=False)
    observer.start()

    logger.info(f"Started monitoring: {folder_path}")
    logger.info(
        f"Organization mode: {'enabled' if enable_organization else 'disabled (rename only)'}"
    )
    logger.info(f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}")

    return observer


def main():
    """
    Main entry point for the file organizer service.

    Loads configuration and starts the file monitoring system. This function
    is called when the organizer is launched in monitor mode from main.py.
    """
    try:
        # Load configuration
        watched_folder, enable_organization, categories, variables = load_config()

        # Start the monitoring service
        observer = start_observer(
            watched_folder, enable_organization, categories, variables
        )

        # Keep the process running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logger.info("Stopping observer...")
        observer.stop()

    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        print(f"ERROR: {e}")
        print("Please run 'python main.py gui' to configure the application.")
        return

    # Wait for observer thread to finish cleanup
    observer.join()


__all__ = ["start_observer", "SUPPORTED_EXTENSIONS", "main"]
