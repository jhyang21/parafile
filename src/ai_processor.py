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

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError(
        "OPENAI_API_KEY not set. Please configure your environment or .env file.")


def categorize_document(document_text: str, categories: Dict[str, Dict[str, str]]) -> str:
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
        categories_list.append({
            "name": name,
            "description": details["description"],
            "naming_pattern": details["naming_pattern"]
        })
    
    system_prompt = """
    You are an expert file organization assistant. Your task is to analyze the text 
    of a document and classify it into one of the user's custom categories based on 
    their descriptions.

    You must return a JSON object with the following keys:
    - category: The name of the category that the document belongs to
    - reasoning: A short explanation of why you chose the category  
    - confidence: A number between 0 and 100 that represents how confident you are in your choice

    Here are the user's categories and their descriptions:

    ---
    """ + f"{categories_list}\n    ---\n"
    
    user_prompt = "Document Text:\n\"\"\"\n" + f"{document_text}\n\"\"\"\n\n"
    
    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[{"role": "system", "content": system_prompt}, 
                  {"role": "user", "content": user_prompt}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "reasoning": "string",
                "confidence": "number",
                "category": "string"
            }
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
        return categories[category]['naming_pattern']
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
    pattern = r'\{([^}]+)\}'
    matches = re.findall(pattern, naming_pattern)
    
    # Return list of variable names (content inside braces)
    return matches

def extract_single_variable(document_text: str, variable_name: str, variables: Dict[str, str], 
                           category: str, category_description: str, naming_pattern: str) -> str:
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
    user_prompt = f"Document Text:\n\"\"\"\n{document_text}\n\"\"\""
    
    # Create schema for a single variable
    json_schema = {
        "type": "object",
        "properties": {
            variable_name: {"type": "string"}
        },
        "required": [variable_name]
    }
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "system", "content": system_prompt}, 
                      {"role": "user", "content": user_prompt}],
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


def _build_prompt(categories: Dict[str, Dict[str, str]], 
                  variables: Dict[str, str], 
                  document_text: str) -> str:
    """
    Construct the prompt to be sent to the OpenAI API.
    
    This function builds a comprehensive prompt that includes:
    1. System instructions for the AI's role
    2. User-defined categories with descriptions and naming patterns
    3. User-defined variables with explanations
    4. The actual document text to analyze
    5. Output format specifications
    
    Args:
        categories: Categories dict with name as key, value contains description and naming_pattern
        variables: Variables dict with name as key, description as value
        document_text: The extracted text content from the document
        
    Returns:
        str: Complete prompt string ready for API submission
    """
    # Build categories section with name, description, and naming pattern
    categories_block = []
    for name, details in categories.items():
        categories_block.append(
            f"# Category: {name}\n"
            f"# Description: {details['description']}\n"
            f"# Naming Pattern: {details['naming_pattern']}"
        )
    categories_section = "\n---\n".join(categories_block)

    # Build variables section - placeholders for use in naming patterns
    variables_block = []
    for name, description in variables.items():
        variables_block.append(
            f"# Variable: {name}\n"
            f"# Description: {description}"
        )
    variables_section = "\n---\n".join(variables_block)

    prompt = (
        "You are an expert file organization assistant. Your task is to "
        "analyze the text of a document and classify it into one of the "
        "user's custom categories based on their descriptions. "
        "Then, you must generate a new filename using the naming pattern "
        "associated with that category.\n\n"
        "Here are the user's categories and rules:\n\n---\n"
        f"{categories_section}\n---\n\n"
        "Here are the user's variables and their meanings:\n\n---\n"
        f"{variables_section}\n---\n\n"
        "If no category is a good fit, use the category \"General\".\n\n"
        "Document Text:\n\"\"\"\n"
        f"{document_text}\n\"\"\"\n\n"
        "Return your response as a single, minified JSON object with the "
        "keys \"category\" and \"suggested_name\". "
        "Fill in the placeholders in the chosen naming pattern with "
        "information found in the document text."
    )
    return prompt


def get_ai_filename_suggestion(document_text: str, 
                               categories: Dict[str, Dict[str, str]], 
                               variables: Dict[str, str]) -> Tuple[str, str]:
    """
    Send document text to OpenAI API and get categorization and naming suggestions.
    
    This function orchestrates the AI analysis process:
    1. Builds a comprehensive prompt with user configuration
    2. Sends the prompt to OpenAI's GPT model
    3. Parses the JSON response
    4. Returns category and suggested filename
    
    Args:
        document_text: Extracted text content from the document
        categories: Categories dict with name as key, value contains description and naming_pattern
        variables: Variables dict with name as key, description as value
        
    Returns:
        Tuple[str, str]: A tuple of (category_name, suggested_filename)
        
    Note:
        If the API call fails or returns malformed JSON, this function
        will gracefully fall back to default values ("General", "unnamed_file")
        to prevent the application from crashing.
    """
    prompt = _build_prompt(categories, variables, document_text)

    try:
        # Use GPT-4 with low temperature for consistent document categorization
        response = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.2,
        )

        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        category = result.get("category", "General")
        suggested_name = result.get("suggested_name", "unnamed_file")
        
        return category, suggested_name
        
    except json.JSONDecodeError:
        # AI returned malformed JSON - fallback to defaults
        return "General", "unnamed_file"
    except Exception:
        # API errors (network, quota, etc.) - graceful degradation
        return "General", "unnamed_file"


__all__ = ["get_ai_filename_suggestion", "categorize_document", "get_naming_pattern", "parse_naming_pattern"] 




