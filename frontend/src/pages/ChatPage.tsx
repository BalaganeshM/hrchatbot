import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'
import { Send, MessageSquareText, Plus } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const STORAGE_KEY = 'hrchat_messages'
const SESSION_KEY = 'hrchat_session_id'

function generateSessionId(): string {
  return `${crypto.randomUUID?.() || Date.now().toString(36)}_${Date.now()}`
}

function loadSession(): { messages: Message[]; sessionId: string } {
  try {
    const msgs = sessionStorage.getItem(STORAGE_KEY)
    const sid = sessionStorage.getItem(SESSION_KEY)
    return {
      messages: msgs ? JSON.parse(msgs) : [],
      sessionId: sid || generateSessionId(),
    }
  } catch {
    return { messages: [], sessionId: generateSessionId() }
  }
}

function saveSession(messages: Message[], sessionId: string) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    sessionStorage.setItem(SESSION_KEY, sessionId)
  } catch { /* ignore */ }
}

export default function ChatPage() {
  const { user } = useAuth()
  const saved = loadSession()
  const [messages, setMessages] = useState<Message[]>(
    saved.messages.length > 0
      ? saved.messages
      : [{ role: 'assistant', content: `Hello ${user?.first_name}! I'm your HR assistant. Ask me anything about HR policies, employee information, or the organization.` }]
  )
  const [sessionId, setSessionId] = useState(saved.sessionId)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  useEffect(() => {
    saveSession(messages, sessionId)
  }, [messages, sessionId])

  const newSession = () => {
    const newId = generateSessionId()
    setSessionId(newId)
    setMessages([{ role: 'assistant', content: `Hello ${user?.first_name}! I'm your HR assistant. Ask me anything about HR policies, employee information, or the organization.` }])
    sessionStorage.removeItem(STORAGE_KEY)
    sessionStorage.setItem(SESSION_KEY, newId)
  }

  const sendMessage = async () => {
    if (!input.trim() || sending) return
    const userMsg = input.trim()
    setInput('')
    setSending(true)

    let fullContent = ''
    setMessages((prev) => [...prev, { role: 'user' as const, content: userMsg }, { role: 'assistant' as const, content: '' }])

    api.askStream(
      userMsg,
      sessionId,
      (token) => {
        fullContent += token
        setMessages((prev) => {
          const copy = [...prev]
          const last = copy[copy.length - 1]
          copy[copy.length - 1] = { role: 'assistant' as const, content: fullContent }
          return copy
        })
      },
      () => {
        setSending(false)
      },
      (err) => {
        setSending(false)
        setMessages((prev) => {
          const copy = [...prev]
          copy[copy.length - 1] = { role: 'assistant' as const, content: `Error: ${err.message}` }
          return copy
        })
      },
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessageSquareText className="w-6 h-6 text-blue-600" /> AI Chat
        </h1>
        <button
          onClick={newSession}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          <Plus className="w-4 h-4" /> New Session
        </button>
      </div>

      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-lg'
                    : 'bg-gray-100 text-gray-800 rounded-bl-lg'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-2xl rounded-bl-lg px-4 py-3 text-sm text-gray-500">
                <span className="animate-pulse">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="border-t border-gray-100 p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask me anything about HR..."
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
            />
            <button
              onClick={sendMessage}
              disabled={sending || !input.trim()}
              className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
