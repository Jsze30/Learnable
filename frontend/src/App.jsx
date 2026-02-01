import { useState, useRef } from 'react'
import { ArrowUp, Microphone } from '@phosphor-icons/react'
import Beams from '@/components/Beams'
import SessionPage from '@/components/SessionPage'

function App() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [page, setPage] = useState('landing')
  const [activeTab, setActiveTab] = useState('chat')
  const [sessionPrompt, setSessionPrompt] = useState('')
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [autoStartMic, setAutoStartMic] = useState(false)
  const fileInputRef = useRef(null)

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
    setUploadedFiles([...uploadedFiles, ...files])
  }

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files || [])
    setUploadedFiles([...uploadedFiles, ...files])
  }

  const handleSendChat = () => {
    const prompt = chatInput.trim()
    if (!prompt) return
    setSessionPrompt(prompt)
    setAutoStartMic(false)
    setChatInput('')
    setIsTransitioning(true)
    setTimeout(() => {
      setPage('session')
      setIsTransitioning(false)
    }, 260)
  }

  const showLanding = page === 'landing'
  const showSession = page === 'session' || isTransitioning

  return (
    <div className="relative min-h-screen overflow-hidden">
      {showLanding && (
        <div
          className={`absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 ${
            isTransitioning ? 'page-fade-out' : ''
          }`}
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
              LearnIt
            </header>

            {/* Main Content */}
            <main className="flex flex-1 flex-col items-center justify-center gap-8 text-center">
              <h1 className="text-4xl font-bold text-white drop-shadow-lg md:text-5xl">
                Your personalized AI lecturer
              </h1>

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
                  {uploadedFiles.length > 0 && (
                    <div className="mt-3 text-left">
                      <p className="text-xs text-white/80">Uploaded files:</p>
                      <ul className="mt-2 space-y-1">
                        {uploadedFiles.map((file, idx) => (
                          <li key={idx} className="text-xs text-white/70 truncate">
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
                    onClick={() => {
                      setAutoStartMic(true)
                      setIsTransitioning(true)
                      setTimeout(() => {
                        setPage('session')
                        setIsTransitioning(false)
                      }, 260)
                    }}
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
            sessionPrompt={sessionPrompt}
            animateIn={isTransitioning}
            uploadedFiles={uploadedFiles}
            onBack={() => {
              setPage('landing')
              setAutoStartMic(false)
            }}
            autoStartMic={autoStartMic}
          />
        </div>
      )}
    </div>
  )
}

export default App
