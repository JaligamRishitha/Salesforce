#!/usr/bin/env python3
"""
MCP Server for ServiceNow Integration
Provides tools to interact with ServiceNow ITSM
"""

import json
import httpx
from typing import Optional
from mcp.server import Server
from mcp.types import TextContent

# ServiceNow Configuration
SERVICENOW_INSTANCE = "https://dev12345.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASSWORD = "password"

server = Server("servicenow-integration")


async def servicenow_api_call(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    """Make authenticated API call to ServiceNow"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = f"{SERVICENOW_INSTANCE}/api/now{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0, auth=(SERVICENOW_USER, SERVICENOW_PASSWORD)) as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code >= 400:
            return {
                "error": f"ServiceNow API Error {response.status_code}",
                "details": response.text,
            }
        return response.json()


# ============================================================================
# SERVICENOW INCIDENT TOOLS
# ============================================================================

@server.call_tool()
async def list_incidents(skip: int = 0, limit: int = 50, query: str = ""):
    """List ServiceNow incidents"""
    params = {"offset": skip, "limit": limit}
    if query:
        params["sysparm_query"] = query
    result = await servicenow_api_call("GET", "/table/incident", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_incident(incident_id: str):
    """Get ServiceNow incident by ID"""
    result = await servicenow_api_call("GET", f"/table/incident/{incident_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_incident(
    short_description: str,
    description: str = "",
    priority: str = "3",
    urgency: str = "3",
    impact: str = "3",
    assignment_group: str = "",
):
    """Create new ServiceNow incident"""
    data = {
        "short_description": short_description,
        "description": description,
        "priority": priority,
        "urgency": urgency,
        "impact": impact,
    }
    if assignment_group:
        data["assignment_group"] = assignment_group
    result = await servicenow_api_call("POST", "/table/incident", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_incident(incident_id: str, **kwargs):
    """Update ServiceNow incident"""
    result = await servicenow_api_call("PUT", f"/table/incident/{incident_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def close_incident(incident_id: str, close_notes: str = ""):
    """Close ServiceNow incident"""
    data = {
        "state": "7",
        "close_notes": close_notes,
    }
    result = await servicenow_api_call("PUT", f"/table/incident/{incident_id}", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SERVICENOW CHANGE REQUEST TOOLS
# ============================================================================

@server.call_tool()
async def list_change_requests(skip: int = 0, limit: int = 50):
    """List ServiceNow change requests"""
    params = {"offset": skip, "limit": limit}
    result = await servicenow_api_call("GET", "/table/change_request", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_change_request(change_id: str):
    """Get ServiceNow change request by ID"""
    result = await servicenow_api_call("GET", f"/table/change_request/{change_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_change_request(
    short_description: str,
    description: str = "",
    type: str = "normal",
    priority: str = "3",
):
    """Create new ServiceNow change request"""
    data = {
        "short_description": short_description,
        "description": description,
        "type": type,
        "priority": priority,
    }
    result = await servicenow_api_call("POST", "/table/change_request", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_change_request(change_id: str, **kwargs):
    """Update ServiceNow change request"""
    result = await servicenow_api_call("PUT", f"/table/change_request/{change_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SERVICENOW PROBLEM TOOLS
# ============================================================================

@server.call_tool()
async def list_problems(skip: int = 0, limit: int = 50):
    """List ServiceNow problems"""
    params = {"offset": skip, "limit": limit}
    result = await servicenow_api_call("GET", "/table/problem", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_problem(problem_id: str):
    """Get ServiceNow problem by ID"""
    result = await servicenow_api_call("GET", f"/table/problem/{problem_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_problem(
    short_description: str,
    description: str = "",
    priority: str = "3",
):
    """Create new ServiceNow problem"""
    data = {
        "short_description": short_description,
        "description": description,
        "priority": priority,
    }
    result = await servicenow_api_call("POST", "/table/problem", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SERVICENOW CONFIGURATION ITEM TOOLS
# ============================================================================

@server.call_tool()
async def list_config_items(skip: int = 0, limit: int = 50, query: str = ""):
    """List ServiceNow configuration items"""
    params = {"offset": skip, "limit": limit}
    if query:
        params["sysparm_query"] = query
    result = await servicenow_api_call("GET", "/table/cmdb_ci", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_config_item(ci_id: str):
    """Get ServiceNow configuration item by ID"""
    result = await servicenow_api_call("GET", f"/table/cmdb_ci/{ci_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SERVICENOW USER TOOLS
# ============================================================================

@server.call_tool()
async def list_users(skip: int = 0, limit: int = 50):
    """List ServiceNow users"""
    params = {"offset": skip, "limit": limit}
    result = await servicenow_api_call("GET", "/table/sys_user", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_user(user_id: str):
    """Get ServiceNow user by ID"""
    result = await servicenow_api_call("GET", f"/table/sys_user/{user_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SERVICENOW KNOWLEDGE BASE TOOLS
# ============================================================================

@server.call_tool()
async def search_knowledge_base(query: str, limit: int = 10):
    """Search ServiceNow knowledge base"""
    params = {"sysparm_query": f"short_descriptionLIKE{query}", "limit": limit}
    result = await servicenow_api_call("GET", "/table/kb_knowledge", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_knowledge_article(article_id: str):
    """Get ServiceNow knowledge article by ID"""
    result = await servicenow_api_call("GET", f"/table/kb_knowledge/{article_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SERVICENOW HEALTH CHECK
# ============================================================================

@server.call_tool()
async def servicenow_health_check():
    """Check ServiceNow connectivity"""
    try:
        result = await servicenow_api_call("GET", "/table/sys_user?sysparm_limit=1")
        return [TextContent(type="text", text=json.dumps({"status": "healthy", "message": "Connected to ServiceNow"}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "unhealthy", "error": str(e)}))]


if __name__ == "__main__":
    server.run()
