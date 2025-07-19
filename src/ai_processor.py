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
from typing import List, Dict, Tuple

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError(
        "OPENAI_API_KEY not set. Please configure your environment or .env file.")


def _build_prompt(categories: List[Dict[str, str]], 
                  variables: List[Dict[str, str]], 
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
        categories: List of category dictionaries containing name, 
                   description, and naming_pattern
        variables: List of variable dictionaries containing name and description
        document_text: The extracted text content from the document
        
    Returns:
        str: Complete prompt string ready for API submission
    """
    # Build categories section with name, description, and naming pattern
    categories_block = []
    for cat in categories:
        categories_block.append(
            f"# Category: {cat['name']}\n"
            f"# Description: {cat['description']}\n"
            f"# Naming Pattern: {cat['naming_pattern']}"
        )
    categories_section = "\n---\n".join(categories_block)

    # Build variables section - placeholders for use in naming patterns
    variables_block = []
    for var in variables:
        variables_block.append(
            f"# Variable: {var['name']}\n"
            f"# Description: {var['description']}"
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
                               categories: List[Dict[str, str]], 
                               variables: List[Dict[str, str]]) -> Tuple[str, str]:
    """
    Send document text to OpenAI API and get categorization and naming suggestions.
    
    This function orchestrates the AI analysis process:
    1. Builds a comprehensive prompt with user configuration
    2. Sends the prompt to OpenAI's GPT model
    3. Parses the JSON response
    4. Returns category and suggested filename
    
    Args:
        document_text: Extracted text content from the document
        categories: User-defined categories with naming patterns
        variables: User-defined variables for filename construction
        
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


__all__ = ["get_ai_filename_suggestion"] 