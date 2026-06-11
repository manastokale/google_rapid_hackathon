import {
  BarChart3,
  Bot,
  BrainCircuit,
  CircleDot,
  Database,
  Loader2,
  MonitorDot,
  Route,
  Server,
  ShieldCheck,
  Workflow,
} from 'lucide-react'
import type { ReactNode } from 'react'

type HopKind = 'ui' | 'api' | 'warehouse' | 'connector' | 'agent' | 'score' | 'render' | 'queue'

export interface ServiceHop {
  label: string
  detail: string
  kind?: HopKind
}

interface ServiceLoadingProps {
  title: string
  caption?: string
  hops: ServiceHop[]
  compact?: boolean
  framed?: boolean
  className?: string
}

const icons: Record<HopKind, ReactNode> = {
  ui: <MonitorDot className="h-4 w-4" />,
  api: <Server className="h-4 w-4" />,
  warehouse: <Database className="h-4 w-4" />,
  connector: <Route className="h-4 w-4" />,
  agent: <Bot className="h-4 w-4" />,
  score: <BrainCircuit className="h-4 w-4" />,
  render: <BarChart3 className="h-4 w-4" />,
  queue: <Workflow className="h-4 w-4" />,
}

export function ServiceLoading({
  title,
  caption,
  hops,
  compact = false,
  framed = true,
  className = '',
}: ServiceLoadingProps) {
  return (
    <div
      className={`${framed ? 'surface rounded-lg p-5' : ''} ${compact ? 'space-y-3' : 'space-y-5'} ${className}`}
      aria-live="polite"
      aria-busy="true"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Loader2 className="h-4 w-4 animate-spin text-sky-300" />
            {title}
          </div>
          {caption ? <p className="mt-1 text-sm text-slate-400">{caption}</p> : null}
        </div>
        {!compact ? <ShieldCheck className="h-5 w-5 text-emerald-300" /> : null}
      </div>

      <div className={`grid gap-3 ${compact ? '' : 'md:grid-cols-2 xl:grid-cols-5'}`}>
        {hops.map((hop, index) => (
          <div key={`${hop.label}-${index}`} className="min-w-0">
            <div className="flex items-center gap-2">
              <div className="service-node grid h-8 w-8 shrink-0 place-items-center rounded-md border border-sky-300/20 bg-sky-400/10 text-sky-200">
                {icons[hop.kind ?? 'queue'] ?? <CircleDot className="h-4 w-4" />}
              </div>
              <div className="min-w-0">
                <div className="truncate text-xs font-semibold uppercase text-slate-300">{hop.label}</div>
                <div className="truncate text-xs text-slate-500">{hop.detail}</div>
              </div>
            </div>
            <div className="service-progress mt-2" style={{ animationDelay: `${index * 140}ms` }} />
          </div>
        ))}
      </div>
    </div>
  )
}
