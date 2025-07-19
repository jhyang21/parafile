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

# Load environment variables from .env file if present
# This ensures API keys and other secrets are properly loaded
load_dotenv()

# Initialize OpenAI client with API key from environment
# The client will be used for all API calls throughout the module
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Validate that the API key is available before proceeding
# This prevents runtime errors when making API calls
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
    # Build the categories section of the prompt
    # Each category includes its name, description, and naming pattern
    categories_block = []
    for cat in categories:
        categories_block.append(
            f"# Category: {cat['name']}\n"
            f"# Description: {cat['description']}\n"
            f"# Naming Pattern: {cat['naming_pattern']}"
        )
    categories_section = "\n---\n".join(categories_block)

    # Build the variables section of the prompt
    # Variables are placeholders that can be used in naming patterns
    variables_block = []
    for var in variables:
        variables_block.append(
            f"# Variable: {var['name']}\n"
            f"# Description: {var['description']}"
        )
    variables_section = "\n---\n".join(variables_block)

    # Construct the complete prompt with clear instructions
    # The prompt is designed to guide the AI to:
    # 1. Understand its role as a file organization assistant
    # 2. Analyze the document content
    # 3. Choose the most appropriate category
    # 4. Generate a filename using the category's naming pattern
    # 5. Return results in the specified JSON format
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
    # Build the prompt using the helper function
    prompt = _build_prompt(categories, variables, document_text)

    try:
        # Make the API call to OpenAI
        # Using GPT-4 for better document analysis and categorization
        # Temperature of 0.2 provides consistent results with minimal randomness
        response = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",  # Latest GPT-4 model for best performance
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,  # Sufficient for category and filename response
            temperature=0.2,  # Low temperature for consistent, focused responses
        )

        # Extract the response content
        content = response.choices[0].message.content.strip()

        # Parse the JSON response from the AI
        # The AI is instructed to return a JSON object with specific keys
        result = json.loads(content)
        category = result.get("category", "General")
        suggested_name = result.get("suggested_name", "unnamed_file")
        
        return category, suggested_name
        
    except json.JSONDecodeError:
        # Handle cases where AI returns malformed JSON
        # This can happen if the AI doesn't follow instructions exactly
        return "General", "unnamed_file"
    except Exception:
        # Handle any other API-related errors (network, quota, etc.)
        # Graceful degradation ensures the application continues working
        return "General", "unnamed_file"


# Define the public API of this module
# This helps other developers understand what functions are intended for external use
__all__ = ["get_ai_filename_suggestion"] 