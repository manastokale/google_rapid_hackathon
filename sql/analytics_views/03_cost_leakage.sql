CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.cost_leakage` AS
WITH duplicated_spend AS (
  SELECT
    TO_HEX(MD5(CONCAT(
      COALESCE(campaign_name, ''),
      '|',
      COALESCE(channel, ''),
      '|',
      CAST(COALESCE(spend_amount, 0) AS STRING),
      '|',
      CAST(spend_date AS STRING)
    ))) AS campaign_id,
    campaign_name,
    channel,
    spend_date,
    COUNT(*) AS duplicate_count,
    ROUND(SUM(COALESCE(spend_amount, 0)), 2) AS total_recorded_spend,
    ROUND(MAX(COALESCE(spend_amount, 0)), 2) AS expected_spend,
    ARRAY_AGG(spend_id ORDER BY spend_id) AS duplicate_spend_ids
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.marketing_spend`
  GROUP BY campaign_id, campaign_name, channel, spend_date
)
SELECT
  campaign_id,
  campaign_name,
  channel,
  spend_date,
  duplicate_count,
  total_recorded_spend,
  expected_spend,
  ROUND(total_recorded_spend - expected_spend, 2) AS duplicate_spend_leakage,
  duplicate_spend_ids,
  'Marketing / Finance' AS recommended_owner,
  'Deduplicate repeated campaign spend rows before CAC and ROI reporting refresh' AS recommended_action,
  'synthetic_demo' AS data_label
FROM duplicated_spend
WHERE duplicate_count > 1;
