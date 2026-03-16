from agno.agent import Agent
from agno.models.openai import OpenAIChat
from tools.sql_tools import execute_sql_on_csv

def get_sql_agent(csv_path: str) -> Agent:
    """
    Returns the SQL Agent responsible for writing and executing SQL queries on the CSV using DuckDB.
    """
    
    # We create a closure so the agent doesn't need to guess the CSV path
    def run_sql(query: str) -> str:
        """
        Thực thi câu lệnh SQL trên file CSV.
        Tên bảng bắt buộc phải là 'data'. Không dùng tên file làm tên bảng.
        Ví dụ: SELECT * FROM data LIMIT 10;
        """
        return execute_sql_on_csv(csv_path, query)
        
    return Agent(
        name="SQL Agent",
        role="Chuyên gia phân tích dữ liệu Data Engineer và viết SQL.",
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[run_sql],
        instructions=[
            "Bạn sẽ nhận được yêu cầu truy xuất dữ liệu từ Analyzer Agent.",
            "Nhiệm vụ của bạn là viết câu lệnh SQL và sử dụng tool `run_sql` để thực thi câu lệnh đó nhằm lấy ra dữ liệu.",
            "LƯU Ý QUAN TRỌNG VỀ SQL: Tên bảng (table name) trong câu lệnh SQL LUÔN LUÔN là 'data', bất kể tên file csv được cung cấp là gì. Ví dụ: SELECT * FROM data;",
            "Nếu kết quả truy vấn bị lỗi, hãy phân tích lỗi, sửa lại câu SQL rồi chạy lại tool.",
            "Bạn có thể chạy thử truy vấn nhiều lần.",
            "Sau khi có kết quả thành công, hãy trình bày lại kết quả dữ liệu một cách rõ ràng dưới dạng Markdown Table hoặc danh sách.",
            "Nếu người dùng (thông qua Analyzer) có yêu cầu chuẩn bị dữ liệu để vẽ biểu đồ, hãy cung cấp kết quả thật chi tiết (toàn bộ các dòng kết quả) ở output của bạn để Chart Agent có thể đọc được.",
        ],
        markdown=True
    )
