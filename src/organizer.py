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

# Configure logging for the organizer module
# Provides timestamped logs for monitoring and debugging
logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Define supported file extensions for processing
# Only files with these extensions will be monitored and processed
SUPPORTED_EXTENSIONS: List[str] = [".pdf", ".docx"]


def ensure_category_folder(base_folder: Path, category_name: str) -> Path:
    """
    Create (if necessary) and return the path to the category subfolder.
    
    This function ensures that the category folder structure exists within
    the monitored directory. Each category gets its own subfolder to keep
    organized files properly separated.
    
    Args:
        base_folder: The root monitored directory
        category_name: Name of the category (used as folder name)
        
    Returns:
        Path: Full path to the category folder
        
    Note:
        This function is safe to call multiple times - it won't raise errors
        if the folder already exists. Parent directories are also created
        if needed.
    """
    # Create the category subfolder path
    category_folder = base_folder / category_name
    
    # Create the folder and any necessary parent directories
    # exist_ok=True prevents errors if folder already exists
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
        
        This method is called whenever a new file is created in the watched
        folder. It filters for supported file types and processes them.
        
        Args:
            event: FileCreatedEvent containing information about the new file
            
        Note:
            Directory creation events are ignored. Only regular files with
            supported extensions are processed.
        """
        # Ignore directory creation events
        if event.is_directory:
            return

        # Convert event path to Path object for easier handling
        filepath = Path(event.src_path)
        
        # Check if the file has a supported extension
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        # Log the detection and process the file
        logger.info(f"New file detected: {filepath.name}")
        self.process_file(filepath)

    def on_moved(self, event):
        """
        Handle file move events into the monitored directory.
        
        This method captures files that are moved into the monitored directory
        from elsewhere. This is common when files are downloaded or copied
        from other locations.
        
        Args:
            event: FileMovedEvent containing source and destination paths
            
        Note:
            Only processes the destination (final) location of moved files.
        """
        # Ignore directory move events
        if event.is_directory:
            return

        # Process the destination path where the file was moved to
        filepath = Path(event.dest_path)
        
        # Check if the moved file has a supported extension
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        # Log the detection and process the file
        logger.info(f"New file moved into directory: {filepath.name}")
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
        # Configuration for retry mechanism
        # Files may be temporarily locked after creation/download
        max_retries = 3
        retry_delay = 2  # seconds between retries
        
        # Retry loop to handle temporary file access issues
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

                # Construct the new filename, preserving the original extension
                # This ensures files remain openable by their original applications
                suggested_filename = f"{suggested_name}{filepath.suffix.lower()}"
                dest_path = category_folder / suggested_filename

                # Handle naming conflicts by appending sequential numbers
                # This prevents overwriting existing files with similar names
                counter = 1
                while dest_path.exists():
                    # Create a new filename with counter suffix
                    dest_path = category_folder / (
                        f"{suggested_name}_{counter}{filepath.suffix.lower()}")
                    counter += 1

                # Move the file to its new organized location
                shutil.move(str(filepath), dest_path)
                
                # Log the successful organization with relative path for clarity
                logger.info(f"Moved '{filepath.name}' to "
                           f"'{dest_path.relative_to(base_folder)}'")
                           
                return  # Success - exit the retry loop
                
            except PermissionError as exc:
                # Handle permission/access errors with retry logic
                if attempt < max_retries - 1:
                    # Log warning and retry
                    logger.warning(
                        f"Permission denied for '{filepath.name}' "
                        f"(attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed - log error and give up
                    logger.error(
                        f"Failed to process file '{filepath}' "
                        f"after {max_retries} attempts: {exc}")
                        
            except Exception as exc:
                # Handle all other errors (corrupted files, AI errors, etc.)
                # Don't retry for these types of errors as they're unlikely to resolve
                logger.error(f"Failed to process file '{filepath}': {exc}")
                break  # Exit retry loop immediately


def start_observer(config):
    """
    Start the file system observer for monitoring the configured folder.
    
    This function sets up and starts the watchdog observer that monitors
    the specified directory for file changes. It validates the configuration
    and creates the watch folder if needed.
    
    Args:
        config: Configuration dictionary containing watched_folder and other settings
        
    Note:
        This function runs indefinitely until interrupted (Ctrl+C). It's designed
        to be the main loop for the monitoring service.
    """
    # Get the folder path from configuration
    watched_folder_path = config["watched_folder"]
    
    # Validate that a folder has been selected
    if watched_folder_path == "SELECT FOLDER":
        logger.error("No folder selected for monitoring. "
                    "Please run the GUI and select a folder first.")
        print("ERROR: No folder selected for monitoring.")
        print("Please run 'python main.py gui' and select a folder to monitor.")
        return
    
    # Convert to Path object and validate/create the folder
    watched_folder = Path(watched_folder_path)
    if not watched_folder.exists():
        logger.warning(f"Watched folder does not exist: {watched_folder}. "
                      f"Creating it.")
        # Create the folder and any necessary parent directories
        watched_folder.mkdir(parents=True)

    # Set up the file system observer
    event_handler = DocumentHandler(config)
    observer = Observer()
    
    # Schedule monitoring of the target folder
    # recursive=False means we only watch the root folder, not subfolders
    # This prevents processing files that have already been organized
    observer.schedule(event_handler, str(watched_folder), recursive=False)
    
    # Start the observer thread
    observer.start()

    logger.info(f"Started monitoring '{watched_folder}' for new documents...")
    
    try:
        # Main monitoring loop - keep the process alive
        # The observer runs in a separate thread, so we just need to prevent exit
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logger.info("Stopping observer...")
        observer.stop()
        
    # Wait for observer thread to finish cleanup
    observer.join()


def main():
    """
    Main entry point for the file organizer service.
    
    Loads configuration and starts the file monitoring system. This function
    is called when the organizer is launched in monitor mode.
    """
    # Load the current configuration
    config = load_config()
    
    # Start the monitoring service
    start_observer(config)


if __name__ == "__main__":
    main() 