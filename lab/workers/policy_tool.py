"""
workers/policy_tool.py — Policy & Tool Worker
Sprint 2+3: Kiểm tra policy, gọi MCP tools.
"""

import os
from datetime import datetime
from typing import Dict, Any, List

WORKER_NAME = "policy_tool_worker"

def _call_mcp_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gọi MCP tool qua dispatcher trong mcp_server.py.
    """
    from mcp_server import dispatch_tool
    
    try:
        result = dispatch_tool(tool_name, tool_input)
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": result,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def analyze_policy(task: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Phân tích policy dựa trên context chunks.
    """
    task_lower = task.lower()
    context_text = " ".join([c["text"] for c in chunks]).lower()
    
    exceptions = []
    
    # Exception detection
    if "flash sale" in task_lower or "flash sale" in context_text:
        exceptions.append({
            "type": "flash_sale_exception",
            "rule": "Đơn hàng Flash Sale không được hoàn tiền (Điều 3, chính sách v4).",
            "source": "policy_refund_v4.txt"
        })
        
    if any(kw in task_lower for kw in ["license", "key", "subscription", "kỹ thuật số"]):
        exceptions.append({
            "type": "digital_product_exception",
            "rule": "Sản phẩm kỹ thuật số (license key, subscription) không được hoàn tiền.",
            "source": "policy_refund_v4.txt"
        })
        
    if any(kw in task_lower for kw in ["đã kích hoạt", "đã dùng", "đã đăng ký"]):
        exceptions.append({
            "type": "activated_product_exception",
            "rule": "Sản phẩm đã kích hoạt/đã dùng không được hoàn tiền.",
            "source": "policy_refund_v4.txt"
        })
        
    policy_name = "refund_policy_v4"
    policy_version_note = ""
    # Temporal check (if order before 01/02/2026)
    if any(kw in task_lower for kw in ["31/01", "30/01", "trước tháng 2", "trước 01/02"]):
        policy_version_note = "Đơn hàng đặt trước 01/02/2026 áp dụng chính sách v3 (không có trong tài liệu hiện tại)."
        
    policy_applies = len(exceptions) == 0
    
    return {
        "policy_applies": policy_applies,
        "policy_name": policy_name,
        "exceptions_found": exceptions,
        "source": list({c["source"] for c in chunks}),
        "policy_version_note": policy_version_note
    }

def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker entry point.
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)
    
    mcp_tools_used = state.get("mcp_tools_used", [])
    
    # Step 1: Nếu chưa có chunks và supervisor bảo cần tool
    if not chunks and needs_tool:
        mcp_res = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
        mcp_tools_used.append(mcp_res)
        if mcp_res["output"] and "chunks" in mcp_res["output"]:
            chunks = mcp_res["output"]["chunks"]

    # Step 2: Policy Analysis
    policy_result = analyze_policy(task, chunks)
    
    # Step 3: Ticket status if needed
    if "ticket" in task.lower() or "jira" in task.lower():
        mcp_res = _call_mcp_tool("get_ticket_info", {"ticket_id": "P1-LATEST"})
        mcp_tools_used.append(mcp_res)
        
    # Step 4: Access check if needed
    if "access" in task.lower() or "quyền" in task.lower():
        level = 1
        if "level 2" in task.lower(): level = 2
        elif "level 3" in task.lower(): level = 3
        mcp_res = _call_mcp_tool("check_access_permission", {
            "access_level": level, 
            "requester_role": "User", 
            "is_emergency": "khẩn cấp" in task.lower() or "emergency" in task.lower()
        })
        mcp_tools_used.append(mcp_res)
        
    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "chunks_count": len(chunks)},
        "output": {"policy_applies": policy_result["policy_applies"]},
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "retrieved_chunks": chunks,
        "policy_result": policy_result,
        "mcp_tools_used": mcp_tools_used,
        "worker_io_logs": state.get("worker_io_logs", []) + [worker_io]
    }
