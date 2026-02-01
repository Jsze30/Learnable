"""
Flask API for the lectures generator.

Provides REST endpoints to generate educational video lectures from
user prompts and source materials (PDF or text).
"""

import logging
import os
import tempfile
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

from lectures_generator import generate_lectures, DEFAULT_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max file size


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route("/generate", methods=["POST"])
def generate():
    """
    Generate video lectures from user prompt and source material.

    Request can be either:
    1. JSON body with user_prompt and source_text
    2. Multipart form with user_prompt and source_pdf file

    Request body (JSON):
        {
            "user_prompt": "Explain backtracking algorithms",
            "source_text": "Optional source text content...",
            "model": "azure/gpt-5",  // optional, defaults to DEFAULT_MODEL
            "max_videos": 3  // optional, defaults to unlimited
        }

    Request body (multipart/form-data):
        - user_prompt: string (required)
        - source_pdf: file (optional)
        - source_text: string (optional)
        - model: string (optional)
        - max_videos: int (optional)

    Returns:
        JSON response with list of generated video paths:
        {
            "success": true,
            "videos": ["3b1b_manimations/videos/Video1/...", ...],
            "count": 3
        }

        Or error response:
        {
            "success": false,
            "error": "Error message"
        }
    """
    logger.info("Received /generate request")

    try:
        # Parse request parameters
        if request.is_json:
            data = request.get_json()
            user_prompt = data.get("user_prompt")
            source_text = data.get("source_text")
            source_pdf_path = None
            model = data.get("model", DEFAULT_MODEL)
            max_videos = data.get("max_videos")
        else:
            user_prompt = request.form.get("user_prompt")
            source_text = request.form.get("source_text")
            model = request.form.get("model", DEFAULT_MODEL)
            max_videos_str = request.form.get("max_videos")
            max_videos = int(max_videos_str) if max_videos_str else None
            source_pdf_path = None

            # Handle file upload
            if "source_pdf" in request.files:
                file = request.files["source_pdf"]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    source_pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(source_pdf_path)
                    logger.info(f"Saved uploaded PDF to: {source_pdf_path}")
                elif file and file.filename:
                    return jsonify({
                        "success": False,
                        "error": "Invalid file type. Only PDF files are allowed."
                    }), 400

        # Validate required parameters
        if not user_prompt:
            return jsonify({
                "success": False,
                "error": "user_prompt is required"
            }), 400

        if not source_pdf_path and not source_text:
            return jsonify({
                "success": False,
                "error": "Either source_pdf or source_text must be provided"
            }), 400

        logger.info(f"Generating lectures for prompt: {user_prompt[:100]}...")
        logger.info(f"Model: {model}")
        logger.info(f"Max videos: {max_videos}")

        # Generate lectures
        video_paths = generate_lectures(
            user_prompt=user_prompt,
            source_pdf_path=source_pdf_path,
            source_text=source_text,
            model=model,
            max_videos=max_videos,
        )

        # Clean up uploaded file
        if source_pdf_path and os.path.exists(source_pdf_path):
            os.remove(source_pdf_path)
            logger.info(f"Cleaned up uploaded file: {source_pdf_path}")

        return jsonify({
            "success": True,
            "videos": video_paths,
            "count": len(video_paths),
        }), 200

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except RuntimeError as e:
        logger.error(f"Runtime error during generation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return jsonify({
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True, use_reloader=False)
