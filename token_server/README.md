Token server for LiveKit (local)

Setup
- Copy .env.example to .env and fill in LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET.
- Install deps: npm install
- Start server: npm run dev

Endpoint
GET /token?room=YOUR_ROOM&identity=YOUR_IDENTITY
Returns JSON: { token, livekitUrl }
