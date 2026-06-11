CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.dashboard_trust` AS
WITH connector_rollup AS (
  SELECT
    COUNTIF(status = 'broken') AS broken_count,
    COUNTIF(status = 'delayed') AS delayed_count,
    COUNTIF(schema_changes_detected) AS schema_drift_count,
    COUNTIF(status = 'connected' AND sync_delay_hours > 1) AS stale_connected_count,
    STRING_AGG(
      IF(
        status != 'connected'
        OR schema_changes_detected
        OR sync_delay_hours > 1,
        connector_name,
        NULL
      ),
      ', '
      ORDER BY connector_name
    ) AS impacted_connectors
  FROM `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.connector_health`
),
cost_rollup AS (
  SELECT
    COALESCE(SUM(duplicate_spend_leakage), 0) AS duplicate_spend_leakage
  FROM `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.cost_leakage`
),
scored AS (
  SELECT
    'Executive Revenue Dashboard' AS dashboard_name,
    broken_count,
    delayed_count,
    schema_drift_count,
    stale_connected_count,
    duplicate_spend_leakage,
    COALESCE(impacted_connectors, 'None') AS impacted_connectors,
    GREATEST(
      0,
      100
      - broken_count * 7
      - delayed_count * 4
      - schema_drift_count * 3
      - stale_connected_count * 1
      - IF(duplicate_spend_leakage > 0, 2, 0)
    ) AS trust_score
  FROM connector_rollup
  CROSS JOIN cost_rollup
)
SELECT
  dashboard_name,
  trust_score,
  impacted_connectors,
  broken_count,
  delayed_count,
  schema_drift_count,
  stale_connected_count,
  duplicate_spend_leakage,
  CONCAT(
    'Score starts at 100 and subtracts penalties for ',
    CAST(broken_count AS STRING),
    ' broken connectors, ',
    CAST(delayed_count AS STRING),
    ' delayed connectors, ',
    CAST(schema_drift_count AS STRING),
    ' schema drift warnings, ',
    CAST(stale_connected_count AS STRING),
    ' stale connected sources, and duplicate spend leakage.'
  ) AS reason,
  CASE
    WHEN trust_score >= 80 THEN 'Dashboard can be used for operating review; monitor connector drift.'
    WHEN trust_score >= 50 THEN 'Use with caution; repair degraded connectors before final executive decisions.'
    ELSE 'Do not use for executive decisions until upstream connector issues are remediated.'
  END AS recommendation,
  'synthetic_demo' AS data_label
FROM scored;
