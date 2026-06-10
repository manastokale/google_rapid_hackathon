import { AlertTriangle, CheckCircle2, CircleDot, XCircle } from 'lucide-react'

interface StatusBadgeProps {
  status: string
}

const statusMap: Record<string, string> = {
  connected: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300',
  delayed: 'border-amber-400/30 bg-amber-500/10 text-amber-300',
  broken: 'border-rose-400/30 bg-rose-500/10 text-rose-300',
  critical: 'border-rose-400/30 bg-rose-500/10 text-rose-300',
  high: 'border-orange-400/30 bg-orange-500/10 text-orange-300',
  medium: 'border-amber-400/30 bg-amber-500/10 text-amber-300',
  low: 'border-blue-400/30 bg-blue-500/10 text-blue-300',
  acknowledged: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300',
  new: 'border-violet-400/30 bg-violet-500/10 text-violet-300',
}

function Icon({ status }: StatusBadgeProps) {
  if (status === 'connected' || status === 'acknowledged') return <CheckCircle2 className="h-3.5 w-3.5" />
  if (status === 'broken' || status === 'critical') return <XCircle className="h-3.5 w-3.5" />
  if (status === 'delayed' || status === 'high' || status === 'medium') return <AlertTriangle className="h-3.5 w-3.5" />
  return <CircleDot className="h-3.5 w-3.5" />
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toLowerCase()
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold capitalize ${statusMap[normalized] ?? statusMap.low}`}>
      <Icon status={normalized} />
      {status.replace('_', ' ')}
    </span>
  )
}

