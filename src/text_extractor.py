from pathlib import Path
from typing import Union

import PyPDF2
from docx import Document


FilePath = Union[str, Path]


def extract_text_from_pdf(filepath: FilePath) -> str:
    """Extract text from a PDF file using PyPDF2."""
    filepath = Path(filepath)
    text_parts = []
    with filepath.open("rb") as fp:
        reader = PyPDF2.PdfReader(fp)
        for page in reader.pages:
            text = page.extract_text() or ""
            text_parts.append(text)
    return "\n".join(text_parts)


def extract_text_from_docx(filepath: FilePath) -> str:
    """Extract text from a Word (.docx) file using python-docx."""
    filepath = Path(filepath)
    doc = Document(filepath)
    return "\n".join(para.text for para in doc.paragraphs)


__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_docx",
] 