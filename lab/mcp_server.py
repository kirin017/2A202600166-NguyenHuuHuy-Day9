"""
mcp_server.py — Mock MCP Server
Sprint 3: Implement search_kb, get_ticket_info, check_access_permission.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List

# ─────────────────────────────────────────────
# 1. Tool Implementations
# ─────────────────────────────────────────────

def search_kb(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Search Knowledge Base via ChromaDB.
    """
    from workers.retrieval import retrieve_dense
    
    try:
        chunks = retrieve_dense(query, top_k=top_k)
        sources = list({c["source"] for c in chunks})
        return {
            "chunks": chunks,
            "sources": sources,
            "total_found": len(chunks),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


def get_ticket_info(ticket_id: str) -> Dict[str, Any]:
    """
    Tra cứu thông tin ticket (mock data).
    """
    mock_tickets = {
        "P1-LATEST": {
            "ticket_id": "P1-2026-0413",
            "priority": "P1",
            "status": "Escalated",
            "assignee": "Senior Engineer (On-call)",
            "created_at": "2026-04-13T14:00:00",
            "sla_deadline": "2026-04-13T18:00:00",
            "notifications_sent": ["Email", "Slack", "SMS"],
        },
        "IT-1234": {
            "ticket_id": "IT-1234",
            "priority": "P2",
            "status": "In Progress",
            "assignee": "Helpdesk Level 1",
            "created_at": "2026-04-12T09:00:00",
            "sla_deadline": "2026-04-14T09:00:00",
            "notifications_sent": ["Email"],
        }
    }
    
    # Default return for unknown ticket
    ticket = mock_tickets.get(ticket_id, {
        "ticket_id": ticket_id,
        "priority": "P3",
        "status": "Open",
        "assignee": "Unassigned",
        "created_at": datetime.now().isoformat(),
        "sla_deadline": "N/A",
        "notifications_sent": []
    })
    
    return ticket


def check_access_permission(access_level: int, requester_role: str, is_emergency: bool = False) -> Dict[str, Any]:
    """
    Kiểm tra quyền truy cập.
    """
    can_grant = False
    required_approvers = []
    notes = []

    if access_level == 1:
        can_grant = True
        required_approvers = ["Direct Manager"]
    elif access_level == 2:
        if requester_role in ["Senior Engineer", "Admin"]:
            can_grant = True
        required_approvers = ["Direct Manager", "IT Manager"]
    elif access_level == 3:
        if is_emergency:
            notes.append("Emergency override requested.")
        can_grant = False # Level 3 always needs multi-approver
        required_approvers = ["Direct Manager", "IT Manager", "CTO"]

    return {
        "can_grant": can_grant,
        "required_approvers": required_approvers,
        "emergency_override": is_emergency,
        "notes": notes,
        "source": "access_control_sop.txt"
    }

# ─────────────────────────────────────────────
# 2. Dispatcher — Entry point cho workers
# ─────────────────────────────────────────────

def list_tools() -> List[Dict[str, Any]]:
    """Trả về danh sách các tools khả dụng."""
    return [
        {"name": "search_kb", "description": "Search internal knowledge base"},
        {"name": "get_ticket_info", "description": "Get status of a support ticket"},
        {"name": "check_access_permission", "description": "Check if an access request is allowed"}
    ]

def dispatch_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lộ trình gọi tool dựa trên tên.
    """
    if tool_name == "search_kb":
        return search_kb(
            query=tool_input.get("query", ""),
            top_k=tool_input.get("top_k", 3)
        )
    elif tool_name == "get_ticket_info":
        return get_ticket_info(
            ticket_id=tool_input.get("ticket_id", "")
        )
    elif tool_name == "check_access_permission":
        return check_access_permission(
            access_level=tool_input.get("access_level", 1),
            requester_role=tool_input.get("requester_role", "User"),
            is_emergency=tool_input.get("is_emergency", False)
        )
    else:
        return {"error": f"Tool '{tool_name}' not found."}


if __name__ == "__main__":
    # Test dispatcher
    print("Testing MCP Dispatcher...")
    print(f"search_kb: {dispatch_tool('search_kb', {'query': 'SLA P1'})['total_found']} chunks found")
    print(f"get_ticket_info: {dispatch_tool('get_ticket_info', {'ticket_id': 'P1-LATEST'})['status']}")
    print(f"check_access_permission: {dispatch_tool('check_access_permission', {'access_level': 3})['required_approvers']}")
