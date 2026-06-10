import asyncio

from app.services.bigquery_service import get_dashboard_overview, get_expansion_gap_accounts, get_underbilled_accounts


def test_demo_story_totals():
    async def run():
        underbilled = await get_underbilled_accounts()
        expansion = await get_expansion_gap_accounts()
        overview = await get_dashboard_overview()
        assert len(underbilled) == 14
        assert round(sum(row["underbilling_gap"] for row in underbilled)) == 126000
        assert len(expansion) == 8
        assert round(sum(row["estimated_annual_expansion"] for row in expansion)) == 420000
        assert overview["overall_trust_score"] == 62

    asyncio.run(run())

