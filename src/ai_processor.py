"""
AI processing module for the Parafile application.

This module handles AI-powered filename suggestions using OpenAI's API
to analyze document content and generate appropriate filenames based on
user-defined categories and variables. It constructs detailed prompts
that guide the AI to categorize documents and generate meaningful names
following user-specified patterns.

The module requires an OpenAI API key to be set in the environment
variables or .env file as OPENAI_API_KEY.
"""

import json
import os
import re
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError(
        "OPENAI_API_KEY not set. Please configure your environment or .env file."
    )


def categorize_document(
    document_text: str, categories: Dict[str, Dict[str, str]]
) -> str:
    """
    Categorize the document based on the categories and descriptions defined by the user.

    Args:
        document_text: The extracted text content from the document
        categories: Categories dict with name as key, value contains description and naming_pattern

    Returns:
        str: The name of the category that best matches the document
    """

    # Convert categories dict to list format for the prompt
    categories_list = []
    for name, details in categories.items():
        categories_list.append(
            {
                "name": name,
                "description": details["description"],
                "naming_pattern": details["naming_pattern"],
            }
        )

    system_prompt = (
        """
    You are an expert file organization assistant. Your task is to analyze the text 
    of a document and classify it into one of the user's custom categories based on 
    their descriptions.

    You must return a JSON object with the following keys:
    - category: The name of the category that the document belongs to
    - reasoning: A short explanation of why you chose the category  
    - confidence: A number between 0 and 100 that represents how confident you are in your choice

    Here are the user's categories and their descriptions:

    ---
    """
        + f"{categories_list}\n    ---\n"
    )

    user_prompt = 'Document Text:\n"""\n' + f'{document_text}\n"""\n\n'

    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "reasoning": "string",
                "confidence": "number",
                "category": "string",
            },
        },
        max_tokens=256,
        temperature=0.2,
    )

    response_json = response.choices[0].message.content.strip()
    response_dict = json.loads(response_json)

    return response_dict


def get_naming_pattern(category: str, categories: Dict[str, Dict[str, str]]) -> str:
    """
    Retrieve the naming pattern from the categories dict given the category name.

    Args:
        category: Name of the category to look up
        categories: Categories dict with name as key, value contains description and naming_pattern

    Returns:
        str: The naming pattern for the category, or None if not found
    """
    if category in categories:
        return categories[category]["naming_pattern"]
    return None


def parse_naming_pattern(naming_pattern: str) -> List[str]:
    """
    Parse a naming pattern string and extract all variable placeholders.

    This function identifies all variable placeholders in a naming pattern
    using the format {variable_name} and returns a list of the variable names.
    This is useful for determining which variables need to be extracted from
    a document to generate a complete filename.

    Args:
        naming_pattern: The naming pattern string containing variable placeholders
                       in the format {variable_name}

    Returns:
        List[str]: List of variable names found in the pattern, without the braces

    Examples:
        >>> parse_naming_pattern("{date}_{company}_{document_type}.pdf")
        ['date', 'company', 'document_type']

        >>> parse_naming_pattern("report_{year}_{month}.docx")
        ['year', 'month']

        >>> parse_naming_pattern("simple_filename.txt")
        []
    """
    # Use regex to find all occurrences of {variable_name} pattern
    pattern = r"\{([^}]+)\}"
    matches = re.findall(pattern, naming_pattern)

    # Return list of variable names (content inside braces)
    return matches


def extract_single_variable(
    document_text: str,
    variable_name: str,
    variables: Dict[str, str],
    category: str,
    category_description: str,
    naming_pattern: str,
) -> str:
    """
    Extract a single variable's value from document text using structured output.

    This function takes a single variable name and its description,
    along with document category context, and then calls the OpenAI API
    to extract the corresponding value from the provided document text.
    It uses JSON schema validation to ensure structured output.

    Args:
        document_text: The text content of the document to analyze.
        variable_name: The name of the variable to be extracted.
        variables: A dictionary where keys are variable names and values
                   are their descriptions, to help the AI understand
                   what to look for.
        category: The document category name for context.
        category_description: Description of what this category represents.
        naming_pattern: The naming pattern this variable is part of.

    Returns:
        str: The extracted text for the variable. Returns a
             placeholder value on failure.
    """
    variable_description = variables.get(variable_name, f"The {variable_name}")

    system_prompt = f"""
    You are a data extraction expert. Your task is to analyze the document text
    and extract the following piece of information. Return a JSON object
    that matches the required schema.

    Document Context:
    - Category: {category}
    - Category Description: {category_description}
    - Naming Pattern: {naming_pattern}

    Variable To Extract:
    - {variable_name}: {variable_description}

    Please extract the specific value for "{variable_name}" that would be 
    appropriate for this type of document ({category}) and fit well in 
    the naming pattern: {naming_pattern}
    """
    user_prompt = f'Document Text:\n"""\n{document_text}\n"""'

    # Create schema for a single variable
    json_schema = {
        "type": "object",
        "properties": {variable_name: {"type": "string"}},
        "required": [variable_name],
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_schema", "json_schema": json_schema},
            max_tokens=256,
            temperature=0.2,
        )
        response_json = response.choices[0].message.content.strip()
        extracted_data = json.loads(response_json)
        return extracted_data.get(variable_name, f"<{variable_name.upper()}>")

    except (json.JSONDecodeError, Exception):
        # Fallback to placeholder on any error
        return f"<{variable_name.upper()}>"


def generate_ai_filename(
    document_text: str,
    category: str,
    category_description: str,
    naming_pattern: str,
    variables: Dict[str, str],
) -> str:
    """
    Generate the final AI-powered document filename using structured variable extraction.

    This function orchestrates the complete filename assembly process by:
    1. Parsing the naming pattern to identify required variables
    2. Extracting each variable's value from the document text one by one
    3. Substituting all extracted values into the naming pattern
    4. Returning the final reconstructed filename

    Args:
        document_text: The text content of the document to analyze.
        category: The document category name for context.
        category_description: Description of what this category represents.
        naming_pattern: The naming pattern with variable placeholders (e.g., "{date}_{company}_{type}.pdf").
        variables: A dictionary where keys are variable names and values are their descriptions.

    Returns:
        str: The final assembled filename with all placeholders replaced.
             Returns the original naming pattern with placeholder values on failure.
    """
    try:
        # Step 1: Parse the naming pattern to find all required variables
        required_variables = parse_naming_pattern(naming_pattern)

        # Step 2: Extract each variable's value from the document text
        extracted_values = {}
        for var_name in required_variables:
            extracted_value = extract_single_variable(
                document_text=document_text,
                variable_name=var_name,
                variables=variables,
                category=category,
                category_description=category_description,
                naming_pattern=naming_pattern,
            )
            extracted_values[var_name] = extracted_value

        # Step 3: Replace all placeholders in the naming pattern with extracted values
        assembled_filename = naming_pattern.format(**extracted_values)

        return assembled_filename

    except Exception:
        # Fallback: return pattern with placeholder values if anything fails
        required_variables = parse_naming_pattern(naming_pattern)
        fallback_values = {var: f"<{var.upper()}>" for var in required_variables}
        try:
            return naming_pattern.format(**fallback_values)
        except Exception:
            return "unnamed_file"


__all__ = [
    "categorize_document",
    "get_naming_pattern",
    "parse_naming_pattern",
    "extract_single_variable",
    "generate_ai_filename",
]
