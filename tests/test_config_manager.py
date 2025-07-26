"""
Unit tests for config_manager module.

These tests verify configuration loading, saving, and transformation logic.
"""
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from src.config_manager import (
    load_config,
    save_config,
    save_config_from_parts,
    _transform_config,
    DEFAULT_CONFIG
)


class TestConfigManager(unittest.TestCase):
    """Test the config_manager functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "watched_folder": "/test/folder",
            "enable_organization": True,
            "categories": [
                {
                    "name": "Reports",
                    "description": "Financial reports",
                    "naming_pattern": "{date}_{type}_report.pdf"
                },
                {
                    "name": "Invoices",
                    "description": "Customer invoices",
                    "naming_pattern": "{company}_{invoice_id}.pdf"
                }
            ],
            "variables": [
                {
                    "name": "date",
                    "description": "Document date",
                    "type": "date"
                },
                {
                    "name": "company",
                    "description": "Company name",
                    "type": "company"
                },
                {
                    "name": "type",
                    "description": "Document type",
                    "type": "document_type"
                },
                {
                    "name": "invoice_id",
                    "description": "Invoice identifier"
                    # Note: no type field to test backward compatibility
                }
            ]
        }

    def test_transform_config(self):
        """Test the _transform_config function."""
        watched_folder, enable_org, categories, variables, var_types = _transform_config(self.test_config)
        
        # Test returned values
        self.assertEqual(watched_folder, "/test/folder")
        self.assertTrue(enable_org)
        
        # Test categories transformation
        expected_categories = {
            "Reports": {
                "description": "Financial reports",
                "naming_pattern": "{date}_{type}_report.pdf"
            },
            "Invoices": {
                "description": "Customer invoices",
                "naming_pattern": "{company}_{invoice_id}.pdf"
            }
        }
        self.assertEqual(categories, expected_categories)
        
        # Test variables transformation
        expected_variables = {
            "date": "Document date",
            "company": "Company name", 
            "type": "Document type",
            "invoice_id": "Invoice identifier"
        }
        self.assertEqual(variables, expected_variables)
        
        # Test variable types transformation (with fallback for missing type)
        expected_types = {
            "date": "date",
            "company": "company",
            "type": "document_type",
            "invoice_id": "text"  # Default fallback
        }
        self.assertEqual(var_types, expected_types)

    def test_transform_config_with_defaults(self):
        """Test _transform_config with missing fields."""
        minimal_config = {}
        watched_folder, enable_org, categories, variables, var_types = _transform_config(minimal_config)
        
        self.assertEqual(watched_folder, "SELECT FOLDER")
        self.assertTrue(enable_org)
        self.assertEqual(categories, {})
        self.assertEqual(variables, {})
        self.assertEqual(var_types, {})

    @patch('src.config_manager.CONFIG_FILE')
    def test_save_config(self, mock_config_file):
        """Test the save_config function."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = Path(temp_file.name)
        
        mock_config_file.__str__ = lambda: str(temp_path)
        mock_config_file.open = temp_path.open
        
        try:
            # Save the config
            save_config(self.test_config)
            
            # Verify it was saved correctly
            with temp_path.open('r', encoding='utf-8') as f:
                saved_config = json.load(f)
            
            self.assertEqual(saved_config, self.test_config)
            
        finally:
            # Clean up
            temp_path.unlink()

    @patch('src.config_manager.CONFIG_FILE')  
    def test_save_config_from_parts(self, mock_config_file):
        """Test the save_config_from_parts function."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = Path(temp_file.name)
        
        mock_config_file.__str__ = lambda: str(temp_path)
        mock_config_file.open = temp_path.open
        
        try:
            # Prepare test data
            categories = {
                "Reports": {
                    "description": "Financial reports",
                    "naming_pattern": "{date}_{type}_report.pdf"
                }
            }
            variables = {"date": "Document date", "type": "Document type"}
            variable_types = {"date": "date", "type": "document_type"}
            
            # Save from parts
            save_config_from_parts(
                watched_folder="/test/folder",
                enable_organization=True,
                categories=categories,
                variables=variables,
                variable_types=variable_types
            )
            
            # Verify it was saved correctly
            with temp_path.open('r', encoding='utf-8') as f:
                saved_config = json.load(f)
            
            expected_config = {
                "watched_folder": "/test/folder",
                "enable_organization": True,
                "categories": [
                    {
                        "name": "Reports",
                        "description": "Financial reports",
                        "naming_pattern": "{date}_{type}_report.pdf"
                    }
                ],
                "variables": [
                    {
                        "name": "date",
                        "description": "Document date",
                        "type": "date"
                    },
                    {
                        "name": "type",
                        "description": "Document type",
                        "type": "document_type"
                    }
                ]
            }
            
            self.assertEqual(saved_config, expected_config)
            
        finally:
            # Clean up
            temp_path.unlink()

    @patch('src.config_manager.CONFIG_FILE')
    def test_save_config_from_parts_without_types(self, mock_config_file):
        """Test save_config_from_parts without variable types for backward compatibility."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = Path(temp_file.name)
        
        mock_config_file.__str__ = lambda: str(temp_path)
        mock_config_file.open = temp_path.open
        
        try:
            # Prepare test data without types
            categories = {
                "Reports": {
                    "description": "Financial reports",
                    "naming_pattern": "{date}_report.pdf"
                }
            }
            variables = {"date": "Document date"}
            
            # Save from parts without variable_types
            save_config_from_parts(
                watched_folder="/test/folder",
                enable_organization=True,
                categories=categories,
                variables=variables
            )
            
            # Verify it was saved correctly
            with temp_path.open('r', encoding='utf-8') as f:
                saved_config = json.load(f)
            
            # Should not include type field when not provided
            expected_variables = [
                {
                    "name": "date",
                    "description": "Document date"
                }
            ]
            
            self.assertEqual(saved_config["variables"], expected_variables)
            
        finally:
            # Clean up
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main() 