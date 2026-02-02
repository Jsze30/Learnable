import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowUp, Microphone } from '@phosphor-icons/react'
import Beams from '@/components/Beams'
import SplitText from '@/components/SplitText'
import SessionPage from '@/components/SessionPage'
import SubjectTabManager from '@/components/SubjectTabManager'

const makeSubjectId = () => {
  if (typeof crypto?.randomUUID === 'function') {
    return `subject-${crypto.randomUUID()}`
  }
  return `subject-${Math.random().toString(36).slice(2, 10)}`
}

const createSubject = (name) => ({
  id: makeSubjectId(),
  name,
  chatMessages: [],
  sources: [],
})

const mergeSources = (existing, files) => {
  const incoming = files.map((file) => ({
    id: `${file.name}-${file.size}-${file.lastModified}`,
    name: file.name,
    size: file.size,
    file: file, // Store actual File object for API calls
  }))
  const known = new Set(existing.map((item) => item.id))
  return [...existing, ...incoming.filter((item) => !known.has(item.id))]
}

function App() {
  const [isDragging, setIsDragging] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [page, setPage] = useState('landing')
  const [activeTab, setActiveTab] = useState('chat')
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [autoStartMic, setAutoStartMic] = useState(false)
  const [isTabManagerCollapsed, setIsTabManagerCollapsed] = useState(true)
  const [subjects, setSubjects] = useState([])
  const [activeSubjectId, setActiveSubjectId] = useState(null)
  const fileInputRef = useRef(null)
  const transitionTimeoutRef = useRef(null)
  const [landingKey, setLandingKey] = useState(0)
  const [showVideos, setShowVideos] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    if (!subjects.length) {
      if (activeSubjectId !== null) {
        setActiveSubjectId(null)
      }
      return
    }
    if (!subjects.some((subject) => subject.id === activeSubjectId)) {
      setActiveSubjectId(subjects[0].id)
    }
  }, [activeSubjectId, subjects])

  useEffect(() => {
    return () => {
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (page === 'landing') {
      setLandingKey((prev) => prev + 1)
    }
  }, [page])

  const activeSubject = useMemo(() => {
    return subjects.find((subject) => subject.id === activeSubjectId) || null
  }, [activeSubjectId, subjects])

  const updateSubjectById = (subjectId, updater) => {
    if (!subjectId) return
    setSubjects((prev) =>
      prev.map((subject) =>
        subject.id === subjectId ? updater(subject) : subject
      )
    )
  }

  const getNextSubjectName = (existing) =>
    `New Subject ${existing.length + 1}`

  const ensureSubjectForSession = () => {
    if (activeSubjectId) return activeSubjectId
    const newSubject = createSubject(getNextSubjectName(subjects))
    setSubjects((prev) => [...prev, newSubject])
    setActiveSubjectId(newSubject.id)
    return newSubject.id
  }

  const triggerSessionTransition = () => {
    if (transitionTimeoutRef.current) {
      clearTimeout(transitionTimeoutRef.current)
    }
    setPage('session')
    setIsTransitioning(true)
    transitionTimeoutRef.current = setTimeout(() => {
      setIsTransitioning(false)
    }, 50)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (!files.length) return
    const targetSubjectId = ensureSubjectForSession()
    updateSubjectById(targetSubjectId, (subject) => ({
      ...subject,
      sources: mergeSources(subject.sources, files),
    }))
  }

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    const targetSubjectId = ensureSubjectForSession()
    updateSubjectById(targetSubjectId, (subject) => ({
      ...subject,
      sources: mergeSources(subject.sources, files),
    }))
    e.target.value = ''
  }

  const handleSendChat = async () => {
    const prompt = chatInput.trim()
    if (!prompt) return
    const targetSubjectId = ensureSubjectForSession()
    setAutoStartMic(false)
    setChatInput('')

    updateSubjectById(targetSubjectId, (subject) => ({
      ...subject,
      chatMessages: [
        ...subject.chatMessages,
        { id: `prompt-${Date.now()}`, role: 'user', text: prompt },
      ],
    }))
    triggerSessionTransition()

    // Show loading for 10 seconds, then display videos
    setIsGenerating(true)
    setShowVideos(false)
    setTimeout(() => {
      setIsGenerating(false)
      setShowVideos(true)
    }, 10000)

    // Send assistant response with plan after 3 seconds
    const planText = `**Back‑tracking Mini‑Series – Text‑only Plan**

---

### Video 1 – Backtracking in a Nutshell
**Learning goal** – Know what backtracking is and why it works.
**Core ideas**
1. The algorithm builds a decision tree; each node represents a partial solution.
2. It walks the tree depth‑first: try a choice, go deeper, and when the choice fails it "undoes" it and tries the next one.
3. The call‑stack holds the current choices; pushing a choice = going deeper, popping = back‑track.
4. Two kinds of leaf nodes: a complete solution (success) or a dead end (failure).

**Key intuition** – Imagine a maze explorer who leaves a rope at every fork. When she hits a wall she pulls the rope back to the last fork and tries the other tunnel. The rope is the recursion stack.

---

### Video 2 – Recursion Tree and Base Cases
**Learning goal** – See how a backtracking algorithm is represented as a recursion tree and understand the role of base cases.
**Core ideas**
1. Each recursive call is a node; the parameters of the call encode the current state (the partial solution).
2. Children of a node correspond to all legal next decisions.
3. A leaf node appears when the algorithm reaches a base case: either a full solution or a situation where no further legal move exists.
4. The whole tree is a depth‑first search of the state space.

**Key intuition** – Think of a stack of plates: adding a plate means making a new decision, removing a plate means back‑tracking. When the stack is empty we have hit a base case.`

    // Show typing indicator after 1 second
    setTimeout(() => {
      setIsTyping(true)
    }, 1000)

    // Send assistant response after 3 seconds (typing for 2 seconds)
    setTimeout(() => {
      setIsTyping(false)
      updateSubjectById(targetSubjectId, (subject) => ({
        ...subject,
        chatMessages: [
          ...subject.chatMessages,
          { id: `response-${Date.now()}`, role: 'assistant', text: planText },
        ],
      }))
    }, 3000)

    // Make the API call in background
    try {
      console.log({"prompt": prompt})
      const formData = new FormData()
      formData.append('user_prompt', prompt)
      formData.append('model', 'azure/gpt-5')
      formData.append('max_videos', '2')

      const response = await fetch('http://localhost:3000/generate', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      console.log('Generate API response:', data)
    } catch (error) {
      console.error('Failed to call generate API:', error)
    }
  }

  const handleAddSubject = () => {
    const subjectIndex = subjects.length + 1
    const newSubject = createSubject(`New Subject ${subjectIndex}`)
    setSubjects((prev) => [...prev, newSubject])
    setActiveSubjectId(newSubject.id)
    setChatInput('')
    setActiveTab('chat')
    setIsTransitioning(false)
    setAutoStartMic(false)
    setPage('landing')
  }

  const handleDeleteSubject = (id) => {
    setSubjects((prev) => {
      const next = prev.filter((subject) => subject.id !== id)
      if (!next.length) {
        setActiveSubjectId(null)
        setPage('landing')
        setIsTransitioning(false)
        return next
      }
      if (activeSubjectId === id && next.length) {
        const mostRecent = next[next.length - 1]
        setActiveSubjectId(mostRecent.id)
        if (mostRecent.chatMessages.length) {
          triggerSessionTransition()
        } else {
          setPage('landing')
          setIsTransitioning(false)
        }
      } else if (activeSubjectId === id) {
        setActiveSubjectId(null)
        setPage('landing')
        setIsTransitioning(false)
      }
      return next
    })
  }

  const handleChatMessagesChange = (updater) => {
    updateSubjectById(activeSubjectId, (subject) => {
      const nextMessages =
        typeof updater === 'function' ? updater(subject.chatMessages) : updater
      return { ...subject, chatMessages: nextMessages }
    })
  }

  const handleSourcesChange = (updater) => {
    updateSubjectById(activeSubjectId, (subject) => {
      const nextSources =
        typeof updater === 'function' ? updater(subject.sources) : updater
      return { ...subject, sources: nextSources }
    })
  }

  const handleSelectSubject = (id) => {
    if (id === activeSubjectId) return
    setActiveSubjectId(id)
    const selected = subjects.find((subject) => subject.id === id)
    if (selected?.chatMessages?.length) {
      if (page === 'session' && !isTransitioning) {
        setPage('session')
        setIsTransitioning(false)
      } else {
        triggerSessionTransition()
      }
    } else {
      setPage('landing')
      setIsTransitioning(false)
    }
    setAutoStartMic(false)
  }

  const handleRenameSubject = (id, name) => {
    setSubjects((prev) =>
      prev.map((subject) => (subject.id === id ? { ...subject, name } : subject))
    )
  }

  const handleStartMicFromLanding = () => {
    ensureSubjectForSession()
    setAutoStartMic(true)
    triggerSessionTransition()
  }

  const showLanding =
    page === 'landing' || !activeSubjectId || (page === 'session' && isTransitioning)
  const showSession = activeSubjectId && (page === 'session' || isTransitioning)

  return (
    <div className="min-h-screen overflow-hidden">
      <div className="flex min-h-screen w-full">
        <SubjectTabManager
          subjects={subjects}
          activeSubjectId={activeSubjectId}
          isCollapsed={isTabManagerCollapsed}
          onToggleCollapse={() =>
            setIsTabManagerCollapsed((prev) => !prev)
          }
          onSelect={handleSelectSubject}
          onAdd={handleAddSubject}
          onDelete={handleDeleteSubject}
          onRename={handleRenameSubject}
        />

        <div className="relative flex-1 overflow-hidden bg-[#0a0a0f]">
          {showLanding && (
            <div
              className="absolute inset-0 bg-[#0a0a0f]"
            >
              <div className="absolute inset-0">
                <Beams
                  beamWidth={2.6}
                  beamHeight={22}
                  beamNumber={9}
                  lightColor="#ceadff"
                  speed={1.1}
                  noiseIntensity={0.19}
                  scale={0.22}
                  rotation={30}
                />
              </div>

              <div className="relative z-10 flex min-h-screen w-full flex-col px-6 py-8">
                {/* Header */}
                <header className="text-2xl font-bold text-white drop-shadow-lg">
                  Learnable
                </header>

                {/* Main Content */}
                <main className="flex flex-1 flex-col items-center justify-center gap-8 text-center">
                  <SplitText
                    key={landingKey}
                    tag="h1"
                    text="Your personalized AI lecturer"
                    className="text-4xl font-bold text-white drop-shadow-lg md:text-5xl font-['Inter']"
                    delay={30}
                    duration={0.3}
                    ease="power3.out"
                    splitType="chars"
                    from={{ opacity: 0, y: 40 }}
                    to={{ opacity: 1, y: 0 }}
                    threshold={0.1}
                    rootMargin="-100px"
                    textAlign="center"
                  />

                  <div className="w-full max-w-2xl">
                    {/* Upload Box */}
                    <div
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`mb-4 cursor-pointer rounded-2xl border-2 border-dashed p-6 transition-colors ${
                        isDragging
                          ? 'border-white bg-white/20'
                          : 'border-white/50 bg-white/10 hover:bg-white/15'
                      }`}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        onChange={handleFileSelect}
                        className="hidden"
                      />
                      <p className="text-sm font-semibold text-white">
                        Upload your course materials here
                      </p>
                      {activeSubject?.sources?.length > 0 && (
                        <div className="mt-3 text-left">
                          <p className="text-xs text-white/80">Uploaded files:</p>
                          <ul className="mt-2 space-y-1">
                            {activeSubject.sources.map((file) => (
                              <li
                                key={file.id}
                                className="text-xs text-white/70 truncate"
                              >
                                • {file.name}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Chat Input Bar */}
                    <div
                      className={`flex items-center gap-2 rounded-full bg-white/10 px-4 py-3 backdrop-blur-md ${
                        isTransitioning ? 'landing-input-exit' : ''
                      }`}
                    >
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                        placeholder="Ask anything"
                        className="flex-1 bg-transparent text-white placeholder:text-white/50 outline-none"
                      />
                      <button
                        onClick={handleStartMicFromLanding}
                        className="flex-shrink-0 text-white/70 hover:text-white"
                      >
                        <Microphone size={20} />
                      </button>
                      <button
                        onClick={handleSendChat}
                        className="flex-shrink-0 rounded-full bg-black p-2 text-white hover:bg-black/80"
                      >
                        <ArrowUp size={16} weight="bold" />
                      </button>
                    </div>
                  </div>
                </main>
              </div>
            </div>
          )}

          {showSession && (
            <div
              className={`absolute inset-0 ${
                isTransitioning ? 'page-fade-in' : ''
              }`}
            >
              <SessionPage
                activeTab={activeTab}
                onTabChange={setActiveTab}
                animateIn={isTransitioning}
                projectName="Learnable"
                sources={activeSubject?.sources || []}
                onSourcesChange={handleSourcesChange}
                chatMessages={activeSubject?.chatMessages || []}
                onChatMessagesChange={handleChatMessagesChange}
                onBack={() => {
                  setPage('landing')
                  setAutoStartMic(false)
                }}
                autoStartMic={autoStartMic}
                showVideos={showVideos}
                isGenerating={isGenerating}
                isTyping={isTyping}
              />


            </div>
          )}
        </div>

      </div>
    </div>
  )
}

export default App
