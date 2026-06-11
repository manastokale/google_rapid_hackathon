"""Action queue endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
action_store: dict[str, str] = {}


class ActionAck(BaseModel):
    acknowledged: bool = True


def _severity_for_dollars(value: float) -> str:
    if value >= 100000:
        return "critical"
    if value >= 50000:
        return "high"
    if value >= 10000:
        return "medium"
    return "low"


@router.get("/queue")
async def get_action_queue():
    from app.services.bigquery_service import (
        get_cost_leakage,
        get_expansion_gap_accounts,
        get_stale_connectors,
        get_underbilled_accounts,
    )

    actions = []
    priority = 1

    underbilled = await get_underbilled_accounts()
    if underbilled:
        total = round(sum(row.get("underbilling_gap", 0) for row in underbilled), 2)
        actions.append({
            "id": f"action-{priority}",
            "priority": priority,
            "issue_type": "underbilling",
            "description": f"{len(underbilled)} accounts with usage exceeding contract limits but not invoiced for overages",
            "dollar_impact": total,
            "severity": _severity_for_dollars(total),
            "owner": "Finance / Billing Ops",
            "recommended_action": "Fix product_telemetry, recompute overage charges, and issue corrected invoices",
            "status": action_store.get(f"action-{priority}", "new"),
        })
        priority += 1

    expansion = await get_expansion_gap_accounts()
    if expansion:
        total = round(sum(row.get("estimated_annual_expansion", 0) for row in expansion), 2)
        actions.append({
            "id": f"action-{priority}",
            "priority": priority,
            "issue_type": "expansion_gap",
            "description": f"{len(expansion)} high-usage accounts without expansion opportunities in CRM",
            "dollar_impact": total,
            "severity": _severity_for_dollars(total),
            "owner": "Sales / RevOps",
            "recommended_action": "Create expansion opportunities in Salesforce and assign to account owners",
            "status": action_store.get(f"action-{priority}", "new"),
        })
        priority += 1

    cost_leakage = await get_cost_leakage()
    actions.append({
        "id": f"action-{priority}",
        "priority": priority,
        "issue_type": "cost_leakage",
        "description": "Duplicate marketing spend rows detected from a paused connector",
        "dollar_impact": cost_leakage,
        "severity": _severity_for_dollars(cost_leakage),
        "owner": "Marketing / Finance",
        "recommended_action": "Deduplicate marketing spend rows and restart the connector",
        "status": action_store.get(f"action-{priority}", "new"),
    })
    priority += 1

    for connector in await get_stale_connectors():
        action_id = f"connector-{connector['connector_name']}"
        actions.append({
            "id": action_id,
            "priority": priority,
            "issue_type": "connector_health",
            "description": f"Connector '{connector['connector_name']}' is {connector['status']}: {connector.get('error_message', 'investigate')}",
            "dollar_impact": 0,
            "severity": "high" if connector["status"] == "broken" else "medium",
            "owner": connector.get("owner", "Data Team"),
            "recommended_action": f"Fix connector '{connector['connector_name']}' and backfill affected tables",
            "status": action_store.get(action_id, "new"),
        })
        priority += 1

    return {"actions": actions}


@router.post("/{action_id}/acknowledge")
async def acknowledge_action(action_id: str, _: ActionAck | None = None):
    action_store[action_id] = "acknowledged"
    if action_id.startswith("connector-"):
        from app.services.bigquery_service import repair_connector

        repair_connector(action_id.removeprefix("connector-"))
        action_store[action_id] = "repaired"
        return {"action_id": action_id, "status": "repaired"}
    return {"action_id": action_id, "status": "acknowledged"}
