import { FormEvent, useEffect, useRef, useState } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { ChatMessage } from '../components/ChatMessage'
import { ServiceHop, ServiceLoading } from '../components/ServiceLoading'
import { agentApi } from '../services/api'

interface Message {
  role: 'user' | 'agent'
  content: string
}

const chatMessagesKey = 'margintrust.agent.messages'
const chatInputKey = 'margintrust.agent.input'
const chatSessionKey = 'margintrust.agent.session'

const initialMessages: Message[] = [
  {
    role: 'agent',
    content: '## Finding\nAsk me about underbilling, expansion gaps, or dashboard trust. I will quantify impact and recommend owners/actions.',
  },
]

const suggestions = [
  'Are we underbilling any enterprise customers this week?',
  'Which accounts are ready for expansion but missing from CRM pipeline?',
  'Can I trust the revenue dashboard today?',
]

function readMessages(): Message[] {
  if (typeof window === 'undefined') return initialMessages
  try {
    const stored = window.localStorage.getItem(chatMessagesKey)
    if (!stored) return initialMessages
    const parsed = JSON.parse(stored)
    if (!Array.isArray(parsed)) return initialMessages
    return parsed.filter((message) => message?.role && typeof message.content === 'string')
  } catch {
    return initialMessages
  }
}

function readInput(): string {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem(chatInputKey) ?? ''
}

function readSessionId(): string {
  if (typeof window === 'undefined') return 'default'
  const stored = window.localStorage.getItem(chatSessionKey)
  if (stored) return stored
  const created = crypto.randomUUID?.() ?? `session-${Date.now()}`
  window.localStorage.setItem(chatSessionKey, created)
  return created
}

const chatHops: ServiceHop[] = [
  { label: 'Prompt', detail: 'Queued in UI', kind: 'ui' },
  { label: 'Agent API', detail: 'Session route', kind: 'api' },
  { label: 'ADK agent', detail: 'Tool selection', kind: 'agent' },
  { label: 'BigQuery', detail: 'Evidence lookup', kind: 'warehouse' },
  { label: 'Answer', detail: 'Risk summary', kind: 'score' },
]

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(readMessages)
  const [input, setInput] = useState(readInput)
  const [sessionId] = useState(readSessionId)
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    window.localStorage.setItem(chatMessagesKey, JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    window.localStorage.setItem(chatInputKey, input)
  }, [input])

  useEffect(() => {
    const node = scrollRef.current
    if (node) {
      node.scrollTop = node.scrollHeight
    }
  }, [messages, loading])

  const send = async (message: string) => {
    const trimmed = message.trim()
    if (!trimmed || loading) return
    setMessages((items) => [...items, { role: 'user', content: trimmed }])
    setInput('')
    setLoading(true)
    try {
      const response = await agentApi.chat(trimmed, sessionId)
      setMessages((items) => [...items, { role: 'agent', content: response.data.answer }])
    } catch {
      setMessages((items) => [...items, { role: 'agent', content: '## Finding\nThe agent endpoint is unavailable. Start the FastAPI backend and retry.' }])
    } finally {
      setLoading(false)
    }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    void send(input)
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-7rem)] max-h-[calc(100vh-7rem)] min-h-0 max-w-5xl flex-col gap-4 overflow-hidden">
      <div className="surface shrink-0 rounded-lg p-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-lg border border-violet-400/20 bg-violet-500/10 text-violet-200">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white">MarginTrust agent</h1>
            <p className="text-sm text-slate-400">Gemini ADK-ready with deterministic local demo mode.</p>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 hover:bg-white/10"
              onClick={() => void send(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      <div className="surface flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg p-5">
        <div ref={scrollRef} className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain pr-2">
          {messages.map((message, index) => <ChatMessage key={index} {...message} />)}
          {loading ? (
            <ServiceLoading
              title="Tracing agent workflow"
              caption="Usage, billing, CRM, and connector evidence are being assembled."
              hops={chatHops}
              compact
              framed={false}
            />
          ) : null}
        </div>
      </div>

      <form onSubmit={submit} className="surface flex shrink-0 gap-3 rounded-lg p-3">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          className="min-w-0 flex-1 rounded-md border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none focus:border-violet-300/50"
          placeholder="Ask about revenue leakage"
        />
        <button
          className="grid h-12 w-12 shrink-0 place-items-center rounded-md bg-violet-500 text-white hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={loading || !input.trim()}
          title="Send"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  )
}
