# Kế hoạch phát triển Data Agent dựa trên Kiến trúc Query GPT của Uber

## 1. Phân tích Kiến trúc Query GPT của Uber
Dựa vào sơ đồ cung cấp, kiến trúc Data Agent của Uber giải quyết bài toán Text-to-SQL ở quy mô doanh nghiệp với các thành phần chính sau:

*   **Người dùng & Prompt Enhancer**: Nhận câu hỏi bằng ngôn ngữ tự nhiên từ người dùng. Trước khi xử lý, câu hỏi được **mở rộng/làm rõ** (Prompt Enhancer) để bổ sung ngữ cảnh khi câu hỏi quá ngắn hoặc mơ hồ — blog Uber ghi rõ: *"A 'prompt enhancer' was needed to 'massage' the user question into a more context-rich question."*
*   **Intent Agent**: Phân tích ý định để **map câu hỏi vào workspace cụ thể** (ví dụ: Mobility, Ads, Core Services). Đây là bước trung gian quan trọng giúp thu hẹp phạm vi tìm kiếm RAG — blog ghi: *"The intent agent maps the user's question to one or more business domains/workspaces."*
*   **Workspace System (System + Custom Workspaces)**: Các bảng dữ liệu được quy hoạch thành các **Không gian làm việc** (System Workspaces: Rides, Platform Eng; Custom Workspaces: Metrics, COGS). Mỗi workspace chứa một tập SQL samples + tables riêng. Workspace giúp **drastically narrow the search radius** cho RAG.
*   **RAG với SQL Samples & Table Agent**:
    *   Sử dụng cơ chế RAG để tìm kiếm các câu truy vấn SQL mẫu (few-shot) tương tự nhằm định hướng tư duy cho LLM.
    *   **Table Agent** đóng vai trò chắt lọc và chọn ra **một hoặc nhiều bảng** (Tables) cần thiết để trả lời câu hỏi. User có thể **xác nhận hoặc chỉnh sửa** danh sách tables trước khi tiếp tục (human-in-the-loop).
*   **Metadata Gateway & Get Table Schema**: Đóng vai trò cung cấp metadata, cung cấp lược đồ cấu trúc dữ liệu (tên cột, kiểu dữ liệu, ràng buộc khóa).
*   **Column Prune Agent (Đại lý lược bỏ cột)**: Xóa bớt các cột phi logic/không liên quan đến câu hỏi nhằm tối ưu kích thước Context Window của LLM, tránh nhiễu thông tin. Blog ghi nhận component này *"massively improved token size, cost, and latency."*
*   **Custom Instructions**: Cung cấp các hướng dẫn bổ sung đặc thù của doanh nghiệp (ví dụ: quy định xử lý ngày tháng, logic định nghĩa trường "driver license", v.v.). Đây là **các business rules** được inject trực tiếp vào prompt generation.
*   **GenAI Gateway & Azure OpenAI (Generate Query)**: Lắp ghép toàn bộ thông tin thu thập được (Câu hỏi + Schema rút gọn + SQL mẫu + Custom Instructions) để ra lệnh cho LLM sinh câu truy vấn SQL hoàn chỉnh.
*   **Self-Correction / Validation Agent**: Blog đề cập đang thử nghiệm *"a 'Validation' agent that recursively tries to fix hallucinations"*. Khi SQL execution fail, agent tự gửi lỗi + SQL gốc cho LLM để sửa và retry.
*   **Query Explanation Agent**: Giải nghĩa tác dụng của truy vấn SQL thành ngôn ngữ tự nhiên để người dùng dễ kiểm chứng, đồng thời tự động sinh giải nghĩa để làm giàu kho RAG mẫu.

### Pipeline tổng thể (theo blog & architecture diagram):

```
User → [Prompt Enhancer] → Intent Agent → Workspace Selection
    → RAG (SQL Samples) + Table Agent → User ACK Tables
    → Get Table Schema (Metadata Gateway) → Column Prune Agent
    → Custom Instructions → GenAI Gateway → SQL Query
    → [Self-Correction nếu fail] → SQL Execution → Result
    → [Query Explanation Agent → Feedback vào SQL Samples]
```

