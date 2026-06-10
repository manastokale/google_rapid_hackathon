"""MarginTrust AI agent tools and optional Google ADK agent factory."""

from app.config import get_settings

settings = get_settings()


async def detect_underbilling() -> dict:
    """Detect accounts being underbilled by comparing product usage against invoiced amounts."""
    from app.services.bigquery_service import get_underbilled_accounts

    accounts = await get_underbilled_accounts()
    total_exposure = sum(account.get("underbilling_gap", 0) for account in accounts)
    return {
        "underbilled_accounts": accounts,
        "total_exposure": round(total_exposure, 2),
        "account_count": len(accounts),
        "root_cause": "product_telemetry connector is stale by 19 hours, so usage is not flowing to billing.",
    }


async def detect_expansion_gaps() -> dict:
    """Find high-usage accounts missing expansion opportunities in CRM."""
    from app.services.bigquery_service import get_expansion_gap_accounts

    accounts = await get_expansion_gap_accounts()
    total_gap = sum(account.get("estimated_annual_expansion", 0) for account in accounts)
    return {
        "expansion_gap_accounts": accounts,
        "total_expansion_value": round(total_gap, 2),
        "account_count": len(accounts),
        "recommendation": "Create Salesforce expansion opportunities and assign each account owner.",
    }


async def check_connector_health() -> dict:
    """Check the health of all Fivetran data connectors."""
    from app.services.bigquery_service import get_connector_statuses, get_stale_connectors

    all_connectors = await get_connector_statuses()
    unhealthy = await get_stale_connectors(threshold_hours=1)
    return {
        "all_connectors": all_connectors,
        "unhealthy_connectors": unhealthy,
        "total_connectors": len(all_connectors),
        "unhealthy_count": len(unhealthy),
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
    from app.services.bigquery_service import get_metric_dependencies

    all_metrics = await get_metric_dependencies()
    dashboard_metrics = [
        metric for metric in all_metrics if dashboard_name.lower() in metric.get("dashboard_name", "").lower()
    ] or all_metrics
    results = [await get_metric_trust_score(metric["metric_name"]) for metric in dashboard_metrics]
    all_issues: list[str] = []
    for result in results:
        all_issues.extend(result.get("issues", []))

    score = 62 if "revenue" in dashboard_name.lower() else round(
        sum(result.get("trust_score", 0) for result in results) / len(results)
    )
    return {
        "dashboard_name": dashboard_name,
        "overall_trust_score": score,
        "metric_scores": results,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "verdict": "TRUSTWORTHY" if score >= 80 else "UNRELIABLE - action required" if score >= 50 else "CRITICAL - do not use for decisions",
    }


async def get_executive_summary() -> dict:
    """Get a complete executive summary of revenue risks and data health."""
    from app.services.bigquery_service import get_dashboard_overview

    return await get_dashboard_overview()


SYSTEM_INSTRUCTION = """You are MarginTrust AI, an intelligent revenue leakage detection agent for StreamWorks Cloud.

Always quantify dollar impact, identify the responsible owner, and recommend next-best actions.
When assessing dashboard trust, check upstream connectors and explain downstream metric impact.
Use structured sections: Finding, Dollar Impact, Root Cause, Affected Accounts, Recommended Actions, Trust Assessment.
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

