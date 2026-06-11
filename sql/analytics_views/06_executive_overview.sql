CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.executive_overview` AS
WITH underbilling AS (
  SELECT
    COUNT(*) AS underbilled_account_count,
    COALESCE(SUM(underbilling_exposure), 0) AS underbilling_exposure
  FROM `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.underbilling_risk`
),
expansion AS (
  SELECT
    COUNT(*) AS expansion_gap_account_count,
    COALESCE(SUM(estimated_expansion_value), 0) AS expansion_gap
  FROM `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.expansion_gaps`
),
cost AS (
  SELECT
    COALESCE(SUM(duplicate_spend_leakage), 0) AS cost_leakage
  FROM `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.cost_leakage`
),
connectors AS (
  SELECT
    COUNTIF(
      status != 'connected'
      OR schema_changes_detected
      OR sync_delay_hours > 1
    ) AS stale_connector_count,
    COUNTIF(status = 'broken') AS broken_connector_count
  FROM `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.connector_health`
),
trust AS (
  SELECT
    trust_score AS overall_trust_score,
    reason AS trust_reason,
    recommendation AS trust_recommendation
  FROM `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.dashboard_trust`
  WHERE dashboard_name = 'Executive Revenue Dashboard'
  LIMIT 1
)
SELECT
  ROUND(u.underbilling_exposure, 2) AS underbilling_exposure,
  ROUND(e.expansion_gap, 2) AS expansion_gap,
  ROUND(c.cost_leakage, 2) AS cost_leakage,
  ROUND(u.underbilling_exposure + e.expansion_gap + c.cost_leakage, 2) AS total_revenue_at_risk,
  t.overall_trust_score,
  cn.stale_connector_count AS stale_connectors,
  cn.broken_connector_count AS broken_connectors,
  u.underbilled_account_count AS underbilled_accounts_count,
  e.expansion_gap_account_count AS expansion_gap_accounts_count,
  ARRAY<STRUCT<issue STRING, description STRING, impact FLOAT64, severity STRING, owner STRING>>[
    STRUCT(
      'Expansion pipeline gap',
      CONCAT(CAST(e.expansion_gap_account_count AS STRING), ' high-usage accounts have no open CRM expansion opportunity'),
      ROUND(e.expansion_gap, 2),
      IF(e.expansion_gap > 0, 'critical', 'healthy'),
      'Sales / RevOps'
    ),
    STRUCT(
      'Underbilling exposure',
      CONCAT(CAST(u.underbilled_account_count AS STRING), ' accounts exceeded contract limits without enough billed overage'),
      ROUND(u.underbilling_exposure, 2),
      IF(u.underbilling_exposure > 0, 'critical', 'healthy'),
      'Finance / Billing Ops'
    ),
    STRUCT(
      'Duplicate marketing spend',
      'Repeated campaign spend rows are inflating CAC and ROI calculations',
      ROUND(c.cost_leakage, 2),
      IF(c.cost_leakage > 0, 'medium', 'healthy'),
      'Marketing / Finance'
    ),
    STRUCT(
      'Revenue dashboard trust degraded',
      t.trust_reason,
      0.0,
      IF(t.overall_trust_score < 80, 'high', 'healthy'),
      'Data Platform'
    )
  ] AS top_issues,
  t.trust_recommendation AS trust_recommendation,
  'synthetic_demo' AS data_label
FROM underbilling AS u
CROSS JOIN expansion AS e
CROSS JOIN cost AS c
CROSS JOIN connectors AS cn
CROSS JOIN trust AS t;
