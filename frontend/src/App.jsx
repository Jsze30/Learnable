import { useState, useRef } from 'react'
import Beams from '@/components/Beams'
import { Button } from '@/components/ui/button'

function App() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [chatInput, setChatInput] = useState('')
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
    if (chatInput.trim()) {
      // Handle chat send
      setChatInput('')
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500">
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
            <div className="flex items-center gap-2 rounded-full bg-white/10 px-4 py-3 backdrop-blur-md">
              <button className="flex-shrink-0 text-white/70 hover:text-white text-lg">
                +
              </button>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendChat()}
                placeholder="Ask anything"
                className="flex-1 bg-transparent text-white placeholder:text-white/50 outline-none"
              />
              <button className="flex-shrink-0 text-white/70 hover:text-white text-lg">
                🎤
              </button>
              <button
                onClick={handleSendChat}
                className="flex-shrink-0 rounded-full bg-black p-2 text-white hover:bg-black/80"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
