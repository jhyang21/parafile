"""
Text extraction module for the Parafile application.

This module provides functions to extract text content from various document
file formats for AI processing. Currently supports PDF and DOCX files,
with a clean interface that can be easily extended for additional formats.

Supported formats:
- PDF: Uses PyPDF2 for reliable text extraction
- DOCX: Uses python-docx for Microsoft Word documents

The extracted text is used by the AI processor to analyze document content
and generate appropriate filenames and categories.
"""
from pathlib import Path
from typing import Union

import PyPDF2
from docx import Document

# Type alias for improved code readability and documentation
# Accepts both string paths and pathlib.Path objects for flexibility
FilePath = Union[str, Path]


def extract_text_from_pdf(filepath: FilePath) -> str:
    """
    Extract text from a PDF file using PyPDF2.
    
    This function reads a PDF file page by page and extracts all text content.
    It handles various PDF formats and encodings, though some complex PDFs
    with embedded images or unusual layouts may not extract perfectly.
    
    Args:
        filepath: Path to the PDF file (string or Path object)
        
    Returns:
        str: Extracted text content from all pages, separated by newlines
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        PyPDF2.errors.PdfReadError: If the PDF is corrupted or encrypted
        
    Note:
        Some PDFs may have text stored as images (scanned documents).
        This function only extracts actual text content, not OCR from images.
    """
    # Convert to Path object for consistent handling
    filepath = Path(filepath)
    
    # Collect text from all pages
    text_parts = []
    
    # Open file in binary mode as required by PyPDF2
    with filepath.open("rb") as fp:
        reader = PyPDF2.PdfReader(fp)
        
        # Iterate through all pages in the PDF
        for page in reader.pages:
            # Extract text from the current page
            # Some pages may have no extractable text, so handle None return
            text = page.extract_text() or ""
            text_parts.append(text)
    
    # Join all page text with newlines for proper formatting
    return "\n".join(text_parts)


def extract_text_from_docx(filepath: FilePath) -> str:
    """
    Extract text from a Word (.docx) file using python-docx.
    
    This function reads a Microsoft Word document and extracts all paragraph
    text content. It handles standard Word documents but may not capture
    text from headers, footers, tables, or text boxes.
    
    Args:
        filepath: Path to the DOCX file (string or Path object)
        
    Returns:
        str: Extracted text content from all paragraphs, separated by newlines
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        BadZipFile: If the DOCX file is corrupted
        
    Note:
        This function only extracts paragraph text. Complex document elements
        like tables, headers, footers, and embedded objects are not included.
        For more comprehensive extraction, additional processing would be needed.
    """
    # Convert to Path object for consistent handling
    filepath = Path(filepath)
    
    # Load the Word document
    doc = Document(filepath)
    
    # Extract text from all paragraphs and join with newlines
    # Using generator expression for memory efficiency with large documents
    return "\n".join(para.text for para in doc.paragraphs)


# Define the public API of this module
# These functions are intended for use by other modules in the application
__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_docx",
] 