## 2. Áp dụng cho Dự án hiện tại với `@data/InfiAgent/da-dev-tables`

Dự án hiện tại không phải là một Data Warehouse tập trung (như Hive, Snowflake) mà gồm **68 file dữ liệu dạng CSV rời rạc** (ví dụ: `titanic.csv`, `diamonds.csv`, `weather_train.csv`, `microsoft.csv`...) và bộ câu hỏi mẫu tại `da-dev-questions.jsonl`.

Để mô phỏng kiến trúc Uber, hướng tiếp cận sử dụng Python kết hợp với **DuckDB** (truy vấn SQL thẳng trên file CSV) hoặc **Pandas** (Text-to-Python) là thích hợp nhất. Dưới đây là phương án ánh xạ:

### Ánh xạ Kiến trúc

1.  **Prompt Enhancer (Mở rộng câu hỏi)**:
    *   Trước khi bắt đầu pipeline, câu hỏi ngắn/mơ hồ của user sẽ được LLM mở rộng thành câu hỏi chi tiết hơn.
    *   Ví dụ: `"average fare"` → `"Tính giá trị trung bình (average) của cột fare trong bảng dữ liệu liên quan đến vận tải/hành khách"`.
    *   Giúp cải thiện accuracy ở các bước Intent Agent và Table Agent phía sau.

2.  **Workspace System (Phân nhóm dữ liệu)**:
    *   68 file CSV được nhóm thành các **System Workspaces** theo chủ đề:
        *   `finance`: `microsoft.csv`, `stocks.csv`, `financial_data.csv`, ...
        *   `sports`: `nba.csv`, `baseball_reference.csv`, ...
        *   `health`: `medical_data.csv`, `diabetes.csv`, ...
        *   `transportation`: `titanic.csv`, `flights.csv`, ...
        *   `general`: các file không thuộc nhóm cụ thể nào
    *   Workspace mapping lưu trong `workspaces.json`.
    *   User có thể tạo **Custom Workspace** bằng cách config thêm.

3.  **Intent Agent (Định tuyến Workspace)**:
    *   Không chỉ trả về 1 cụm từ chủ đề chung, mà **map trực tiếp vào workspace ID**.
    *   Output: workspace ID (VD: `finance`, `sports`) → thu hẹp phạm vi tables cho Table Agent.
    *   Có thể map đến **nhiều workspaces** nếu câu hỏi liên quan đến nhiều domain.

4.  **Table Agent & Metadata Gateway**:
    *   Thay vì gọi qua API Metadata Gateway phức tạp, chúng ta sẽ viết một đoạn mã Python quét 68 file CSV này để sinh ra một kho dữ liệu Metadata lưu trữ dưới dạng file `schema_registry.json`.
    *   Schema lưu trữ: Tên file, danh sách tên cột, kiểu dữ liệu, workspace, và vài giá trị mẫu đầu tiên.
    *   Table Agent tìm kiếm **chỉ trong workspace đã chọn** (thay vì toàn bộ 68 files) → trả về **Top-1 đến Top-3** file CSV phù hợp nhất.
    *   Trong Streamlit App, user có thể **xác nhận hoặc chỉnh sửa** danh sách tables (human-in-the-loop, giống UI Uber Figure 9).

5.  **Column Prune Agent**:
    *   Các file CSV có thể chứa hàng chục cột. Agent sẽ chạy bước LLM nhỏ để phân định: Đối với câu hỏi về "Fare và Age của Titanic", nó sẽ chỉ trích xuất schema của 2 cột đó, bỏ qua cột "Ticket", "Cabin".

