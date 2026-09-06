"""Tests for the dashboard HTTP activity monitor."""

from app import ActivityLog, DashboardHandler


def test_activity_log_keeps_newest_events_first():
    log = ActivityLog(limit=2)
    log.add({"id": "first"})
    log.add({"id": "second"})
    log.add({"id": "third"})

    snapshot = log.snapshot()
    assert snapshot["total"] == 2
    assert [event["id"] for event in snapshot["events"]] == ["third", "second"]


def test_mcp_context_identifies_tool_routes():
    assert DashboardHandler.mcp_context("/api/servers/fetch/tools") == ("fetch", "list_tools")
    assert DashboardHandler.mcp_context("/api/servers/fetch/execute") == ("fetch", "execute_tool")
    assert DashboardHandler.mcp_context("/api/servers") == (None, None)


def test_mcp_context_decodes_server_key():
    assert DashboardHandler.mcp_context("/api/servers/github%2Fenterprise/tools") == (
        "github/enterprise",
        "list_tools",
    )
