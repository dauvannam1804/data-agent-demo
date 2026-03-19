from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_generator_agent() -> Agent:
    return Agent(
        name="GenAI Gateway",
        role="Tạo truy vấn SQL DuckDB",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=[
            "Bạn là một AI Data Engineer chuyên viết truy vấn SQL cho DuckDB.",
            "Bạn nhận được:",
            "1. Câu hỏi của người dùng.",
            "2. Đường dẫn file CSV.",
            "3. Danh sách các cột (đã lược gọn) của file CSV.",
            "4. Các ví dụ (few-shot) về câu hỏi và câu SQL tương ứng để tham khảo.",
            "Nhiệm vụ của bạn là sinh ra một câu SQL DuckDB HỢP LỆ để lấy dữ liệu trả lời câu hỏi.",
            "QUY TẮC QUAN TRỌNG VỀ ĐỊNH DANH (IDENTIFIERS) & ĐƯỜNG DẪN:",
            "- LUÔN LUÔN bao bọc tên cột bằng dấu ngoặc kép nếu tên cột có khoảng trắng hoặc là từ khóa SQL (ví dụ: \"Happiness Score\", \"Order\").",
            "- LUÔN LUÔN sử dụng CHÍNH XÁC đường dẫn file được cung cấp trong 'CSV File Path' (ví dụ: giữ nguyên dấu / ở đầu nếu có). KHÔNG tự ý thay đổi đường dẫn.",
            "- Tốt nhất hãy bao bọc TẤT CẢ tên cột bằng dấu ngoặc kép để tránh lỗi cú pháp.",
            "DuckDB có thể query trực tiếp file CSV như sau: SELECT \"Column Name\" FROM '/đường/dẫn/đến/file.csv' WHERE ...",
            "Sử dụng các ví dụ tham khảo để hiểu phong cách viết SQL phù hợp với cấu trúc dữ liệu.",
            "Nếu người dùng yêu cầu format đặc biệt (Constraints/Format) như @answer_name[value], hãy gán kết quả bằng cách format chuỗi trong SQL, hoặc TRẢ RA dữ liệu thô để format trong Python sau.",
            "CHỈ TRẢ VỀ CÂU LỆNH SQL HOẶC GIẢI THÍCH NGẮN GỌN. KHÔNG BAO BỌC BẰNG MARKDOWN ```sql NẾU KHÔNG CẦN THIẾT. CHỈ TRẢ RA CÂU SQL ĐỂ CHẠY.",
            "LƯU Ý QUAN TRỌNG: Câu SQL phải là một chuỗi query hợp lệ, không chứa các text giải nghĩa nào khác vì hệ thống sẽ lấy trực tiếp text này để thực thi."
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
