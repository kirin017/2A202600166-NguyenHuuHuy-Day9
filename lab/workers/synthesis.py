"""
workers/synthesis.py — Synthesis Worker
Sprint 2: Tổng hợp câu trả lời từ retrieved_chunks và policy_result.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI

WORKER_NAME = "synthesis_worker"

SYSTEM_PROMPT = """Bạn là trợ lý IT Helpdesk nội bộ.

Quy tắc nghiêm ngặt:
1. CHỈ trả lời dựa vào context được cung cấp. KHÔNG dùng kiến thức ngoài.
2. Nếu context không đủ để trả lời → nói rõ "Không đủ thông tin trong tài liệu nội bộ".
3. Trích dẫn nguồn cuối mỗi câu quan trọng: [tên_file].
4. Trả lời súc tích, có cấu trúc. Không dài dòng.
5. Nếu có exceptions/ngoại lệ → nêu rõ ràng trước khi kết luận.
6. Kết hợp thông tin từ Policy Check và Ticket Info (nếu có).
"""

def _call_llm(messages: List[Dict[str, str]]) -> str:
    """
    Gọi LLM để tổng hợp câu trả lời.
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[SYNTHESIS ERROR] {e}"

def _build_context(chunks: List[Dict[str, Any]], policy_result: Dict[str, Any], mcp_tools_used: List[Dict[str, Any]]) -> str:
    """Xây dựng context string."""
    parts = []
    
    if chunks:
        parts.append("=== TÀI LIỆU THAM KHẢO ===")
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[{i}] Nguồn: {chunk['source']}\n{chunk['text']}")
            
    if policy_result:
        parts.append("\n=== KẾT QUẢ KIỂM TRA CHÍNH SÁCH ===")
        parts.append(f"Policy Name: {policy_result.get('policy_name')}")
        parts.append(f"Applies: {policy_result.get('policy_applies')}")
        if policy_result.get("exceptions_found"):
            parts.append("Ngoại lệ tìm thấy:")
            for ex in policy_result["exceptions_found"]:
                parts.append(f"- {ex['rule']} (Nguồn: {ex['source']})")
        if policy_result.get("policy_version_note"):
            parts.append(f"Lưu ý phiên bản: {policy_result['policy_version_note']}")

    # Add Ticket/Access Info from MCP results
    ticket_info = next((m["output"] for m in mcp_tools_used if m["tool"] == "get_ticket_info"), None)
    if ticket_info:
        parts.append("\n=== THÔNG TIN TICKET HIỆN TẠI ===")
        parts.append(json.dumps(ticket_info, indent=2, ensure_ascii=False))
        
    access_info = next((m["output"] for m in mcp_tools_used if m["tool"] == "check_access_permission"), None)
    if access_info:
        parts.append("\n=== KẾT QUẢ KIỂM TRA QUYỀN TRUY CẬP ===")
        parts.append(json.dumps(access_info, indent=2, ensure_ascii=False))

    return "\n".join(parts)

def _estimate_confidence(chunks: List[Dict[str, Any]], answer: str) -> float:
    """
    Tính toán confidence thực tế dựa trên retrieval scores và nội dung câu trả lời.
    """
    if not chunks:
        return 0.2 if "Không đủ thông tin" in answer else 0.4
    
    # 1. Lấy trung bình cộng của relevance scores từ retrieval
    avg_chunk_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
    
    # 2. Kiểm tra nếu câu trả lời chứa từ khóa phủ định dù có chunks
    if "không có thông tin" in answer.lower() or "không đủ thông tin" in answer.lower():
        return round(avg_chunk_score * 0.5, 2) # Giảm 50% nếu có chunks nhưng vẫn không trả lời được
        
    # 3. Phạt nếu câu trả lời quá ngắn (có thể thiếu ý)
    length_penalty = 1.0
    if len(answer.split()) < 10:
        length_penalty = 0.8
        
    confidence = avg_chunk_score * length_penalty
    
    # Giới hạn trong khoảng [0.1, 0.95]
    return round(max(0.1, min(0.95, confidence)), 2)

def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker entry point.
    """
    import json
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})
    mcp_tools_used = state.get("mcp_tools_used", [])
    
    context = _build_context(chunks, policy_result, mcp_tools_used)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Câu hỏi: {task}\n\nContext:\n{context}"}
    ]
    
    answer = _call_llm(messages)
    
    # Tính toán confidence động
    confidence = _estimate_confidence(chunks, answer)
    
    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "has_context": bool(chunks)},
        "output": {"confidence": confidence},
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "final_answer": answer,
        "sources": list({c["source"] for c in chunks}),
        "confidence": confidence,
        "worker_io_logs": state.get("worker_io_logs", []) + [worker_io]
    }
