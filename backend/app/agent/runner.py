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
if settings.gemini_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.gemini_api_key)

_runner = None
_session_service = None
_adk_error: str | None = None

def _get_adk_runner():
    global _runner, _session_service, _adk_error

    if not settings.gemini_api_key:
        return None, None
    if _runner and _session_service:
        return _runner, _session_service
    if _adk_error:
        return None, None

    try:
        from google.adk.runners import InMemoryRunner

        agent = create_agent()
        _runner = InMemoryRunner(agent=agent, app_name="margintrust")
        _session_service = _runner.session_service
    except Exception as exc:
        _adk_error = str(exc)
        return None, None

    return _runner, _session_service


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _accounts_table(rows: list[dict], value_key: str) -> str:
    if not rows:
        return "- None found"
    lines = []
    for row in rows[:5]:
        lines.append(
            f"- {row['account_name']} ({row['account_id']}): {_money(float(row[value_key]))}, owner {row['owner']}"
        )
    return "\n".join(lines)


def _lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None"


def _top_issue(overview: dict) -> dict:
    issues = sorted(
        overview.get("top_issues", []),
        key=lambda issue: float(issue.get("impact") or 0),
        reverse=True,
    )
    return issues[0] if issues else {
        "issue": "No issue found",
        "description": "No active revenue risk found in the analytics overview",
        "impact": 0,
        "owner": "Data Platform",
        "severity": "healthy",
    }


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

## Evidence Checked
{_lines(underbilling['evidence_checked'])}

## Affected Accounts
{_accounts_table(underbilling['underbilled_accounts'], 'underbilling_gap')}

## Dollar Impact
{_money(underbilling['total_exposure'])} in missed overage charges.

## Root Cause
{underbilling['root_cause']}

## Recommended Owner
{underbilling['recommended_owner']}

## Next Action
{underbilling['next_action']}

## Confidence/Trust Score
Executive Revenue Dashboard trust is {trust['overall_trust_score']}/100. Verdict: {trust['verdict']}."""

    if "expansion" in message or "crm" in message or "pipeline" in message:
        return f"""## Finding
{expansion['account_count']} high-usage accounts are ready for expansion but missing from the CRM pipeline.

## Evidence Checked
{_lines(expansion['evidence_checked'])}

## Affected Accounts
{_accounts_table(expansion['expansion_gap_accounts'], 'estimated_annual_expansion')}

## Dollar Impact
{_money(expansion['total_expansion_value'])} in annual expansion potential.

## Root Cause
{expansion['root_cause']}

## Recommended Owner
{expansion['recommended_owner']}

## Next Action
{expansion['next_action']}

## Confidence/Trust Score
Executive Revenue Dashboard trust is {trust['overall_trust_score']}/100. Verdict: {trust['verdict']}."""

    if "trust" in message or "dashboard" in message or "connector" in message:
        unhealthy = connectors["unhealthy_connectors"]
        unhealthy_lines = "\n".join(
            f"- {row['connector_name']}: {row['status']}, {row.get('staleness_hours', 0)}h stale, owner {row.get('owner', 'Data Team')}"
            for row in unhealthy[:6]
        ) or "- None found"
        return f"""## Finding
Do not use the Executive Revenue Dashboard for final decisions today without remediation.

## Evidence Checked
{_lines(connectors['evidence_checked'])}

## Affected Connectors
{unhealthy_lines}

## Dollar Impact
The dashboard supports {_money(overview['total_revenue_at_risk'])} in identified risk and opportunity.

## Root Cause
{trust.get('reason', 'Several upstream data sources are degraded.')}

## Recommended Owner
{connectors['recommended_owner']}

## Next Action
{connectors['next_action']}

## Confidence/Trust Score
Overall trust score: {trust['overall_trust_score']}/100. Verdict: {trust['verdict']}."""

    if "costing" in message or "costs us" in message or "cost us" in message or "fix first" in message or "finance" in message or "revops" in message:
        issue = _top_issue(overview)
        return f"""## Finding
{issue['issue']} is the highest-dollar issue to fix first.

## Evidence Checked
- analytics.executive_overview
- analytics.underbilling_risk
- analytics.expansion_gaps
- analytics.cost_leakage
- analytics.dashboard_trust

## Affected Accounts/Connectors
See the ranked issue detail in the executive overview; this item is owned by {issue['owner']}.

## Dollar Impact
{_money(float(issue.get('impact') or 0))}. Total risk and opportunity across all tracked issues is {_money(overview['total_revenue_at_risk'])}.

## Root Cause
{issue['description']}

## Recommended Owner
{issue['owner']}

## Next Action
Start with {issue['issue'].lower()}, then refresh the executive dashboard after the owner confirms remediation.

## Confidence/Trust Score
Executive Revenue Dashboard trust score: {overview['overall_trust_score']}/100."""

    top_issue = _top_issue(overview)
    return f"""## Finding
MarginTrust AI found {_money(overview['total_revenue_at_risk'])} in revenue risk and opportunity.

## Evidence Checked
- analytics.executive_overview
- analytics.underbilling_risk
- analytics.expansion_gaps
- analytics.cost_leakage
- analytics.connector_health

## Affected Accounts/Connectors
- Underbilled accounts: {overview['underbilled_accounts_count']}
- Expansion-gap accounts: {overview['expansion_gap_accounts_count']}
- Stale or unhealthy connectors: {overview['stale_connectors']}

## Dollar Impact
- Underbilling: {_money(overview['underbilling_exposure'])}
- Expansion gap: {_money(overview['expansion_gap'])}
- Cost leakage: {_money(overview['cost_leakage'])}

## Root Cause
Highest-dollar issue: {top_issue['issue']} - {top_issue['description']}

## Recommended Owner
{top_issue['owner']}

## Next Action
Address {top_issue['issue'].lower()} first, then rerun the analytics views and refresh the backend.

## Confidence/Trust Score
Executive Revenue Dashboard trust score: {overview['overall_trust_score']}/100."""


async def run_agent_query(user_message: str, session_id: str = "default") -> dict:
    """Send a message to the MarginTrust agent and return the response."""
    runner, session_service = _get_adk_runner()
    if runner and session_service:
        try:
            from google.genai import types

            session = await session_service.get_session(
                app_name="margintrust", user_id="user", session_id=session_id
            )
            if not session:
                session = await session_service.create_session(
                    app_name="margintrust", user_id="user", session_id=session_id
                )

            user_content = types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
            final_response = ""
            async for event in runner.run_async(
                user_id="user", session_id=session.id, new_message=user_content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response += "".join(part.text or "" for part in event.content.parts)
            return {"answer": final_response, "session_id": session.id}
        except Exception as exc:
            answer = await _fallback_response(user_message)
            answer += f"\n\nLocal deterministic mode is active because ADK request failed: {exc}"
            return {"answer": answer, "session_id": session_id}

    answer = await _fallback_response(user_message)
    if _adk_error:
        answer += f"\n\nLocal deterministic mode is active because ADK was unavailable: {_adk_error}"
    return {"answer": answer, "session_id": session_id}