6.  **Custom Instructions (Hướng dẫn Business Rules)**:
    *   File `custom_instructions.json` chứa các quy tắc đặc thù:
        *   Format ngày tháng cho từng dataset
        *   Alias/mapping tên cột (VD: `"revenue"` = `"total_amount"`)
        *   Các filter mặc định (VD: partition filter)
    *   Instructions sẽ được inject vào prompt của GenAI Gateway tùy theo workspace/table đang dùng.

7.  **RAG SQL Samples (Few-shot Retrieval)**:
    *   Xây dựng kho lưu trữ (SQL Sample Store) chứa các cặp `(câu hỏi, câu SQL đúng)` đã được kiểm chứng.
    *   Khi có câu hỏi mới, sử dụng cơ chế Semantic Search (embedding similarity) hoặc Keyword Search để tìm Top-K câu SQL mẫu tương tự nhất.
    *   Các SQL mẫu này được inject vào prompt như few-shot examples, giúp LLM "học" pattern SQL phù hợp với cấu trúc dữ liệu cụ thể.
    *   Ngoài ra, kết quả từ Query Explanation Agent có thể được tự động đưa ngược vào kho mẫu để làm giàu thêm (feedback loop).

8.  **Generator (GenAI Gateway)**:
    *   Tạo thành một Pipeline Prompt Generator tổng hợp: `System Prompt (Hướng dẫn DuckDB)` + `Table Schema đã pruned` + `SQL Samples (few-shot)` + `Custom Instructions` + `Câu hỏi hiện tại`.
    *   SQL Samples cung cấp context bổ sung giúp LLM sinh SQL chính xác hơn, đặc biệt với các schema phức tạp hoặc logic đặc thù.

9.  **Execution Engine + Self-Correction (Xử lý truy vấn)**:
    *   Câu lệnh sinh ra sẽ được tự động thực thi bởi máy ở Sandbox sử dụng DuckDB engine.
    *   **Self-Correction Logic**: Nếu SQL execution fail:
        1.  Lấy error message từ DuckDB.
        2.  Gửi lại `{câu_hỏi, SQL_gốc, error_message, schema}` cho LLM yêu cầu sửa.
        3.  Retry tối đa **2-3 lần** trước khi trả lỗi cho user.
    *   Trả kết quả tự động.

10. **Query Explanation Agent**:
    *   Module giải thích cho người dùng: "Tại sao câu SQL lại có cấu trúc như vậy" dựa trên yêu cầu ban đầu.
    *   Output explanation có thể được tự động thêm vào SQL Sample Store (feedback loop) để cải thiện RAG.

## 3. Lộ trình Triển khai (Roadmap Plan)

Đây là kế hoạch phát triển 5 Giai đoạn:

### Giai đoạn 1: Xây dựng Nền tảng Metadata (Data Foundation) ✅
*   **Task 1**: Phát triển script Quét Metadata (mô phỏng Metadata Gateway). Tự động đọc header 68 file CSV, nhận diện kiểu dữ liệu bằng pandas, trích xuất cấu trúc ra file `schema_registry.json`.
    *   📁 `query_gpt_system/metadata/schema_builder.py` → `schema_registry.json`

### Giai đoạn 2: Xây dựng các Core Agents (Routing & Pruning) ✅ (cần nâng cấp)
*   **Task 2**: Xây dựng Agent Tìm Bảng (Table Agent). Nhận câu hỏi, sử dụng LLM để so sánh semantic với schema của 68 file, trả về danh sách Top-1 đến Top-3 file CSV tương ứng nhất.
    *   📁 `query_gpt_system/core_agents/table_agent.py`
*   **Task 3**: Xây dựng Agent Cắt Cột (Column Prune Agent). Kêu gọi LLM với yêu cầu: "Đây là câu hỏi, đây là toàn bộ cột CSV, hãy liệt kê đúng tên những cột cần giải quyết câu hỏi và bỏ qua phần còn lại".
    *   📁 `query_gpt_system/core_agents/column_pruner.py`
*   **Task 4**: Xây dựng Intent Agent định tuyến các luồng cho hệ thống.
    *   📁 `query_gpt_system/core_agents/intent_agent.py`
