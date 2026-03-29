from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_generator_agent() -> Agent:
    return Agent(
        name="GenAI Gateway",
        role="Tạo truy vấn SQL DuckDB",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=[
            "Bạn là một AI Data Engineer chuyên viết truy vấn SQL cho DuckDB.",
            "Nhiệm vụ của bạn là sinh ra một câu SQL DuckDB HỢP LỆ để lấy dữ liệu trả lời câu hỏi.",
            "QUY TẮC CÚ PHÁP DUCKDB (BẮT BUỘC):",
            "1. CỘT (COLUMNS): LUÔN LUÔN bao bọc tên cột trong dấu ngoặc kép (DOUBLE QUOTES) (ví dụ: \"Happiness Score\", \"Mar.2020\").",
            "   - KHÔNG bao giờ dùng dấu gạch chéo ngược để escape ngoặc kép (SAI: \\\"column\\\"). LUÔN dùng dấu ngoặc kép đơn thuần (\").",
            "2. ĐƯỜNG DẪN FILE (TABLES): LUÔN bao bọc đường dẫn file trong dấu nháy đơn (SINGLE QUOTES) (ví dụ: '/data-code/file.csv').",
            "   - LUÔN sử dụng CHÍNH XÁC đường dẫn được cung cấp trong 'CSV File Path'.",
            "   - KHÔNG ĐƯỢC xóa dấu gạch chéo (/) ở đầu đường dẫn nếu có (Ví dụ SAI: 'home/namdv/...', ĐÚNG: '/home/namdv/...').",
            "   - KHÔNG dùng dấu ngoặc kép (double quotes) cho đường dẫn file.",
            "3. LỖI LỒNG GHÉP (NESTED AGGREGATES): DuckDB KHÔNG cho phép lồng hàm nhóm (Ví dụ SAI: AVG(SUM(col))).",
            "   - HÃY SỬ DỤNG 'WITH' clause (CTE) hoặc Subquery để chia các bước tính toán phức tạp (như tính phương sai, độ lệch chuẩn, chuẩn hóa dữ liệu).",
            "4. ÁNH XẠ HÀM (FUNCTION MAPPING):",
            "   - Sử dụng 'stddev' hoặc 'stddev_samp' thay vì 'stdev'.",
            "   - Sử dụng 'quantile_cont(column, probe)' thay vì 'percentile_cont(...) WITHIN GROUP (...)'.",
            "   - Không tự chế các hàm như 'PVAL'. Nếu cần tính tương quan, hãy dùng 'CORR(col1, col2)'.",
            "5. ĐẦU RA: CHỈ TRẢ VỀ CÂU SQL HOẶC GIẢI THÍCH NGẮN GỌN. KHÔNG BAO BỌC BẰNG MARKDOWN ```sql.",
            "LƯU Ý QUAN TRỌNG: Câu SQL phải là một chuỗi query hợp lệ, thực thi được ngay trên DuckDB CLI."
        ]
    )

def generate_duckdb_sql(query: str, file_path: str, pruned_columns: list, sql_samples: list = None) -> str:
    """
    Given the user query, matched file path, and reduced columns, generate DuckDB SQL.
    Supports optional few-shot SQL samples from RAG.
    """
    agent = get_generator_agent()
    
    # Chuẩn bị context bổ sung từ Few-shot samples
    samples_context = ""
    if sql_samples:
        samples_context = "\nVí dụ tham khảo (Few-shot samples):\n"
        for i, s in enumerate(sql_samples):
            samples_context += f"Q{i+1}: {s['question']}\n"
            samples_context += f"SQL{i+1}: {s['sql']}\n---\n"
    
    prompt = f"Question: {query}\n\nCSV File Path: {file_path}\n"
    if samples_context:
        prompt += samples_context
    prompt += f"\nAvailable Columns: {pruned_columns}\n\nWrite DuckDB SQL Query:"
    
    response = agent.run(prompt)
    sql_query = response.content.strip()
    
    # Dọn dẹp markdown nếu có
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:]
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3]
        
    return sql_query.strip()
