"""Pydantic request and response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    session_id: str


class ConnectorStatus(BaseModel):
    connector_id: str
    connector_name: str
    status: str
    last_sync: str | None = None
    staleness_hours: float | None = None
    error_message: str = ""
    impacted_metrics: list[str] = Field(default_factory=list)


class DashboardOverview(BaseModel):
    total_revenue_at_risk: float
    underbilling_exposure: float
    expansion_gap: float
    cost_leakage: float
    overall_trust_score: int
    stale_connectors: int
    broken_connectors: int
    top_issues: list[dict[str, Any]]


class ActionItem(BaseModel):
    id: str
    issue_type: str
    description: str
    dollar_impact: float
    severity: str
    owner: str
    recommended_action: str
    status: str


class TrustScore(BaseModel):
    score: int
    breakdown: dict[str, Any]
    affected_metrics: list[str]

