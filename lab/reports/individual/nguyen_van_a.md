# Báo cáo cá nhân - Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Văn A  
**Vai trò trong nhóm:** Supervisor Owner & Worker Implementer  

---

## 1. Phần tôi phụ trách

Trong bài Lab này, tôi chịu trách nhiệm chính về việc thiết kế và triển khai kiến trúc điều phối (Orchestration Layer) sử dụng pattern **Supervisor-Worker**. Các phần việc cụ thể bao gồm:
- **Thiết kế State Management:** Xây dựng cấu trúc `AgentState` trong `graph.py` để lưu trữ thông tin xuyên suốt quá trình xử lý, bao gồm cả lịch sử (history) và nhật ký vào/ra của các worker (worker_io_logs).
- **Triển khai Supervisor Node:** Viết logic phân loại câu hỏi dựa trên từ khóa (keyword-based routing) để điều hướng yêu cầu đến đúng Worker chuyên biệt.
- **Phát triển Worker Nodes:** Triển khai 3 worker chính:
    - `retrieval_worker`: Kết nối với ChromaDB, thực hiện dense retrieval bằng OpenAI embeddings.
    - `policy_tool_worker`: Xử lý logic chính sách phức tạp và tích hợp các công cụ MCP để tra cứu thông tin ticket/access.
    - `synthesis_worker`: Sử dụng GPT-4o-mini để tổng hợp câu trả lời cuối cùng từ các bằng chứng thu thập được, đảm bảo có trích dẫn nguồn đầy đủ.
- **Xây dựng MCP Server:** Thiết lập các mock tools như `search_kb`, `get_ticket_info`, và `check_access_permission` để mở rộng khả năng của hệ thống mà không làm phình prompt của LLM.

## 2. Một quyết định kỹ thuật quan trọng

Một trong những quyết định kỹ thuật quan trọng nhất mà tôi đưa ra là việc lựa chọn **OpenAI text-embedding-3-small** làm model embedding mặc định thay vì dùng các model offline của sentence-transformers. 

**Lý do lựa chọn:**
- **Tính đồng nhất:** Khi sử dụng OpenAI cho cả phần synthesis, việc dùng chung hệ sinh thái giúp giảm thiểu sự sai lệch về ngữ nghĩa giữa khâu tìm kiếm và khâu tổng hợp.
- **Hiệu suất:** Model `3-small` của OpenAI có hiệu năng vượt trội và chi phí rất thấp, phù hợp với các hệ thống RAG cần độ chính xác cao trong việc tìm kiếm các đoạn văn bản ngắn (chunks).

**Kết quả từ trace:**
Trong file trace `run_20260414_163541.json`, khi người dùng hỏi về "SLA xử lý ticket P1", retrieval worker đã trả về kết quả với confidence cực cao (0.9), chứng minh rằng việc sử dụng OpenAI embeddings giúp tìm đúng tài liệu `sla_p1_2026.txt` ngay cả khi câu hỏi có sự thay đổi về mặt từ ngữ.

## 3. Một lỗi đã sửa

Trong quá trình triển khai Sprint 4 (Trace & Evaluation), tôi đã gặp một lỗi nghiêm trọng liên quan đến **UnicodeDecodeError** khi chạy script `eval_trace.py`.

**Mô tả lỗi:**
Hệ thống crash khi đang cố gắng đọc các file trace JSON trong thư mục `artifacts/traces/`. Nguyên nhân là do các file này chứa các ký tự tiếng Việt có dấu, trong khi hàm `json.load(f)` mặc định sử dụng encoding hệ thống (thường là cp1252 trên Windows), dẫn đến việc không thể giải mã các byte UTF-8.

**Cách sửa:**
Tôi đã thay đổi phương thức mở file trong hàm `analyze_traces` và `compare_single_vs_multi` bằng cách chỉ định rõ encoding là `utf-8`:
```python
with open(os.path.join(traces_dir, fname), encoding="utf-8") as f:
    traces.append(json.load(f))
```

**Bằng chứng:**
Sau khi sửa, script `python eval_trace.py` đã chạy thành công 100%, xử lý được toàn bộ 15 câu hỏi và tạo ra báo cáo `eval_report.json` với đầy đủ các metrics về latency và confidence.

## 4. Tự đánh giá

**Ưu điểm:**
- Tôi đã hoàn thành đúng hạn tất cả các Sprints theo yêu cầu của bài Lab.
- Hệ thống Multi-Agent do tôi thiết kế có tính module hóa cao, dễ dàng thay thế model hoặc logic của từng worker mà không ảnh hưởng đến supervisor.
- Trace log được thiết kế rất chi tiết, ghi lại được cả input/output của từng bước, giúp việc debug trở nên cực kỳ nhanh chóng.

**Hạn chế:**
- Phần Supervisor hiện tại vẫn đang dùng keyword matching. Trong thực tế, nếu câu hỏi quá phức tạp hoặc mang tính ẩn dụ, supervisor có thể route sai.
- Logic HITL hiện tại mới chỉ là auto-approve, chưa thực sự tương tác với người dùng qua giao diện terminal một cách linh hoạt.

## 5. Cải tiến nếu có thêm 2 giờ

Nếu có thêm 2 giờ, tôi sẽ thực hiện cải tiến **LLM-based Supervisor**. Thay vì dùng các câu lệnh `if/else` và từ khóa, tôi sẽ sử dụng một prompt nhỏ cho GPT-4o-mini để phân loại task.

**Lý do từ trace:**
Mặc dù accuracy hiện tại là 100% trên bộ test, nhưng trace `run_20260414_161735.json` cho thấy khi câu hỏi không chứa keyword nào (như "Tài khoản bị khóa..."), supervisor phải rơi vào `default route`. Việc dùng LLM làm Classifier sẽ giúp supervisor hiểu được ngữ cảnh sâu hơn, từ đó gán đúng `needs_tool` hoặc `risk_high` ngay cả khi không có từ khóa "khẩn cấp" hay "policy". Điều này sẽ giúp hệ thống trở nên thông minh và linh hoạt hơn nhiều.
