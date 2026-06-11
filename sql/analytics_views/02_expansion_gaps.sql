CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.expansion_gaps` AS
WITH usage_totals AS (
  SELECT
    account_id,
    SUM(quantity) AS total_usage
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.product_usage_events`
  GROUP BY account_id
),
expansion_opportunities AS (
  SELECT DISTINCT
    account_id
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.{{OPPORTUNITIES_TABLE}}`
  WHERE LOWER(type) = 'expansion'
),
scored AS (
  SELECT
    a.account_id,
    a.account_name,
    a.tier,
    a.arr,
    a.owner AS recommended_owner,
    c.included_usage_units AS contract_limit,
    c.overage_rate,
    u.total_usage,
    SAFE_DIVIDE(u.total_usage, c.included_usage_units) AS usage_to_contract_ratio
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.accounts` AS a
  JOIN `{{PROJECT_ID}}.{{RAW_DATASET}}.contracts` AS c
    ON a.account_id = c.account_id
  JOIN usage_totals AS u
    ON a.account_id = u.account_id
  LEFT JOIN expansion_opportunities AS o
    ON a.account_id = o.account_id
  WHERE a.status = 'active'
    AND o.account_id IS NULL
)
SELECT
  account_id,
  account_name,
  tier,
  arr,
  recommended_owner,
  total_usage,
  contract_limit,
  ROUND(usage_to_contract_ratio, 3) AS usage_to_contract_ratio,
  ROUND(GREATEST(0, (total_usage - contract_limit) * overage_rate * 12), 2) AS estimated_expansion_value,
  'Usage is above 120% of contracted allowance and no CRM expansion opportunity exists' AS reason,
  'Sales / RevOps' AS recommended_team,
  'Create or reopen an expansion opportunity and assign it to the account owner' AS recommended_action,
  'synthetic_demo' AS data_label
FROM scored
WHERE usage_to_contract_ratio > 1.2;
