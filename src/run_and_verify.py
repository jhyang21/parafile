"""
Verification script for Parafile's automated testing pipeline.

This module runs the file organizer and then verifies the output against
a pre-generated manifest file. It checks that each file was moved to the
correct category and renamed to the exact expected filename.
"""
import os
import sys
import shutil
import time
import json
from pathlib import Path
from typing import Dict, List

# Use absolute imports for sibling modules
from src.config_manager import load_config
from src.organizer import DocumentHandler, SUPPORTED_EXTENSIONS


class TestVerificationError(Exception):
    """Custom exception for test verification failures."""
    pass


class TestVerifier:
    """
    A comprehensive test verifier that checks AI-powered file organization
    against expected results defined in a manifest file.
    """
    
    def __init__(self, test_docs_path: Path):
        self.test_docs_path = test_docs_path
        self.manifest_path = test_docs_path / "manifest.json"
        self.errors: List[str] = []
        
    def load_manifest(self) -> List[Dict]:
        """Load and validate the test manifest file."""
        if not self.manifest_path.exists():
            raise TestVerificationError("manifest.json is missing. Please run test_data_generator.py first.")
        
        try:
            with self.manifest_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            if not isinstance(manifest, list) or not manifest:
                raise TestVerificationError("Invalid manifest format: expected non-empty list")
                
            return manifest
            
        except json.JSONDecodeError as e:
            raise TestVerificationError(f"Invalid JSON in manifest file: {e}")
    
    def prepare_test_files(self, manifest: List[Dict]) -> None:
        """Convert .txt test files to .docx for processing."""
        print("Preparing test files...")
        
        for item in manifest:
            txt_file = self.test_docs_path / f"{item['source_file_stem']}.txt"
            if not txt_file.exists():
                self.errors.append(f"Source file missing: {txt_file.name}")
                continue
                
            docx_file = txt_file.with_suffix(".docx")
            shutil.copy(txt_file, docx_file)
            print(f"  Prepared {docx_file.name} for processing")
        
        if self.errors:
            raise TestVerificationError(f"Failed to prepare {len(self.errors)} test file(s)")
    
    def run_file_organization(self) -> None:
        """Execute the file organization logic on test files."""
        print("Starting file processing...")
        
        # Load configuration
        _, enable_organization, categories, variables, variable_types = load_config()
        
        if not enable_organization:
            raise TestVerificationError(
                "Organization is disabled in config. Automated verification requires organization to be enabled."
            )
        
        # Create and run the document handler
        handler = DocumentHandler(
            str(self.test_docs_path), 
            enable_organization, 
            categories, 
            variables, 
            variable_types
        )
        
        # Process all .docx files
        processed_count = 0
        for file_path in self.test_docs_path.glob("*.docx"):
            print(f"  Processing {file_path.name}...")
            handler.process_file(file_path)
            processed_count += 1
        
        print(f"Processed {processed_count} files")
        
        # Give the system a moment to complete file operations
        time.sleep(1)
    
    def verify_results(self, manifest: List[Dict]) -> None:
        """Verify that the organization results match the manifest expectations."""
        print("Verifying results against manifest...")
        
        expected_files = set()
        
        # Check each manifest entry
        for item in manifest:
            expected_path = self.test_docs_path / item['expected_category'] / item['expected_filename']
            expected_files.add(expected_path)
            
            if not expected_path.exists():
                self.errors.append(
                    f"❌ MISSING: Expected '{item['expected_filename']}' in category '{item['expected_category']}'"
                )
                print(f"  ❌ Missing: {item['expected_filename']}")
            else:
                print(f"  ✅ Found: {item['expected_filename']} in {item['expected_category']}")
        
        # Check for unexpected files in category directories
        actual_files = set()
        for category_dir in self.test_docs_path.iterdir():
            if category_dir.is_dir() and category_dir.name != "__pycache__":
                for file_path in category_dir.iterdir():
                    if file_path.is_file():
                        actual_files.add(file_path)
        
        unexpected_files = actual_files - expected_files
        if unexpected_files:
            self.errors.append(f"❌ UNEXPECTED: Found {len(unexpected_files)} unexpected file(s) in category directories")
            for file_path in unexpected_files:
                rel_path = file_path.relative_to(self.test_docs_path)
                self.errors.append(f"   - {rel_path}")
                print(f"  ❌ Unexpected: {rel_path}")
        
        # Check for leftover files in root directory
        leftover_files = list(self.test_docs_path.glob("*.docx"))
        if leftover_files:
            self.errors.append(f"❌ LEFTOVER: Found {len(leftover_files)} unprocessed file(s) in root directory")
            for file_path in leftover_files:
                self.errors.append(f"   - {file_path.name}")
                print(f"  ❌ Leftover: {file_path.name}")
    
    def generate_detailed_report(self, manifest: List[Dict]) -> str:
        """Generate a detailed verification report."""
        report_lines = []
        report_lines.append("=== PARAFILE TEST VERIFICATION REPORT ===")
        report_lines.append(f"Test Documents Path: {self.test_docs_path}")
        report_lines.append(f"Total Test Cases: {len(manifest)}")
        report_lines.append("")
        
        if not self.errors:
            report_lines.append("✅ ALL TESTS PASSED")
            report_lines.append("")
            report_lines.append("Summary:")
            report_lines.append("- All files were correctly categorized")
            report_lines.append("- All files were correctly renamed")
            report_lines.append("- No unexpected files found")
            report_lines.append("- No files left unprocessed")
        else:
            report_lines.append(f"❌ VERIFICATION FAILED ({len(self.errors)} errors)")
            report_lines.append("")
            report_lines.append("Errors found:")
            for error in self.errors:
                report_lines.append(f"  {error}")
        
        report_lines.append("")
        report_lines.append("=== END REPORT ===")
        
        return "\n".join(report_lines)
    
    def run_verification(self) -> bool:
        """
        Run the complete verification process.
        
        Returns:
            True if verification passed, False otherwise
        """
        try:
            # Step 1: Load manifest
            manifest = self.load_manifest()
            print(f"Loaded manifest with {len(manifest)} test cases")
            
            # Step 2: Prepare test files
            self.prepare_test_files(manifest)
            
            # Step 3: Run file organization
            self.run_file_organization()
            
            # Step 4: Verify results
            self.verify_results(manifest)
            
            # Step 5: Generate report
            report = self.generate_detailed_report(manifest)
            print("\n" + report)
            
            return len(self.errors) == 0
            
        except TestVerificationError as e:
            print(f"\nVerification failed: {e}")
            return False
        except Exception as e:
            print(f"\nUnexpected error during verification: {e}")
            return False


def run_verification():
    """
    Main entry point for the verification script.
    """
    root_path = Path(__file__).resolve().parent.parent
    test_docs_path = root_path / "test_documents"
    
    verifier = TestVerifier(test_docs_path)
    success = verifier.run_verification()
    
    if success:
        print("\n🎉 Verification successful! All tests passed.")
        sys.exit(0)
    else:
        print("\n💥 Verification failed. See errors above.")
        sys.exit(1)


if __name__ == "__main__":
    run_verification() 