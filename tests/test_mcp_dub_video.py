"""Tests for MCP dub_video tool."""
from __future__ import annotations

import json
import pytest


def test_dub_video_tool_registered():
    import mcp_server

    server = mcp_server.create_mcp_server()
    # FastMCP stores registered tools in server._tool_manager._tools or similar
    tools = getattr(server, "_tool_manager", None)
    if tools is not None:
        tool_names = list(tools._tools.keys())
    else:
        # Fallback inspection
        tool_names = [t.name for t in getattr(server, "tools", [])]
    assert "dub_video" in tool_names


def test_dub_video_requires_url_or_path():
    import asyncio
    import mcp_server

    server = mcp_server.create_mcp_server()
    # Call the tool function directly
    tool_fn = None
    if hasattr(server, "_tool_manager"):
        tool_fn = server._tool_manager._tools["dub_video"].fn
    assert tool_fn is not None

    res = asyncio.run(tool_fn())
    data = json.loads(res)
    assert "error" in data
    assert "Either 'url' or 'video_path'" in data["error"]
