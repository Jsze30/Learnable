# LiveKit Voice Bot (Basic)

This is the smallest practical LiveKit voice AI agent based on the Voice AI quickstart.

## Prereqs
- Python 3.10–3.13
- LiveKit Cloud project + API keys
- LiveKit CLI installed and authenticated

## Setup
```bash
# from this repo
uv sync

# write your LiveKit Cloud keys
cp .env.local.example .env.local
# then edit .env.local with your values

# download model files needed by plugins
uv run agent.py download-files
```

## Run locally (console)
```bash
uv run agent.py console
```

## Run in dev mode (connects to LiveKit Cloud)
```bash
uv run agent.py dev
```

## Notes
- This uses the STT-LLM-TTS pipeline from the LiveKit Voice AI quickstart.
- If you prefer a realtime model (single model speech-to-speech), we can swap it.
