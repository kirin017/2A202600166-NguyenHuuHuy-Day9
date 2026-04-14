# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** AI in Action - Group 01
**Ngày:** 2026-04-14

---

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.70 | 0.33 | -0.37 | Day 09 khắt khe hơn khi không có evidence |
| Avg latency (ms) | 1500 | 3175 | +1675 | Multi-agent tốn thêm bước supervisor & workers orchestration |
| Abstain rate (%) | 10% | 60% | +50% | Multi-agent tuân thủ luật "chỉ trả lời từ context" tốt hơn |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | Dễ dàng debug step-by-step |
| Debug time (estimate) | 20 phút | 5 phút | -15 phút | Nhờ trace JSON chi tiết từng worker |

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Cao | Cao |
| Latency | Thấp | Trung bình |
| Observation | Single agent xử lý nhanh hơn do không qua overhead của supervisor. | Multi-agent đảm bảo tính nhất quán qua các worker chuyên biệt. |

**Kết luận:** Với câu hỏi đơn giản, Single agent có lợi thế về tốc độ, nhưng Multi-agent cung cấp trace tốt hơn.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Thấp | Cao hơn |
| Routing visible? | ✗ | ✓ |
| Observation | Single agent dễ bị lẫn lộn thông tin hoặc bỏ sót các phần. | Multi-agent (thông qua MCP tools như check_access) xử lý logic tốt hơn. |

**Kết luận:** Multi-agent vượt trội trong việc xử lý logic phức tạp nhờ sự hỗ trợ của các tools chuyên biệt.

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | Thấp (hay hallucinate) | Cao (nghiêm ngặt hơn) |
| Observation | Single agent hay cố gắng trả lời dựa trên kiến thức sẵn có. | Multi-agent tuân thủ strict prompt tốt hơn nhờ synthesis worker tập trung. |

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu, phải print debug từng dòng.
Thời gian ước tính: 20 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Biết ngay lỗi tại khâu Routing, Retrieval hay Synthesis.
Thời gian ước tính: 5 phút
```

**Câu cụ thể nhóm đã debug:** Câu q09 về mã lỗi ERR-403. Ban đầu Supervisor không nhận diện được, sau khi thêm `risk_keywords` vào `supervisor_node`, hệ thống đã trigger HITL thành công.

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap worker |

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 1-2 LLM calls (Supervisor + Synthesis) |
| Complex query | 1 LLM call | 2-3 LLM calls (Supervisor + Policy LLM + Synthesis) |
| MCP tool call | N/A | Gọi tool qua dispatcher |

**Nhận xét về cost-benefit:** Tăng latency và cost (số token) nhưng đổi lại độ chính xác cao hơn và khả năng bảo trì hệ thống tốt hơn.

---

## 6. Kết luận

**Multi-agent tốt hơn single agent ở điểm nào?**
1. Khả năng debug và quan sát luồng dữ liệu (Observability).
2. Dễ dàng tích hợp tools bên ngoài thông qua MCP mà không làm nhiễu prompt chính.

**Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**
1. Latency cao hơn do overhead của việc điều phối.
2. Chi phí API cao hơn do phải gọi LLM nhiều lần cho một task.

**Khi nào KHÔNG nên dùng multi-agent?**
Khi bài toán đơn giản, chỉ cần retrieval từ 1 nguồn duy nhất và ưu tiên tốc độ phản hồi (latency) hơn là khả năng mở rộng.

**Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**
1. Cải tiến Supervisor bằng LLM để phân loại task tốt hơn keyword matching.
2. Thêm worker chuyên biệt cho từng phòng ban (HR, IT, Finance) để tăng độ chính xác của retrieval.
