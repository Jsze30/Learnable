"""
Plan phase module for generating video lecture plans using KeywordsAI prompt management.

This module provides functionality to extract text from PDF files and
generate structured video lecture plans using LLMs through the KeywordsAI gateway.
"""

import os
import pdfplumber
from openai import OpenAI

# KeywordsAI Prompt ID for video lecture plan generation
PLAN_PROMPT_ID = "4855b3fe351c49be9c41077b64eae569"


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file to extract text from.

    Returns:
        Concatenated text from all pages of the PDF.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
    """
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def query_with_prompt(
    prompt_id: str,
    variables: dict[str, str] | None = None,
    model: str = "groq/openai/gpt-oss-120b",
    api_key: str | None = None,
    version: int | str | None = None,
) -> str:
    """
    Send a query using a KeywordsAI managed prompt.

    Args:
        prompt_id: The unique identifier of the saved prompt template in KeywordsAI.
        variables: Dictionary of variables to inject into the prompt template.
        model: The model identifier to use.
        api_key: KeywordsAI API key. Defaults to KEYWORDSAI_API_KEY_TEST env var.
        version: Optional prompt version. Omit for deployed version, use "latest"
                 for draft, or specify an integer for a specific version.

    Returns:
        The model's response text.

    Raises:
        openai.APIError: If the API request fails.
    """
    gateway = OpenAI(
        base_url="https://api.keywordsai.co/api/",
        api_key=api_key or os.getenv("KEYWORDSAI_API_KEY_TEST"),
    )

    prompt_config = {
        "prompt_id": prompt_id,
        "override": True,  # Use managed prompt instead of messages
    }
    if variables:
        prompt_config["variables"] = variables
    if version is not None:
        prompt_config["version"] = version

    response = gateway.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": ""}],  # Content comes from managed prompt
        extra_body={"prompt": prompt_config},
    )

    return response.choices[0].message.content


def generate_lecture_plan(
    learning_objective: str,
    source_pdf_path: str | None = None,
    source_text: str | None = None,
    model: str = "groq/openai/gpt-oss-120b",
    api_key: str | None = None,
) -> str:
    """
    Generate a structured video lecture plan for a given learning objective.

    Uses the KeywordsAI managed prompt to create a pedagogically sound
    video lecture plan with appropriate complexity and structure.

    Args:
        learning_objective: What the user wants to learn (maps to USER_PROMPT).
        source_pdf_path: Optional path to a PDF file to use as source material.
        source_text: Optional text content to use as source material.
                     If both pdf_path and source_text are provided, they are combined.
        model: The model identifier to use.
        api_key: KeywordsAI API key. Defaults to KEYWORDSAI_API_KEY_TEST env var.

    Returns:
        A structured video lecture plan with titles, goals, and content for each video.
    """
    # Build source content from PDF and/or text
    sources = []
    if source_pdf_path:
        sources.append(extract_text_from_pdf(source_pdf_path))
    if source_text:
        sources.append(source_text)

    user_sources = "\n\n".join(sources) if sources else ""

    variables = {
        "USER_SOURCES": user_sources,
        "USER_PROMPT": learning_objective,
    }

    return query_with_prompt(
        prompt_id=PLAN_PROMPT_ID,
        variables=variables,
        model=model,
        api_key=api_key,
    )


if __name__ == "__main__":
    result = generate_lecture_plan(
        learning_objective="Explain backtracking algorithms and how to apply them",
        source_pdf_path="source_example/02-backtracking.pdf",
    )
    print(result)
