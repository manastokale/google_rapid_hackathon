import { Activity, Database, RefreshCcw, Wrench } from 'lucide-react'
import { Connector } from '../types'
import { StatusBadge } from './StatusBadge'

interface ConnectorCardProps {
  connector: Connector
  onRepair?: (connectorName: string) => void
  repairing?: boolean
}

export function ConnectorCard({ connector, onRepair, repairing = false }: ConnectorCardProps) {
  const border =
    connector.status === 'broken'
      ? 'border-rose-400/30'
      : connector.status === 'delayed' || connector.schema_changes_detected
        ? 'border-amber-400/30'
        : 'border-emerald-400/25'

  return (
    <article className={`surface rounded-lg p-5 ${border}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">{connector.connector_name}</h3>
          <p className="mt-1 text-sm text-slate-400">{connector.source_system} to {connector.destination_table}</p>
        </div>
        <StatusBadge status={connector.schema_changes_detected ? 'delayed' : connector.status} />
      </div>
      <div className="mt-5 grid gap-3 text-sm text-slate-300">
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-2 text-slate-400"><RefreshCcw className="h-4 w-4" />Last sync</span>
          <span>{connector.staleness_hours ?? 0}h ago</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-2 text-slate-400"><Database className="h-4 w-4" />Rows synced</span>
          <span>{connector.rows_synced_last.toLocaleString()}</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-2 text-slate-400"><Activity className="h-4 w-4" />Owner</span>
          <span>{connector.owner}</span>
        </div>
      </div>
      {connector.error_message ? (
        <p className="mt-4 rounded-md border border-white/10 bg-black/20 p-3 text-sm text-slate-300">
          {connector.error_message}
        </p>
      ) : null}
      {connector.status === 'broken' && onRepair ? (
        <button
          className="mt-4 inline-flex h-9 items-center gap-2 rounded-md border border-emerald-400/25 bg-emerald-500/10 px-3 text-sm font-semibold text-emerald-200 hover:bg-emerald-500/15 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={repairing}
          onClick={() => onRepair(connector.connector_name)}
        >
          <Wrench className={`h-4 w-4 ${repairing ? 'animate-spin' : ''}`} />
          {repairing ? 'Repairing' : 'Repair connector'}
        </button>
      ) : null}
    </article>
  )
}
