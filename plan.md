# Kế hoạch phát triển Data Agent dựa trên Kiến trúc Query GPT của Uber

## 1. Phân tích Kiến trúc Query GPT của Uber
Dựa vào sơ đồ cung cấp, kiến trúc Data Agent của Uber giải quyết bài toán Text-to-SQL ở quy mô doanh nghiệp với các thành phần chính sau:

*   **Người dùng & Intent Agent**: Nhận câu hỏi bằng ngôn ngữ tự nhiên từ người dùng. Intent Agent phân tích ý định để phân luồng (ví dụ: truy vấn dữ liệu vận hành hay báo cáo tài chính).
*   **Workspace Retrieval (Lấy không gian làm việc)**: Các bảng dữ liệu được quy hoạch thành các Không gian làm việc (System/Custom Workspaces như Rides, Platform Eng, Metrics, COGS). Hệ thống sẽ tìm workspace phù hợp với ngữ cảnh câu hỏi.
*   **RAG với SQL Samples & Table Agent**:
    *   Sử dụng cơ chế RAG để tìm kiếm các câu truy vấn SQL mẫu (few-shot) tương tự nhằm định hướng tư duy cho LLM.
    *   **Table Agent** đóng vai trò chắt lọc và chọn ra chính xác các bảng (Tables) cần thiết để trả lời câu hỏi.
*   **Metadata Gateway & Get Table Schema**: Đóng vai trò cung cấp metadata, cung cấp lược đồ cấu trúc dữ liệu (tên cột, kiểu dữ liệu, ràng buộc khóa).
*   **Column Prune Agent (Đại lý lược bỏ cột)**: Xóa bớt các cột phi logic/không liên quan đến câu hỏi nhằm tối ưu kích thước Context Window của LLM, tránh nhiễu thông tin.
*   **Custom Instructions**: Cung cấp các hướng dẫn bổ sung đặc thù của doanh nghiệp (ví dụ: quy định xử lý ngày tháng, logic định nghĩa trường "driver license", v.v.).
*   **GenAI Gateway & Azure OpenAI (Generate Query)**: Lắp ghép toàn bộ thông tin thu thập được (Câu hỏi + Schema rút gọn + SQL mẫu + Hướng dẫn) để ra lệnh cho LLM sinh câu truy vấn SQL hoàn chỉnh.
*   **Query Explanation Agent**: Giải nghĩa tác dụng của truy vấn SQL thành ngôn ngữ tự nhiên để người dùng dễ kiểm chứng, đồng thời tự động sinh giải nghĩa để làm giàu kho RAG mẫu.

## 2. Áp dụng cho Dự án hiện tại với `@data/InfiAgent/da-dev-tables`

Dự án hiện tại không phải là một Data Warehouse tập trung (như Hive, Snowflake) mà gồm **68 file dữ liệu dạng CSV rời rạc** (ví dụ: `titanic.csv`, `diamonds.csv`, `weather_train.csv`, `microsoft.csv`...) và bộ câu hỏi mẫu tại `da-dev-questions.jsonl`.

Để mô phỏng kiến trúc Uber, hướng tiếp cận sử dụng Python kết hợp với **DuckDB** (truy vấn SQL thẳng trên file CSV) hoặc **Pandas** (Text-to-Python) là thích hợp nhất. Dưới đây là phương án ánh xạ:

### Ánh xạ Kiến trúc
1.  **Dữ liệu (Workspaces / Tables)**: Mỗi file `.csv` lớn trong thư mục `da-dev-tables` sẽ được coi là một **Table**. File thư mục đóng vai trò như Workspace chứa dữ liệu.
2.  **Intent Agent**: Một Pipeline LLM nhẹ làm nhiệm vụ quét nội dung xem người dùng đang hỏi về chủ đề gì (tài chính, y tế, Titanic, bóng chày) nhằm định hướng tập dữ liệu.
3.  **Table Agent & Metadata Gateway**:
    *   Thay vì gọi qua API Metadata Gateway phức tạp, chúng ta sẽ viết một đoạn mã Python quét 68 file CSV này để sinh ra một kho dữ liệu Metadata lưu trữ dưới dạng file `metadata_registry.json`.
    *   Schema lưu trữ: Tên file, danh sách tên cột, kiểu dữ liệu, và vài giá trị mẫu đầu tiên.
    *   Khi có truy vấn (ví dụ "fare and passengers"), Table Agent sẽ tìm kiếm Semantic Search / Keyword Search trong file Metadata này để quyết định Table dùng là `titanic.csv`.
