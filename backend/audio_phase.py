"""
Audio phase module for generating video narration using KeywordsAI prompt management.

This module provides functionality to generate AI narration scripts for
video lectures using the Deepgram Text-to-Speech API through KeywordsAI.
"""

import os
from openai import OpenAI

# KeywordsAI Prompt ID for audio generation
AUDIO_PROMPT_ID = "d3ecb2fe5bbc449b966c2666f13b51a5"


def read_template_file(template_path: str) -> str:
    """
    Read the gen_audio_template.py file content.

    Args:
        template_path: Path to the gen_audio_template.py file.

    Returns:
        The template file content as a string.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    with open(template_path, "r") as f:
        return f.read()


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


def generate_audio_script(
    video_number: int,
    lesson_plan: str,
    template_path: str = "gen_audio_template.py",
    model: str = "groq/openai/gpt-oss-120b",
    api_key: str | None = None,
) -> str:
    """
    Generate an ai_gen_audio.py script for a specific video's narration.

    Uses the KeywordsAI managed prompt to create a Python script that
    generates narration audio using Deepgram TTS API.

    Args:
        video_number: The video number to generate narration for.
        lesson_plan: The structured lesson plan content.
        template_path: Path to the gen_audio_template.py file.
        model: The model identifier to use.
        api_key: KeywordsAI API key. Defaults to KEYWORDSAI_API_KEY_TEST env var.

    Returns:
        A Python script (ai_gen_audio.py) that generates narration for the video.
    """
    template_content = read_template_file(template_path)

    variables = {
        "AI_GEN_AUDIO_TEMPLATE_FILE": template_content,
        "VIDEO_NUMBER": str(video_number),
        "THE_PLAN": lesson_plan,
    }

    return query_with_prompt(
        prompt_id=AUDIO_PROMPT_ID,
        variables=variables,
        model=model,
        api_key=api_key,
    )


if __name__ == "__main__":
    # Example usage
    example_plan = """
    Video 1: Introduction to Backtracking
    - Learning goal: Understand what backtracking is
    - Core ideas: Trial and error, systematic search, pruning
    """

    result = generate_audio_script(
        video_number=1,
        lesson_plan=example_plan,
        template_path="templates/gen_audio_template.txt",
    )
    print(result)