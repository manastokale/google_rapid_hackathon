import { Bot, User } from 'lucide-react'

interface ChatMessageProps {
  role: 'user' | 'agent'
  content: string
}

function MarkdownBlock({ content }: { content: string }) {
  return (
    <div className="min-w-0 space-y-2 break-words">
      {content.split('\n').map((line, index) => {
        if (line.startsWith('## ')) {
          return <h3 key={index} className="pt-2 text-sm font-semibold uppercase tracking-wide text-violet-200">{line.replace('## ', '')}</h3>
        }
        if (line.startsWith('- ')) {
          return <p key={index} className="pl-3 text-sm text-slate-300">{line}</p>
        }
        if (/^\d+\./.test(line)) {
          return <p key={index} className="pl-3 text-sm text-slate-300">{line}</p>
        }
        if (!line.trim()) {
          return <div key={index} className="h-1" />
        }
        return <p key={index} className="text-sm leading-6 text-slate-200">{line}</p>
      })}
    </div>
  )
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isAgent = role === 'agent'
  return (
    <div className={`flex min-w-0 gap-3 ${isAgent ? '' : 'justify-end'}`}>
      {isAgent ? (
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-violet-400/20 bg-violet-500/10 text-violet-200">
          <Bot className="h-4 w-4" />
        </div>
      ) : null}
      <div className={`min-w-0 max-w-[min(44rem,calc(100%-3rem))] overflow-hidden rounded-lg border px-4 py-3 ${isAgent ? 'border-white/10 bg-slate-900/75' : 'border-emerald-400/20 bg-emerald-500/10 text-emerald-50'}`}>
        {isAgent ? <MarkdownBlock content={content} /> : <p className="break-words text-sm">{content}</p>}
      </div>
      {!isAgent ? (
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-emerald-400/20 bg-emerald-500/10 text-emerald-200">
          <User className="h-4 w-4" />
        </div>
      ) : null}
    </div>
  )
}
