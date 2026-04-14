# System Architecture — Lab Day 09

**Nhóm:** AI in Action - Group 01
**Ngày:** 2026-04-14
**Version:** 1.0

---

## 1. Tổng quan kiến trúc

**Pattern đã chọn:** Supervisor-Worker  
**Lý do chọn pattern này (thay vì single agent):**
- Tách biệt trách nhiệm (Separation of Concerns): Supervisor chỉ lo điều phối, Workers lo chuyên môn.
- Dễ dàng mở rộng: Thêm capability mới chỉ cần thêm worker hoặc MCP tool mà không phá vỡ logic cũ.
- Khả năng quan sát (Observability): Trace rõ ràng từng bước routing và output của từng worker.
- Dễ debug: Có thể test độc lập từng worker (retrieval, policy, synthesis).

---

## 2. Sơ đồ Pipeline

```
User Request
     │
     ▼
┌──────────────┐
│  Supervisor  │  ← route_reason, risk_high, needs_tool
└──────┬───────┘
       │
   [route_decision]
       │
  ┌────┴──────────────────────────┐
  │                               │
  ▼                               ▼
Retrieval Worker         Policy Tool Worker
  (Dense Retrieval)        (Policy Analysis + MCP)
  │          ▲                    │
  │          └────────────────────┘
  │             (MCP search_kb)
  └─────────────┬─────────────────┘
                │
                ▼
          Synthesis Worker
            (GPT-4o-mini Answer + Citation)
                │
                ▼
             Output
```

---

## 3. Vai trò từng thành phần

### Supervisor (`graph.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Phân tích câu hỏi để quyết định luồng xử lý và gán nhãn risk. |
| **Input** | Câu hỏi từ người dùng (task) |
| **Output** | supervisor_route, route_reason, risk_high, needs_tool |
| **Routing logic** | Keyword-based matching (refund, access, P1, SLA, etc.) |
| **HITL condition** | Trigger khi phát hiện mã lỗi lạ hoặc yêu cầu khẩn cấp (P1). |

### Retrieval Worker (`workers/retrieval.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Tìm kiếm thông tin liên quan từ ChromaDB. |
| **Embedding model** | OpenAI text-embedding-3-small |
| **Top-k** | 3 (mặc định) |
| **Stateless?** | Yes |

### Policy Tool Worker (`workers/policy_tool.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Kiểm tra các quy định đặc biệt (flash sale, digital products) và gọi MCP tools. |
| **MCP tools gọi** | search_kb, get_ticket_info, check_access_permission |
| **Exception cases xử lý** | Flash Sale, Digital Products, Activated Products, Temporal scoping (< 01/02/2026) |

### Synthesis Worker (`workers/synthesis.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **LLM model** | GPT-4o-mini |
| **Temperature** | 0.1 |
| **Grounding strategy** | System prompt nghiêm ngặt "CHỈ trả lời dựa vào context", yêu cầu citation [file_name]. |
| **Abstain condition** | Khi context trống hoặc LLM xác định không có thông tin trong context. |

### MCP Server (`mcp_server.py`)

| Tool | Input | Output |
|------|-------|--------|
| search_kb | query, top_k | chunks, sources |
| get_ticket_info | ticket_id | ticket details (mock) |
| check_access_permission | access_level, role, emergency | can_grant, approvers |

---

## 4. Shared State Schema

| Field | Type | Mô tả | Ai đọc/ghi |
|-------|------|-------|-----------|
| task | str | Câu hỏi đầu vào | supervisor đọc |
| supervisor_route | str | Worker được chọn | supervisor ghi |
| route_reason | str | Lý do route | supervisor ghi |
| retrieved_chunks | list | Evidence từ retrieval | retrieval ghi, synthesis đọc |
| policy_result | dict | Kết quả kiểm tra policy | policy_tool ghi, synthesis đọc |
| mcp_tools_used | list | Tool calls đã thực hiện | policy_tool ghi |
| final_answer | str | Câu trả lời cuối | synthesis ghi |
| confidence | float | Mức tin cậy | synthesis ghi |
| workers_called | list | Danh sách worker đã qua | Tất cả ghi |
| history | list | Log các bước thực hiện | Tất cả ghi |

---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí | Single Agent (Day 08) | Supervisor-Worker (Day 09) |
|----------|----------------------|--------------------------|
| Debug khi sai | Khó — không rõ lỗi ở đâu | Dễ hơn — test từng worker độc lập |
| Thêm capability mới | Phải sửa toàn prompt | Thêm worker/MCP tool riêng |
| Routing visibility | Không có | Có route_reason trong trace |
| Khả năng mở rộng | Hạn chế bởi context window | Tốt hơn nhờ chuyên môn hóa worker |

---

## 6. Giới hạn và điểm cần cải tiến

1. Supervisor hiện tại dùng keyword matching đơn giản, có thể cải tiến bằng LLM classifier để chính xác hơn.
2. Chưa có cơ chế retry tự động khi worker trả về kết quả không thỏa mãn.
3. HITL (Human-in-the-loop) hiện tại mới chỉ là placeholder tự động approve.
