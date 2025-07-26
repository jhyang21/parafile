"""
Unit tests for organizer module.

These tests verify file organization logic with mocked AI calls.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.organizer import DocumentHandler, ensure_category_folder


class TestEnsureCategoryFolder(unittest.TestCase):
    """Test the ensure_category_folder function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_create_new_category_folder(self):
        """Test creating a new category folder."""
        category_folder = ensure_category_folder(self.temp_dir, "Reports")

        # Check that folder was created
        self.assertTrue(category_folder.exists())
        self.assertTrue(category_folder.is_dir())
        self.assertEqual(category_folder.name, "Reports")

    def test_existing_category_folder(self):
        """Test with an existing category folder."""
        # Create folder first
        existing_folder = self.temp_dir / "Invoices"
        existing_folder.mkdir()

        category_folder = ensure_category_folder(self.temp_dir, "Invoices")

        # Should return the existing folder
        self.assertEqual(category_folder, existing_folder)
        self.assertTrue(category_folder.exists())


class TestDocumentHandler(unittest.TestCase):
    """Test the DocumentHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.categories = {
            "Reports": {
                "description": "Financial reports",
                "naming_pattern": "{date}_{type}_report",
            },
            "Invoices": {
                "description": "Customer invoices",
                "naming_pattern": "{company}_{invoice_id}",
            },
        }
        self.variables = {
            "date": "Document date",
            "type": "Document type",
            "company": "Company name",
            "invoice_id": "Invoice ID",
        }

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def create_test_file(self, filename: str, content: str = "test content") -> Path:
        """Create a test file with the given name and content."""
        file_path = self.temp_dir / filename
        file_path.write_text(content)
        return file_path

    @patch("src.organizer.extract_text_from_pdf")
    @patch("src.organizer.categorize_document")
    @patch("src.organizer.generate_ai_filename")
    def test_process_pdf_file_with_organization(
        self, mock_generate_filename, mock_categorize, mock_extract_text
    ):
        """Test processing a PDF file with organization enabled."""
        # Set up mocks
        mock_extract_text.return_value = "Sample invoice text from TechCorp"
        mock_categorize.return_value = {
            "category": "Invoices",
            "confidence": 95,
            "reasoning": "Contains invoice information",
        }
        mock_generate_filename.return_value = "TechCorp_INV001"

        # Create test file
        test_file = self.create_test_file("test_invoice.pdf")

        # Create handler with organization enabled
        handler = DocumentHandler(
            watched_folder=str(self.temp_dir),
            enable_organization=True,
            categories=self.categories,
            variables=self.variables,
        )

        # Process the file
        handler.process_file(test_file)

        # Verify mocks were called
        mock_extract_text.assert_called_once_with(test_file)
        mock_categorize.assert_called_once_with(
            "Sample invoice text from TechCorp", self.categories
        )
        mock_generate_filename.assert_called_once()

        # Verify file was moved and renamed
        expected_path = self.temp_dir / "Invoices" / "TechCorp_INV001.pdf"
        self.assertTrue(expected_path.exists())
        self.assertFalse(test_file.exists())  # Original file should be moved

    @patch("src.organizer.extract_text_from_docx")
    @patch("src.organizer.categorize_document")
    @patch("src.organizer.generate_ai_filename")
    def test_process_docx_file_without_organization(
        self, mock_generate_filename, mock_categorize, mock_extract_text
    ):
        """Test processing a DOCX file without organization (rename only)."""
        # Set up mocks
        mock_extract_text.return_value = "Financial report for Q1 2024"
        mock_categorize.return_value = {
            "category": "Reports",
            "confidence": 90,
            "reasoning": "Contains report information",
        }
        mock_generate_filename.return_value = "2024-Q1_Financial_Report"

        # Create test file
        test_file = self.create_test_file("quarterly_report.docx")

        # Create handler with organization disabled
        handler = DocumentHandler(
            watched_folder=str(self.temp_dir),
            enable_organization=False,
            categories=self.categories,
            variables=self.variables,
        )

        # Process the file
        handler.process_file(test_file)

        # Verify file was renamed but stayed in watched folder
        expected_path = self.temp_dir / "2024-Q1_Financial_Report.docx"
        self.assertTrue(expected_path.exists())
        self.assertFalse(test_file.exists())  # Original file should be moved

        # No category folder should be created
        reports_folder = self.temp_dir / "Reports"
        self.assertFalse(reports_folder.exists())

    @patch("src.organizer.extract_text_from_pdf")
    @patch("src.organizer.categorize_document")
    @patch("src.organizer.generate_ai_filename")
    def test_file_naming_conflict_resolution(
        self, mock_generate_filename, mock_categorize, mock_extract_text
    ):
        """Test that naming conflicts are resolved with number suffixes."""
        # Set up mocks
        mock_extract_text.return_value = "Invoice text"
        mock_categorize.return_value = {
            "category": "Invoices",
            "confidence": 95,
            "reasoning": "Invoice document",
        }
        mock_generate_filename.return_value = "TechCorp_Invoice"

        # Create category folder and existing file
        invoices_folder = self.temp_dir / "Invoices"
        invoices_folder.mkdir()
        existing_file = invoices_folder / "TechCorp_Invoice.pdf"
        existing_file.write_text("existing content")

        # Create test file to process
        test_file = self.create_test_file("new_invoice.pdf")

        # Create handler
        handler = DocumentHandler(
            watched_folder=str(self.temp_dir),
            enable_organization=True,
            categories=self.categories,
            variables=self.variables,
        )

        # Process the file
        handler.process_file(test_file)

        # Verify file was renamed with conflict resolution
        expected_path = self.temp_dir / "Invoices" / "TechCorp_Invoice_1.pdf"
        self.assertTrue(expected_path.exists())
        self.assertTrue(existing_file.exists())  # Original file should still exist
        self.assertFalse(test_file.exists())  # Processed file should be moved

    @patch("src.organizer.extract_text_from_pdf")
    def test_extraction_failure_handling(self, mock_extract_text):
        """Test handling of text extraction failures."""
        # Mock extraction failure
        mock_extract_text.side_effect = Exception("Extraction failed")

        # Create test file
        test_file = self.create_test_file("corrupted.pdf")

        # Create handler
        handler = DocumentHandler(
            watched_folder=str(self.temp_dir),
            enable_organization=True,
            categories=self.categories,
            variables=self.variables,
        )

        # Process the file - should not raise exception
        handler.process_file(test_file)

        # File should still exist (processing failed gracefully)
        self.assertTrue(test_file.exists())

    def test_unsupported_file_handling(self):
        """Test that unsupported files are ignored."""
        # Create unsupported file
        test_file = self.create_test_file("document.txt")

        # Create handler
        handler = DocumentHandler(
            watched_folder=str(self.temp_dir),
            enable_organization=True,
            categories=self.categories,
            variables=self.variables,
        )

        # Process the file
        handler.process_file(test_file)

        # File should remain unchanged (not processed)
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_text(), "test content")


if __name__ == "__main__":
    unittest.main()
