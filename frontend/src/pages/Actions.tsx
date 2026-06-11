import { useMemo, useState } from 'react'
import { Filter } from 'lucide-react'
import { ActionItem } from '../components/ActionItem'
import { ServiceHop, ServiceLoading } from '../components/ServiceLoading'
import { actionsApi } from '../services/api'
import { ActionItem as ActionItemType } from '../types'
import { useApi } from '../hooks/useApi'

const actionHops: ServiceHop[] = [
  { label: 'React UI', detail: 'Requesting queue', kind: 'ui' },
  { label: 'FastAPI', detail: 'Collecting incidents', kind: 'api' },
  { label: 'BigQuery', detail: 'Risk tables', kind: 'warehouse' },
  { label: 'Scoring', detail: 'Severity ranking', kind: 'score' },
  { label: 'Queue', detail: 'Owner actions', kind: 'queue' },
]

export function Actions() {
  const queue = useApi<{ actions: ActionItemType[] }>(actionsApi.getQueue)
  const [severity, setSeverity] = useState('all')
  const [type, setType] = useState('all')

  const actions = queue.data?.actions ?? []
  const filtered = useMemo(() => {
    return actions.filter((action) => {
      const severityMatch = severity === 'all' || action.severity === severity
      const typeMatch = type === 'all' || action.issue_type === type
      return severityMatch && typeMatch
    })
  }, [actions, severity, type])

  const acknowledge = async (id: string) => {
    const response = await actionsApi.acknowledge(id)
    if (id.startsWith('connector-')) {
      const refreshed = await actionsApi.getQueue()
      queue.setData(refreshed.data)
      return
    }
    queue.setData({
      actions: actions.map((action) => (action.id === id ? { ...action, status: response.data.status } : action)),
    })
  }

  if (queue.loading) {
    return (
      <ServiceLoading
        title="Building action queue"
        caption="Revenue incidents are being ranked by impact, owner, and connector risk."
        hops={actionHops}
        className="min-h-96"
      />
    )
  }

  return (
    <div className="space-y-5">
      <div className="surface rounded-lg p-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-xl font-semibold text-white">Action queue</h1>
            <p className="mt-1 text-sm text-slate-400">Recommended fixes sorted by business impact and data risk.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <Filter className="h-4 w-4" />
              <select value={type} onChange={(event) => setType(event.target.value)} className="rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-slate-200">
                <option value="all">All types</option>
                <option value="underbilling">Underbilling</option>
                <option value="expansion_gap">Expansion</option>
                <option value="connector_health">Connectors</option>
                <option value="cost_leakage">Cost</option>
              </select>
            </label>
            <select value={severity} onChange={(event) => setSeverity(event.target.value)} className="rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200">
              <option value="all">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      <div className="surface overflow-hidden rounded-lg">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px] text-left">
            <thead className="bg-white/5 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3 text-right">Impact</th>
                <th className="px-4 py-3">Owner</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Ack</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((action) => (
                <ActionItem key={action.id} action={action} onAcknowledge={(id) => void acknowledge(id)} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
