import { AlertTriangle, ArrowUpRight, CircleDollarSign, DatabaseZap, LineChart, ShieldAlert } from 'lucide-react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { KpiCard } from '../components/KpiCard'
import { StatusBadge } from '../components/StatusBadge'
import { TrustGauge } from '../components/TrustGauge'
import { dashboardApi } from '../services/api'
import { Connector, DashboardOverview } from '../types'
import { useApi } from '../hooks/useApi'

const money = (value: number) => `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`

export function Dashboard() {
  const overview = useApi<DashboardOverview>(dashboardApi.getOverview)
  const connectors = useApi<Connector[]>(dashboardApi.getConnectors)

  if (overview.loading) {
    return <div className="surface h-96 animate-pulse rounded-lg" />
  }
  if (overview.error || !overview.data) {
    return <div className="surface rounded-lg p-6 text-rose-200">Dashboard data failed to load.</div>
  }

  const data = overview.data
  const pieData = [
    { name: 'Underbilling', value: data.underbilling_exposure, color: '#f43f5e' },
    { name: 'Expansion', value: data.expansion_gap, color: '#8b5cf6' },
    { name: 'Cost leakage', value: data.cost_leakage, color: '#f59e0b' },
  ]

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <KpiCard title="Revenue at risk" value={data.total_revenue_at_risk} formatter={money} tone="rose" icon={<ShieldAlert className="h-5 w-5" />} caption="Total exposure" />
        <KpiCard title="Underbilling" value={data.underbilling_exposure} formatter={money} tone="amber" icon={<CircleDollarSign className="h-5 w-5" />} caption={`${data.underbilled_accounts_count} accounts`} />
        <KpiCard title="Expansion gap" value={data.expansion_gap} formatter={money} tone="violet" icon={<ArrowUpRight className="h-5 w-5" />} caption={`${data.expansion_gap_accounts_count} accounts`} />
        <KpiCard title="Cost leakage" value={data.cost_leakage} formatter={money} tone="blue" icon={<LineChart className="h-5 w-5" />} caption="Duplicate spend" />
        <KpiCard title="Trust score" value={data.overall_trust_score} formatter={(value) => `${Math.round(value)}/100`} tone="emerald" icon={<DatabaseZap className="h-5 w-5" />} caption={`${data.stale_connectors} unhealthy connectors`} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <div className="surface rounded-lg p-6">
          <TrustGauge score={data.overall_trust_score} />
          <div className="mt-5 flex flex-wrap gap-2">
            {(connectors.data ?? []).map((connector) => (
              <span
                key={connector.connector_id}
                title={connector.connector_name}
                className={`h-3 w-3 rounded-full ${
                  connector.status === 'broken' ? 'bg-rose-400' : connector.status === 'delayed' || connector.schema_changes_detected ? 'bg-amber-300' : 'bg-emerald-400'
                }`}
              />
            ))}
          </div>
        </div>

        <div className="surface rounded-lg p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-xl font-semibold text-white">Executive risk dashboard</h1>
              <p className="mt-1 text-sm text-slate-400">Prioritized leakage, opportunity, and data trust incidents.</p>
            </div>
            <AlertTriangle className="h-5 w-5 text-amber-300" />
          </div>
          <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_260px]">
            <div className="overflow-hidden rounded-lg border border-white/10">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="bg-white/5 text-xs uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Issue</th>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3 text-right">Impact</th>
                    <th className="px-4 py-3">Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_issues.map((issue) => (
                    <tr key={issue.issue} className="border-t border-white/5">
                      <td className="px-4 py-4">
                        <div className="font-medium text-white">{issue.issue}</div>
                        <div className="mt-1 text-slate-400">{issue.description}</div>
                      </td>
                      <td className="px-4 py-4"><StatusBadge status={issue.severity} /></td>
                      <td className="px-4 py-4 text-right font-semibold text-white">{money(issue.impact)}</td>
                      <td className="px-4 py-4 text-slate-300">{issue.owner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" innerRadius={52} outerRadius={88} paddingAngle={4}>
                    {pieData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                  </Pie>
                  <Tooltip formatter={(value) => money(Number(value))} contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,.1)', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

