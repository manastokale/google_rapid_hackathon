import { FormEvent, useState } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { ChatMessage } from '../components/ChatMessage'
import { agentApi } from '../services/api'

interface Message {
  role: 'user' | 'agent'
  content: string
}

const suggestions = [
  'Are we underbilling any enterprise customers this week?',
  'Which accounts are ready for expansion but missing from CRM pipeline?',
  'Can I trust the revenue dashboard today?',
]

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'agent',
      content: '## Finding\nAsk me about underbilling, expansion gaps, or dashboard trust. I will quantify impact and recommend owners/actions.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const send = async (message: string) => {
    const trimmed = message.trim()
    if (!trimmed || loading) return
    setMessages((items) => [...items, { role: 'user', content: trimmed }])
    setInput('')
    setLoading(true)
    try {
      const response = await agentApi.chat(trimmed)
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
    <div className="mx-auto flex max-w-5xl flex-col gap-5">
      <div className="surface rounded-lg p-5">
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

      <div className="surface min-h-[520px] rounded-lg p-5">
        <div className="space-y-5">
          {messages.map((message, index) => <ChatMessage key={index} {...message} />)}
          {loading ? (
            <div className="flex items-center gap-3 text-sm text-slate-400">
              <div className="h-2 w-2 animate-pulse rounded-full bg-violet-300" />
              Analyzing usage, billing, CRM, and connector health
            </div>
          ) : null}
        </div>
      </div>

      <form onSubmit={submit} className="surface flex gap-3 rounded-lg p-3">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          className="min-w-0 flex-1 rounded-md border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none focus:border-violet-300/50"
          placeholder="Ask about revenue leakage"
        />
        <button className="grid h-12 w-12 place-items-center rounded-md bg-violet-500 text-white hover:bg-violet-400" title="Send">
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  )
}

