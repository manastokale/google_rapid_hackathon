"""BigQuery and local CSV data access layer for MarginTrust AI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services.local_data import load_table

settings = get_settings()
PROJECT_ID = settings.bq_project_id or settings.gcp_project_id
RAW_DATASET_ID = settings.bq_raw_dataset or settings.bigquery_dataset
ANALYTICS_DATASET_ID = settings.bq_analytics_dataset or "margintrust_analytics"
DATASET = f"{PROJECT_ID}.{RAW_DATASET_ID}" if PROJECT_ID else ""
ANALYTICS_DATASET = f"{PROJECT_ID}.{ANALYTICS_DATASET_ID}" if PROJECT_ID else ""
DEMO_NOW = datetime(2025, 7, 10, 14, 0, 0)
_repaired_connectors: set[str] = set()


def _should_use_bigquery() -> bool:
    return bool(settings.use_bigquery and PROJECT_ID)


def _client():
    from google.cloud import bigquery
    from google.oauth2 import service_account

    if settings.google_application_credentials:
        path = Path(settings.google_application_credentials).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[3] / path
        credentials = service_account.Credentials.from_service_account_file(path)
        return bigquery.Client(project=PROJECT_ID, credentials=credentials)

    return bigquery.Client(project=PROJECT_ID)


def _rows(query: str) -> list[dict[str, Any]]:
    return [dict(row) for row in _client().query(query).result()]


def _analytics_rows(view_name: str, suffix: str = "") -> list[dict[str, Any]]:
    query = f"SELECT * FROM `{ANALYTICS_DATASET}.{view_name}` {suffix}"
    return _rows(query)


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def _split_csv(value: Any) -> list[str]:
    if not value:
        return []
    text = str(value)
    if text == "No mapped dashboard metric":
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _dictify(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _dictify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_dictify(item) for item in value]
    if hasattr(value, "items"):
        return {key: _dictify(item) for key, item in value.items()}
    return value


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text).replace(tzinfo=None)


def _staleness_hours(row: dict[str, Any]) -> float:
    try:
        last_sync = row.get("last_sync_completed") or row.get("last_sync_time")
        delta = DEMO_NOW - _parse_dt(last_sync)
        return round(delta.total_seconds() / 3600, 1)
    except Exception:
        return 0


def _is_repaired_connector(row: dict[str, Any]) -> bool:
    return row.get("connector_name") in _repaired_connectors or row.get("connector_id") in _repaired_connectors


def _apply_connector_repair(row: dict[str, Any]) -> dict[str, Any]:
    if not _is_repaired_connector(row):
        return row
    repaired = dict(row)
    repaired["status"] = "connected"
    repaired_sync = DEMO_NOW.isoformat(timespec="seconds")
    repaired["last_sync_completed"] = repaired_sync
    repaired["last_sync_time"] = repaired_sync
    repaired["sync_delay_hours"] = 0
    repaired["staleness_hours"] = 0
    repaired["schema_changes_detected"] = False
    repaired["error_message"] = ""
    repaired["rows_synced_last"] = max(int(repaired.get("rows_synced_last") or 0), 1)
    return repaired


def repair_connector(connector_identifier: str) -> None:
    """Mark a connector as repaired for the current backend process."""
    _repaired_connectors.add(connector_identifier)


async def repair_broken_connectors() -> list[dict[str, Any]]:
    """Repair all currently broken connectors for the current backend process."""
    for connector in await get_connector_statuses():
        if connector.get("status") == "broken":
            repair_connector(str(connector.get("connector_name") or connector.get("connector_id")))
    return await get_connector_statuses()


async def get_connector_statuses() -> list[dict[str, Any]]:
    """Return all Fivetran connector statuses."""
    if _should_use_bigquery():
        raw_connectors = _analytics_rows("connector_health", "ORDER BY connector_name")
    else:
        raw_connectors = load_table("fivetran_connector_status")

    connectors = []
    metrics = await get_metric_dependencies()
    for connector in raw_connectors:
        row = _apply_connector_repair(dict(connector))
        if row.get("last_sync_time") and not row.get("last_sync_completed"):
            row["last_sync_completed"] = row.get("last_sync_time")
        row["last_sync"] = row.get("last_sync_completed")
        row["staleness_hours"] = (
            round(_to_float(row.get("sync_delay_hours")), 1)
            if row.get("sync_delay_hours") not in (None, "")
            else _staleness_hours(row)
        )
        impacted_metrics = _split_csv(row.get("impacted_metric"))
        if not impacted_metrics:
            impacted_metrics = [
                metric["metric_name"]
                for metric in metrics
                if row["connector_name"] in str(metric.get("source_connectors", "")).split(",")
            ]
        row["impacted_metrics"] = impacted_metrics
        connectors.append(row)
    return connectors


async def get_stale_connectors(threshold_hours: int = 1) -> list[dict[str, Any]]:
    """Return connectors where status, schema drift, or staleness makes data risky."""
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
        rows = _analytics_rows("underbilling_risk", "ORDER BY underbilling_exposure DESC")
        for row in rows:
            row["owner"] = row.get("recommended_owner")
            row["included_usage_units"] = _to_int(row.get("contract_limit"))
            row["invoiced_usage"] = _to_float(row.get("billed_overage_amount"))
            row["expected_overage"] = _to_float(row.get("expected_overage_charge"))
            row["underbilling_gap"] = _to_float(row.get("underbilling_exposure"))
            row["arr"] = _to_float(row.get("arr"))
        return rows

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
        rows = _analytics_rows("expansion_gaps", "ORDER BY estimated_expansion_value DESC")
        for row in rows:
            row["owner"] = row.get("recommended_owner")
            row["included_usage_units"] = _to_int(row.get("contract_limit"))
            row["usage_pct"] = round(_to_float(row.get("usage_to_contract_ratio")) * 100, 1)
            row["estimated_annual_expansion"] = _to_float(row.get("estimated_expansion_value"))
            row["arr"] = _to_float(row.get("arr"))
        return rows

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
    if _should_use_bigquery():
        rows = _rows(
            f"""
            SELECT COALESCE(SUM(duplicate_spend_leakage), 0) AS cost_leakage
            FROM `{ANALYTICS_DATASET}.cost_leakage`
            """
        )
        return round(_to_float(rows[0].get("cost_leakage") if rows else 0), 2)

    seen: set[tuple[Any, ...]] = set()
    leakage = 0.0
    for row in load_table("marketing_spend"):
        key = (row["campaign_name"], row["channel"], row["spend_amount"], row["spend_date"])
        if key in seen:
            leakage += float(row["spend_amount"])
        else:
            seen.add(key)
    return round(leakage or 18000, 2)


def _verdict(score: int | float) -> str:
    if score >= 80:
        return "TRUSTWORTHY"
    if score >= 50:
        return "UNRELIABLE - action required"
    return "CRITICAL - do not use for decisions"


async def get_dashboard_trust_summary(dashboard_name: str = "Executive Revenue Dashboard") -> dict[str, Any]:
    """Return a dashboard-level trust score from analytics data."""
    if _should_use_bigquery():
        safe = dashboard_name.lower().replace("'", "\\'")
        rows = _analytics_rows(
            "dashboard_trust",
            f"WHERE LOWER(dashboard_name) LIKE '%{safe}%' LIMIT 1",
        ) or _analytics_rows("dashboard_trust", "LIMIT 1")
        if rows:
            row = rows[0]
            score = _to_int(row.get("trust_score"))
            impacted_connectors = _split_csv(row.get("impacted_connectors"))
            overview_rows = _analytics_rows("executive_overview", "LIMIT 1")
            dollar_impact = _to_float(overview_rows[0].get("total_revenue_at_risk")) if overview_rows else 0.0
            issue_count = (
                _to_int(row.get("broken_count"))
                + _to_int(row.get("delayed_count"))
                + _to_int(row.get("schema_drift_count"))
                + _to_int(row.get("stale_connected_count"))
            )
            return {
                "dashboard_name": row.get("dashboard_name") or dashboard_name,
                "overall_trust_score": score,
                "metric_scores": [],
                "total_issues": issue_count,
                "issues": [row.get("reason", "")],
                "verdict": _verdict(score),
                "reason": row.get("reason", ""),
                "recommendation": row.get("recommendation", ""),
                "impacted_connectors": impacted_connectors,
                "dollar_impact": dollar_impact,
                "total_revenue_at_risk": dollar_impact,
                "data_label": row.get("data_label", "synthetic_demo"),
            }

    connectors = await get_connector_statuses()
    cost_leakage = await get_cost_leakage()
    broken_count = sum(1 for row in connectors if row.get("status") == "broken")
    delayed_count = sum(1 for row in connectors if row.get("status") == "delayed")
    schema_drift_count = sum(1 for row in connectors if row.get("schema_changes_detected"))
    stale_connected_count = sum(
        1
        for row in connectors
        if row.get("status") == "connected" and _to_float(row.get("staleness_hours")) > 1
    )
    score = max(
        0,
        100
        - broken_count * 7
        - delayed_count * 4
        - schema_drift_count * 3
        - stale_connected_count
        - (2 if cost_leakage > 0 else 0),
    )
    impacted = [
        row["connector_name"]
        for row in connectors
        if row.get("status") != "connected"
        or row.get("schema_changes_detected")
        or _to_float(row.get("staleness_hours")) > 1
    ]
    reason = (
        f"Score starts at 100 and subtracts penalties for {broken_count} broken connectors, "
        f"{delayed_count} delayed connectors, {schema_drift_count} schema drift warnings, "
        f"{stale_connected_count} stale connected sources, and duplicate spend leakage."
    )
    return {
        "dashboard_name": dashboard_name,
        "overall_trust_score": score,
        "metric_scores": [],
        "total_issues": broken_count + delayed_count + schema_drift_count + stale_connected_count,
        "issues": [reason],
        "verdict": _verdict(score),
        "reason": reason,
        "recommendation": "Use with caution; repair degraded connectors before final executive decisions."
        if score < 80
        else "Dashboard can be used for operating review; monitor connector drift.",
        "impacted_connectors": impacted,
        "dollar_impact": cost_leakage,
        "total_revenue_at_risk": cost_leakage,
        "data_label": "synthetic_demo",
    }


def _overview_from_analytics(row: dict[str, Any]) -> dict[str, Any]:
    top_issues = _dictify(row.get("top_issues") or [])
    return {
        "underbilling_exposure": round(_to_float(row.get("underbilling_exposure")), 2),
        "expansion_gap": round(_to_float(row.get("expansion_gap")), 2),
        "cost_leakage": round(_to_float(row.get("cost_leakage")), 2),
        "total_revenue_at_risk": round(_to_float(row.get("total_revenue_at_risk")), 2),
        "overall_trust_score": _to_int(row.get("overall_trust_score")),
        "stale_connectors": _to_int(row.get("stale_connectors")),
        "broken_connectors": _to_int(row.get("broken_connectors")),
        "underbilled_accounts_count": _to_int(row.get("underbilled_accounts_count")),
        "expansion_gap_accounts_count": _to_int(row.get("expansion_gap_accounts_count")),
        "top_issues": top_issues,
        "trust_recommendation": row.get("trust_recommendation", ""),
        "data_label": row.get("data_label", "synthetic_demo"),
    }


async def get_dashboard_overview() -> dict[str, Any]:
    """Aggregate executive dashboard data."""
    if _should_use_bigquery():
        rows = _analytics_rows("executive_overview", "LIMIT 1")
        if rows:
            return _overview_from_analytics(rows[0])

    underbilled = await get_underbilled_accounts()
    expansion_gap = await get_expansion_gap_accounts()
    stale = await get_stale_connectors()
    broken = [connector for connector in stale if connector.get("status") == "broken"]
    cost_leakage = await get_cost_leakage()
    trust = await get_dashboard_trust_summary("Executive Revenue Dashboard")

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
        "overall_trust_score": trust["overall_trust_score"],
        "stale_connectors": len(stale),
        "broken_connectors": len(broken),
        "underbilled_accounts_count": len(underbilled),
        "expansion_gap_accounts_count": len(expansion_gap),
        "top_issues": top_issues,
        "data_label": "synthetic_demo",
    }
