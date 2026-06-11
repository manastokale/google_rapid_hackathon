import asyncio
import os

os.environ["USE_BIGQUERY"] = "false"

from app.services.bigquery_service import (
    get_cost_leakage,
    get_dashboard_overview,
    get_expansion_gap_accounts,
    get_stale_connectors,
    get_underbilled_accounts,
)
from app.services.local_data import load_table


def test_demo_story_totals():
    async def run():
        underbilled = await get_underbilled_accounts()
        expansion = await get_expansion_gap_accounts()
        overview = await get_dashboard_overview()
        assert len(underbilled) == 14
        assert round(sum(row["underbilling_gap"] for row in underbilled)) == 126000
        assert len(expansion) == 8
        assert round(sum(row["estimated_annual_expansion"] for row in expansion)) == 420000
        assert await get_cost_leakage() == 18000
        assert overview["overall_trust_score"] == 62

    asyncio.run(run())


def test_seed_data_has_poc_scale_and_connector_coverage():
    accounts = load_table("accounts")
    usage_events = load_table("product_usage_events")
    marketing = load_table("marketing_spend")
    tickets = load_table("support_tickets")
    metrics = load_table("metric_dependency_map")
    connectors = load_table("fivetran_connector_status")

    assert len(accounts) == 750
    assert len(usage_events) > 65000
    assert len(marketing) > 800
    assert len(tickets) > 1500
    assert len(metrics) == 20

    statuses = {connector["status"] for connector in connectors}
    assert {"connected", "delayed", "broken"} <= statuses
    assert any(connector["schema_changes_detected"] for connector in connectors)

    async def run():
        stale = await get_stale_connectors()
        assert len(stale) >= 8

    asyncio.run(run())
