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
from typing import List

from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from watchdog.observers import Observer

from config_manager import load_config
from text_extractor import extract_text_from_pdf, extract_text_from_docx
from ai_processor import get_ai_filename_suggestion

logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(levelname)s - %(message)s")
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

    def __init__(self, config):
        """
        Initialize the document handler with configuration.
        
        Args:
            config: Configuration dictionary containing categories, variables,
                   and watched folder information
        """
        super().__init__()
        self.config = config

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
        # Retry configuration - files may be temporarily locked after creation/download
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Extract text based on file type
                if filepath.suffix.lower() == ".pdf":
                    document_text = extract_text_from_pdf(filepath)
                else:  # .docx
                    document_text = extract_text_from_docx(filepath)

                # Get AI-powered categorization and naming suggestion
                category, suggested_name = get_ai_filename_suggestion(
                    document_text, 
                    self.config["categories"], 
                    self.config.get("variables", []))
                    
                logger.info(f"AI suggestion: category='{category}', "
                           f"name='{suggested_name}'")

                # Prepare target location for the organized file
                base_folder = Path(self.config["watched_folder"])
                category_folder = ensure_category_folder(base_folder, category)

                # Construct new filename, preserving original extension
                suggested_filename = f"{suggested_name}{filepath.suffix.lower()}"
                dest_path = category_folder / suggested_filename

                # Handle naming conflicts by appending sequential numbers
                counter = 1
                while dest_path.exists():
                    dest_path = category_folder / (
                        f"{suggested_name}_{counter}{filepath.suffix.lower()}")
                    counter += 1

                shutil.move(str(filepath), dest_path)
                logger.info(f"Moved '{filepath.name}' to "
                           f"'{dest_path.relative_to(base_folder)}'")
                           
                return  # Success - exit retry loop
                
            except PermissionError as exc:
                # Handle permission/access errors with retry logic
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Permission denied for '{filepath.name}' "
                        f"(attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(
                        f"Failed to process file '{filepath}' "
                        f"after {max_retries} attempts: {exc}")
                        
            except Exception as exc:
                # Handle all other errors - don't retry as they're unlikely to resolve
                logger.error(f"Failed to process file '{filepath}': {exc}")
                break


def start_observer(config):
    """
    Start the file system observer for monitoring the configured folder.
    
    This function sets up and starts the watchdog observer that monitors
    the specified directory for file changes. It validates the configuration
    and creates the watch folder if needed.
    
    Args:
        config: Configuration dictionary with watched_folder and other settings
        
    Returns:
        Observer: The started watchdog observer instance
        
    Raises:
        ValueError: If watched_folder is not configured or doesn't exist
    """
    watched_folder = config.get("watched_folder")
    if not watched_folder or watched_folder == "SELECT FOLDER":
        raise ValueError("No watched folder configured. Please set up configuration first.")
    
    folder_path = Path(watched_folder)
    if not folder_path.exists():
        # Create the folder if it doesn't exist
        folder_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created watched folder: {folder_path}")

    # Set up and start the file system observer
    event_handler = DocumentHandler(config)
    observer = Observer()
    observer.schedule(event_handler, str(folder_path), recursive=False)
    observer.start()
    
    logger.info(f"Started monitoring: {folder_path}")
    logger.info(f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}")
    
    return observer


__all__ = ["start_observer", "SUPPORTED_EXTENSIONS"] 