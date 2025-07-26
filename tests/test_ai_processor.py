"""
Unit tests for ai_processor module.

These tests focus on the pure logic functions that don't require AI calls,
and use mocking to test functions that do require AI calls.
"""

import unittest
from unittest.mock import patch, MagicMock
import json

from src.ai_processor import (
    parse_naming_pattern,
    get_naming_pattern,
    extract_single_variable,
    generate_ai_filename,
)


class TestParseNamingPattern(unittest.TestCase):
    """Test the parse_naming_pattern function."""

    def test_simple_pattern_with_variables(self):
        """Test parsing a pattern with multiple variables."""
        pattern = "{date}_{company}_{document_type}.pdf"
        expected = ["date", "company", "document_type"]
        result = parse_naming_pattern(pattern)
        self.assertEqual(result, expected)

    def test_pattern_with_no_variables(self):
        """Test parsing a pattern with no variables."""
        pattern = "simple_filename.txt"
        expected = []
        result = parse_naming_pattern(pattern)
        self.assertEqual(result, expected)

    def test_pattern_with_single_variable(self):
        """Test parsing a pattern with a single variable."""
        pattern = "report_{year}.docx"
        expected = ["year"]
        result = parse_naming_pattern(pattern)
        self.assertEqual(result, expected)

    def test_pattern_with_duplicate_variables(self):
        """Test parsing a pattern with duplicate variables."""
        pattern = "{date}_{date}_{company}.pdf"
        expected = ["date", "date"]
        result = parse_naming_pattern(pattern)
        self.assertEqual(result, expected)

    def test_pattern_with_nested_braces(self):
        """Test that nested braces are handled correctly."""
        pattern = "file_{meta{data}}_end.txt"
        # Should only match complete {variable} patterns
        expected = []
        result = parse_naming_pattern(pattern)
        self.assertEqual(result, expected)


class TestGetNamingPattern(unittest.TestCase):
    """Test the get_naming_pattern function."""

    def test_existing_category(self):
        """Test retrieving pattern for existing category."""
        categories = {
            "Reports": {
                "description": "Financial reports",
                "naming_pattern": "{date}_{type}_report.pdf",
            },
            "Invoices": {
                "description": "Customer invoices",
                "naming_pattern": "{company}_{invoice_id}.pdf",
            },
        }
        result = get_naming_pattern("Reports", categories)
        expected = "{date}_{type}_report.pdf"
        self.assertEqual(result, expected)

    def test_nonexistent_category(self):
        """Test retrieving pattern for non-existent category."""
        categories = {
            "Reports": {
                "description": "Financial reports",
                "naming_pattern": "{date}_{type}_report.pdf",
            }
        }
        result = get_naming_pattern("NonExistent", categories)
        self.assertIsNone(result)

    def test_empty_categories(self):
        """Test with empty categories dict."""
        categories = {}
        result = get_naming_pattern("Any", categories)
        self.assertIsNone(result)


class TestExtractSingleVariable(unittest.TestCase):
    """Test the extract_single_variable function with mocking."""

    @patch("src.ai_processor.client")
    def test_successful_extraction(self, mock_client):
        """Test successful variable extraction."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"company_name": "TechCorp"}'
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_single_variable(
            document_text="This is a contract with TechCorp for software services.",
            variable_name="company_name",
            variables={"company_name": "The name of the company"},
            category="Contracts",
            category_description="Legal contracts",
            naming_pattern="{company_name}_contract.pdf",
        )

        self.assertEqual(result, "TechCorp")
        # Verify the API was called
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.ai_processor.client")
    def test_api_failure_returns_placeholder(self, mock_client):
        """Test that API failures return placeholder values."""
        # Mock an API failure
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        result = extract_single_variable(
            document_text="Some document text",
            variable_name="company_name",
            variables={"company_name": "The name of the company"},
            category="Contracts",
            category_description="Legal contracts",
            naming_pattern="{company_name}_contract.pdf",
        )

        self.assertEqual(result, "<COMPANY_NAME>")

    @patch("src.ai_processor.client")
    def test_invalid_json_returns_placeholder(self, mock_client):
        """Test that invalid JSON responses return placeholder values."""
        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "invalid json"
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_single_variable(
            document_text="Some document text",
            variable_name="company_name",
            variables={"company_name": "The name of the company"},
            category="Contracts",
            category_description="Legal contracts",
            naming_pattern="{company_name}_contract.pdf",
        )

        self.assertEqual(result, "<COMPANY_NAME>")


class TestGenerateAiFilename(unittest.TestCase):
    """Test the generate_ai_filename function with mocking."""

    @patch("src.ai_processor.extract_single_variable")
    def test_successful_filename_generation(self, mock_extract):
        """Test successful filename generation."""
        # Mock successful variable extraction
        mock_extract.side_effect = ["2024-03-15", "TechCorp", "Invoice"]

        result = generate_ai_filename(
            document_text="Invoice from TechCorp dated 2024-03-15",
            category="Invoices",
            category_description="Customer invoices",
            naming_pattern="{date}_{company}_{type}.pdf",
            variables={
                "date": "Document date",
                "company": "Company name",
                "type": "Document type",
            },
        )

        expected = "2024-03-15_TechCorp_Invoice.pdf"
        self.assertEqual(result, expected)

        # Verify extract_single_variable was called for each variable
        self.assertEqual(mock_extract.call_count, 3)

    @patch("src.ai_processor.extract_single_variable")
    def test_partial_failure_with_placeholders(self, mock_extract):
        """Test filename generation with some failed extractions."""
        # Mock mixed success/failure
        mock_extract.side_effect = ["2024-03-15", "<COMPANY>", "Invoice"]

        result = generate_ai_filename(
            document_text="Some document text",
            category="Invoices",
            category_description="Customer invoices",
            naming_pattern="{date}_{company}_{type}.pdf",
            variables={
                "date": "Document date",
                "company": "Company name",
                "type": "Document type",
            },
        )

        expected = "2024-03-15_<COMPANY>_Invoice.pdf"
        self.assertEqual(result, expected)

    @patch("src.ai_processor.parse_naming_pattern")
    def test_exception_handling(self, mock_parse):
        """Test that exceptions are handled gracefully."""
        # Mock an exception in parse_naming_pattern
        mock_parse.side_effect = Exception("Parse error")

        result = generate_ai_filename(
            document_text="Some text",
            category="Test",
            category_description="Test category",
            naming_pattern="{invalid}",
            variables={},
        )

        # Should return fallback filename
        self.assertEqual(result, "unnamed_file")


if __name__ == "__main__":
    unittest.main()
