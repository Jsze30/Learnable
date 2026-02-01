import { useEffect, useRef, useState } from 'react'
import { CaretDoubleLeft, CaretDoubleRight, Plus, X } from '@phosphor-icons/react'

const getInitials = (name) =>
  name
    .split(' ')
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()

function SubjectTabManager({
  subjects,
  activeSubjectId,
  onSelect,
  onAdd,
  onDelete,
  onRename,
  isCollapsed,
  onToggleCollapse,
}) {
  const [editingId, setEditingId] = useState(null)
  const [draftName, setDraftName] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    if (!editingId) return
    inputRef.current?.focus()
    inputRef.current?.select()
  }, [editingId])

  const startRename = (subject) => {
    setEditingId(subject.id)
    setDraftName(subject.name)
  }

  const commitRename = () => {
    const trimmed = draftName.trim()
    if (editingId && trimmed) {
      onRename(editingId, trimmed)
    }
    setEditingId(null)
    setDraftName('')
  }

  const cancelRename = () => {
    setEditingId(null)
    setDraftName('')
  }

  return (
    <aside
      className={`relative flex h-screen flex-col overflow-hidden border-r border-white/10 bg-gradient-to-b from-[#0e0b1c] via-[#141225] to-[#0b0b13] text-white transition-[width] duration-200 ${
        isCollapsed ? 'w-20' : 'w-72'
      }`}
    >
      <div className="flex items-center justify-between px-4 pt-5 pb-3">
        {!isCollapsed && (
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-white/60">
            Subjects
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          className={`rounded-full border border-white/10 bg-white/5 p-2 text-white/70 transition hover:bg-white/10 hover:text-white ${
            isCollapsed ? 'mx-auto' : ''
          }`}
          aria-label={isCollapsed ? 'Expand subject tabs' : 'Collapse subject tabs'}
        >
          {isCollapsed ? (
            <CaretDoubleRight size={16} />
          ) : (
            <CaretDoubleLeft size={16} />
          )}
        </button>
      </div>

      {!isCollapsed && (
        <div className="px-4 pb-3">
          <button
            onClick={onAdd}
            className="flex w-full items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white/90 transition hover:bg-white/10"
          >
            New subject
            <Plus size={16} weight="bold" />
          </button>
        </div>
      )}

      {isCollapsed && (
        <div className="flex items-center justify-center px-3 pb-3">
          <button
            onClick={onAdd}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/80 transition hover:bg-white/10"
            aria-label="Create new subject"
          >
            <Plus size={16} weight="bold" />
          </button>
        </div>
      )}

      <div className="flex-1 space-y-2 overflow-y-auto px-3 pb-6">
        {subjects.map((subject) => {
          const isActive = subject.id === activeSubjectId
          return (
            <div
              key={subject.id}
              className={`group relative flex items-center ${
                isCollapsed ? 'justify-center' : 'justify-between'
              }`}
            >
              <button
                onClick={() => onSelect(subject.id)}
                className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-3 text-left text-sm font-semibold transition ${
                  isActive
                    ? 'border-white/30 bg-white/15 text-white'
                    : 'border-white/5 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white'
                } ${isCollapsed ? 'justify-center px-2' : ''}`}
              >
                <span
                  className={`flex h-9 w-9 items-center justify-center rounded-xl text-xs font-bold ${
                    isActive ? 'bg-white text-[#1a1226]' : 'bg-white/10 text-white/80'
                  }`}
                >
                  {getInitials(subject.name)}
                </span>
                {!isCollapsed && (
                  <>
                    {editingId === subject.id ? (
                      <input
                        ref={inputRef}
                        value={draftName}
                        onChange={(event) => setDraftName(event.target.value)}
                        onBlur={commitRename}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') commitRename()
                          if (event.key === 'Escape') cancelRename()
                        }}
                        className="min-w-0 flex-1 truncate rounded-lg border border-white/20 bg-white/10 px-2 py-1 text-sm font-semibold text-white outline-none"
                      />
                    ) : (
                      <span
                        onDoubleClick={() => startRename(subject)}
                        className="min-w-0 flex-1 truncate"
                      >
                        {subject.name}
                      </span>
                    )}
                  </>
                )}
              </button>
              {!isCollapsed && (
                <button
                  onClick={(event) => {
                    event.stopPropagation()
                    onDelete(subject.id)
                  }}
                  className={`absolute right-3 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white/60 transition hover:text-white ${
                    isActive
                      ? 'border border-white/20'
                      : 'border border-white/10'
                  }`}
                  aria-label={`Delete ${subject.name}`}
                >
                  <X size={12} />
                </button>
              )}
            </div>
          )
        })}
      </div>

      {!isCollapsed && <div className="border-t border-white/10 px-5 py-4" />}
    </aside>
  )
}

export default SubjectTabManager
