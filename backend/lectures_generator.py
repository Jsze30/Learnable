"""
Lectures generator module - orchestrates the full video lecture generation pipeline.

This module coordinates plan generation, audio narration, and video animation
to produce complete educational video lectures from a user prompt and source material.
"""

import logging
import os
import re
import subprocess
import sys

from plan_phase import generate_lecture_plan
from audio_phase import generate_audio_script
from video_phase import generate_video_script

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Hardcoded paths
AUDIO_TEMPLATE_PATH = "templates/gen_audio_template.txt"
VIDEO_TEMPLATE_PATH = "templates/gen_video_template.txt"
MANIMATIONS_DIR = "3b1b_manimations"
AUDIO_SCRIPT_PATH = os.path.join(MANIMATIONS_DIR, "ai_gen_audio.py")
VIDEO_SCRIPT_PATH = os.path.join(MANIMATIONS_DIR, "ai_gen_video.py")
VIDEOS_OUTPUT_DIR = os.path.join(MANIMATIONS_DIR, "videos")

# Default model
DEFAULT_MODEL = "azure/gpt-5"


def parse_video_count(plan: str) -> int:
    """
    Parse the lesson plan to determine the number of videos.

    Looks for patterns like "Video 1", "Video 2", etc. and returns the highest number found.

    Args:
        plan: The generated lesson plan text.

    Returns:
        The total number of videos in the plan.

    Raises:
        ValueError: If no video numbers are found in the plan.
    """
    logger.info("Parsing plan to determine video count...")

    # Find all occurrences of "Video N" (case-insensitive)
    matches = re.findall(r"video\s+(\d+)", plan, re.IGNORECASE)

    if not matches:
        raise ValueError("Could not find any video numbers in the plan. "
                         "Expected format: 'Video 1', 'Video 2', etc.")

    video_numbers = [int(m) for m in matches]
    max_video = max(video_numbers)

    logger.info(f"Found {max_video} video(s) in the plan")
    return max_video


def strip_code_fences(code: str) -> str:
    """
    Remove the first and last lines from generated code (code fence markers).

    Args:
        code: The generated code with potential markdown code fences.

    Returns:
        The code with first and last lines removed.
    """
    lines = code.strip().split("\n")

    if len(lines) <= 2:
        logger.warning("Generated code has 2 or fewer lines, returning as-is")
        return code

    return "\n".join(lines[1:-1])


def save_script(content: str, path: str) -> None:
    """
    Save script content to a file.

    Args:
        content: The script content to save.
        path: The file path to save to.
    """
    logger.info(f"Saving script to {path}")
    with open(path, "w") as f:
        f.write(content)
    logger.info(f"Successfully saved script to {path}")


