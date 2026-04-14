# Routing Decisions Log — Lab Day 09

**Nhóm:** AI in Action - Group 01
**Ngày:** 2026-04-14

---

## Routing Decision #1

**Task đầu vào:**
> Ai phải phê duyệt để cấp quyền Level 3?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword`  
**MCP tools được gọi:** search_kb, check_access_permission  
**Workers called sequence:** policy_tool_worker -> retrieval_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): Cần sự phê duyệt từ Quản lý trực tiếp, Quản lý IT và CTO.
- confidence: 0.4
- Correct routing? Yes

**Nhận xét:** Routing đúng vì câu hỏi liên quan đến quyền truy cập (access level), Supervisor đã nhận diện từ khóa "quyền" và route sang policy_tool_worker để kiểm tra MCP.

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword`  
**MCP tools được gọi:** search_kb  
**Workers called sequence:** policy_tool_worker -> retrieval_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): Không đủ thông tin trong tài liệu nội bộ.
- confidence: 0.3
- Correct routing? Yes

**Nhận xét:** Supervisor route đúng sang policy_tool_worker do có từ khóa "hoàn tiền". Tuy nhiên, kết quả là abstain vì MCP search_kb không tìm thấy chunk liên quan (do index hoặc query chưa tối ưu).

---

## Routing Decision #3

**Task đầu vào:**
> Tài khoản bị khóa sau bao nhiêu lần đăng nhập sai?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `default route`  
**MCP tools được gọi:** None  
**Workers called sequence:** retrieval_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): Không đủ thông tin trong tài liệu nội bộ.
- confidence: 0.3
- Correct routing? Yes

**Nhận xét:** Đây là một câu hỏi thông tin chung, không chứa keyword đặc biệt về policy hay ticket khẩn cấp, nên route vào retrieval_worker là hợp lý.

---

## Routing Decision #4 (Tuỳ chọn)

**Task đầu vào:**
> ERR-403-AUTH là lỗi gì và cách xử lý?

**Worker được chọn:** `human_review` (sau đó route sang `retrieval_worker`)  
**Route reason:** `unknown error code + risk_high → human review`

**Nhận xét: Đây là trường hợp routing thú vị vì nó kích hoạt HITL.**
Supervisor nhận diện mã lỗi "ERR-" và gán nhãn `risk_high`, dẫn đến việc route sang `human_review_node`. Sau khi "human" (ở đây là auto-approve) duyệt, nó mới quay lại `retrieval_worker`.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 18 | 51% |
| policy_tool_worker | 17 | 48% |
| human_review | 1 | 1% (kích hoạt cho q09) |

### Routing Accuracy

- Câu route đúng: 15 / 15 (trong bộ test_questions)
- Câu route sai: 0
- Câu trigger HITL: 1

### Lesson Learned về Routing

1. Keyword matching đơn giản nhưng hiệu quả cho các bài toán có domain rõ ràng như Policy vs Technical Support.
2. Cần bổ sung thêm logic cho Supervisor để nhận diện các câu hỏi multi-hop phức tạp hơn (VD: kết hợp cả technical SLA và access policy).

### Route Reason Quality

Các `route_reason` trong trace hiện tại khá rõ ràng (VD: "task contains policy/access keyword", "default route"), giúp việc debug rất nhanh chóng. Cải tiến tiếp theo có thể là ghi thêm các keywords cụ thể mà Supervisor đã "bắt" được.