4.  **Column Prune Agent**:
    *   Các file CSV có thể chứa hàng chục cột. Agent sẽ chạy bước LLM nhỏ để phân định: Đối với câu hỏi về "Fare và Age của Titanic", nó sẽ chỉ trích xuất schema của 2 cột đó, bỏ qua cột "Ticket", "Cabin".
5.  **Generator (GenAI Gateway)**:
    *   Tạo thành một Pipeline Prompt Generator tổng hợp: `System Prompt (Hướng dẫn DuckDB hoặc Pandas)` + `Table Schema đã pruned` + `Câu hỏi hiện tại`. (Không dùng SQL RAG Samples vì các LLM hiện đại như GPT-4o-mini dư sức zero-shot sinh code chính xác từ Data Schema mà không cần example mồi).
6.  **Execution Engine (Xử lý truy vấn)**: Câu lệnh sinh ra sẽ được tự động thực thi bởi máy ở Sandbox sử dụng DuckDB engine.
    *   Vd: `SELECT AVG(fare) FROM 'data/InfiAgent/da-dev-tables/titanic.csv'`
    *   Trả kết quả tự động.

## 3. Lộ trình Triển khai (Roadmap Plan)

Đây là kế hoạch phát triển 3 Giai đoạn:

### Giai đoạn 1: Xây dựng Nền tảng Metadata (Data Foundation)
*   **Task 1**: Phát triển script Quét Metadata (mô phỏng Metadata Gateway). Tự động đọc header 68 file CSV, nhận diện kiểu dữ liệu bằng pandas, trích xuất cấu trúc ra file `schemas.json`.

### Giai đoạn 2: Xây dựng các Core Agents (Routing & Pruning)
*   **Task 2**: Xây dựng Agent Tìm Bảng (Table Agent). Nhận câu hỏi, embed câu hỏi bằng thư viện nhẹ (sentence-transformers), so sánh với mô tả / schema của 68 file để trả về danh sách Top-1 đến Top-2 file CSV tương ứng nhất.
*   **Task 3**: Xây dựng Agent Cắt Cột (Column Prune Agent). Kêu gọi LLM với yêu cầu: "Đây là câu hỏi, đây là toàn bộ cột CSV, hãy liệt kê đúng tên những cột cần giải quyết câu hỏi và bỏ qua phần còn lại".
*   **Task 4**: Xây dựng khối Intent Agent định tuyến các luồng cho hệ thống.

### Giai đoạn 3: Tích hợp Pipeline sinh Sinh Code, Thực thi và Hoàn thiện
*   **Task 5**: Thiết kế GenAI Prompt Pipeline tổng hợp toàn bộ các kết quả từ: Danh sách cột cần, Câu hỏi đầu vào.
*   **Task 6**: Viết Sandboxed Executor: Tự động chạy SQL do LLM sinh ra để lọc kết quả vào một Dataframe tạm thời, xuất ra thông điệp hoặc đáp án chính xác. Trang bị thêm cơ chế tự đọc báo lỗi và fix code tự động (Self-Correction Logic).
*   **Task 7**: Query Explanation Agent - Thiết lập module tuỳ chọn: giải thích cho người dùng là "Tại sao câu SQL lại có cấu trúc như vậy" dựa trên yêu cầu ban đầu.

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
│   │   ├── intent_agent.py     
│   │   ├── table_agent.py      
│   │   ├── column_pruner.py    
│   │   └── genai_gateway.py    
│   ├── metadata/               
│   │   ├── schema_builder.py   # Quét tự động 68 file CSV
│   │   └── schema_registry.json# Metadata cache
│   ├── executor/               
│   │   └── sql_engine.py       # Engine DuckDB
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
2. Truyền câu hỏi qua `intent_agent.py` và `table_agent.py` để tìm file CSV phù hợp.
3. Đưa qua `genai_gateway.py` để LLM sinh câu trả lời SQL với format chuẩn: `@answer_name[value]`.
4. Extractor trong script benchmark sẽ regex lấy kết quả và so với đáp án ở `da-dev-labels.jsonl`.
5. Xuất kết quả riêng biệt vào `benchmark/results_query_gpt.json` và `benchmark/summary_query_gpt.txt` để đối chiếu với `results.json` của hệ thống cũ.
