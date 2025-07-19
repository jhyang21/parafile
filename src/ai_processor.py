"""
AI processing module for the Parafile application.

This module handles AI-powered filename suggestions using OpenAI's API
to analyze document content and generate appropriate filenames based on
user-defined categories and variables.
"""
import json
import os
from typing import List, Dict, Tuple

from openai import OpenAI
from dotenv import load_dotenv

# Ensure .env values are loaded into environment
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError(
        "OPENAI_API_KEY not set. Please configure your environment or .env file.")


def _build_prompt(categories: List[Dict[str, str]], 
                  variables: List[Dict[str, str]], 
                  document_text: str) -> str:
    """Construct the prompt to be sent to the OpenAI API."""
    categories_block = []
    for cat in categories:
        categories_block.append(
            f"# Category: {cat['name']}\n"
            f"# Description: {cat['description']}\n"
            f"# Naming Pattern: {cat['naming_pattern']}"
        )
    categories_section = "\n---\n".join(categories_block)

    # Build variables section
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
    """Send prompt to OpenAI and parse the response.

    Returns a tuple of (category, suggested_name).
    """
    prompt = _build_prompt(categories, variables, document_text)

    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()

    try:
        result = json.loads(content)
        category = result.get("category", "General")
        suggested_name = result.get("suggested_name", "unnamed_file")
        return category, suggested_name
    except json.JSONDecodeError:
        # Fallback: if parsing fails, return default
        return "General", "unnamed_file"


__all__ = ["get_ai_filename_suggestion"] 