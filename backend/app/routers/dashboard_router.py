"""Dashboard data endpoints."""

from fastapi import APIRouter

from app.agent.agent import get_dashboard_trust_assessment, get_metric_trust_score
from app.services.bigquery_service import (
    get_connector_statuses,
    get_dashboard_overview,
    get_expansion_gap_accounts,
    get_metric_dependencies,
    get_stale_connectors,
    get_underbilled_accounts,
)

router = APIRouter()


@router.get("/overview")
async def overview():
    return await get_dashboard_overview()


@router.get("/connectors")
async def connectors():
    return await get_connector_statuses()


@router.get("/connectors/unhealthy")
async def unhealthy_connectors():
    return await get_stale_connectors()


@router.get("/underbilling")
async def underbilling():
    return await get_underbilled_accounts()


@router.get("/expansion-gaps")
async def expansion_gaps():
    return await get_expansion_gap_accounts()


@router.get("/metrics")
async def metrics():
    return await get_metric_dependencies()


@router.get("/metrics/{metric_name}/trust")
async def metric_trust(metric_name: str):
    return await get_metric_trust_score(metric_name)


@router.get("/trust")
async def dashboard_trust(name: str = "Executive Revenue Dashboard"):
    return await get_dashboard_trust_assessment(name)

