import { ConnectorCard } from '../components/ConnectorCard'
import { dashboardApi } from '../services/api'
import { Connector } from '../types'
import { useApi } from '../hooks/useApi'

export function Connectors() {
  const connectors = useApi<Connector[]>(dashboardApi.getConnectors)

  if (connectors.loading) {
    return <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }).map((_, index) => <div key={index} className="surface h-48 animate-pulse rounded-lg" />)}</div>
  }

  if (connectors.error || !connectors.data) {
    return <div className="surface rounded-lg p-6 text-rose-200">Connector health failed to load.</div>
  }

  return (
    <div className="space-y-5">
      <div className="surface rounded-lg p-5">
        <h1 className="text-xl font-semibold text-white">Connector health</h1>
        <p className="mt-1 text-sm text-slate-400">Fivetran pipeline status mapped to downstream business metrics.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {connectors.data.map((connector) => <ConnectorCard key={connector.connector_id} connector={connector} />)}
      </div>
    </div>
  )
}

