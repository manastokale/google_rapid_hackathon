import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export const dashboardApi = {
  getOverview: () => api.get('/dashboard/overview'),
  getConnectors: () => api.get('/dashboard/connectors'),
  getUnhealthyConnectors: () => api.get('/dashboard/connectors/unhealthy'),
  repairConnector: (connectorName: string) => api.post(`/dashboard/connectors/${encodeURIComponent(connectorName)}/repair`),
  repairBrokenConnectors: () => api.post('/dashboard/connectors/repair-broken'),
  getUnderbilling: () => api.get('/dashboard/underbilling'),
  getExpansionGaps: () => api.get('/dashboard/expansion-gaps'),
  getMetrics: () => api.get('/dashboard/metrics'),
}

export const agentApi = {
  chat: (message: string, sessionId = 'default') =>
    api.post('/agent/chat', { message, session_id: sessionId }),
}

export const actionsApi = {
  getQueue: () => api.get('/actions/queue'),
  acknowledge: (actionId: string) => api.post(`/actions/${actionId}/acknowledge`),
}
