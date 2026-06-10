export interface DashboardOverview {
  total_revenue_at_risk: number
  underbilling_exposure: number
  expansion_gap: number
  cost_leakage: number
  overall_trust_score: number
  stale_connectors: number
  broken_connectors: number
  underbilled_accounts_count: number
  expansion_gap_accounts_count: number
  top_issues: TopIssue[]
}

export interface TopIssue {
  issue: string
  description: string
  impact: number
  severity: Severity
  owner: string
}

export interface Connector {
  connector_id: string
  connector_name: string
  source_system: string
  destination_table: string
  status: 'connected' | 'delayed' | 'broken'
  last_sync_completed: string
  staleness_hours?: number
  sync_frequency_minutes: number
  rows_synced_last: number
  schema_changes_detected: boolean
  error_message: string
  owner: string
  impacted_metrics?: string[]
}

export interface ActionItem {
  id: string
  priority: number
  issue_type: string
  description: string
  dollar_impact: number
  severity: Severity
  owner: string
  recommended_action: string
  status: string
}

export interface AccountRisk {
  account_id: string
  account_name: string
  tier: string
  owner: string
  arr: number
  total_usage: number
  usage_pct?: number
  underbilling_gap?: number
  estimated_annual_expansion?: number
}

export type Severity = 'critical' | 'high' | 'medium' | 'low'

