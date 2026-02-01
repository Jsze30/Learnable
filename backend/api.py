"""
Flask API for the lectures generator.

Provides REST endpoints to generate educational video lectures from
user prompts and source materials (PDF or text).
"""

import logging
import os
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
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
CORS(app)  # Enable CORS for all routes

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


@app.route("/videos/<path:filename>", methods=["GET"])
def serve_video(filename):
    """Serve video files from the 3b1b_manimations directory."""
    return send_from_directory("3b1b_manimations", filename)


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
            uploaded_file = False
            model = data.get("model", DEFAULT_MODEL)
            max_videos = data.get("max_videos")
        else:
            user_prompt = request.form.get("user_prompt")
            source_text = request.form.get("source_text")
            model = request.form.get("model", DEFAULT_MODEL)
            max_videos_str = request.form.get("max_videos")
            max_videos = int(max_videos_str) if max_videos_str else None
            uploaded_file = False

            # Always use the hardcoded template PDF
            source_pdf_path = "source_example/02-backtracking.pdf"
            logger.info(f"Using hardcoded source PDF: {source_pdf_path}")

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

        # Clean up uploaded file (only if it was actually uploaded, not a path string)
        if uploaded_file and source_pdf_path and os.path.exists(source_pdf_path):
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


@app.route("/generate-problem", methods=["POST"])
def generate_problem():
    """
    Generate a customized practice problem for tutoring.
    
    Request body:
        {
            "user_prompt": "Generate a problem about...",
            "subject": "mathematics",
            "topic": "algebra",
            "difficulty": "intermediate",
            "student_level": "intermediate"
        }
    
    Returns:
        Problem with hints and answer key
    """
    logger.info("Received /generate-problem request")
    
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        user_prompt = data.get("user_prompt", "Generate a practice problem")
        subject = data.get("subject", "general")
        
        logger.info(f"Generating problem: {user_prompt[:100]}")
        
        return jsonify({
            "success": True,
            "problem": {
                "prompt": user_prompt,
                "subject": subject,
                "hints": [
                    "Think about the key concepts",
                    "Work through the problem step by step",
                    "Check your work"
                ],
                "answer": "See the detailed explanation"
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating problem: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/track-progress", methods=["POST"])
def track_progress():
    """
    Track student progress for adaptive learning.
    
    Request body:
        {
            "student_id": "student_123",
            "session_id": "session_456",
            "topic": "algebra",
            "correct": true,
            "response_time": 45.5,
            "difficulty_level": "intermediate"
        }
    
    Returns:
        Success confirmation
    """
    logger.info("Received /track-progress request")
    
    try:
        data = request.get_json()
        
        student_id = data.get("student_id")
        session_id = data.get("session_id")
        topic = data.get("topic")
        correct = data.get("correct")
        response_time = data.get("response_time")
        difficulty_level = data.get("difficulty_level")
        
        logger.info(
            f"Progress tracked - Student: {student_id}, Topic: {topic}, "
            f"Correct: {correct}, Time: {response_time}s"
        )
        
        # Here you would typically store this in a database
        # For now, we just log it
        
        return jsonify({
            "success": True,
            "message": "Progress tracked successfully"
        }), 200
    
    except Exception as e:
        logger.error(f"Error tracking progress: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/student-insights/<student_id>", methods=["GET"])
def get_student_insights(student_id):
    """
    Get learning insights for a specific student.
    
    Returns:
        Student profile and learning analytics
    """
    logger.info(f"Received insights request for student: {student_id}")
    
    try:
        # This would typically query a database
        # For now, return a template response
        
        return jsonify({
            "success": True,
            "student_id": student_id,
            "subjects": ["mathematics", "physics", "chemistry"],
            "average_mastery": 72.5,
            "learning_style": "mixed",
            "preferred_difficulty": "intermediate",
            "recent_topics": ["algebra", "geometry", "trigonometry"],
            "strength_areas": ["geometry"],
            "improvement_areas": ["word problems"]
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting student insights: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/adaptive-content", methods=["POST"])
def generate_adaptive_content():
    """
    Generate content adapted to student's current level.
    
    Request body:
        {
            "student_id": "student_123",
            "topic": "algebra",
            "mastery_level": 65.5,
            "learning_style": "visual",
            "difficulty_adjustment": 1.2
        }
    
    Returns:
        Recommended content and resources
    """
    logger.info("Received /adaptive-content request")
    
    try:
        data = request.get_json()
        
        student_id = data.get("student_id")
        topic = data.get("topic")
        mastery_level = data.get("mastery_level", 50)
        learning_style = data.get("learning_style", "mixed")
        
        logger.info(
            f"Generating adaptive content - Student: {student_id}, "
            f"Topic: {topic}, Mastery: {mastery_level}%"
        )
        
        # Determine difficulty based on mastery
        if mastery_level >= 85:
            recommended_level = "advanced"
            recommendation = "Ready for advanced concepts and applications"
        elif mastery_level >= 60:
            recommended_level = "intermediate"
            recommendation = "Continue building mastery with guided practice"
        else:
            recommended_level = "beginner"
            recommendation = "Focus on foundational concepts with extra support"
        
        return jsonify({
            "success": True,
            "student_id": student_id,
            "topic": topic,
            "recommended_level": recommended_level,
            "recommendation": recommendation,
            "suggested_resources": [
                {"type": "video_lesson", "topic": topic, "difficulty": recommended_level},
                {"type": "practice_problem", "count": 3, "difficulty": recommended_level},
                {"type": "interactive_example", "focus": "conceptual understanding"}
            ],
            "estimated_time": "15-20 minutes"
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating adaptive content: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/session-summary", methods=["POST"])
def get_session_summary():
    """
    Get a summary of a tutoring session.
    
    Request body:
        {
            "session_id": "session_123",
            "student_id": "student_456"
        }
    
    Returns:
        Session summary with statistics
    """
    logger.info("Received /session-summary request")
    
    try:
        data = request.get_json()
        
        session_id = data.get("session_id")
        student_id = data.get("student_id")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "student_id": student_id,
            "topics_covered": [],
            "total_interactions": 0,
            "average_mastery": 0,
            "key_achievements": [],
            "areas_for_improvement": [],
            "recommended_next_topic": ""
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting session summary: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True, use_reloader=False)
