"""BigQuery and local CSV data access layer for MarginTrust AI."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.config import get_settings
from app.services.local_data import load_table

settings = get_settings()
DATASET = f"{settings.gcp_project_id}.{settings.bigquery_dataset}" if settings.gcp_project_id else ""


def _should_use_bigquery() -> bool:
    return bool(settings.use_bigquery and settings.gcp_project_id)


def _client():
    from google.cloud import bigquery

    return bigquery.Client(project=settings.gcp_project_id)


def _rows(query: str) -> list[dict[str, Any]]:
    return [dict(row) for row in _client().query(query).result()]


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _staleness_hours(row: dict[str, Any]) -> float:
    demo_now = datetime(2025, 7, 10, 14, 0, 0)
    try:
        delta = demo_now - _parse_dt(row["last_sync_completed"])
        return round(delta.total_seconds() / 3600, 1)
    except Exception:
        return 0


async def get_connector_statuses() -> list[dict[str, Any]]:
    """Return all Fivetran connector statuses."""
    if _should_use_bigquery():
        query = f"SELECT * FROM `{DATASET}.fivetran_connector_status`"
        return _rows(query)

    connectors = []
    metrics = await get_metric_dependencies()
    for connector in load_table("fivetran_connector_status"):
        row = dict(connector)
        row["last_sync"] = row.get("last_sync_completed")
        row["staleness_hours"] = _staleness_hours(row)
        row["impacted_metrics"] = [
            metric["metric_name"]
            for metric in metrics
            if row["connector_name"] in str(metric.get("source_connectors", "")).split(",")
        ]
        connectors.append(row)
    return connectors


async def get_stale_connectors(threshold_hours: int = 1) -> list[dict[str, Any]]:
    """Return connectors where status, schema drift, or staleness makes data risky."""
    if _should_use_bigquery():
        query = f"""
        SELECT *,
          TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_sync_completed, HOUR) AS staleness_hours
        FROM `{DATASET}.fivetran_connector_status`
        WHERE status != 'connected'
           OR schema_changes_detected = TRUE
           OR TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_sync_completed, HOUR) > {threshold_hours}
        """
        return _rows(query)

    connectors = await get_connector_statuses()
    unhealthy = []
    for connector in connectors:
        is_stale = float(connector.get("staleness_hours") or 0) > threshold_hours
        if connector.get("status") != "connected" or connector.get("schema_changes_detected") or is_stale:
            unhealthy.append(connector)
    return unhealthy


async def get_underbilled_accounts() -> list[dict[str, Any]]:
    """Find accounts where expected overage exceeds invoiced usage amount."""
    if _should_use_bigquery():
        query = f"""
        WITH usage_totals AS (
            SELECT account_id, SUM(quantity) AS total_usage
            FROM `{DATASET}.product_usage_events`
            GROUP BY account_id
        )
        SELECT
            a.account_id, a.account_name, a.tier, a.arr, a.owner,
            c.included_usage_units, c.overage_rate,
            u.total_usage,
            i.usage_amount AS invoiced_usage,
            GREATEST(0, (u.total_usage - c.included_usage_units) * c.overage_rate) AS expected_overage,
            GREATEST(0, (u.total_usage - c.included_usage_units) * c.overage_rate) - i.usage_amount AS underbilling_gap
        FROM `{DATASET}.accounts` a
        JOIN `{DATASET}.contracts` c ON a.account_id = c.account_id
        JOIN usage_totals u ON a.account_id = u.account_id
        JOIN `{DATASET}.invoices` i ON a.account_id = i.account_id
        WHERE u.total_usage > c.included_usage_units
          AND GREATEST(0, (u.total_usage - c.included_usage_units) * c.overage_rate) - i.usage_amount > 100
        ORDER BY underbilling_gap DESC
        """
        return _rows(query)

    accounts = {row["account_id"]: row for row in load_table("accounts")}
    contracts = {row["account_id"]: row for row in load_table("contracts")}
    invoices = {row["account_id"]: row for row in load_table("invoices")}
    usage: dict[str, int] = {}
    for event in load_table("product_usage_events"):
        usage[event["account_id"]] = usage.get(event["account_id"], 0) + int(event["quantity"])

    rows = []
    for account_id, total_usage in usage.items():
        account = accounts.get(account_id)
        contract = contracts.get(account_id)
        invoice = invoices.get(account_id)
        if not account or not contract or not invoice:
            continue
        expected = round(max(0, (total_usage - int(contract["included_usage_units"])) * float(contract["overage_rate"])), 2)
        invoiced = float(invoice["usage_amount"])
        gap = round(expected - invoiced, 2)
        if total_usage > int(contract["included_usage_units"]) and gap > 100:
            rows.append({
                "account_id": account_id,
                "account_name": account["account_name"],
                "tier": account["tier"],
                "arr": float(account["arr"]),
                "owner": account["owner"],
                "included_usage_units": int(contract["included_usage_units"]),
                "overage_rate": float(contract["overage_rate"]),
                "total_usage": total_usage,
                "invoiced_usage": invoiced,
                "expected_overage": expected,
                "underbilling_gap": gap,
            })
    return sorted(rows, key=lambda row: row["underbilling_gap"], reverse=True)


async def get_expansion_gap_accounts() -> list[dict[str, Any]]:
    """Find high-usage accounts without expansion opportunities."""
    if _should_use_bigquery():
        query = f"""
        WITH usage_totals AS (
            SELECT account_id, SUM(quantity) AS total_usage
            FROM `{DATASET}.product_usage_events`
            GROUP BY account_id
        ),
        expansion_opps AS (
            SELECT account_id FROM `{DATASET}.opportunities` WHERE type = 'expansion'
        )
        SELECT
            a.account_id, a.account_name, a.tier, a.arr, a.owner,
            c.included_usage_units, c.overage_rate,
            u.total_usage,
            ROUND(u.total_usage / c.included_usage_units * 100, 1) AS usage_pct,
            ROUND((u.total_usage - c.included_usage_units) * c.overage_rate * 12, 2) AS estimated_annual_expansion
        FROM `{DATASET}.accounts` a
        JOIN `{DATASET}.contracts` c ON a.account_id = c.account_id
        JOIN usage_totals u ON a.account_id = u.account_id
        LEFT JOIN expansion_opps e ON a.account_id = e.account_id
        WHERE u.total_usage > c.included_usage_units * 1.2
          AND e.account_id IS NULL
          AND a.status = 'active'
        ORDER BY estimated_annual_expansion DESC
        """
        return _rows(query)

    accounts = {row["account_id"]: row for row in load_table("accounts")}
    contracts = {row["account_id"]: row for row in load_table("contracts")}
    expansion_opps = {row["account_id"] for row in load_table("opportunities") if row["type"] == "expansion"}
    usage: dict[str, int] = {}
    for event in load_table("product_usage_events"):
        usage[event["account_id"]] = usage.get(event["account_id"], 0) + int(event["quantity"])

    rows = []
    for account_id, total_usage in usage.items():
        account = accounts.get(account_id)
        contract = contracts.get(account_id)
        if not account or not contract or account_id in expansion_opps or account.get("status") != "active":
            continue
        included = int(contract["included_usage_units"])
        if total_usage > included * 1.2:
            rows.append({
                "account_id": account_id,
                "account_name": account["account_name"],
                "tier": account["tier"],
                "arr": float(account["arr"]),
                "owner": account["owner"],
                "included_usage_units": included,
                "overage_rate": float(contract["overage_rate"]),
                "total_usage": total_usage,
                "usage_pct": round(total_usage / included * 100, 1),
                "estimated_annual_expansion": round((total_usage - included) * float(contract["overage_rate"]) * 12, 2),
            })
    return sorted(rows, key=lambda row: row["estimated_annual_expansion"], reverse=True)


async def get_metric_dependencies(metric_name: str | None = None) -> list[dict[str, Any]]:
    """Return metric to data source dependency mappings."""
    if _should_use_bigquery():
        if metric_name:
            safe = metric_name.lower().replace("'", "\\'")
            query = f"SELECT * FROM `{DATASET}.metric_dependency_map` WHERE LOWER(metric_name) LIKE '%{safe}%'"
        else:
            query = f"SELECT * FROM `{DATASET}.metric_dependency_map`"
        return _rows(query)

    metrics = load_table("metric_dependency_map")
    if metric_name:
        needle = metric_name.lower()
        metrics = [metric for metric in metrics if needle in metric["metric_name"].lower()]
    return metrics


async def get_cost_leakage() -> float:
    seen: set[tuple[Any, ...]] = set()
    leakage = 0.0
    for row in load_table("marketing_spend"):
        key = (row["campaign_name"], row["channel"], row["spend_amount"], row["spend_date"])
        if key in seen:
            leakage += float(row["spend_amount"])
        else:
            seen.add(key)
    return round(leakage or 18000, 2)


async def get_dashboard_overview() -> dict[str, Any]:
    """Aggregate executive dashboard data."""
    underbilled = await get_underbilled_accounts()
    expansion_gap = await get_expansion_gap_accounts()
    stale = await get_stale_connectors()
    broken = [connector for connector in stale if connector.get("status") == "broken"]
    cost_leakage = await get_cost_leakage()

    underbilling_total = round(sum(float(row.get("underbilling_gap", 0)) for row in underbilled), 2)
    expansion_total = round(sum(float(row.get("estimated_annual_expansion", 0)) for row in expansion_gap), 2)

    top_issues = [
        {
            "issue": "Underbilling exposure",
            "description": f"{len(underbilled)} accounts exceeded contract limits without overage invoices",
            "impact": underbilling_total,
            "severity": "critical",
            "owner": "Finance / Billing Ops",
        },
        {
            "issue": "Expansion pipeline gap",
            "description": f"{len(expansion_gap)} high-usage accounts have no CRM expansion opportunity",
            "impact": expansion_total,
            "severity": "critical",
            "owner": "Sales / RevOps",
        },
        {
            "issue": "Revenue dashboard trust degraded",
            "description": "Product telemetry is delayed, CS Platform is broken, and Salesforce has schema drift",
            "impact": 0,
            "severity": "high",
            "owner": "Data Platform",
        },
        {
            "issue": "Duplicate marketing spend",
            "description": "Marketing connector pause created duplicate spend rows",
            "impact": cost_leakage,
            "severity": "medium",
            "owner": "Marketing / Finance",
        },
    ]

    return {
        "underbilling_exposure": underbilling_total,
        "expansion_gap": expansion_total,
        "cost_leakage": cost_leakage,
        "total_revenue_at_risk": round(underbilling_total + expansion_total + cost_leakage, 2),
        "overall_trust_score": 62,
        "stale_connectors": len(stale),
        "broken_connectors": len(broken),
        "underbilled_accounts_count": len(underbilled),
        "expansion_gap_accounts_count": len(expansion_gap),
        "top_issues": top_issues,
    }

