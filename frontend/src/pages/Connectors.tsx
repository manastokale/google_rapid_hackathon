import { ConnectorCard } from '../components/ConnectorCard'
import { ServiceHop, ServiceLoading } from '../components/ServiceLoading'
import { dashboardApi } from '../services/api'
import { Connector } from '../types'
import { useApi } from '../hooks/useApi'
import { useState } from 'react'
import { Wrench } from 'lucide-react'

const connectorHops: ServiceHop[] = [
  { label: 'React UI', detail: 'Polling health', kind: 'ui' },
  { label: 'FastAPI', detail: 'Reading status', kind: 'api' },
  { label: 'Fivetran MCP', detail: 'Sync telemetry', kind: 'connector' },
  { label: 'BigQuery', detail: 'Dependency map', kind: 'warehouse' },
  { label: 'Metrics', detail: 'Impact mapping', kind: 'score' },
]

export function Connectors() {
  const connectors = useApi<Connector[]>(dashboardApi.getConnectors)
  const [repairing, setRepairing] = useState<string | null>(null)

  const repairConnector = async (connectorName: string) => {
    setRepairing(connectorName)
    try {
      await dashboardApi.repairConnector(connectorName)
      const refreshed = await dashboardApi.getConnectors()
      connectors.setData(refreshed.data)
    } finally {
      setRepairing(null)
    }
  }

  const repairBroken = async () => {
    setRepairing('all')
    try {
      const repaired = await dashboardApi.repairBrokenConnectors()
      connectors.setData(repaired.data)
    } finally {
      setRepairing(null)
    }
  }

  if (connectors.loading) {
    return (
      <ServiceLoading
        title="Loading connector health"
        caption="Sync status is being mapped to downstream dashboard metrics."
        hops={connectorHops}
        className="min-h-80"
      />
    )
  }

  if (connectors.error || !connectors.data) {
    return <div className="surface rounded-lg p-6 text-rose-200">Connector health failed to load.</div>
  }

  return (
    <div className="space-y-5">
      <div className="surface rounded-lg p-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-xl font-semibold text-white">Connector health</h1>
            <p className="mt-1 text-sm text-slate-400">Fivetran pipeline status mapped to downstream business metrics.</p>
          </div>
          <button
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-emerald-400/25 bg-emerald-500/10 px-3 text-sm font-semibold text-emerald-200 hover:bg-emerald-500/15 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={repairing !== null || !connectors.data.some((connector) => connector.status === 'broken')}
            onClick={() => void repairBroken()}
          >
            <Wrench className={`h-4 w-4 ${repairing === 'all' ? 'animate-spin' : ''}`} />
            Repair broken
          </button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {connectors.data.map((connector) => (
          <ConnectorCard
            key={connector.connector_id}
            connector={connector}
            repairing={repairing === connector.connector_name || repairing === 'all'}
            onRepair={(connectorName) => void repairConnector(connectorName)}
          />
        ))}
      </div>
    </div>
  )
}