*   **Task 4b** 🆕: Xây dựng Workspace System.
    *   Phân nhóm 68 file CSV vào các workspace (finance, sports, health, ...).
    *   Tạo file `workspaces.json` chứa mapping.
    *   Cập nhật Intent Agent output từ topic → workspace ID.
    *   Cập nhật Table Agent: tìm kiếm chỉ trong workspace đã chọn.
    *   📁 `query_gpt_system/metadata/workspaces.json` + sửa `intent_agent.py`, `table_agent.py`
*   **Task 4c** 🆕: Xây dựng Prompt Enhancer.
    *   Module LLM nhẹ mở rộng câu hỏi ngắn/mơ hồ thành câu chi tiết.
    *   Chạy trước Intent Agent trong pipeline.
    *   📁 `query_gpt_system/core_agents/prompt_enhancer.py` [NEW]

### Giai đoạn 3: Tích hợp Pipeline, Thực thi và Hoàn thiện ✅ (cần nâng cấp)
*   **Task 5**: Thiết kế GenAI Prompt Pipeline tổng hợp toàn bộ các kết quả từ: Danh sách cột cần, Câu hỏi đầu vào.
    *   📁 `query_gpt_system/core_agents/genai_gateway.py`
*   **Task 5b** 🆕: Xây dựng Custom Instructions Module.
    *   Tạo file `custom_instructions.json` chứa business rules theo workspace/table.
    *   Cập nhật `genai_gateway.py` để inject custom instructions vào prompt.
    *   📁 `query_gpt_system/metadata/custom_instructions.json` [NEW] + sửa `genai_gateway.py`
*   **Task 6**: Viết Sandboxed Executor + **Self-Correction Logic**.
    *   Tự động chạy SQL do LLM sinh ra. Nếu fail → retry loop (tối đa 2-3 lần):
        1.  Lấy error message.
        2.  Gọi LLM để sửa SQL dựa trên error.
        3.  Re-execute SQL đã sửa.
    *   📁 `query_gpt_system/executor/sql_engine.py` (cập nhật + bổ sung retry)
*   **Task 7**: Query Explanation Agent.
    *   Giải thích cho người dùng SQL query được sinh ra.
    *   Output kết hợp feedback loop cho SQL Sample Store.
    *   📁 `query_gpt_system/core_agents/query_explanation_agent.py` [NEW]

### Giai đoạn 4: RAG SQL Samples (Few-shot Retrieval) ✅ (Sắp triển khai)

> **Mục tiêu**: Cải thiện chất lượng SQL generation bằng cách cung cấp few-shot examples từ kho SQL mẫu đã kiểm chứng, sử dụng Agno framework, ChromaDB và OpenAI.

*   **Task 8**: Chuẩn bị dữ liệu SQL Sample
    *   Sử dụng file dữ liệu mẫu: `data/sql_samples.json` (chứa 1285 samples/257 questions với các variant: direct, cte, subquery, ...).
    *   Cấu trúc mỗi sample: `{question, sql, variants, concepts, level, table, file}`.

