import http from 'http'
import { URL } from 'url'
import { AccessToken } from 'livekit-server-sdk'
import { config } from 'dotenv'

config()

const PORT = Number(process.env.PORT || 3001)
const API_KEY = process.env.LIVEKIT_API_KEY
const API_SECRET = process.env.LIVEKIT_API_SECRET
const LIVEKIT_URL = process.env.LIVEKIT_URL

const sendJson = (res, statusCode, body) => {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  })
  res.end(JSON.stringify(body))
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`)
  if (req.method !== 'GET') {
    return sendJson(res, 405, { error: 'Method not allowed' })
  }

  if (url.pathname !== '/token') {
    return sendJson(res, 404, { error: 'Not found' })
  }

  if (!API_KEY || !API_SECRET) {
    return sendJson(res, 500, { error: 'Missing LIVEKIT_API_KEY/SECRET' })
  }

  const room = url.searchParams.get('room') || 'easylearn'
  const identity = url.searchParams.get('identity') || `web-${Date.now()}`

  const token = new AccessToken(API_KEY, API_SECRET, { identity })
  token.addGrant({
    room,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  })

  return token
    .toJwt()
    .then((jwt) =>
      sendJson(res, 200, {
        token: jwt,
        livekitUrl: LIVEKIT_URL || null,
      })
    )
    .catch((err) =>
      sendJson(res, 500, { error: 'Failed to generate token', detail: err.message })
    )
})

server.listen(PORT, () => {
  console.log(`Token server listening on http://localhost:${PORT}`)
})
