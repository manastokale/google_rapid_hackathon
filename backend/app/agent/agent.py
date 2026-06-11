"""MarginTrust AI agent tools and optional Google ADK agent factory."""

from app.config import get_settings

settings = get_settings()


async def detect_underbilling() -> dict:
    """Detect accounts being underbilled by comparing product usage against invoiced amounts."""
    from app.services.bigquery_service import get_underbilled_accounts

    accounts = await get_underbilled_accounts()
    total_exposure = sum(account.get("underbilling_gap", 0) for account in accounts)
    impacted_accounts = [account.get("account_name") for account in accounts[:5]]
    return {
        "underbilled_accounts": accounts,
        "total_exposure": round(total_exposure, 2),
        "account_count": len(accounts),
        "evidence_checked": [
            "analytics.underbilling_risk",
            "product usage totals",
            "contract allowances",
            "invoice overage amounts",
        ],
        "affected_accounts": impacted_accounts,
        "root_cause": accounts[0].get("reason", "Usage exceeded contract allowance while billed overage lagged expected charges")
        if accounts
        else "No active underbilling exposure found in analytics views",
        "recommended_owner": "Finance / Billing Ops",
        "next_action": "Recompute current-period overages, validate invoice line items, and issue corrected invoices.",
    }


async def detect_expansion_gaps() -> dict:
    """Find high-usage accounts missing expansion opportunities in CRM."""
    from app.services.bigquery_service import get_expansion_gap_accounts

    accounts = await get_expansion_gap_accounts()
    total_gap = sum(account.get("estimated_annual_expansion", 0) for account in accounts)
    impacted_accounts = [account.get("account_name") for account in accounts[:5]]
    return {
        "expansion_gap_accounts": accounts,
        "total_expansion_value": round(total_gap, 2),
        "account_count": len(accounts),
        "evidence_checked": [
            "analytics.expansion_gaps",
            "product usage totals",
            "contract allowances",
            "open CRM expansion opportunities",
        ],
        "affected_accounts": impacted_accounts,
        "root_cause": accounts[0].get("reason", "High usage accounts lack open expansion opportunities")
        if accounts
        else "No expansion gap found in analytics views",
        "recommended_owner": "Sales / RevOps",
        "next_action": "Create or reopen expansion opportunities and assign each to the account owner.",
        "recommendation": "Create Salesforce expansion opportunities and assign each account owner.",
    }


async def check_connector_health() -> dict:
    """Check the health of all Fivetran data connectors."""
    from app.services.bigquery_service import get_connector_statuses, get_stale_connectors

    all_connectors = await get_connector_statuses()
    unhealthy = await get_stale_connectors(threshold_hours=1)
    impacted_connectors = [connector.get("connector_name") for connector in unhealthy[:6]]
    return {
        "all_connectors": all_connectors,
        "unhealthy_connectors": unhealthy,
        "total_connectors": len(all_connectors),
        "unhealthy_count": len(unhealthy),
        "evidence_checked": ["analytics.connector_health", "metric dependency map", "connector sync freshness"],
        "affected_connectors": impacted_connectors,
        "recommended_owner": "Data Platform",
        "next_action": "Repair broken connectors, clear delayed syncs, and rerun downstream dashboard refreshes.",
    }


async def get_metric_trust_score(metric_name: str) -> dict:
    """Calculate trust score for a metric from upstream connector health."""
    from app.services.bigquery_service import get_connector_statuses, get_metric_dependencies

    metrics = await get_metric_dependencies(metric_name)
    connectors = await get_connector_statuses()
    connector_map = {connector["connector_name"]: connector for connector in connectors}

    if not metrics:
        return {"error": f"Metric '{metric_name}' not found"}

    metric = metrics[0]
    source_connectors = [item.strip() for item in metric.get("source_connectors", "").split(",") if item.strip()]
    score_components = []
    issues = []

    for name in source_connectors:
        connector = connector_map.get(name)
        if not connector:
            score_components.append(50)
            issues.append(f"Connector '{name}' not found in status table")
            continue
        if connector["status"] == "broken":
            score_components.append(0)
            issues.append(f"{name} is broken: {connector.get('error_message', '')}")
        elif connector["status"] == "delayed":
            score_components.append(30)
            issues.append(f"{name} is delayed since {connector['last_sync_completed']}")
        elif connector.get("schema_changes_detected"):
            score_components.append(60)
            issues.append(f"{name} has schema drift: {connector.get('error_message', '')}")
        elif float(connector.get("staleness_hours") or 0) > 2:
            score_components.append(75)
            issues.append(f"{name} is stale by {connector['staleness_hours']} hours")
        else:
            score_components.append(100)

    score = round(sum(score_components) / len(score_components)) if score_components else 0
    return {
        "metric_name": metric["metric_name"],
        "trust_score": score,
        "dashboard": metric["dashboard_name"],
        "criticality": metric["business_criticality"],
        "source_connectors_checked": source_connectors,
        "issues": issues,
        "recommendation": "Fix broken connectors and re-sync before relying on this metric" if score < 80 else "Metric data sources are healthy",
    }


async def get_dashboard_trust_assessment(dashboard_name: str) -> dict:
    """Assess whether a dashboard can be trusted."""
    from app.services.bigquery_service import get_dashboard_trust_summary

    return await get_dashboard_trust_summary(dashboard_name)


async def get_executive_summary() -> dict:
    """Get a complete executive summary of revenue risks and data health."""
    from app.services.bigquery_service import get_dashboard_overview

    return await get_dashboard_overview()


SYSTEM_INSTRUCTION = """You are MarginTrust AI, an intelligent revenue leakage detection agent for StreamWorks Cloud.

Always quantify dollar impact, identify the responsible owner, and recommend next-best actions.
When assessing dashboard trust, check upstream connectors and explain downstream metric impact.
Use only tool outputs for numbers; never invent static placeholder values.
Use structured sections: Finding, Evidence Checked, Affected Accounts/Connectors, Dollar Impact, Root Cause, Recommended Owner, Next Action, Confidence/Trust Score.
"""


def create_agent():
    """Create and return the MarginTrust ADK agent when google-adk is installed."""
    from google.adk.agents import Agent

    return Agent(
        name="margintrust_agent",
        model=settings.gemini_model,
        instruction=SYSTEM_INSTRUCTION,
        tools=[
            detect_underbilling,
            detect_expansion_gaps,
            check_connector_health,
            get_metric_trust_score,
            get_dashboard_trust_assessment,
            get_executive_summary,
        ],
    )
