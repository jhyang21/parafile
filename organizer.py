import logging
import shutil
import time
from pathlib import Path
from typing import List

from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from watchdog.observers import Observer

from config_manager import load_config
from text_extractor import extract_text_from_pdf, extract_text_from_docx
from ai_processor import get_ai_suggestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS: List[str] = [".pdf", ".docx"]


def ensure_category_folder(base_folder: Path, category_name: str) -> Path:
    """Create (if necessary) and return the path to the category subfolder."""
    category_folder = base_folder / category_name
    category_folder.mkdir(parents=True, exist_ok=True)
    return category_folder


class DocumentHandler(FileSystemEventHandler):
    """Watchdog event handler that processes new files."""

    def __init__(self, config):
        super().__init__()
        self.config = config

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        logger.info(f"New file detected: {filepath.name}")
        self.process_file(filepath)

    def process_file(self, filepath: Path):
        # Retry mechanism for file access issues
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                if filepath.suffix.lower() == ".pdf":
                    document_text = extract_text_from_pdf(filepath)
                else:
                    document_text = extract_text_from_docx(filepath)

                category, suggested_name = get_ai_suggestion(document_text, self.config["categories"], self.config.get("variables", []))
                logger.info(f"AI suggestion: category='{category}', name='{suggested_name}'")

                # Determine target folder and full destination path
                base_folder = Path(self.config["watched_folder"])
                category_folder = ensure_category_folder(base_folder, category)

                # Ensure filename has the same extension
                suggested_filename = f"{suggested_name}{filepath.suffix.lower()}"
                dest_path = category_folder / suggested_filename

                # Resolve name conflicts by appending counter
                counter = 1
                while dest_path.exists():
                    dest_path = category_folder / f"{suggested_name}_{counter}{filepath.suffix.lower()}"
                    counter += 1

                shutil.move(str(filepath), dest_path)
                logger.info(f"Moved '{filepath.name}' to '{dest_path.relative_to(base_folder)}'")
                return  # Success, exit retry loop
                
            except PermissionError as exc:
                if attempt < max_retries - 1:
                    logger.warning(f"Permission denied for '{filepath.name}' (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Failed to process file '{filepath}' after {max_retries} attempts: {exc}")
            except Exception as exc:
                logger.error(f"Failed to process file '{filepath}': {exc}")
                break  # Don't retry for non-permission errors



def start_observer(config):
    watched_folder = Path(config["watched_folder"])
    if not watched_folder.exists():
        logger.warning(f"Watched folder does not exist: {watched_folder}. Creating it.")
        watched_folder.mkdir(parents=True)

    event_handler = DocumentHandler(config)
    observer = Observer()
    observer.schedule(event_handler, str(watched_folder), recursive=False)
    observer.start()

    logger.info(f"Started monitoring '{watched_folder}' for new documents...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping observer...")
        observer.stop()
    observer.join()


def main():
    config = load_config()
    start_observer(config)


if __name__ == "__main__":
    main() 