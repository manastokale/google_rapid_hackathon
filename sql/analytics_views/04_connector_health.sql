CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.connector_health` AS
WITH connector_base AS (
  SELECT
    c.*,
    MAX(last_sync_completed) OVER () AS reference_sync_time
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.{{CONNECTOR_STATUS_TABLE}}` AS c
),
connector_metrics AS (
  SELECT
    c.connector_id,
    c.connector_name,
    c.source_system,
    c.destination_table,
    c.status,
    c.last_sync_completed AS last_sync_time,
    c.sync_frequency_minutes,
    c.rows_synced_last,
    c.schema_changes_detected,
    c.error_message,
    c.owner,
    ROUND(TIMESTAMP_DIFF(c.reference_sync_time, c.last_sync_completed, MINUTE) / 60.0, 1) AS sync_delay_hours,
    STRING_AGG(DISTINCT m.metric_name, ', ' ORDER BY m.metric_name) AS impacted_metric,
    COUNTIF(m.business_criticality = 'critical') AS critical_metric_count,
    COUNTIF(m.business_criticality = 'high') AS high_metric_count
  FROM connector_base AS c
  LEFT JOIN `{{PROJECT_ID}}.{{RAW_DATASET}}.metric_dependency_map` AS m
    ON c.connector_name IN UNNEST(SPLIT(REPLACE(COALESCE(m.source_connectors, ''), ' ', ''), ','))
  GROUP BY
    c.connector_id,
    c.connector_name,
    c.source_system,
    c.destination_table,
    c.status,
    c.last_sync_completed,
    c.sync_frequency_minutes,
    c.rows_synced_last,
    c.schema_changes_detected,
    c.error_message,
    c.owner,
    sync_delay_hours
)
SELECT
  connector_id,
  connector_name,
  source_system,
  destination_table,
  status,
  last_sync_time,
  sync_delay_hours,
  sync_frequency_minutes,
  rows_synced_last,
  schema_changes_detected,
  error_message,
  owner,
  COALESCE(impacted_metric, 'No mapped dashboard metric') AS impacted_metric,
  CASE
    WHEN critical_metric_count > 0 THEN 'Critical revenue or billing metrics impacted'
    WHEN high_metric_count > 0 THEN 'High-priority operating metrics impacted'
    WHEN status != 'connected' OR schema_changes_detected THEN 'Non-critical reporting quality impacted'
    ELSE 'No active metric impact detected'
  END AS business_impact,
  CASE
    WHEN status = 'broken' THEN 'Repair authentication or connector error, then run a manual sync'
    WHEN status = 'delayed' THEN 'Clear upstream backlog and backfill missed records'
    WHEN schema_changes_detected THEN 'Review schema drift and update downstream metric contracts'
    WHEN sync_delay_hours > sync_frequency_minutes / 60.0 THEN 'Investigate sync lag against expected cadence'
    ELSE 'Monitor normally'
  END AS recommended_action,
  'synthetic_demo' AS data_label
FROM connector_metrics;
