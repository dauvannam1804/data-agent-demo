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
            "Nhiệm vụ của bạn là sinh ra một câu SQL DuckDB HỢP LỆ để lấy dữ liệu trả lời câu hỏi.",
            "DuckDB có thể query trực tiếp file CSV như sau: SELECT col1, col2 FROM 'path/to/file.csv' WHERE ...",
            "Nếu người dùng yêu cầu format đặc biệt (Constraints/Format) như @answer_name[value], hãy gán kết quả bằng cách format chuỗi trong SQL, hoặc TRẢ RA dữ liệu thô để format trong Python sau.",
            "CHỈ TRẢ VỀ CÂU LỆNH SQL HOẶC GIẢI THÍCH NGẮN GỌN. KHÔNG BAO BỌC BẰNG MARKDOWN ```sql NẾU KHÔNG CẦN THIẾT. CHỈ TRẢ RA CÂU SQL ĐỂ CHẠY.",
            "LƯU Ý QUAN TRỌNG: Câu SQL phải là một chuỗi query hợp lệ, không chứa các text giải nghĩa nào khác vì hệ thống sẽ lấy trực tiếp text này để thực thi."
        ]
    )

def generate_duckdb_sql(query: str, file_path: str, pruned_columns: list) -> str:
    """
    Given the user query, matched file path, and reduced columns, generate DuckDB SQL.
    """
    agent = get_generator_agent()
    prompt = f"Question: {query}\n\nCSV File Path: {file_path}\n\nAvailable Columns: {pruned_columns}\n\nWrite DuckDB SQL Query:"
    
    response = agent.run(prompt)
    sql_query = response.content.strip()
    
    # Dọn dẹp markdown nếu có
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:]
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3]
        
    return sql_query.strip()
