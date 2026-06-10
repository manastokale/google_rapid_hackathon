"""Mock Fivetran MCP Server using FastMCP."""

from mcp.server import fastmcp

from app.services.bigquery_service import get_connector_statuses, get_stale_connectors

mcp = fastmcp.FastMCP("FivetranMCP")


@mcp.tool()
async def list_connectors() -> list[dict]:
    """List all Fivetran connectors and their current sync status."""
    return await get_connector_statuses()


@mcp.tool()
async def get_connector_details(connector_id: str) -> dict:
    """Get detailed status for a specific Fivetran connector."""
    for connector in await get_connector_statuses():
        if connector["connector_id"] == connector_id:
            return connector
    return {"error": f"Connector {connector_id} not found"}


@mcp.tool()
async def get_unhealthy_connectors() -> list[dict]:
    """Get all connectors that are broken, delayed, stale, or drifting."""
    return await get_stale_connectors(threshold_hours=1)


@mcp.tool()
async def get_connector_sync_history(connector_id: str) -> dict:
    """Get recent sync history for a Fivetran connector."""
    for connector in await get_connector_statuses():
        if connector["connector_id"] == connector_id:
            return {
                "connector_id": connector_id,
                "recent_syncs": [
                    {
                        "sync_id": f"sync-{connector_id}-001",
                        "status": connector["status"],
                        "started_at": connector["last_sync_completed"],
                        "rows_synced": connector["rows_synced_last"],
                        "schema_changes": connector["schema_changes_detected"],
                    }
                ],
            }
    return {"error": f"Connector {connector_id} not found"}

