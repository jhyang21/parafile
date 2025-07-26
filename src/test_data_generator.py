"""
Test Data Generation Module for Parafile.

This module generates a suite of test documents based on the user's
configuration file (config.json). It uses AI to create realistic
document text that aligns with each category's description and includes
information relevant to the naming pattern variables.

The purpose of this module is to provide a consistent and automated way
to create a test set for verifying the application's categorization and
file-naming capabilities before deploying to production.

To run this module, execute it directly from the command line:
`python -m src.test_data_generator`
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from faker import Faker
from openai import OpenAI

from src.ai_processor import parse_naming_pattern

# Use absolute import for sibling modules
from src.config_manager import load_config

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
fake = Faker()

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError(
        "OPENAI_API_KEY not set. Please configure your environment or .env file."
    )


class TestDataGenerator:
    """
    A config-driven test data generator that creates realistic test values
    based on variable type definitions.
    """

    def __init__(self):
        self.fake = Faker()
        # Set seed for reproducible test data
        Faker.seed(42)

    def generate_value_by_type(
        self, variable_type: str, variable_name: str = ""
    ) -> str:
        """
        Generate a realistic value based on the variable type.

        Args:
            variable_type: The type defined in the config
            variable_name: The variable name for additional context

        Returns:
            A string value appropriate for the type
        """
        type_generators = {
            # Date and time types
            "date": lambda: self.fake.date(),
            "year": lambda: str(self.fake.year()),
            "month": lambda: f"{self.fake.month():02d}",
            "day": lambda: f"{self.fake.day_of_month():02d}",
            # Name types
            "first_name": lambda: self.fake.first_name(),
            "last_name": lambda: self.fake.last_name(),
            "person_name": lambda: self.fake.name().replace(" ", "_"),
            # Business types
            "company": lambda: self.fake.company()
            .replace(" ", "")
            .replace(",", "")
            .replace(".", ""),
            "document_type": lambda: self.fake.random_element(
                ["Report", "Analysis", "Summary", "Proposal", "Invoice"]
            ),
            "agreement_type": lambda: self.fake.random_element(
                ["NDA", "MSA", "SOW", "Contract", "Agreement"]
            ),
            # Technical types
            "version": lambda: f"v{self.fake.random_int(1, 5)}.{self.fake.random_int(0, 9)}",
            "period": lambda: f"Q{self.fake.random_int(1, 4)}-{datetime.now().year}",
            # Generic types
            "text": lambda: "_".join(self.fake.words(3)),
            "uuid": lambda: str(self.fake.uuid4())[:8],
        }

        generator = type_generators.get(variable_type, type_generators["text"])
        return generator()

    def _infer_variable_type(self, variable_name: str) -> str:
        """
        Infer the variable type from the variable name using common patterns.

        Args:
            variable_name: The name of the variable to infer the type for

        Returns:
            The inferred type string
        """
        variable_name_lower = variable_name.lower()

        # Date/time patterns
        if any(
            pattern in variable_name_lower
            for pattern in ["date", "year", "month", "day", "time"]
        ):
            if "year" in variable_name_lower:
                return "year"
            elif "month" in variable_name_lower:
                return "month"
            elif "day" in variable_name_lower:
                return "day"
            else:
                return "date"

        # Name patterns
        if any(
            pattern in variable_name_lower for pattern in [
                "first_name",
                "firstname"]):
            return "first_name"
        elif any(
            pattern in variable_name_lower
            for pattern in ["last_name", "lastname", "surname"]
        ):
            return "last_name"
        elif any(
            pattern in variable_name_lower
            for pattern in ["name", "employee", "person", "author"]
        ):
            return "person_name"

        # Business patterns
        if any(
            pattern in variable_name_lower
            for pattern in ["company", "corporation", "organization", "org"]
        ):
            return "company"
        elif any(
            pattern in variable_name_lower
            for pattern in ["doc_type", "document_type", "type"]
        ):
            return "document_type"
        elif any(
            pattern in variable_name_lower for pattern in ["agreement", "contract"]
        ):
            return "agreement_type"

        # Technical patterns
        elif any(pattern in variable_name_lower for pattern in ["version", "ver", "v"]):
            return "version"
        elif any(
            pattern in variable_name_lower for pattern in ["period", "quarter", "q"]
        ):
            return "period"
        elif any(pattern in variable_name_lower for pattern in ["uuid", "id"]):
            return "uuid"

        # Default to text
        return "text"

    def generate_test_document_text(
        self,
        category_name: str,
        category_description: str,
        naming_pattern: str,
        generated_values: Dict[str, Any],
    ) -> str:
        """
        Generate realistic document text that contains specific pre-determined values.
        """
        system_prompt = f"""
        You are a test data generator. Your task is to create a sample document text that
        fits a specific user-defined category.

        The document MUST be a perfect example for the category '{category_name}' ({category_description})
        and it ABSOLUTELY MUST contain the following specific pieces of information, exactly as written:

        ---
        {json.dumps(generated_values, indent=2)}
        ---

        Generate a sample document text (2-3 paragraphs) that is coherent and naturally
        weaves in all the required values listed above. Do not wrap the output in any
        code blocks or special formatting. The text you generate will be used to test
        if an AI can extract these exact values.
        """
        user_prompt = "Please generate the document text now."
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=500,
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating text for category '{category_name}': {e}")
            return f"Error: Could not generate test document for {category_name}."

    def generate_test_suite(self):
        """
        Generates a full test suite including documents and a manifest file.
        """
        print("Loading configuration...")
        _, _, categories, variables = load_config()

        root_path = Path(__file__).resolve().parent.parent
        test_docs_path = root_path / "test_documents"
        print(f"Test documents will be saved in: {test_docs_path}")

        if test_docs_path.exists():
            shutil.rmtree(test_docs_path)
        test_docs_path.mkdir(exist_ok=True)

        manifest = []
        doc_counter = 1

        for name, details in categories.items():
            if name == "General":
                continue

            print(f"Generating test case for category: '{name}'...")

            # 1. Generate plausible values for the variables in the naming
            # pattern
            naming_pattern = details["naming_pattern"]
            required_vars = parse_naming_pattern(naming_pattern)

            # Skip 'original_name' as it's added by the organizer, not
            # extracted
            required_vars = [v for v in required_vars if v != "original_name"]

            generated_values = {}
            for var in required_vars:
                # Infer variable type from variable name patterns
                var_type = self._infer_variable_type(var)
                generated_values[var] = self.generate_value_by_type(
                    var_type, var)

            # 2. Construct the expected final filename
            # We handle original_name separately if present
            pattern_values = generated_values.copy()
            source_filename_stem = f"test_doc_{doc_counter:03d}"
            if "original_name" in details["naming_pattern"]:
                pattern_values["original_name"] = source_filename_stem

            expected_filename_stem = naming_pattern.format(**pattern_values)
            # Assuming all test files will be converted to .docx
            expected_filename = f"{expected_filename_stem}.docx"

            # 3. Generate document text containing these specific values
            document_text = self.generate_test_document_text(
                category_name=name,
                category_description=details["description"],
                naming_pattern=naming_pattern,
                generated_values=generated_values,
            )

            # 4. Save the source text file
            source_filepath = test_docs_path / f"{source_filename_stem}.txt"
            source_filepath.write_text(document_text, encoding="utf-8")
            print(f"  -> Saved source file: {source_filepath.name}")

            # 5. Add this test case to our manifest
            manifest.append(
                {
                    "source_file_stem": source_filename_stem,
                    "expected_category": name,
                    "expected_filename": expected_filename,
                    "generated_values": generated_values,
                    "naming_pattern": naming_pattern,
                }
            )
            doc_counter += 1

        # 6. Save the final manifest file
        manifest_path = test_docs_path / "manifest.json"
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"\nSaved test manifest to: {manifest_path}")

        print(
            f"\nTest suite generation complete. Generated {len(manifest)} test cases."
        )


def generate_test_suite():
    """
    Convenience function for backwards compatibility and CLI usage.
    """
    generator = TestDataGenerator()
    generator.generate_test_suite()


if __name__ == "__main__":
    generate_test_suite()

__all__ = ["TestDataGenerator", "generate_test_suite"]
