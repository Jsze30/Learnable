# Learnable

## The Problem We Are Solving

Traditional education often relies on static textbooks and one-size-fits-all lecture formats that don't engage all learning styles. Students struggle to find personalized, visual explanations of complex topics, and educators spend countless hours creating educational content. The process of transforming educational materials (like PDFs) into engaging, animated video lectures is time-consuming, expensive, and requires specialized skills in both pedagogy and video production.

EasyLearn solves this by automating the entire process of generating professional-quality educational videos from source materials in minutes.

## Our Solution

EasyLearn is an AI-powered educational content generation platform that transforms course materials and prompts into engaging animated video lectures. The system uses a multi-phase pipeline that leverages state-of-the-art LLMs and the ManimGL animation engine (used by 3Blue1Brown) to create visually stunning educational videos with synchronized narration.

Users can:

- Upload PDF course materials or provide text
- Request videos on specific topics
- Interact with an AI voice tutor in real-time
- Get automatically generated, professionally-animated video lectures complete with synchronized narration

## Our Overall Architecture

EasyLearn is built as a distributed system with four main components:

### 1. **Frontend (React + Vite)**

Located in `/frontend`, this is the user-facing web application built with React 19, Tailwind CSS, and Three.js for 3D visualizations. Features include:

- Interactive subject/topic management
- File upload for PDF course materials
- Real-time chat with the AI voice tutor via LiveKit
- Video playback and session management
- Beautiful animated UI with GSAP animations

### 2. **Backend Video Generation Service (Python)**

Located in `/backend`, this is the core content generation engine with a three-phase pipeline:

**Phase 1: Plan Generation** (`plan_phase.py`)

- Extracts text from user-provided PDFs
- Uses KeywordsAI prompt management with LLMs (default: `groq/openai/gpt-oss-120b`)
- Generates structured lesson plans that outline video content

**Phase 2: Audio Generation** (`audio_phase.py`)

- Takes the lesson plan and generates detailed narration scripts
- Uses KeywordsAI-managed prompts for consistent quality
- Scripts are optimized for Deepgram Text-to-Speech synthesis

**Phase 3: Video Animation** (`video_phase.py`)

- Generates ManimGL (3Blue1Brown's animation engine) Python code
- Creates synchronized animations that match the audio narration
- Renders professional-quality animated videos

**API Server** (`api.py`)

- Flask REST API that orchestrates the full pipeline
- Handles multipart file uploads (PDFs up to 50MB)
- Manages video generation requests and returns video paths
- CORS-enabled for frontend integration

**ManimGL Animation System** (`3b1b_manimations/`)

- Custom configuration and automation scripts
- Generated animation code execution
- Audio and video synthesis and rendering

### 3. **Voice AI Tutor (Python + LiveKit)**

Located in `/voice_agent`, this is a real-time conversational AI tutor:

- Uses LiveKit for WebRTC-based real-time communication
- Integrates with Deepgram for speech recognition (via `deepgram/nova-3`)
- Uses OpenAI GPT-4.1-mini as the language model
- Dynamically loads course context from PDFs
- Provides personalized tutoring sessions with natural conversation flow
- Features multilingual turn detection and noise cancellation

### 4. **Token Server (Node.js)**

Located in `/token_server`, this is a lightweight authentication service:

- Issues LiveKit access tokens for secure WebRTC connections
- Handles token generation with proper permissions
- Enables secure, authenticated voice sessions between frontend and voice agent

## Features

### Content Generation

- **Automated Lesson Planning**: AI-generated structured lesson plans from course materials
- **Intelligent Script Generation**: LLM-powered narration scripts optimized for TTS
- **Professional Animation**: ManimGL-based animations that match mathematical and educational content
- **Quality Video Output**: Rendered videos with synchronized audio and visuals
- **Flexible Input**: Support for PDF uploads or direct text input

### Interactive Learning

- **Real-time Voice Tutoring**: Live conversational AI assistant powered by LiveKit
- **Context-Aware Responses**: Tutor references uploaded course materials
- **Natural Speech**: High-quality TTS with Deepgram's Aura model
- **Multi-subject Support**: Manage multiple subjects/topics simultaneously
- **Session Management**: Track chat history and learning sessions

### User Experience

- **Modern Web Interface**: React-based responsive design with Tailwind CSS
- **Smooth Animations**: GSAP-powered transitions and interactive elements
- **Real-time Interaction**: Instant feedback from AI systems
- **File Management**: Intuitive upload and management of course materials
- **Video Playback**: Integrated viewer for generated videos

### Technical Features

- **LLM Integration**: Support for multiple LLM providers (Azure, Groq, OpenAI)
- **Prompt Management**: KeywordsAI-based prompt versioning and deployment
- **Scalable API**: RESTful Flask backend with CORS support
- **Secure Communication**: LiveKit-based encrypted WebRTC connections
- **Extensible Architecture**: Modular design for adding new features and providers
