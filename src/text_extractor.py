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

FilePath = Union[str, Path]


def extract_text_from_pdf(filepath: FilePath) -> str:
    """
    Extract text from a PDF file using PyPDF2.
    
    Args:
        filepath: Path to the PDF file (string or Path object)
        
    Returns:
        str: Extracted text content from all pages, separated by newlines
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        PyPDF2.errors.PdfReadError: If the PDF is corrupted or encrypted
        
    Note:
        Only extracts actual text content, not OCR from scanned documents.
    """
    filepath = Path(filepath)
    text_parts = []
    
    with filepath.open("rb") as fp:
        reader = PyPDF2.PdfReader(fp)
        for page in reader.pages:
            text = page.extract_text() or ""
            text_parts.append(text)
    
    return "\n".join(text_parts)


def extract_text_from_docx(filepath: FilePath) -> str:
    """
    Extract text from a Word (.docx) file using python-docx.
    
    Args:
        filepath: Path to the DOCX file (string or Path object)
        
    Returns:
        str: Extracted text content from all paragraphs, separated by newlines
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        BadZipFile: If the DOCX file is corrupted
        
    Note:
        Only extracts paragraph text. Tables, headers, footers, and embedded 
        objects are not included.
    """
    filepath = Path(filepath)
    doc = Document(filepath)
    return "\n".join(para.text for para in doc.paragraphs)


__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_docx",
] 