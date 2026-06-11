CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{ANALYTICS_DATASET}}.underbilling_risk` AS
WITH usage_totals AS (
  SELECT
    account_id,
    SUM(quantity) AS total_usage
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.product_usage_events`
  GROUP BY account_id
),
invoice_totals AS (
  SELECT
    account_id,
    SUM(COALESCE(usage_amount, 0)) AS billed_overage_amount
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.invoices`
  GROUP BY account_id
),
scored AS (
  SELECT
    a.account_id,
    a.account_name,
    a.tier,
    a.arr,
    a.owner AS recommended_owner,
    'Finance / Billing Ops' AS recommended_team,
    u.total_usage,
    c.included_usage_units AS contract_limit,
    c.overage_rate,
    GREATEST(0, u.total_usage - c.included_usage_units) AS overage_units,
    ROUND(GREATEST(0, (u.total_usage - c.included_usage_units) * c.overage_rate), 2) AS expected_overage_charge,
    ROUND(COALESCE(i.billed_overage_amount, 0), 2) AS billed_overage_amount
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.accounts` AS a
  JOIN `{{PROJECT_ID}}.{{RAW_DATASET}}.contracts` AS c
    ON a.account_id = c.account_id
  JOIN usage_totals AS u
    ON a.account_id = u.account_id
  LEFT JOIN invoice_totals AS i
    ON a.account_id = i.account_id
  WHERE a.status = 'active'
)
SELECT
  account_id,
  account_name,
  tier,
  arr,
  recommended_owner,
  recommended_team,
  total_usage,
  contract_limit,
  overage_rate,
  overage_units,
  expected_overage_charge,
  billed_overage_amount,
  ROUND(expected_overage_charge - billed_overage_amount, 2) AS underbilling_exposure,
  'Usage exceeded contracted allowance and billed overage is below expected charge' AS reason,
  'Recompute usage overage, validate invoice line items, and issue a corrected invoice' AS recommended_action,
  'synthetic_demo' AS data_label
FROM scored
WHERE total_usage > contract_limit
  AND expected_overage_charge - billed_overage_amount > 100;
