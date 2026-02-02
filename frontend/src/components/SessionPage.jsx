import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, ArrowUp, CaretDoubleLeft, CaretDoubleRight, Microphone } from '@phosphor-icons/react'
import { Room, RoomEvent, createLocalAudioTrack } from 'livekit-client'
import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'

const PANEL_MIN = 320
const PANEL_MAX = 560
const PANEL_COLLAPSED = 72

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function SessionPage({
  activeTab,
  onTabChange,
  animateIn,
  projectName,
  sources,
  onSourcesChange,
  chatMessages,
  onChatMessagesChange,
  onBack,
  autoStartMic = false,
  showVideos = false,
  isGenerating = false,
  isTyping = false,
}) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [panelWidth, setPanelWidth] = useState(420)
  const [isResizing, setIsResizing] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [currentVideo, setCurrentVideo] = useState(1)
  const [micStatus, setMicStatus] = useState('idle')
  const [micError, setMicError] = useState('')
  const roomRef = useRef(null)
  const audioTrackRef = useRef(null)
  const remoteAudioRef = useRef(null)
  const autoStartRef = useRef(false)
  const resizeFrameRef = useRef(null)
  const pendingResizeRef = useRef(null)

  useEffect(() => {
    if (!isResizing) return
    const handleMove = (event) => {
      const clientX = event.clientX ?? 0
      if (resizeFrameRef.current) {
        pendingResizeRef.current = clientX
        return
      }
      pendingResizeRef.current = clientX
      resizeFrameRef.current = requestAnimationFrame(() => {
        const nextClientX = pendingResizeRef.current ?? 0
        const viewportWidth = window.innerWidth
        const nextWidth = clamp(viewportWidth - nextClientX, PANEL_MIN, PANEL_MAX)
        setPanelWidth(nextWidth)
        setIsCollapsed(false)
        resizeFrameRef.current = null
      })
    }
    const stopResize = () => setIsResizing(false)
    window.addEventListener('mousemove', handleMove)
    window.addEventListener('mouseup', stopResize)
    return () => {
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('mouseup', stopResize)
    }
  }, [isResizing])

  useEffect(() => {
    if (!autoStartMic) {
      autoStartRef.current = false
      return
    }
    if (autoStartRef.current) return
    if (micStatus !== 'idle') return
    autoStartRef.current = true
    startMicSession()
  }, [autoStartMic, micStatus])

  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect()
      }
      if (audioTrackRef.current) {
        audioTrackRef.current.stop()
      }
      if (resizeFrameRef.current) {
        cancelAnimationFrame(resizeFrameRef.current)
        resizeFrameRef.current = null
      }
    }
  }, [])

  const mergeSources = (existing, files) => {
    const incoming = files.map((file) => ({
      id: `${file.name}-${file.size}-${file.lastModified}`,
      name: file.name,
      size: file.size,
    }))
    const known = new Set(existing.map((item) => item.id))
    return [...existing, ...incoming.filter((item) => !known.has(item.id))]
  }

  const handleDrop = (event) => {
    event.preventDefault()
    const files = Array.from(event.dataTransfer?.files || [])
    if (!files.length) return
    onSourcesChange((prev) => mergeSources(prev, files))
  }

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files || [])
    if (!files.length) return
    onSourcesChange((prev) => mergeSources(prev, files))
  }

  const handleRemoveSource = (id) => {
    onSourcesChange((prev) => prev.filter((item) => item.id !== id))
  }

  const handleSendMessage = () => {
    const trimmed = chatInput.trim()
    if (!trimmed) return
    onChatMessagesChange((prev) => [
      ...prev,
      { id: `${Date.now()}`, role: 'user', text: trimmed },
    ])
    setChatInput('')
  }

  const getLiveKitIdentity = () => {
    if (import.meta.env.VITE_LIVEKIT_IDENTITY) {
      return import.meta.env.VITE_LIVEKIT_IDENTITY
    }
    if (typeof crypto?.randomUUID === 'function') {
      return `web-${crypto.randomUUID()}`
    }
    return `web-${Math.random().toString(36).slice(2, 10)}`
  }

  const fetchLiveKitToken = async () => {
    const tokenServerUrl = import.meta.env.VITE_LIVEKIT_TOKEN_SERVER
    const livekitUrl = import.meta.env.VITE_LIVEKIT_URL
    const sandboxId = import.meta.env.VITE_LIVEKIT_SANDBOX_ID
    const roomName = import.meta.env.VITE_LIVEKIT_ROOM || 'easylearn'
    if (!tokenServerUrl || !livekitUrl) {
      throw new Error('Missing LiveKit env vars')
    }

    const params = new URLSearchParams()
    if (sandboxId) params.set('sandboxId', sandboxId)
    params.set('room', roomName)
    params.set('identity', getLiveKitIdentity())
    const requestUrl = `${tokenServerUrl}?${params.toString()}`

    const response = await fetch(requestUrl)
    if (!response.ok) {
      throw new Error('Token server request failed')
    }
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      const data = await response.json()
      const token = data.token || data.accessToken || data.jwt
      if (!token) throw new Error('Token missing in response')
      return { token, livekitUrl }
    }
    const token = (await response.text()).trim()
    if (!token) throw new Error('Token missing in response')
    return { token, livekitUrl }
  }

  const stopMicSession = async () => {
    console.log('[LiveKit] stopping mic session')
    try {
      if (roomRef.current) {
        roomRef.current.disconnect()
        roomRef.current = null
      }
      if (audioTrackRef.current) {
        audioTrackRef.current.stop()
        audioTrackRef.current = null
      }
      if (remoteAudioRef.current) {
        remoteAudioRef.current.srcObject = null
      }
    } finally {
      setMicStatus('idle')
      setMicError('')
    }
  }

  const startMicSession = async () => {
    if (micStatus === 'connecting') return
    setMicStatus('connecting')
    setMicError('')
    try {
      console.log('[LiveKit] fetching token')
      const { token, livekitUrl } = await fetchLiveKitToken()
      console.log('[LiveKit] token fetched, connecting to', livekitUrl)
      const room = new Room()
      roomRef.current = room

      room.on(RoomEvent.Disconnected, () => {
        console.log('[LiveKit] disconnected')
        if (audioTrackRef.current) {
          audioTrackRef.current.stop()
          audioTrackRef.current = null
        }
        roomRef.current = null
        if (remoteAudioRef.current) {
          remoteAudioRef.current.srcObject = null
        }
        setMicStatus('idle')
      })

      room.on(RoomEvent.TrackSubscribed, (track) => {
        console.log('[LiveKit] track subscribed', track.kind)
        if (track.kind !== 'audio') return
        if (!remoteAudioRef.current) return
        track.attach(remoteAudioRef.current)
      })

      room.on(RoomEvent.TrackUnsubscribed, (track) => {
        console.log('[LiveKit] track unsubscribed', track.kind)
        if (track.kind !== 'audio') return
        track.detach()
        if (remoteAudioRef.current) {
          remoteAudioRef.current.srcObject = null
        }
      })

      await room.connect(livekitUrl, token)
      console.log('[LiveKit] connected, creating local audio track')
      const audioTrack = await createLocalAudioTrack()
      audioTrackRef.current = audioTrack
      await room.localParticipant.publishTrack(audioTrack)
      console.log('[LiveKit] local audio published')
      setMicStatus('connected')
    } catch (error) {
      console.error('[LiveKit] start failed', error)
      setMicStatus('error')
      setMicError('Unable to start microphone session.')
      if (roomRef.current) {
        roomRef.current.disconnect()
        roomRef.current = null
      }
      if (audioTrackRef.current) {
        audioTrackRef.current.stop()
        audioTrackRef.current = null
      }
      if (remoteAudioRef.current) {
        remoteAudioRef.current.srcObject = null
      }
    }
  }

  const handleMicClick = () => {
    if (micStatus === 'connected') {
      stopMicSession()
      return
    }
    startMicSession()
  }

  const displayWidth = isCollapsed ? PANEL_COLLAPSED : panelWidth
  const panelStyles = {
    width: `${displayWidth}px`,
  }
  const toggleTab = () => {
    onTabChange(activeTab === 'chat' ? 'sources' : 'chat')
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <audio ref={remoteAudioRef} autoPlay />
      <div className="flex min-h-screen w-full">
        {/* Video / AI Response */}
        <section className="relative flex-1 overflow-hidden bg-[#0a0a0f]">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(99,102,241,0.24),transparent_55%),radial-gradient(circle_at_80%_80%,rgba(236,72,153,0.2),transparent_50%)]" />
          <div className="relative z-10 flex h-full flex-col">
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
              {onBack ? (
                <button
                  onClick={onBack}
                  className="text-lg font-semibold text-white/90 hover:text-white"
                >
                  {projectName}
                </button>
              ) : (
                <div className="text-lg font-semibold text-white/90">
                  {projectName}
                </div>
              )}
            </div>
            <div className="flex flex-1 px-6 py-4 overflow-hidden">
              <div className="flex h-full w-full flex-col items-center justify-center rounded-3xl border border-white/10 bg-white/5 p-4 overflow-hidden">
                {isGenerating && (
                  <>
                    <div className="text-sm uppercase tracking-[0.3em] text-white/50">
                      Generating
                    </div>
                    <div className="mt-2 text-2xl font-semibold text-white/80">
                      Creating your lecture...
                    </div>
                  </>
                )}
                {!isGenerating && !showVideos && (
                  <>
                    <div className="text-sm uppercase tracking-[0.3em] text-white/50">
                      Video/AI Response
                    </div>
                    <div className="mt-2 text-2xl font-semibold text-white/80">
                      Rendering Output
                    </div>
                  </>
                )}
                {!isGenerating && showVideos && (
                  <>
                    <video
                      key={currentVideo}
                      src={`/videos/Video${currentVideo}_example.mp4`}
                      controls
                      autoPlay
                      className="max-w-full max-h-[calc(100%-60px)] rounded-2xl object-contain"
                    />
                    <div className="mt-2 flex items-center gap-4">
                      {currentVideo > 1 && (
                        <button
                          onClick={() => setCurrentVideo(currentVideo - 1)}
                          className="flex items-center gap-2 rounded-full bg-white/10 px-6 py-2 text-white font-medium hover:bg-white/20 transition"
                        >
                          <ArrowLeft size={20} weight="bold" />
                          Previous video lesson
                        </button>
                      )}
                      {currentVideo < 2 && (
                        <button
                          onClick={() => setCurrentVideo(currentVideo + 1)}
                          className="flex items-center gap-2 rounded-full bg-white/10 px-6 py-2 text-white font-medium hover:bg-white/20 transition"
                        >
                          Next video lesson
                          <ArrowRight size={20} weight="bold" />
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Right Panel */}
        <aside
          style={panelStyles}
          className={`relative flex flex-col overflow-hidden border-l border-white/10 bg-[#2a1426] text-white shadow-[0_24px_60px_rgba(15,23,42,0.35)] transition-[width] duration-200 ${
            animateIn ? 'session-panel-enter' : ''
          }`}
        >
          <button
            onClick={() => setIsCollapsed((prev) => !prev)}
            className={`absolute z-10 flex items-center justify-center rounded-full border border-white/10 bg-white/5 p-2 text-white/70 transition hover:bg-white/10 hover:text-white ${
              isCollapsed
                ? 'left-1/2 top-3 -translate-x-1/2'
                : 'left-3 top-3'
            }`}
            aria-label={isCollapsed ? 'Expand panel' : 'Collapse panel'}
          >
            {isCollapsed ? (
              <CaretDoubleLeft size={16} />
            ) : (
              <CaretDoubleRight size={16} />
            )}
          </button>
          {!isCollapsed && (
            <div className="flex items-center justify-end px-4 pt-4 pb-2">
              <button
                onClick={toggleTab}
                className="inline-flex h-8 items-center justify-center rounded-full border border-white/10 bg-white/10 px-3 text-xs font-semibold uppercase tracking-wide text-white hover:bg-white/20"
              >
                {activeTab === 'chat' ? 'Sources' : 'Chat'}
              </button>
            </div>
          )}

          {!isCollapsed && (
            <div className="relative flex-1">
              <div
                className={`absolute inset-0 flex h-full flex-col transition-all duration-300 ease-out ${
                  activeTab === 'chat'
                    ? 'opacity-100 translate-x-0'
                    : 'pointer-events-none opacity-0 translate-x-4'
                }`}
              >
                <div className="flex-1 overflow-y-auto p-4">
                  <div className="flex flex-col gap-3">
                    {chatMessages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[90%] rounded-2xl p-3 text-sm shadow-sm ${
                            message.role === 'user'
                              ? 'bg-white/15 text-white text-right'
                              : 'bg-white/10 text-white text-left'
                          }`}
                        >
                          {message.role !== 'user' && (
                            <div className="text-[11px] font-semibold uppercase tracking-widest text-white/60 mb-2">
                              Lecturer
                            </div>
                          )}
                          {message.role === 'user' ? (
                            <div className="text-sm font-normal whitespace-pre-wrap">
                              {message.text}
                            </div>
                          ) : (
                            <div className="text-sm font-normal prose prose-invert prose-sm max-w-none prose-a:no-underline prose-hr:border-white/20 prose-strong:text-white prose-headings:text-white">
                              <ReactMarkdown remarkPlugins={[remarkBreaks]}>{message.text}</ReactMarkdown>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {isTyping && (
                      <div className="flex justify-start">
                        <div className="bg-white/10 rounded-2xl p-3 text-sm shadow-sm">
                          <div className="text-[11px] font-semibold uppercase tracking-widest text-white/60 mb-2">
                            Lecturer
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                            <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                            <span className="w-2 h-2 bg-white/60 rounded-full animate-bounce"></span>
                          </div>
                        </div>
                      </div>
                    )}
                    {!chatMessages.length && !isTyping && (
                      <div className="w-full rounded-2xl border border-dashed border-white/20 bg-white/10 p-3 text-left text-xs text-white/60">
                        Start the conversation to guide your lecture.
                      </div>
                    )}
                  </div>
                </div>
                <div className="border-t border-white/10 p-4">
                  <div
                    className={`flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-3 shadow-[0_12px_30px_rgba(0,0,0,0.18)] ${
                      animateIn ? 'session-input-enter' : ''
                    }`}
                  >
                    <button
                      onClick={handleMicClick}
                      aria-pressed={micStatus === 'connected'}
                      className={`flex-shrink-0 rounded-full p-2 transition ${
                        micStatus === 'connected'
                          ? 'bg-white text-[#1a1226]'
                          : 'text-white/80 hover:text-white'
                      }`}
                      title={
                        micStatus === 'connected'
                          ? 'Stop microphone'
                          : 'Start microphone'
                      }
                    >
                      <Microphone size={20} />
                    </button>
                    <input
                      type="text"
                      value={chatInput}
                      onChange={(event) => setChatInput(event.target.value)}
                      onKeyDown={(event) =>
                        event.key === 'Enter' && handleSendMessage()
                      }
                      placeholder="Send a message"
                      className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-white/50"
                    />
                    <button
                      onClick={handleSendMessage}
                      className="flex-shrink-0 rounded-full bg-white p-2 text-[#1a1226] hover:bg-white/90"
                    >
                      <ArrowUp size={16} weight="bold" />
                    </button>
                  </div>
                  {micError && (
                    <div className="mt-3 text-xs font-medium text-rose-300">
                      {micError}
                    </div>
                  )}
                </div>
              </div>

              <div
                className={`absolute inset-0 flex h-full flex-col transition-all duration-300 ease-out ${
                  activeTab === 'sources'
                    ? 'opacity-100 translate-x-0'
                    : 'pointer-events-none opacity-0 -translate-x-4'
                }`}
              >
                <div className="flex-1 overflow-y-auto p-4">
                  <div
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={handleDrop}
                    className="relative flex min-h-[140px] flex-col items-center justify-center rounded-2xl border border-dashed border-white/30 bg-white/10 p-6 text-center text-sm text-white/70 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.12)]"
                  >
                    Add course materials here
                    <div className="mt-2 text-xs text-white/50">
                      or click to upload
                    </div>
                    <input
                      type="file"
                      multiple
                      onChange={handleFileSelect}
                      className="absolute inset-0 cursor-pointer opacity-0"
                    />
                  </div>

                  <div className="mt-4 space-y-3">
                    {sources.map((source) => (
                      <div
                        key={source.id}
                        className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/10 px-3 py-2 text-sm shadow-sm"
                      >
                        <div className="min-w-0">
                          <div className="truncate font-medium text-white">
                            {source.name}
                          </div>
                          <div className="text-xs text-white/50">
                            {(source.size / 1024).toFixed(1)} KB
                          </div>
                        </div>
                        <button
                          onClick={() => handleRemoveSource(source.id)}
                          className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs font-semibold text-white/80 hover:bg-white/20"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                    {!sources.length && (
                      <div className="rounded-2xl border border-dashed border-white/20 bg-white/5 px-3 py-6 text-center text-xs text-white/50">
                        No sources yet. Add files to ground the lecture.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {isCollapsed && <div className="flex h-full items-center justify-center" />}
        </aside>
      </div>
    </div>
  )
}

export default SessionPage
