"""Wrapper to run the ADK agent from FastAPI endpoints with a local fallback."""

from __future__ import annotations

import os

from app.agent.agent import (
    check_connector_health,
    create_agent,
    detect_expansion_gaps,
    detect_underbilling,
    get_dashboard_trust_assessment,
    get_executive_summary,
)
from app.config import get_settings

settings = get_settings()
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

_runner = None
_session_service = None
_adk_error: str | None = None

try:
    if settings.gemini_api_key:
        from google.adk.runners import InMemoryRunner
        from google.adk.sessions import InMemorySessionService

        agent = create_agent()
        _session_service = InMemorySessionService()
        _runner = InMemoryRunner(agent=agent, app_name="margintrust", session_service=_session_service)
except Exception as exc:
    _adk_error = str(exc)


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _accounts_table(rows: list[dict], value_key: str) -> str:
    lines = []
    for row in rows[:5]:
        lines.append(
            f"- {row['account_name']} ({row['account_id']}): {_money(float(row[value_key]))}, owner {row['owner']}"
        )
    return "\n".join(lines)


async def _fallback_response(user_message: str) -> str:
    message = user_message.lower()
    underbilling = await detect_underbilling()
    expansion = await detect_expansion_gaps()
    connectors = await check_connector_health()
    trust = await get_dashboard_trust_assessment("Executive Revenue Dashboard")
    overview = await get_executive_summary()

    if "underbill" in message or "billing" in message or "invoice" in message:
        return f"""## Finding
Yes. StreamWorks Cloud has {underbilling['account_count']} underbilled accounts.

## Dollar Impact
{_money(underbilling['total_exposure'])} in missed overage charges.

## Root Cause
{underbilling['root_cause']}

## Affected Accounts
{_accounts_table(underbilling['underbilled_accounts'], 'underbilling_gap')}

## Recommended Actions
1. Fix the product_telemetry Fivetran connector.
2. Recompute usage overages for the current billing period.
3. Issue corrected invoices and add a billing validation rule.

## Trust Assessment
Revenue dashboard trust is {trust['overall_trust_score']}/100 because product_telemetry is delayed and Salesforce CRM has schema drift."""

    if "expansion" in message or "crm" in message or "pipeline" in message:
        return f"""## Finding
{expansion['account_count']} high-usage accounts are ready for expansion but missing from the CRM pipeline.

## Dollar Impact
{_money(expansion['total_expansion_value'])} in annual expansion potential.

## Root Cause
Usage exceeded 120% of contracted units, but no matching Salesforce expansion opportunities exist.

## Affected Accounts
{_accounts_table(expansion['expansion_gap_accounts'], 'estimated_annual_expansion')}

## Recommended Actions
1. Create expansion opportunities for all flagged accounts.
2. Assign each opportunity to the existing account owner.
3. Add a RevOps alert when usage stays above 120% for three weeks.

## Trust Assessment
Pipeline confidence is degraded by the salesforce_crm schema drift warning."""

    if "trust" in message or "dashboard" in message or "connector" in message:
        unhealthy = connectors["unhealthy_connectors"]
        unhealthy_lines = "\n".join(
            f"- {row['connector_name']}: {row['status']}, {row.get('staleness_hours', 0)}h stale, owner {row.get('owner', 'Data Team')}"
            for row in unhealthy[:6]
        )
        return f"""## Finding
Do not use the Executive Revenue Dashboard for final decisions today without remediation.

## Dollar Impact
The dashboard supports {_money(overview['total_revenue_at_risk'])} in identified risk and opportunity.

## Root Cause
Several upstream data sources are degraded.

## Affected Connectors
{unhealthy_lines}

## Recommended Actions
1. Re-authenticate cs_platform.
2. Resolve product_telemetry rate limiting and backfill usage.
3. Review Salesforce schema changes before refreshing executive metrics.

## Trust Assessment
Overall trust score: {trust['overall_trust_score']}/100. Verdict: {trust['verdict']}."""

    return f"""## Finding
MarginTrust AI found {_money(overview['total_revenue_at_risk'])} in revenue risk and opportunity.

## Dollar Impact
- Underbilling: {_money(overview['underbilling_exposure'])}
- Expansion gap: {_money(overview['expansion_gap'])}
- Cost leakage: {_money(overview['cost_leakage'])}

## Root Cause
The highest-impact issue is stale product telemetry, followed by CRM schema drift and broken CS/marketing connectors.

## Recommended Actions
1. Fix product_telemetry and recompute invoices.
2. Create missing expansion opportunities.
3. Repair broken Fivetran connectors before refreshing executive dashboards.

## Trust Assessment
Executive Revenue Dashboard trust score: {overview['overall_trust_score']}/100."""


async def run_agent_query(user_message: str, session_id: str = "default") -> dict:
    """Send a message to the MarginTrust agent and return the response."""
    if _runner and _session_service:
        from google.genai import types

        session = await _session_service.get_session(
            app_name="margintrust", user_id="user", session_id=session_id
        )
        if not session:
            session = await _session_service.create_session(
                app_name="margintrust", user_id="user", session_id=session_id
            )

        user_content = types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
        final_response = ""
        async for event in _runner.run_async(
            user_id="user", session_id=session.id, new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_response += "".join(part.text or "" for part in event.content.parts)
        return {"answer": final_response, "session_id": session.id}

    answer = await _fallback_response(user_message)
    if _adk_error:
        answer += f"\n\nLocal deterministic mode is active because ADK was unavailable: {_adk_error}"
    return {"answer": answer, "session_id": session_id}