*   **Task 9**: Xây dựng SQL Sample Retriever (RAG)
    *   **Công nghệ**:
        *   **Framework**: [Agno](https://agno.com) (phidata) để quản lý RAG pipeline.
        *   **Embedding Model**: `text-embedding-3-small` của OpenAI (độ chính xác cao, chi phí thấp).
        *   **Vector Database**: **ChromaDB** (lưu trữ vector cục bộ, tốc độ truy vấn nhanh).
    *   **Chi tiết triển khai**:
        *   Viết script `query_gpt_system/sql_samples/ingest_samples.py` để chuyển đổi `sql_samples.json` vào ChromaDB. Chú ý chỉ embed `question` và lưu các variant SQL vào metadata.
        *   Xây dựng `query_gpt_system/core_agents/sql_sample_retriever.py` sử dụng Agno Knowledge Base để tìm Top-K samples tương tự nhất dựa trên câu hỏi người dùng.
        *   Hỗ trợ lọc theo `table_name` hoặc `workspace` để tăng độ chính xác của ngữ cảnh.

*   **Task 10**: Tích hợp SQL Samples vào GenAI Gateway Pipeline
    *   Cập nhật `genai_gateway.py` để nhận thêm `sql_samples` parameter.
    *   Inject SQL samples vào prompt theo format few-shot (cung cấp ví dụ thực tế cho LLM).
    *   Cập nhật `app_query_gpt.py` thêm bước RAG giữa bước "Tối ưu Schema" và "Sinh SQL".

### Giai đoạn 5: Nâng cấp UX & Table Agent (Nice-to-have)
*   **Task 11** 🆕: Table Agent Multi-table + User Confirmation.
    *   Cho phép Table Agent trả về **nhiều tables** (Top-2 hoặc Top-3).
    *   Trong `app_query_gpt.py`, thêm bước user confirm: "Bạn có muốn dùng các tables này không?" (giống Figure 9 trong blog Uber).
    *   Hỗ trợ JOIN query khi cần dữ liệu từ nhiều tables.
*   **Task 12** 🆕: Chat Mode — Iterative Query Refinement.
    *   Cho phép user tinh chỉnh query đã sinh thông qua chat (VD: "Thêm filter WHERE year > 2020").
    *   Giữ context của query trước đó trong conversation history.

## 4. Đề xuất Tổ chức Cấu trúc Thư mục (Directory Structure)

Để đáp ứng yêu cầu **vừa giữ nguyên hệ thống cũ (Streamlit + agents cũ)** cùng các kết quả benchmark, **vừa phát triển hệ thống mới (kiến trúc Uber)** chạy độc lập, cấu trúc thư mục nên được phân tách rõ ràng như sau:

```text
data-agent-demo/
├── data/                       # Dữ liệu CSV và file questions (giữ nguyên)
├── benchmark/                  # Kết quả benchmark cũ (giữ nguyên)
│
├── baseline_system/            # 👉 DI CHUYỂN TOÀN BỘ CODE CŨ (BASELINE) VÀO ĐÂY
│   ├── agents/                 # (Cũ) analyzer_agent, sql_agent, chart_agent
│   ├── tools/                  # (Cũ) tools
│   ├── utils/                  # (Cũ) utils
│   ├── output/                 # (Cũ) output chart/html
│   └── app_baseline.py         # Đổi tên từ main.py thành app_baseline.py
│
├── query_gpt_system/           # 👉 HỆ THỐNG MỚI (KIẾN TRÚC UBER)
│   ├── core_agents/            
│   │   ├── prompt_enhancer.py       # [NEW] Mở rộng câu hỏi mơ hồ
│   │   ├── intent_agent.py          # Phân loại → workspace ID
│   │   ├── table_agent.py           # Chọn Top-K tables trong workspace
│   │   ├── column_pruner.py         # Lược bỏ cột không cần thiết
│   │   ├── sql_sample_retriever.py  # [NEW] Retriever cho SQL samples
│   │   ├── genai_gateway.py         # Pipeline tổng hợp sinh SQL
│   │   └── query_explanation_agent.py # [NEW] Giải thích SQL
│   ├── sql_samples/            # [NEW] Kho SQL mẫu
│   │   ├── sql_sample_store.json    # Dữ liệu samples {question, sql, table, ...}
│   │   └── seed_samples.py          # Script tạo samples ban đầu
│   ├── metadata/               
│   │   ├── schema_builder.py        # Quét tự động 68 file CSV
│   │   ├── schema_registry.json     # Metadata cache
│   │   ├── workspaces.json          # [NEW] Workspace mapping
│   │   └── custom_instructions.json # [NEW] Business rules
│   ├── executor/               
│   │   └── sql_engine.py            # Engine DuckDB + Self-Correction
│   ├── output/                 # Output độc lập cho hệ thống mới
│   └── app_query_gpt.py        # Streamlit App CHUẨN cho hệ thống mới
│
├── .env
├── requirements.txt
├── README.md
├── plan.md                     # Tài liệu thiết kế
│
├── run_baseline.sh             # Script tiện ích: streamlit run baseline_system/app_baseline.py
└── run_query_gpt.sh            # Script tiện ích: streamlit run query_gpt_system/app_query_gpt.py
```

### Ưu điểm của kiến trúc này:
1.  **Không gây xung đột (Zero Conflict)**: Hai hệ thống được cô lập hoàn toàn về mặt logic code, file thực thi và output. 
2.  **Chia sẻ chung dữ liệu (Data Sharing)**: Thư mục `data/`, `.env` và `benchmark/` được đặt ở root, giúp cả 2 hệ thống đều tái sử dụng được mà không cần duplicate.
3.  **So sánh dễ dàng (A/B Testing)**: Bạn có thể bật cùng lúc 2 terminal chạy lệnh `streamlit run` để so sánh trải nghiệm, độ trễ và độ chính xác sinh mã SQL giữa Agent System cũ và Uber Query GPT.

## 5. Đánh giá Benchmark cho Hệ thống Mới

Để đo lường hiệu năng của kiến trúc Query GPT so với hệ thống Baseline, thư mục `benchmark/` sẽ được tái sử dụng và tinh chỉnh lại.

### Ý tưởng cốt lõi:
- **Tập dữ liệu**: Vẫn sử dụng `data/InfiAgent/da-dev-questions.jsonl` làm tập test chung, và đối chiếu đáp án từ `da-dev-labels.jsonl`.
- **Tách script chạy benchmark**: Script đánh giá hiện tại (`benchmark/run_eval.py`) đang import cứng code cũ (ví dụ `from agents.analyzer_agent import get_analyzer_agent`). Ta sẽ tách ra làm hai:
  - `benchmark/run_eval_baseline.py` (Script cũ trỏ vào `baseline_system`)
  - `benchmark/run_eval_query_gpt.py` (Script mới trỏ vào `query_gpt_system`)

### Luồng Benchmark của Query GPT:
1. Đọc câu hỏi và Metadata Schema tương ứng từ thư mục `query_gpt_system/metadata/`.
2. (Nếu có) Prompt Enhancer mở rộng câu hỏi.
3. Truyền câu hỏi qua `intent_agent.py` để lấy workspace ID.
4. `table_agent.py` tìm file CSV phù hợp **trong workspace đã chọn**.
5. `column_pruner.py` cắt bớt các cột không liên quan.
6. `sql_sample_retriever.py` tìm Top-K SQL mẫu tương tự từ `sql_sample_store.json`.
7. Đưa qua `genai_gateway.py` (kèm SQL samples + Custom Instructions) để LLM sinh câu trả lời SQL với format chuẩn: `@answer_name[value]`.
8. **Self-Correction**: Nếu SQL fail → retry tối đa 2-3 lần.
9. Extractor trong script benchmark sẽ regex lấy kết quả và so với đáp án ở `da-dev-labels.jsonl`.
10. Xuất kết quả riêng biệt vào `benchmark/results_query_gpt.json` và `benchmark/summary_query_gpt.txt` để đối chiếu với `results.json` của hệ thống cũ.

### Evaluation Metrics (theo blog Uber):
| Metric | Mô tả |
|---|---|
| **Intent Accuracy** | Intent Agent chọn đúng workspace? |
| **Table Overlap Score** | Tỷ lệ tables đúng (0-1). VD: cần `[A, B]`, chọn `[A, C]` → 0.5 |
| **Successful Run** | SQL chạy thành công (không lỗi syntax)? |
| **Run Has Output** | Kết quả trả về > 0 records? |
| **Answer Accuracy** | Đáp án trích xuất khớp với golden answer? |
| **Qualitative Similarity** | LLM-based score so sánh SQL sinh ra vs golden SQL (0-1) |