def run_command(command: list[str], working_dir: str, step_description: str) -> None:
    """
    Run a shell command and handle errors.

    Args:
        command: The command to run as a list of arguments.
        working_dir: The directory to run the command in.
        step_description: A description of the step for logging.

    Raises:
        RuntimeError: If the command fails.
    """
    logger.info(f"Running: {' '.join(command)} (in {working_dir})")

    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout:
            logger.info(f"stdout:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"stderr:\n{result.stderr}")

        logger.info(f"Successfully completed: {step_description}")

    except subprocess.CalledProcessError as e:
        logger.error(f"FAILED: {step_description}")
        logger.error(f"Exit code: {e.returncode}")
        if e.stdout:
            logger.error(f"stdout:\n{e.stdout}")
        if e.stderr:
            logger.error(f"stderr:\n{e.stderr}")
        raise RuntimeError(f"Command failed during: {step_description}") from e


def find_latest_video(video_num: int) -> str | None:
    """
    Find the most recently created video file for a given video number.

    ManimGL outputs videos to a nested directory structure. This function
    finds the latest .mp4 file matching the video number.

    Args:
        video_num: The video number to find.

    Returns:
        Relative path to the video file, or None if not found.
    """
    if not os.path.exists(VIDEOS_OUTPUT_DIR):
        return None

    # Search for mp4 files containing the video class name
    video_pattern = f"Video{video_num}"
    latest_video = None
    latest_time = 0

    for root, dirs, files in os.walk(VIDEOS_OUTPUT_DIR):
        for file in files:
            if file.endswith(".mp4") and video_pattern in root:
                file_path = os.path.join(root, file)
                file_time = os.path.getmtime(file_path)
                if file_time > latest_time:
                    latest_time = file_time
                    latest_video = file_path

    return latest_video


def generate_lectures(
    user_prompt: str,
    source_pdf_path: str | None = None,
    source_text: str | None = None,
    model: str = DEFAULT_MODEL,
    max_videos: int | None = None,
) -> list[str]:
    """
    Generate complete video lectures from a user prompt and source material.

    This function orchestrates the entire pipeline:
    1. Generate a lesson plan from the source material
    2. For each video in the plan:
       a. Generate audio narration script
       b. Run the audio script to create narration.wav
       c. Generate video animation script
       d. Run the video script with ManimGL

    Args:
        user_prompt: The learning objective / what the user wants to learn.
        source_pdf_path: Path to the source PDF file (optional if source_text provided).
        source_text: Raw text content to use as source (optional if source_pdf_path provided).
        model: The LLM model to use for all generation phases.
        max_videos: Maximum number of videos to generate. If None, generates all videos in the plan.

    Returns:
        List of relative paths to the generated video files.

    Raises:
        ValueError: If the plan cannot be parsed or no source provided.
        RuntimeError: If any step in the pipeline fails.
        FileNotFoundError: If required files are missing.
    """
    logger.info("=" * 60)
    logger.info("STARTING LECTURE GENERATION PIPELINE")
    logger.info("=" * 60)
    logger.info(f"User prompt: {user_prompt}")
    logger.info(f"Source PDF: {source_pdf_path}")
    logger.info(f"Source text provided: {bool(source_text)}")
    logger.info(f"Model: {model}")
    logger.info(f"Max videos: {max_videos if max_videos else 'unlimited'}")

    # Validate inputs
    if not source_pdf_path and not source_text:
        raise ValueError("Either source_pdf_path or source_text must be provided")

    if source_pdf_path and not os.path.exists(source_pdf_path):
        raise FileNotFoundError(f"Source PDF not found: {source_pdf_path}")

    if not os.path.exists(AUDIO_TEMPLATE_PATH):
        raise FileNotFoundError(f"Audio template not found: {AUDIO_TEMPLATE_PATH}")

    if not os.path.exists(VIDEO_TEMPLATE_PATH):
        raise FileNotFoundError(f"Video template not found: {VIDEO_TEMPLATE_PATH}")

    if not os.path.exists(MANIMATIONS_DIR):
        raise FileNotFoundError(f"Manimations directory not found: {MANIMATIONS_DIR}")

    # Step 1: Generate the lesson plan
    logger.info("-" * 60)
    logger.info("STEP 1: Generating lesson plan...")
    logger.info("-" * 60)

    try:
        plan = generate_lecture_plan(
            learning_objective=user_prompt,
            source_pdf_path=source_pdf_path,
            source_text=source_text,
            model=model,
        )
        logger.info("Successfully generated lesson plan")
        logger.info(f"Plan preview (first 500 chars):\n{plan[:500]}...")
    except Exception as e:
        logger.error(f"FAILED to generate lesson plan: {e}")
        raise

    # Step 2: Parse video count from plan
    try:
        video_count = parse_video_count(plan)
    except ValueError as e:
        logger.error(f"FAILED to parse video count: {e}")
        raise

    # Apply max_videos limit if specified
    if max_videos is not None and video_count > max_videos:
        logger.info(f"Limiting video count from {video_count} to {max_videos} (max_videos setting)")
        video_count = max_videos

    # Track generated video paths
    generated_videos: list[str] = []

    # Step 3: Generate each video
    for video_num in range(1, video_count + 1):
        logger.info("=" * 60)
        logger.info(f"PROCESSING VIDEO {video_num} OF {video_count}")
        logger.info("=" * 60)

        # Step 3a: Generate audio script
        logger.info("-" * 60)
        logger.info(f"STEP 3a: Generating audio script for Video {video_num}...")
        logger.info("-" * 60)

        try:
            audio_code = generate_audio_script(
                video_number=video_num,
                lesson_plan=plan,
                template_path=AUDIO_TEMPLATE_PATH,
                model=model,
            )
            logger.info(f"Successfully generated audio script for Video {video_num}")
        except Exception as e:
            logger.error(f"FAILED to generate audio script for Video {video_num}: {e}")
            raise

        # Strip code fences and save
        audio_code_clean = strip_code_fences(audio_code)
        save_script(audio_code_clean, AUDIO_SCRIPT_PATH)

        # Step 3b: Run audio script
        logger.info("-" * 60)
        logger.info(f"STEP 3b: Running audio script for Video {video_num}...")
        logger.info("-" * 60)

        run_command(
            command=["python3", "ai_gen_audio.py"],
            working_dir=MANIMATIONS_DIR,
            step_description=f"Audio generation for Video {video_num}",
        )

        # Step 3c: Generate video script
        logger.info("-" * 60)
        logger.info(f"STEP 3c: Generating video script for Video {video_num}...")
        logger.info("-" * 60)

        try:
            video_code = generate_video_script(
                video_number=video_num,
                lesson_plan=plan,
                video_template_path=VIDEO_TEMPLATE_PATH,
                audio_script_path=AUDIO_SCRIPT_PATH,
                model=model,
            )
            logger.info(f"Successfully generated video script for Video {video_num}")
        except Exception as e:
            logger.error(f"FAILED to generate video script for Video {video_num}: {e}")
            raise

        # Strip code fences and save
        video_code_clean = strip_code_fences(video_code)
        save_script(video_code_clean, VIDEO_SCRIPT_PATH)

        # Step 3d: Run ManimGL
        logger.info("-" * 60)
        logger.info(f"STEP 3d: Running ManimGL for Video {video_num}...")
        logger.info("-" * 60)

        run_command(
            command=["manimgl", "ai_gen_video.py", f"Video{video_num}", "-w"],
            working_dir=MANIMATIONS_DIR,
            step_description=f"ManimGL rendering for Video {video_num}",
        )

        # Find and track the generated video path
        video_path = find_latest_video(video_num)
        if video_path:
            generated_videos.append(video_path)
            logger.info(f"Generated video saved to: {video_path}")
        else:
            logger.warning(f"Could not find generated video file for Video {video_num}")

        logger.info(f"Successfully completed Video {video_num}")

    logger.info("=" * 60)
    logger.info("LECTURE GENERATION PIPELINE COMPLETE")
    logger.info(f"Generated {video_count} video(s)")
    logger.info(f"Video paths: {generated_videos}")
    logger.info("=" * 60)

    return generated_videos


if __name__ == "__main__":
    # Example usage (uses DEFAULT_MODEL by default)
    video_paths = generate_lectures(
        user_prompt="Explain backtracking algorithms and how to apply them",
        source_pdf_path="source_example/02-backtracking.pdf",
        # source_text="Alternative: pass raw text instead of PDF",
        # model="groq/llama3-70b-8192",  # Can override model here
        max_videos=2,
    )
    print(f"Generated videos: {video_paths}")
